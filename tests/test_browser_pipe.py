"""Real subprocess pipes cover multiplexing and cancellation without a browser SDK."""
import asyncio
import json
from pathlib import Path
from types import SimpleNamespace
import sys
from unittest.mock import AsyncMock
import pytest
from plugins._browser.helpers import sandbox


@pytest.mark.asyncio
async def test_real_pipe_concurrency_cleanup_ack_and_frame_backpressure(tmp_path):
    script = tmp_path / 'fixture.py'
    script.write_text('''
import asyncio, contextvars, runpy, sys, types
from pathlib import Path
sys.path.insert(0, str(Path(sys.argv[1]).resolve().parents[3]))
class Core:
    def __init__(self, *args, **kwargs):
        self.request_context_id = contextvars.ContextVar('context')
        self.request_options = contextvars.ContextVar('options')
        self.request_uploads = contextvars.ContextVar('uploads')
        self.interactive_view = types.SimpleNamespace(close=lambda: None)
        self.cleaned = False
        self.on_startup = kwargs['on_startup']
    async def progress(self):
        self.on_startup('browser', 'Launching Chromium')
        await asyncio.sleep(.01)
        return True
    async def echo(self):
        return [self.request_context_id.get(), self.cleaned]
    async def slow(self):
        try:
            await asyncio.sleep(60)
        finally:
            await asyncio.sleep(.03)
            self.cleaned = True
    async def attach_screencast_consumer(self, stream, consume, stopped):
        await consume({'pixels': 'fixture'})
        return 'frame acknowledged'
    async def close(self): pass
sys.modules['plugins._browser.sandbox.runtime'] = types.SimpleNamespace(_BrowserRuntimeCore=Core)
sys.modules['plugins._browser.sandbox.display'] = types.SimpleNamespace()
runpy.run_path(sys.argv[1], run_name='__main__')
''')
    process = await asyncio.create_subprocess_exec(sys.executable, str(script),
        str(Path(sandbox.__file__).parents[1] / 'sandbox/rpc.py'),
        stdin=asyncio.subprocess.PIPE, stdout=asyncio.subprocess.PIPE)
    async def send(value):
        process.stdin.write(json.dumps(value).encode() + b'\n')
        await process.stdin.drain()
    async def receive():
        return json.loads(await asyncio.wait_for(process.stdout.readline(), 3))
    async def request(id, method, **kwargs):
        await send({'id': id, 'method': method, 'context_id': id, 'args': [], 'kwargs': kwargs})
    try:
        await request('init', 'init', keyboard={})
        assert (await receive())['result'] is True
        await request('progress', 'progress')
        assert await receive() == {'startup': {'stage': 'browser', 'message': 'Launching Chromium'}}
        assert (await receive())['result'] is True
        await request('slow', 'slow')
        await request('other', 'echo')
        assert await receive() == {'id': 'other', 'result': ['other', False]}
        await send({'cancel': 'slow'})
        assert await receive() == {'id': 'slow', 'cancelled': True}
        await request('after', 'echo')
        assert (await receive())['result'] == ['after', True]
        await send({'id': 'frame', 'method': 'attach_screencast_consumer', 'context_id': 'ctx', 'args': ['s'], 'kwargs': {}})
        frame = await receive()
        assert frame['frame'] == {'pixels': 'fixture'}
        await request('while-frame', 'echo')
        assert (await receive())['id'] == 'while-frame'
        await send({'frame_ack': frame['frame_id']})
        assert await receive() == {'id': 'frame', 'result': 'frame acknowledged'}
        process.stdin.close()
        assert await asyncio.wait_for(process.wait(), 3) == 0
    finally:
        if process.returncode is None:
            process.kill()
            await process.wait()


@pytest.mark.asyncio
@pytest.mark.parametrize('failure', [RuntimeError('fixture setup failure'), asyncio.CancelledError()])
async def test_setup_failure_cleans_owned_worker_before_retry(monkeypatch, tmp_path, failure):
    monkeypatch.setattr(sandbox, 'files', SimpleNamespace(get_abs_path=lambda *parts: str(tmp_path.joinpath(*parts))))
    connection = sandbox.BrowserConnection('fixture')
    connection.profile = tmp_path / 'profile'
    connection.downloads = tmp_path / 'downloads'
    monkeypatch.setattr(sandbox.worker, 'aprepare', AsyncMock(side_effect=failure))
    cleanup = AsyncMock()
    monkeypatch.setattr(connection, 'close', cleanup)
    with pytest.raises(type(failure)):
        await connection.start('fixture')
    cleanup.assert_awaited_once()
    assert (tmp_path / 'tmp/browser/sessions/shared').is_dir()
    assert connection.startup_status()['state'] == 'error'


def test_browser_progress_distinguishes_dependency_readiness_from_chromium(monkeypatch):
    connection = sandbox.BrowserConnection('fixture')
    monkeypatch.setattr(sandbox.worker, 'status', lambda: {'state': 'ready', 'stage': 'ready'})
    assert connection.startup_status()['state'] == 'idle'
    connection.startup_progress('sandbox', 'Preparing browser sandbox')
    assert connection.startup_status()['state'] == 'starting'
    for stage, step in [('sandbox', 1), ('installing', 2), ('viewer', 2), ('chromium', 3)]:
        monkeypatch.setattr(sandbox.worker, 'status', lambda stage=stage: {'state': 'starting', 'stage': stage})
        status = connection.startup_status()
        assert (status['step'], status['steps']) == (step, 6)
    for stage, step in [('display', 4), ('browser', 5), ('tabs', 6), ('ready', 6)]:
        connection.startup_progress(stage, 'fixture stage')
        status = connection.startup_status()
        assert (status['step'], status['steps']) == (step, 6)
        assert status['state'] == ('ready' if stage == 'ready' else 'starting')


@pytest.mark.asyncio
async def test_browser_status_tracks_pending_requests_per_context_without_waiting(monkeypatch):
    from plugins._browser.helpers import runtime
    from plugins._browser.api import ws_browser
    connection = sandbox.BrowserConnection('fixture')
    connection.startup_progress('ready', 'Browser is running')
    monkeypatch.setattr(runtime, '_shared_runtime', SimpleNamespace(_core=connection))
    monkeypatch.setattr(runtime, '_startup_requests', {})
    entered, release = asyncio.Event(), asyncio.Event()
    handler = object.__new__(ws_browser.WsBrowser)
    async def opening(data, sid):
        entered.set()
        await release.wait()
        raise RuntimeError('fixture failure')
    monkeypatch.setattr(handler, '_command', opening)
    task = asyncio.create_task(handler.process('browser_viewer_command', {'context_id':'fixture', 'command':'open'}, 'sid'))
    try:
        await entered.wait()
        status = (await handler.process('browser_startup_status', {'context_id':'fixture'}, 'sid'))['startup']
        assert status['state'] == 'ready' and status['pending'] is True
        assert runtime.browser_startup_status('other')['pending'] is False
        with runtime.browser_startup_request('fixture'):
            release.set()
            with pytest.raises(RuntimeError, match='fixture failure'):
                await task
            assert runtime.browser_startup_status('fixture')['pending'] is True
        assert runtime.browser_startup_status('fixture')['pending'] is False
        assert runtime._startup_requests == {}
    finally:
        release.set()
        await asyncio.gather(task, return_exceptions=True)
