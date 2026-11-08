"""Browser RPC client. No browser SDK or bundled driver executes in the host."""
import asyncio
import base64
import contextlib
import json
import mimetypes
from pathlib import Path
import re
import shutil
import uuid

from helpers.sandbox_worker import SandboxWorker
from helpers.sandbox import SandboxMount
from helpers import files, kvp, chat_media, virtual_desktop
from helpers.errors import RepairableException

worker = SandboxWorker('_browser', idle_seconds=None)
root = Path(__file__).resolve().parents[3]
worker.support_files = {
    'native_display.py': root / 'helpers/native_display.py',
    'errors.py': root / 'helpers/errors.py',
    'build-gui.sh': root / 'plugins/_desktop/build/gui.sh',
    'bundle-gui.sh': root / 'plugins/_desktop/build/bundle-gui.sh',
}
MAX_MESSAGE = 128 * 1024 * 1024


def upload_request(path='', paths=None):
    if paths is not None and not isinstance(paths, list):
        raise ValueError('paths must be a list of file paths')
    selected = [*(paths or []), *([path] if str(path or '').strip() else [])]
    result = {'paths': [], 'files': []}
    for item in selected:
        raw = str(item or '').strip()
        if not raw:
            continue
        candidate = Path(files.fix_dev_path(raw) if raw.startswith('/a0/') else raw).expanduser()
        if not candidate.is_absolute():
            candidate = Path(files.get_abs_path(str(candidate)))
        candidate = candidate.resolve()
        if not candidate.is_file():
            raise FileNotFoundError(f'Upload file does not exist: {candidate}')
        result['paths'].append(str(candidate))
        result['files'].append({'name': candidate.name, 'mimeType': mimetypes.guess_type(candidate.name)[0] or 'application/octet-stream',
                                'buffer': base64.b64encode(candidate.read_bytes()).decode()})
    if not result['files']:
        raise ValueError('upload_file requires path or non-empty paths')
    return result


