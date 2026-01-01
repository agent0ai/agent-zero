import sys
import threading
from pathlib import Path
from typing import Any

import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from python.helpers.websocket_manager import WebSocketManager
from python.websocket_handlers.dev_websocket_test_handler import (
    DevWebsocketTestHandler,
)


class FakeSocketIOServer:
    def __init__(self) -> None:
        from unittest.mock import AsyncMock

        self.emit = AsyncMock()
        self.disconnect = AsyncMock()


async def _create_manager() -> tuple[WebSocketManager, DevWebsocketTestHandler, FakeSocketIOServer]:
    socketio = FakeSocketIOServer()
    manager = WebSocketManager(socketio, threading.RLock())
    DevWebsocketTestHandler._reset_instance_for_testing()
    handler = DevWebsocketTestHandler.get_instance(socketio, threading.RLock())
    manager.register_handlers([handler])
    await manager.handle_connect("sid-primary")
    return manager, handler, socketio


@pytest.mark.asyncio
async def test_harness_emit_broadcasts_to_active_connections():
    manager, _handler, socketio = await _create_manager()

    await manager.route_event(
        "ws_tester_emit",
        {"message": "emit-check", "timestamp": "2025-10-29T12:00:00Z"},
        "sid-primary",
    )

    socketio.emit.assert_awaited()
    emit_calls = [(call.args, call.kwargs) for call in socketio.emit.await_args_list]
    match = next((c for c in emit_calls if c[0] and c[0][0] == "ws_tester_broadcast"), None)
    assert match is not None
    args, kwargs = match
    envelope = args[1]
    assert envelope["handlerId"].endswith("DevWebsocketTestHandler")
    assert envelope["data"]["message"] == "emit-check"
    assert kwargs == {"to": "sid-primary"}


@pytest.mark.asyncio
async def test_harness_request_returns_per_handler_result():
    manager, _handler, _socketio = await _create_manager()

    response = await manager.route_event(
        "ws_tester_request",
        {"value": 42},
        "sid-primary",
    )

    assert isinstance(response, dict)
    assert response["results"]
    first = response["results"][0]
    assert first["ok"] is True
    assert first["data"]["echo"] == 42
    assert response["correlationId"]
    assert first["handlerId"].endswith("DevWebsocketTestHandler")
    assert first["correlationId"] == response["correlationId"]


@pytest.mark.asyncio
async def test_harness_request_delayed_waits_for_sleep(monkeypatch):
    manager, _handler, _socketio = await _create_manager()

    calls: list[float] = []

    async def _fake_sleep(delay: float) -> None:  # pragma: no cover - helper
        calls.append(delay)

    monkeypatch.setattr(
        "python.websocket_handlers.dev_websocket_test_handler.asyncio.sleep",
        _fake_sleep,
    )

    await manager.route_event(
        "ws_tester_request_delayed",
        {"delay_ms": 1500},
        "sid-primary",
    )

    assert calls == [1.5]


@pytest.mark.asyncio
async def test_harness_persistence_emit_targets_requesting_sid():
    manager, _handler, socketio = await _create_manager()

    await manager.route_event(
        "ws_tester_trigger_persistence",
        {"phase": "after"},
        "sid-primary",
    )

    socketio.emit.assert_awaited()
    emit_calls = [(call.args, call.kwargs) for call in socketio.emit.await_args_list]
    match = next((c for c in emit_calls if c[0] and c[0][0] == "ws_tester_persistence"), None)
    assert match is not None
    args, kwargs = match
    payload = args[1]
    assert payload["handlerId"] == _handler.identifier
    assert payload["data"] == {"phase": "after", "handler": _handler.identifier}
    assert kwargs == {"to": "sid-primary"}


@pytest.mark.asyncio
async def test_harness_request_all_aggregates_all_connections():
    manager, _handler, _socketio = await _create_manager()
    await manager.handle_connect("sid-secondary")

    response = await manager.route_event(
        "ws_tester_request_all",
        {"marker": "aggregate"},
        "sid-primary",
    )

    assert response["results"] and response["results"][0]["ok"] is True
    data = response["results"][0]["data"]
    aggregated = data.get("results") or data.get("result")
    assert isinstance(aggregated, list)
    by_sid: dict[str, Any] = {entry["sid"]: entry["results"] for entry in aggregated}
    assert set(by_sid.keys()) == {"sid-primary", "sid-secondary"}
    for results in by_sid.values():
        assert results and results[0]["ok"] is True
        payload = results[0]["data"]
        assert payload["handler"].endswith("DevWebsocketTestHandler")
        assert results[0]["handlerId"].endswith("DevWebsocketTestHandler")
        assert results[0]["correlationId"] == response["results"][0]["correlationId"]
    assert response["correlationId"]


@pytest.mark.asyncio
async def test_harness_request_all_respects_exclude_handlers():
    manager, handler, _socketio = await _create_manager()
    await manager.handle_connect("sid-secondary")

    response = await manager.route_event(
        "ws_tester_request_all",
        {
            "marker": "exclude",
            "excludeHandlers": [handler.identifier],
        },
        "sid-primary",
    )

    assert response["correlationId"]
    first = response["results"][0]
    assert first["ok"] is False
    assert first["error"]["code"] == "INVALID_FILTER"
    assert "excludeHandlers" in first["error"]["error"]
