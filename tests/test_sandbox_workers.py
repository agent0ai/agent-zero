from __future__ import annotations

import asyncio
import json
import subprocess
import sys
from pathlib import Path
import threading
from concurrent.futures import ThreadPoolExecutor
from types import SimpleNamespace

import pytest

from helpers.sandbox_worker import SandboxWorker
import helpers.sandbox_worker as worker_module
from plugins._sandboxing.helpers.manager import SandboxError, SandboxMount
from tests.test_sandboxing import manager
from tests.test_sandbox_services import create_disk


def test_worker_mount_survives_plugin_reload():
    # Namespace purging in-process would replace other tests' active plugins.
    subprocess.run([sys.executable, "-c", """
from pathlib import Path
from helpers import plugins, sandbox_worker
mount = sandbox_worker.SandboxMount(Path('/tmp'), '/request')
plugins.refresh_plugin_modules(['_kokoro_tts'])
from plugins._sandboxing.helpers.manager import SandboxManager, SandboxError
manager = SandboxManager.__new__(SandboxManager)
assert manager._normalize_mounts([mount]) == (mount,)
assert SandboxError is sandbox_worker.SandboxError
"""], check=True, cwd=Path(__file__).resolve().parents[1])


@pytest.fixture
def worker(tmp_path, monkeypatch):
    instance = tmp_path / 'instances/service-test'
    instance.mkdir(parents=True)
    (instance / 'metadata.json').write_text('{}')
    exchange = tmp_path / 'input'
    exchange.mkdir()
    stopped = []
    fake = SimpleNamespace(config=SimpleNamespace(instances_dir=instance.parent),
                           inspect=lambda name: SimpleNamespace(service=True, ownership={"plugin_id": "_test"}),
                           stop=lambda name: stopped.append(name))
    result = SandboxWorker('_test', idle_seconds=None)
    def start(cancel=None, *, mounts=None):
        result.ready = True
        return fake
    monkeypatch.setattr(result, '_paths', lambda: (fake, exchange))
    monkeypatch.setattr(result, 'start', start)
    original_write = result._write_request
    last_id = ['']
    def write(directory, payload):
        if payload.get('id'):
            last_id[0] = payload['id']
        original_write(directory, payload)
        if not payload:
            fake.read_file = lambda *a, **kw: json.dumps({'id': last_id[0]})
    monkeypatch.setattr(result, '_write_request', write)
    return result, fake, exchange, stopped


def test_worker_returns_only_matching_response_and_clears_input(worker):
    service, manager, exchange, stopped = worker
    reads = []
    def read(*args, **kwargs):
        request = json.loads((exchange / 'request.json').read_text())
        reads.append(request)
        if len(reads) == 1:
            return json.dumps({'id': 'previous-request', 'result': 'wrong'})
        return json.dumps({'id': request['id'], 'result': request['payload']})
    manager.read_file = read
    assert service.call({'text': 'private'}) == {'text': 'private'}
    assert json.loads((exchange / 'request.json').read_text()) == {}
    assert stopped == []


def test_worker_error_and_timeout_stop_guest(worker):
    service, manager, exchange, stopped = worker
    manager.read_file = lambda *a, **kw: json.dumps({
        'id': json.loads((exchange / 'request.json').read_text())['id'], 'error': 'parser failed'})
    with pytest.raises(SandboxError, match='parser failed'):
        service.call({})
    assert not service.ready and len(stopped) == 1
    with pytest.raises(SandboxError, match='timed out'):
        service.call({}, timeout=0)
    assert len(stopped) == 2


def test_worker_cancellation_waits_for_guest_cleanup(worker):
    service, manager, exchange, stopped = worker
    entered = threading.Event()
    def read(*a, **kw):
        entered.set()
        return '{}'
    manager.read_file = read
    async def run():
        task = asyncio.create_task(service.acall({}))
        assert await asyncio.to_thread(entered.wait, 2)
        task.cancel()
        with pytest.raises(asyncio.CancelledError):
            await task
    asyncio.run(run())
    assert not service.ready and stopped == [service.name]