class BrowserConnection:
    def __init__(self, context_id):
        self.context_id = context_id
        self.process = None
        self.reader_task = None
        self.pending = {}
        self.consumers = {}
        self.frame_tasks = set()
        self.start_lock = asyncio.Lock()
        self.write_lock = asyncio.Lock()
        self.token = 'browser-' + uuid.uuid4().hex
        self.profile = Path(files.get_abs_path('tmp/browser/sessions/shared'))
        self.downloads = Path(files.get_abs_path('usr/downloads/browser'))

    async def start(self, context_id):
        async with self.start_lock:
            if self.process and self.process.returncode is None and self.reader_task and not self.reader_task.done():
                return
            if self.process:
                await self.close()
            from plugins._browser.helpers.config import get_browser_config, build_browser_launch_config
            config = get_browser_config()
            launch = build_browser_launch_config(config)
            self.profile.parent.mkdir(parents=True, exist_ok=True)
            self.adopt_legacy_profile(context_id)
            self.profile.mkdir(exist_ok=True)
            self.downloads.mkdir(parents=True, exist_ok=True)
            worker.mounts = [SandboxMount(self.profile.resolve(), str(self.profile), False),
                             SandboxMount(self.downloads.resolve(), str(self.downloads), False)]
            worker.mounts.extend(SandboxMount(Path(path).resolve(), path) for path in launch['extensions']['active_paths'])
            display_bundle = Path('/usr/local/lib/tuxee-gui')
            if (display_bundle / 'bin/tuxee-Xvnc').is_file():
                worker.mounts.append(SandboxMount(display_bundle, '/opt/tuxee-gui'))
            try:
                await worker.aprepare()
                manager, _ = worker._paths()
                command = manager.process_command(worker.name, ['/opt/runtime/bin/python', '/plugin/sandbox/rpc.py'])
                self.process = await asyncio.create_subprocess_exec(*command, stdin=asyncio.subprocess.PIPE,
                    stdout=asyncio.subprocess.PIPE, stderr=None, limit=MAX_MESSAGE)
                self.reader_task = asyncio.create_task(self.read())
                from plugins._browser.helpers.runtime import _load_browser_tabs
                exists, tabs = _load_browser_tabs()
                await self.request('init', context_id, [], {'config': config, 'launch_config': launch,
                    'profile': str(self.profile), 'downloads': str(self.downloads), 'tabs': tabs if exists else None,
                    'keyboard': {'layout': config.get('keyboard_layout', ''), 'variant': config.get('keyboard_variant', '')}})
            except BaseException:
                await self.close()
                raise

    def adopt_legacy_profile(self, context_id):
        legacy = self.profile.parent / (re.sub(r'[^a-zA-Z0-9_.-]+', '_', context_id).strip('._') or 'default')
        if not self.profile.exists() and legacy.is_dir() and legacy != self.profile:
            legacy.rename(self.profile)

    async def send(self, payload):
        data = json.dumps(payload, separators=(',', ':')).encode() + b'\n'
        if len(data) > MAX_MESSAGE:
            raise ValueError('Browser request exceeds the IPC limit')
        async with self.write_lock:
            self.process.stdin.write(data)
            await self.process.stdin.drain()

    async def read(self):
        try:
            while line := await self.process.stdout.readline():
                message = json.loads(line)
                if 'tabs' in message:
                    kvp.set_persistent('browser_open_tabs', {'version': 1, 'tabs': message['tabs']})
                elif 'stream' in message:
                    task = asyncio.create_task(self.deliver_frame(message))
                    self.frame_tasks.add(task)
                    task.add_done_callback(self.frame_tasks.discard)
                else:
                    future = self.pending.get(message.get('id'))
                    if future and not future.done():
                        future.set_result(message)
        finally:
            for future in self.pending.values():
                if not future.done():
                    future.set_exception(ConnectionError('Browser worker pipe closed; operation outcome is unconfirmed'))

    async def deliver_frame(self, message):
        consumer = self.consumers.get(message['stream'])
        try:
            if consumer:
                callback = consumer[1] if message.get('stopped') else consumer[0]
                if callback:
                    result = callback() if message.get('stopped') else callback(message['frame'])
                    if asyncio.iscoroutine(result):
                        await result
        finally:
            if message.get('frame_id'):
                with contextlib.suppress(Exception):
                    await self.send({'frame_ack': message['frame_id']})

    async def request(self, method, context_id, args, kwargs, options=None, uploads=None):
        request_id = uuid.uuid4().hex
        future = self.pending[request_id] = asyncio.get_running_loop().create_future()
        try:
            await self.send({'id': request_id, 'method': method, 'context_id': context_id,
                             'args': args, 'kwargs': kwargs, 'options': options or {}, 'uploads': uploads or {}})
            try:
                response = await asyncio.wait_for(asyncio.shield(future), 180)
            except (asyncio.CancelledError, asyncio.TimeoutError):
                await self.send({'cancel': request_id})
                try:
                    await asyncio.wait_for(asyncio.shield(future), 20)
                except Exception as exc:
                    raise RuntimeError('Browser cancellation cleanup was not confirmed') from exc
                raise
            if 'error' in response:
                errors = {'TimeoutError': TimeoutError, 'ValueError': ValueError, 'KeyError': KeyError,
                          'RepairableException': RepairableException}
                raise errors.get(response.get('error_type'), RuntimeError)(response['error'])
            if response.get('cancelled'):
                raise asyncio.CancelledError()
            return response['result']
        finally:
            self.pending.pop(request_id, None)

    async def call(self, context_id, method, *args, **kwargs):
        from plugins._browser.helpers.config import get_browser_config
        from agent import AgentContext
        from plugins._browser.helpers.runtime import has_restorable_browser_tabs
        if not self.process and method in {'list', 'list_all', 'close_context'} and not has_restorable_browser_tabs(context_id):
            return {'browsers': [], 'last_interacted_browser_id': None, 'last_interacted_browser_ids': {}} if method != 'close_context' else None
        await self.start(context_id)
        context = AgentContext.get(context_id)
        options = get_browser_config(agent=context.agent0 if context else None)
        uploads = {}
        calls = args[0] if method == 'multi' else []
        selected = calls if method == 'multi' else ([{'action': method, 'path': args[2] if len(args) > 2 else kwargs.get('path', ''),
                     'paths': args[3] if len(args) > 3 else kwargs.get('paths')}] if method == 'upload_file' else [])
        for call in selected:
            if str(call.get('action') or '').strip().lower().replace('-', '_') == 'upload_file':
                path, paths = call.get('path') or '', call.get('paths')
                try:
                    uploads[json.dumps([path, paths])] = upload_request(path, paths)
                except Exception as exc:
                    uploads[json.dumps([path, paths])] = {'error': str(exc)}
        if method == 'attach_screencast_consumer':
            self.consumers[args[0]] = (args[1], args[2] if len(args) > 2 else None)
            args = args[:1]
        result = await self.request(method, context_id, args, kwargs, options, uploads)
        if method == 'stop_screencast':
            self.consumers.pop(args[0], None)
        if method == 'screenshot_file':
            result = self.save_screenshot(result, kwargs.get('path', ''))
        if method == 'multi':
            for call, item in zip(calls, result):
                if item.get('ok') and str(call.get('action') or '').strip().lower() == 'screenshot':
                    item['result'] = self.save_screenshot(item['result'], call.get('path', ''))
        if method == 'interactive_viewer' and result.get('available'):
            self.loop = asyncio.get_running_loop()
            virtual_desktop.register_session(token=self.token, host='127.0.0.1', port=int(result['port']),
                                             owner='browser-vnc', title='Browser', resize=self.resize, password=result.pop('password'))
            result.update(token=self.token, url=f'/browser/vnc/session/{self.token}/index.html')
        return result

    def resize(self, width, height):
        future = asyncio.run_coroutine_threadsafe(
            self.request('resize_display', self.context_id, [width, height], {}), self.loop)
        try:
            return future.result(timeout=20)
        except Exception:
            future.cancel()
            return {'ok': False, 'error': 'Browser resize failed'}

    def save_screenshot(self, result, path):
        image = base64.b64decode(result.pop('image'), validate=True)
        if not str(path or '').strip():
            saved = chat_media.save_image_bytes(context_id=result['context_id'], payload=image,
                mime_type=result['mime'], category='screenshots', source='browser',
                preferred_name=f"browser-{result['browser_id']}.jpg")
            result.update(path=saved.path, a0_path=saved.a0_path, ephemeral=False, chat_scoped=True)
            load_path = saved.a0_path
        else:
            output = Path(files.fix_dev_path(path) if path.startswith('/a0/') else path)
            if not output.is_absolute():
                output = Path(files.get_abs_path(str(output)))
            if output.suffix.lower() not in {'.jpg', '.jpeg', '.png'}:
                output = output.with_name(output.name + '.jpg')
            output.parent.mkdir(parents=True, exist_ok=True)
            output.write_bytes(image)
            load_path = str(output)
            result.update(path=str(output), a0_path=files.normalize_a0_path(str(output)))
        result['vision_load'] = {'tool_name': 'vision_load', 'tool_args': {'paths': [load_path]}}
        return result

    async def close(self, delete_profile=False):
        if self.process:
            if self.process.returncode is None:
                if self.reader_task and not self.reader_task.done():
                    with contextlib.suppress(Exception):
                        await asyncio.wait_for(self.request('close', self.context_id, [], {'delete_profile': delete_profile}), 20)
                self.process.stdin.close()
                try:
                    await asyncio.wait_for(self.process.wait(), 15)
                except asyncio.TimeoutError:
                    self.process.kill()
                    await self.process.wait()
            if self.reader_task:
                await asyncio.gather(self.reader_task, return_exceptions=True)
            self.process = None
        for task in list(self.frame_tasks):
            task.cancel()
        await asyncio.gather(*list(self.frame_tasks), return_exceptions=True)
        virtual_desktop.unregister_session(self.token)
        self.consumers.clear()
        await asyncio.to_thread(worker.stop)
        if delete_profile:
            shutil.rmtree(self.profile, ignore_errors=True)
