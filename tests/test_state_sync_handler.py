import sys
import threading
from pathlib import Path

import pytest
import asyncio
import time

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from helpers.ws_manager import WsManager

NAMESPACE = "/ws"


class FakeSocketIOServer:
    def __init__(self) -> None:
        from unittest.mock import AsyncMock

        self.emit = AsyncMock()
        self.disconnect = AsyncMock()


async def _create_manager() -> tuple[WsManager, "WsWebui"]:
    from api.ws_webui import WsWebui
    from helpers.state_monitor import _reset_state_monitor_for_testing

    socketio = FakeSocketIOServer()
    lock = threading.RLock()
    manager = WsManager(socketio, lock)

    _reset_state_monitor_for_testing()
    handler = WsWebui(socketio, lock, manager=manager, namespace=NAMESPACE)
    await manager.handle_connect(NAMESPACE, "sid-1")
    await handler.on_connect("sid-1")
    return manager, handler


async def _create_manager_with_socketio() -> tuple[WsManager, "WsWebui", FakeSocketIOServer]:
    from api.ws_webui import WsWebui
    from helpers.state_monitor import _reset_state_monitor_for_testing

    socketio = FakeSocketIOServer()
    lock = threading.RLock()
    manager = WsManager(socketio, lock)

    _reset_state_monitor_for_testing()
    handler = WsWebui(socketio, lock, manager=manager, namespace=NAMESPACE)
    await manager.handle_connect(NAMESPACE, "sid-1")
    await handler.on_connect("sid-1")
    return manager, handler, socketio


@pytest.mark.asyncio
async def test_state_request_success_returns_wire_level_shape_and_contract_payload():
    _manager, handler = await _create_manager()

    result = await handler.process(
        "state_request",
        {
            "correlationId": "client-1",
            "context": None,
            "log_from": 0,
            "notifications_from": 0,
            "timezone": "UTC",
        },
        "sid-1",
    )

    assert isinstance(result, dict)
    assert set(result.keys()) >= {"runtime_epoch", "seq_base"}
    assert isinstance(result["runtime_epoch"], str) and result["runtime_epoch"]
    assert isinstance(result["seq_base"], int)


@pytest.mark.asyncio
async def test_state_request_invalid_payload_returns_invalid_request_error():
    _manager, handler = await _create_manager()

    result = await handler.process(
        "state_request",
        {
            "correlationId": "client-2",
            "context": None,
            "log_from": -1,
            "notifications_from": 0,
            "timezone": "UTC",
        },
        "sid-1",
    )

    assert isinstance(result, dict)
    assert result.get("code") == "INVALID_REQUEST"


@pytest.mark.asyncio
async def test_state_push_gating_and_initial_snapshot_delivery():
    from helpers.state_monitor import get_state_monitor
    from helpers.state_snapshot import validate_snapshot_schema_v1

    manager, handler, socketio = await _create_manager_with_socketio()

    push_ready = asyncio.Event()
    captured: dict[str, object] = {}

    async def _emit(event_type, envelope, **_kwargs):
        if event_type == "state_push":
            captured["envelope"] = envelope
            push_ready.set()

    socketio.emit.side_effect = _emit

    # INVARIANT.STATE.GATING: no push before a successful state_request.
    get_state_monitor().mark_dirty(NAMESPACE, "sid-1")
    await asyncio.sleep(0.2)
    assert not push_ready.is_set()

    start = time.monotonic()
    await handler.process(
        "state_request",
        {
            "correlationId": "client-gating",
            "context": None,
            "log_from": 0,
            "notifications_from": 0,
            "timezone": "UTC",
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

    await manager.handle_disconnect(NAMESPACE, "sid-1")
