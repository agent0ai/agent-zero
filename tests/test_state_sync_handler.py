import sys
import threading
from pathlib import Path

import pytest
import asyncio
import time

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from python.helpers.websocket_manager import WebSocketManager


class FakeSocketIOServer:
    def __init__(self) -> None:
        from unittest.mock import AsyncMock

        self.emit = AsyncMock()
        self.disconnect = AsyncMock()


async def _create_manager() -> WebSocketManager:
    socketio = FakeSocketIOServer()
    manager = WebSocketManager(socketio, threading.RLock())

    from python.websocket_handlers.state_sync_handler import StateSyncHandler
    from python.helpers.state_monitor import _reset_state_monitor_for_testing

    _reset_state_monitor_for_testing()
    StateSyncHandler._reset_instance_for_testing()
    handler = StateSyncHandler.get_instance(socketio, threading.RLock())
    manager.register_handlers([handler])
    await manager.handle_connect("sid-1")
    return manager


async def _create_manager_with_socketio() -> tuple[WebSocketManager, FakeSocketIOServer]:
    socketio = FakeSocketIOServer()
    manager = WebSocketManager(socketio, threading.RLock())

    from python.websocket_handlers.state_sync_handler import StateSyncHandler
    from python.helpers.state_monitor import _reset_state_monitor_for_testing

    _reset_state_monitor_for_testing()
    StateSyncHandler._reset_instance_for_testing()
    handler = StateSyncHandler.get_instance(socketio, threading.RLock())
    manager.register_handlers([handler])
    await manager.handle_connect("sid-1")
    return manager, socketio


@pytest.mark.asyncio
async def test_state_request_success_returns_wire_level_shape_and_contract_payload():
    manager = await _create_manager()

    response = await manager.route_event(
        "state_request",
        {
            "correlationId": "client-1",
            "ts": "2025-12-28T00:00:00.000Z",
            "data": {
                "context": None,
                "log_from": 0,
                "notifications_from": 0,
                "timezone": "UTC",
            },
        },
        "sid-1",
    )

    assert response["correlationId"] == "client-1"
    assert isinstance(response.get("results"), list)
    assert response["results"]

    first = response["results"][0]
    assert first["ok"] is True
    assert first["correlationId"] == "client-1"
    assert isinstance(first.get("data"), dict)
    assert set(first["data"].keys()) >= {"runtime_epoch", "seq_base"}
    assert isinstance(first["data"]["runtime_epoch"], str) and first["data"]["runtime_epoch"]
    assert isinstance(first["data"]["seq_base"], int)


@pytest.mark.asyncio
async def test_state_request_invalid_payload_returns_invalid_request_error():
    manager = await _create_manager()

    response = await manager.route_event(
        "state_request",
        {
            "correlationId": "client-2",
            "ts": "2025-12-28T00:00:00.000Z",
            "data": {
                "context": None,
                "log_from": -1,
                "notifications_from": 0,
                "timezone": "UTC",
            },
        },
        "sid-1",
    )

    assert response["correlationId"] == "client-2"
    assert response["results"]
    first = response["results"][0]
    assert first["ok"] is False
    assert first["error"]["code"] == "INVALID_REQUEST"


@pytest.mark.asyncio
async def test_state_push_gating_and_initial_snapshot_delivery():
    from python.helpers.state_monitor import get_state_monitor
    from python.helpers.snapshot import validate_snapshot_schema_v1

    manager, socketio = await _create_manager_with_socketio()

    push_ready = asyncio.Event()
    captured: dict[str, object] = {}

    async def _emit(event_type, envelope, **_kwargs):
        if event_type == "state_push":
            captured["envelope"] = envelope
            push_ready.set()

    socketio.emit.side_effect = _emit

    # INVARIANT.STATE.GATING: no push before a successful state_request.
    get_state_monitor().mark_dirty("sid-1")
    await asyncio.sleep(0.2)
    assert not push_ready.is_set()

    start = time.monotonic()
    await manager.route_event(
        "state_request",
        {
            "correlationId": "client-gating",
            "ts": "2025-12-28T00:00:00.000Z",
            "data": {
                "context": None,
                "log_from": 0,
                "notifications_from": 0,
                "timezone": "UTC",
            },
        },
        "sid-1",
    )

    await asyncio.wait_for(push_ready.wait(), timeout=1.0)
    assert (time.monotonic() - start) <= 1.0

    envelope = captured.get("envelope")
    assert isinstance(envelope, dict)
    data = envelope.get("data")
    assert isinstance(data, dict)
    assert set(data.keys()) >= {"runtime_epoch", "seq", "snapshot"}
    assert isinstance(data["runtime_epoch"], str) and data["runtime_epoch"]
    assert isinstance(data["seq"], int)
    assert isinstance(data["snapshot"], dict)
    validate_snapshot_schema_v1(data["snapshot"])

    await manager.handle_disconnect("sid-1")