def test_batch_worker_stops_after_success(worker):
    service, manager, exchange, stopped = worker
    service.idle_seconds = 0
    manager.read_file = lambda *a, **kw: json.dumps({
        'id': json.loads((exchange / 'request.json').read_text())['id'], 'result': 'done'})
    assert service.call({}) == 'done'
    assert stopped == [service.name]


def test_worker_does_not_stop_another_owners_sandbox(worker):
    service, manager, _, stopped = worker
    manager.inspect = lambda name: SimpleNamespace(service=False, ownership={})
    with pytest.raises(SandboxError, match="another caller"):
        SandboxWorker.start(service, mounts=[SandboxMount(Path("/tmp"), "/index")])
    service.stop()
    assert not stopped


def test_service_has_common_exchange_without_usr_mount(manager, monkeypatch):
    create_disk(manager, monkeypatch, service=True, share_usr=False)
    spec = json.loads((manager.config.instances_dir / 'service/bundle/config.json').read_text())
    mounts = {target: source for source, target in spec['bindings']}
    assert mounts['/shared'] == str(manager.config.shared_dir)
    assert '/a0/usr' not in mounts


def test_mount_changes_require_stopped_guest_and_reject_host_root(manager, monkeypatch, tmp_path):
    create_disk(manager, monkeypatch, service=True, share_usr=False)
    with pytest.raises(SandboxError, match='Stop the sandbox'):
        manager.set_mounts('service', [SandboxMount(tmp_path, '/input')])
    monkeypatch.setattr(manager, '_runtime_state', lambda *a: ({'status': 'stopped'}, None))
    with pytest.raises(SandboxError, match='Host root'):
        manager.set_mounts('service', [SandboxMount(Path('/'), '/host')])
    manager.set_mounts('service', [SandboxMount(tmp_path, '/input')])
    assert manager._read_metadata('service')['mounts'][0]['read_only']

    transient = tmp_path / 'chat'
    transient.mkdir()
    manager.set_mounts('service', [SandboxMount(transient, '/index', read_only=False)])
    transient.rmdir()
    assert manager.inspect('service').service
    with pytest.raises(SandboxError, match="existing"):
        manager._process_command('service', manager._read_metadata('service'), ['true'])
    manager.set_mounts('service', [])
    assert manager.inspect('service').mounts == ()


def test_browser_pipe_command_is_instance_scoped(manager, monkeypatch):
    create_disk(manager, monkeypatch, service=True, share_usr=False)
    argv = manager.process_command('service', ['/opt/runtime/bin/python', '-V'])
    assert argv[-2:] == ['/opt/runtime/bin/python', '-V']
    assert 'execute' in argv and str(manager.config.instances_dir / 'service/bundle/config.json') in argv


def test_private_worker_inputs_are_scoped_to_instance(tmp_path, monkeypatch):
    worker = SandboxWorker('_test')
    paths = []
    for instance in ('first', 'second'):
        manager = SimpleNamespace(config=SimpleNamespace(instances_dir=tmp_path / 'instances' / instance))
        monkeypatch.setattr(worker_module, 'get_manager', lambda: manager)
        paths.append(worker._paths()[1])
    assert paths[0] != paths[1]
    assert paths[0].is_relative_to(tmp_path / 'instances/first')
    assert paths[1].is_relative_to(tmp_path / 'instances/second')


