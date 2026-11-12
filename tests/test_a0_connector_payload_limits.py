import threading
from unittest.mock import AsyncMock

import pytest

from helpers.ws_manager import WsManager
from plugins._a0_connector.api.ws_connector import WsConnector
from plugins._a0_connector.helpers.ws_runtime import (
    store_sid_connector_capabilities,
    ws_max_payload_bytes_for_sid,
)


class _FakeSocketIOServer:
    def __init__(self) -> None:
        self.emit = AsyncMock()
        self.disconnect = AsyncMock()


@pytest.mark.asyncio
async def test_oversized_core_event_becomes_connector_error_without_disconnect() -> None:
    socketio = _FakeSocketIOServer()
    manager = WsManager(socketio, threading.RLock())
    manager.set_server_restart_broadcast(False)
    handler = WsConnector(socketio, threading.RLock(), manager=manager, namespace="/ws")
    manager.register_handlers({"/ws": [handler]})
    await manager.handle_connect("/ws", "sid-limit")
    store_sid_connector_capabilities(
        "sid-limit",
        {"ws_max_payload_bytes": 2048},
    )

    await handler.emit_to(
        "sid-limit",
        "connector_context_event",
        {"context_id": "ctx-1", "data": {"text": "x" * 4096}},
    )

    assert ("/ws", "sid-limit") in manager.connections
    assert socketio.disconnect.await_count == 0
    socketio.emit.assert_awaited_once()
    event, envelope = socketio.emit.await_args.args[:2]
    assert event == "connector_error"
    assert envelope["data"]["code"] == "PAYLOAD_TOO_LARGE"
    assert envelope["data"]["rejected_event"] == "connector_context_event"
    assert envelope["data"]["details"]["alternative"] == "http_bulk_transfer"
    await manager.handle_disconnect("/ws", "sid-limit")


@pytest.mark.asyncio
async def test_connector_hello_negotiates_peer_receive_limit() -> None:
    socketio = _FakeSocketIOServer()
    manager = WsManager(socketio, threading.RLock())
    manager.set_server_restart_broadcast(False)
    handler = WsConnector(socketio, threading.RLock(), manager=manager, namespace="/ws")
    manager.register_handlers({"/ws": [handler]})
    await manager.handle_connect("/ws", "sid-hello")

    result = await handler.process(
        "connector_hello",
        {"capabilities": {"ws_max_payload_bytes": 16 * 1024 * 1024}},
        "sid-hello",
    )

    assert result["capabilities"]["ws_max_payload_bytes"] == 50 * 1024 * 1024
    assert ws_max_payload_bytes_for_sid("sid-hello") == 16 * 1024 * 1024
    assert manager.connections[("/ws", "sid-hello")].max_payload_bytes == 16 * 1024 * 1024
    await manager.handle_disconnect("/ws", "sid-hello")
