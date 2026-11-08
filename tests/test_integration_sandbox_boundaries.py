import asyncio
import base64
import importlib
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import AsyncMock, Mock
import pytest


@pytest.mark.asyncio
async def test_telegram_recreates_guest_bot_after_restart_and_waits_for_webhook_delivery(monkeypatch):
    from plugins._telegram_integration.helpers import bot_manager as bm
    monkeypatch.setattr(bm, '_bots', {})
    worker = SimpleNamespace(aprepare=AsyncMock(), ready=True, generation=1)
    monkeypatch.setattr(bm, 'worker', worker)
    rpc = AsyncMock(return_value={'id': 1, 'username': 'fixture'})
    monkeypatch.setattr(bm, 'rpc', rpc)
    received = []
    async def delivery(event):
        await asyncio.sleep(0)
        received.append(event.text)
    bot = bm.create_bot('fixture', '123456:fixture', delivery, delivery)
    await bm.cache_bot_info(bot)
    await bm.cache_bot_info(bot)
    assert rpc.await_count == 1
    worker.generation += 1
    await bm.cache_bot_info(bot)
    assert rpc.await_count == 2
    rpc.return_value = [{'kind': 'message', 'event': {'text': 'fixture'}}]
    await bm.feed_webhook(bot, {})
    assert received == ['fixture']


@pytest.mark.asyncio
async def test_cancelling_telegram_request_does_not_kill_other_bots(monkeypatch):
    from plugins._telegram_integration.helpers import sandbox
    done = asyncio.Event()
    async def call(payload):
        await asyncio.sleep(.02)
        done.set()
        return True
    monkeypatch.setattr(sandbox.worker, 'acall', call)
    task = asyncio.create_task(sandbox.rpc({}))
    await asyncio.sleep(0)
    task.cancel()
    with pytest.raises(asyncio.CancelledError):
        await task
    assert done.is_set()


def test_mail_attachment_boundary_and_private_files(monkeypatch, tmp_path):
    from plugins._email_integration.helpers import imap_client as imap
    monkeypatch.setattr(imap.files, 'get_abs_path', lambda *parts: str(tmp_path.joinpath(*parts)))
    def message(name, data='Zml4dHVyZQ=='):
        return {'sender': 'fixture@example.invalid', 'subject': '', 'body': 'attachment://' + name,
                'attachments': [{'name': name, 'data': data}]}
    for name, data in [('../escape', ''), ('/absolute', ''), ('file', '@not-base64')]:
        with pytest.raises(ValueError):
            imap._messages([message(name, data)])
    assert list(tmp_path.rglob('*')) == []
    result = imap._messages([message('file.txt')])[0]
    path = Path(result.attachments[0])
    assert path.read_bytes() == b'fixture' and path.stat().st_mode & 0o777 == 0o600
    assert result.body == 'attachment://' + str(path)


@pytest.mark.asyncio
async def test_mail_uid_checkpoint_survives_cleanup_and_retries_failed_poll(monkeypatch):
    from plugins._email_integration.helpers import handler
    monkeypatch.setattr(handler, 'connect_imap', AsyncMock(return_value='opaque'))
    monkeypatch.setattr(handler, 'disconnect_imap', AsyncMock())
    fetch = AsyncMock(side_effect=[RuntimeError('fixture transport error'), ([], 12)])
    monkeypatch.setattr(handler, 'fetch_new', fetch)
    state = {'fixture': {'last_uid': 10}}
    with pytest.raises(RuntimeError):
        await handler._poll_single_handler({'name': 'fixture'}, state)
    assert state['fixture']['last_uid'] == 10
    await handler._poll_single_handler({'name': 'fixture'}, state)
    assert state['fixture']['last_uid'] == 12
    assert handler.disconnect_imap.await_count == 2


@pytest.mark.asyncio
async def test_disabled_mail_does_not_start_transport(monkeypatch):
    module = importlib.import_module('plugins._email_integration.extensions.python.job_loop._10_email_poll')
    from plugins._email_integration.helpers import handler
    monkeypatch.setattr(module.plugins, 'get_plugin_config', lambda _: {'handlers': [{'name': 'fixture', 'enabled': True}]})
    monkeypatch.setattr(module.plugins, 'get_enabled_plugins', lambda _: [])
    poll = AsyncMock()
    monkeypatch.setattr(handler, '_poll_single_handler', poll)
    await module._handler_poll_loop('fixture')
    poll.assert_not_awaited()