def test_worker_progress_is_nonblocking_boot_scoped_and_does_not_expose_logs(monkeypatch):
    service = SandboxWorker('_test')
    monkeypatch.setattr(service, '_paths', lambda: pytest.fail('Status must not start a sandbox'))
    assert service.status()['state'] == 'idle'
    now = [100.0]
    monkeypatch.setattr(worker_module.time, 'time', lambda: now[0])
    service._set_progress('starting', 'sandbox', 'Initializing sandbox')
    service._boot_id = 'current'
    progress = {'boot': 'old', 'stage': 'chromium', 'message': 'Downloading Chromium'}
    calls = []

    def read(name, path, *, limit):
        calls.append((path, limit))
        return json.dumps(progress) if path.endswith('progress.json') else 'private installer output'

    service._progress_manager = SimpleNamespace(read_file=read)
    entered, release = threading.Event(), threading.Event()
    def setup_lock():
        with service.lock:
            entered.set()
            release.wait(5)
    with ThreadPoolExecutor(max_workers=2) as pool:
        locked = pool.submit(setup_lock)
        try:
            assert entered.wait(1)
            assert pool.submit(service.status).result(timeout=1)['stage'] == 'sandbox'
            progress['boot'] = 'current'
            first = pool.submit(service.status).result(timeout=1)
            assert first['stage'] == 'chromium'
            assert 'private' not in json.dumps(first)
            now[0] += 40
            quiet = service.status()
            assert quiet['elapsed_seconds'] == quiet['quiet_seconds'] == 40
            progress['message'] = '<script>' * 100
            progress['stage'] = 'viewer'
            assert len(service.status()['message']) == 240
        finally:
            release.set()
            locked.result(timeout=1)
    assert all(limit == 4096 for _, limit in calls)


@pytest.mark.parametrize('state', [{'status': 'running'}, {'status': 'stopped'}, None])
def test_worker_liveness_never_scans_disk(manager, monkeypatch, state):
    create_disk(manager, monkeypatch, service=True)
    monkeypatch.setattr(manager, '_runtime_state', lambda *a: (state, 'container not found'))
    monkeypatch.setattr('plugins._sandboxing.helpers.manager.allocated_bytes',
                        lambda *a: pytest.fail('Liveness must not scan disk'))
    assert manager.is_running('service') is bool(state and state['status'] == 'running')


def test_setup_failure_keeps_progress_error_during_cleanup(monkeypatch):
    service = SandboxWorker('_test')
    monkeypatch.setattr(service, '_start', lambda cancel: (_ for _ in ()).throw(SandboxError('failed')))
    with pytest.raises(SandboxError):
        service.start()
    assert service.status()['state'] == 'error'


@pytest.mark.asyncio
async def test_browser_status_event_does_not_wait_for_browser_startup(monkeypatch):
    from plugins._browser.api import ws_browser
    monkeypatch.setattr(ws_browser, 'get_runtime', lambda *a, **kw: pytest.fail('Status must not start Chromium'))
    monkeypatch.setattr(ws_browser, 'browser_startup_status', lambda context_id: {'stage': 'chromium', 'state': 'starting'})
    handler = object.__new__(ws_browser.WsBrowser)
    result = await handler.process('browser_startup_status', {}, 'fixture')
    assert result == {'startup': {'stage': 'chromium', 'state': 'starting'}}


def test_custom_ocr_data_is_the_only_explicit_read_only_mount(tmp_path):
    from plugins._document_query.helpers.sandbox import parser_config
    config = {'liteparse_tessdata_path': str(tmp_path)}
    guest_config, mounts = parser_config(config)
    assert guest_config['liteparse_tessdata_path'] == '/tessdata'
    assert mounts == [SandboxMount(tmp_path, '/tessdata', True)]
    assert config['liteparse_tessdata_path'] == str(tmp_path)
    with pytest.raises(ValueError, match='language-data directory'):
        parser_config({'liteparse_tessdata_path': '/'})


@pytest.mark.parametrize('image_cache', [False, True])
def test_disk_usage_does_not_follow_guest_symlinks(tmp_path, monkeypatch, image_cache):
    from plugins._sandboxing.helpers.manager import allocated_bytes
    from plugins._sandboxing.helpers.images import SandboxImageManager

    link = tmp_path / 'guest-python'
    link.symlink_to('/root/private/python')
    original_stat = Path.stat

    def guarded_stat(path, *, follow_symlinks=True):
        if path == link and follow_symlinks:
            raise PermissionError('Guest absolute path is inaccessible on the host')
        return original_stat(path, follow_symlinks=follow_symlinks)

    monkeypatch.setattr(Path, 'stat', guarded_stat)
    measure = SandboxImageManager._allocated_bytes if image_cache else allocated_bytes
    assert measure(tmp_path) == (tmp_path.lstat().st_blocks + link.lstat().st_blocks) * 512
