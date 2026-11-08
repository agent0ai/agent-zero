import asyncio
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest
from plugins._whatsapp_integration.helpers import bridge_manager as manager


@pytest.fixture
def worker(monkeypatch):
    fake = SimpleNamespace(ready=False, mounts=[], acall=AsyncMock(return_value=True), stop=lambda: None)
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
