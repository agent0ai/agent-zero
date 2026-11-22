import asyncio
import os
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest
from plugins._whatsapp_integration.helpers import bridge_manager as manager


@pytest.fixture
def worker(monkeypatch):
    fake = SimpleNamespace(ready=False, mounts=[], prepare_directory=lambda p: p.mkdir(exist_ok=True), acall=AsyncMock(return_value=True), stop=lambda: None)
    manager._bridge_config.clear()
    manager._bridge_lock = None
    monkeypatch.setattr(manager, 'worker', fake)
    return fake


def test_disabled_checks_never_provision(worker):
    assert not manager.is_process_alive()
    worker.acall.assert_not_called()


def test_first_use_mounts_only_session_and_media_and_reuses_warm_guest(worker, monkeypatch, tmp_path):
    async def run():
        args = (3100, str(tmp_path / 'session'), str(tmp_path / 'media'))
        assert await manager.start_bridge(*args, allowed_numbers=['+001234'])
        payload = worker.acall.call_args.args[0]
        mounts = worker.acall.call_args.kwargs['mounts']
        assert payload['config']['allowed-numbers'] == '1234'
        assert [m.source for m in mounts] == [tmp_path / 'session', tmp_path / 'media']
        assert all(not m.read_only for m in mounts)
        assert payload['token'] and payload['token'] not in repr(manager.get_running_config())
        worker.mounts = mounts
        monkeypatch.setattr(manager, 'is_process_alive', lambda: True)
        assert await manager.start_bridge(*args, allowed_numbers=['+001234'])
        assert worker.acall.await_count == 1
        assert await manager.start_bridge(*args, allowed_numbers=['999'])
        assert worker.acall.await_count == 2
    asyncio.run(run())


def test_failed_install_retries_without_publishing_configuration(worker, tmp_path):
    worker.acall.side_effect = [RuntimeError('installation failed'), True]
    async def run():
        args = (3100, str(tmp_path / 'session'), str(tmp_path / 'media'))
        with pytest.raises(RuntimeError, match='installation failed'):
            await manager.start_bridge(*args)
        assert manager.get_running_config() == {}
        assert await manager.start_bridge(*args)
    asyncio.run(run())


def test_stop_preserves_login_state(worker, tmp_path):
    session = tmp_path / 'session'
    session.mkdir()
    (session / 'creds.json').write_text('fixture')
    stopped = []
    worker.stop = lambda: stopped.append(True)
    asyncio.run(manager.stop_bridge())
    assert stopped == [True]
    assert (session / 'creds.json').read_text() == 'fixture'


@pytest.mark.skipif(getattr(os, 'geteuid', lambda: -1)() != 0, reason='requires sandbox process credentials')
def test_outgoing_media_is_private_to_the_bridge(monkeypatch):
    import tempfile
    from unittest.mock import MagicMock
    from plugins._sandboxing.helpers.storage import prepare_workspace
    from plugins._whatsapp_integration.helpers import wa_client

    with tempfile.TemporaryDirectory() as temporary:
        parent = Path(temporary)
        parent.chmod(0o711)
        directory = parent / 'media'
        uid = 24157
        service = SimpleNamespace(uid=uid, prepare_directory=lambda path: prepare_workspace(path, gid=uid))
        monkeypatch.setattr(wa_client, 'worker', service)
        monkeypatch.setattr(wa_client, 'get_bridge_media_dir', lambda: directory)
        source = parent / 'private.jpg'
        source.write_bytes(b'media')
        source.chmod(0o600)
        client = MagicMock()
        monkeypatch.setattr(wa_client.aiohttp, 'ClientSession', client)

        def post(url, *, json, timeout):
            staged = Path(json['filePath'])
            assert staged.parent == directory
            assert staged.stat().st_uid == uid
            assert staged.stat().st_mode & 0o777 == 0o600
            assert staged.read_bytes() == b'media'
            response = MagicMock()
            response.__aenter__.return_value.json = AsyncMock(return_value={'ok': True})
            return response

        client.return_value.__aenter__.return_value.post = post
        assert asyncio.run(wa_client.send_media('http://bridge', 'chat', str(source))) == {'ok': True}
        assert list(directory.iterdir()) == []
