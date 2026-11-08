"""On-demand plugin workers using private files, without an outer service or port."""
from __future__ import annotations

import asyncio
import json
import os
from pathlib import Path
import shutil
import tempfile
import threading
import time
import uuid

from helpers.sandbox import SandboxError, SandboxMount, get_manager


class SandboxWorker:
    def __init__(self, plugin: str, *, idle_seconds: float | None = 120):
        self.plugin = plugin
        self.name = 'service-' + plugin.lstrip('_').replace('_', '-')
        self.idle_seconds = idle_seconds
        self.lock = threading.RLock()
        self.timer: threading.Timer | None = None
        self.ready = False
        self.generation = 0
        self.busy = False
        self.mounts: list[SandboxMount] = []
        self.support_files: dict[str, Path] = {}
        self._progress_lock = threading.Lock()
        self._progress = {'state': 'idle', 'stage': 'idle', 'message': 'Not started'}
        self._progress_manager = None
        self._boot_id = None
        self._last_log = None

    def _set_progress(self, state: str, stage: str, message: str):
        with self._progress_lock:
            now = time.time()
            if stage == 'sandbox':
                self._boot_id = None
            started = now if stage == 'sandbox' else self._progress.get('started_at', now)
            self._progress = {'state': state, 'stage': stage, 'message': message,
                              'started_at': started, 'updated_at': now, 'stage_started_at': now}

    def status(self) -> dict:
        """Read bounded progress without waiting on the setup/request lock or starting a guest."""
        with self._progress_lock:
            if self._progress['state'] == 'starting' and self._progress_manager and self._boot_id:
                manager = self._progress_manager
                try:
                    progress = json.loads(manager.read_file(self.name, 'var/lib/a0-worker/progress.json', limit=4096))
                    if isinstance(progress, dict) and progress.get('boot') == self._boot_id:
                        stage, message = progress.get('stage'), progress.get('message')
                        if isinstance(stage, str) and isinstance(message, str) and stage != self._progress['stage']:
                            self._progress.update(stage=stage[:64], message=message[:240],
                                                  stage_started_at=time.time(), updated_at=time.time())
                        log = manager.read_file(self.name, 'var/lib/a0-worker/install.log', limit=4096)
                        if log != self._last_log:
                            self._last_log = log
                            self._progress['updated_at'] = time.time()
                except (OSError, ValueError, SandboxError):
                    pass
            result = dict(self._progress)
        now = time.time()
        end = now if result['state'] == 'starting' else result.get('updated_at', now)
        result['elapsed_seconds'] = max(0, int(end - result.get('started_at', end)))
        result['stage_seconds'] = max(0, int(end - result.get('stage_started_at', end)))
        result['quiet_seconds'] = max(0, int(end - result.get('updated_at', end)))
        return result

    def _paths(self):
        manager = get_manager()
        # This directory is masked in usr mounts and never exposed to other guests.
        request_dir = manager.config.instances_dir / '.worker-inputs' / self.name
        request_dir.mkdir(parents=True, exist_ok=True, mode=0o700)
        return manager, request_dir

    def start(self, cancel: threading.Event | None = None):
        with self.lock:
            try:
                return self._start(cancel)
            except BaseException:
                self._set_progress('error', 'error', 'Sandbox setup failed or was cancelled; retry to resume installation')
                raise

    def _start(self, cancel: threading.Event | None):
        manager, request_dir = self._paths()
        if self.timer:
            self.timer.cancel()
        if self.ready and manager.is_running(self.name):
            return manager
        self.ready = False
        self._set_progress('starting', 'sandbox', 'Initializing sandbox')
        root = Path(__file__).resolve().parents[1]
        plugin_dir = root / 'plugins' / self.plugin
        command = ['/bin/sh', '/worker/boot.sh']
        support = request_dir / 'support'
        support.mkdir(exist_ok=True)
        for filename, source in self.support_files.items():
            if Path(filename).name != filename:
                raise ValueError('Invalid support filename')
            shutil.copyfile(source, support / filename)
        mounts = [SandboxMount(plugin_dir, '/plugin'),
                  SandboxMount(root / 'plugins/_sandboxing/sandbox', '/worker'),
                  SandboxMount(request_dir, '/request'),
                  SandboxMount(support, '/support'), *self.mounts]
        boot_id = uuid.uuid4().hex
        with self._progress_lock:
            self._boot_id = boot_id
            self._progress_manager = manager
            self._last_log = None
        self._write_request(request_dir, {'boot': boot_id})
        if (manager.config.instances_dir / self.name / 'metadata.json').exists():
            info = manager.inspect(self.name)
            if not info.service or info.ownership.get('plugin_id') != self.plugin:
                raise SandboxError('Sandbox name is already owned by another caller')
            manager.stop(self.name)
            manager.set_mounts(self.name, mounts)
            manager.set_command(self.name, command)
            manager.start(self.name)
        else:
            manager.create(
                self.name, sandbox_type='permanent', service=True,
                standalone=False, share_usr=False, network='host',
                ownership={'plugin_id': self.plugin}, command=command,
                mounts=mounts,
            )
        deadline = time.monotonic() + 1800
        state_check = 0
        while time.monotonic() < deadline:
            if cancel and cancel.is_set():
                manager.stop(self.name)
                raise SandboxError('Sandbox setup cancelled')
            try:
                status = json.loads(manager.read_file(self.name, 'var/lib/a0-worker/ready.json'))
                if status.get('boot') == boot_id:
                    self.ready = True
                    self.generation += 1
                    self._set_progress('ready', 'ready', 'Sandbox ready')
                    return manager
            except (OSError, ValueError):
                pass
            if time.monotonic() >= state_check:
                if not manager.is_running(self.name):
                    raise SandboxError(f'{self.plugin} setup exited; see its sandbox /var/lib/a0-worker/install.log')
                state_check = time.monotonic() + 1
            time.sleep(.2)
        manager.stop(self.name)
        raise SandboxError(f'{self.plugin} dependency setup timed out')

    @staticmethod
    def _write_request(directory: Path, payload: dict):
        fd, path = tempfile.mkstemp(dir=directory)
        try:
            with os.fdopen(fd, 'w') as stream:
                json.dump(payload, stream)
            os.replace(path, directory / 'request.json')
        finally:
            Path(path).unlink(missing_ok=True)

    def call(self, payload: dict, *, timeout: float = 120, cancel: threading.Event | None = None,
             mounts: list[SandboxMount] | None = None):
        with self.lock:
            self.busy = True
            failed = False
            request_id = None
            try:
                if mounts is not None and self.mounts != mounts:
                    self.stop()
                    self.mounts = mounts
                manager = self.start(cancel)
                _, directory = self._paths()
                request_id = uuid.uuid4().hex
                self._write_request(directory, {'id': request_id, 'payload': payload})
                deadline = time.monotonic() + timeout
                state_check = time.monotonic() + 1
                while time.monotonic() < deadline:
                    if cancel and cancel.is_set():
                        raise SandboxError('Sandbox request cancelled')
                    try:
                        result = json.loads(manager.read_file(self.name, 'var/lib/a0-worker/response.json', limit=128 * 1024 * 1024))
                    except (OSError, ValueError):
                        result = {}
                    if result.get('id') == request_id:
                        if 'error' in result:
                            raise SandboxError(str(result['error']))
                        return result['result']
                    if time.monotonic() >= state_check:
                        if not manager.is_running(self.name):
                            raise SandboxError(f'{self.plugin} worker exited during the request')
                        state_check = time.monotonic() + 1
                    time.sleep(.05)
                raise SandboxError(f'{self.plugin} request timed out after {timeout:g}s')
            except BaseException:
                failed = True
                raise
            finally:
                self.busy = False
                _, directory = self._paths()
                self._write_request(directory, {})
                if self.ready and request_id:
                    # Let the guest discard speech/document results before stopping.
                    deadline = time.monotonic() + 1
                    while time.monotonic() < deadline:
                        try:
                            if json.loads(manager.read_file(self.name, 'var/lib/a0-worker/ack.json')).get('id') == request_id:
                                break
                        except (OSError, ValueError, SandboxError):
                            pass
                        time.sleep(.05)
                if failed:
                    self.stop()
                elif self.ready and self.idle_seconds is not None:
                    if self.idle_seconds == 0:
                        self.stop()
                    else:
                        self.timer = threading.Timer(self.idle_seconds, self.stop)
                        self.timer.daemon = True
                        self.timer.start()

    async def acall(self, payload: dict, *, timeout: float = 120, mounts: list[SandboxMount] | None = None):
        cancel = threading.Event()
        task = asyncio.create_task(asyncio.to_thread(self.call, payload, timeout=timeout, cancel=cancel, mounts=mounts))
        try:
            return await asyncio.shield(task)
        except asyncio.CancelledError:
            cancel.set()
            await asyncio.gather(task, return_exceptions=True)
            raise

    async def aprepare(self):
        """Keep first-use installation outside a caller's processing deadline."""
        cancel = threading.Event()
        task = asyncio.create_task(asyncio.to_thread(self.start, cancel))
        try:
            await asyncio.shield(task)
        except asyncio.CancelledError:
            cancel.set()
            await asyncio.gather(task, return_exceptions=True)
            raise

    def stop(self):
        with self.lock:
            if self.timer:
                self.timer.cancel()
                self.timer = None
            manager, _ = self._paths()
            if (manager.config.instances_dir / self.name / 'metadata.json').exists():
                manager.stop(self.name)
            self.ready = False
            if self._progress['state'] != 'error':
                self._set_progress('idle', 'idle', 'Sandbox stopped')
