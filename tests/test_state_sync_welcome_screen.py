import asyncio
import sys
import threading
import time
from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from python.helpers.websocket_manager import WebSocketManager

NAMESPACE = "/state_sync"


class FakeSocketIOServer:
    def __init__(self) -> None:
        from unittest.mock import AsyncMock

        self.emit = AsyncMock()
        self.disconnect = AsyncMock()


@pytest.mark.asyncio
async def test_state_sync_handshake_and_initial_snapshot_work_with_no_selected_context() -> (
    None
):
    """
    Regression for Welcome screen: the UI has no selected context, so `state_request.context`
    is null. We must still handshake and receive an initial `state_push` quickly (no hang).
    """

    from python.helpers.state_monitor import _reset_state_monitor_for_testing
    from python.helpers.state_snapshot import validate_snapshot_schema_v1
    from python.websocket_handlers.state_sync_handler import StateSyncHandler

    socketio = FakeSocketIOServer()
    manager = WebSocketManager(socketio, threading.RLock())

    _reset_state_monitor_for_testing()
    StateSyncHandler._reset_instance_for_testing()
    handler = StateSyncHandler.get_instance(socketio, threading.RLock())
    manager.register_handlers({NAMESPACE: [handler]})
    await manager.handle_connect(NAMESPACE, "sid-1")

    push_ready = asyncio.Event()
    captured: dict[str, object] = {}

    async def _emit(event_type, envelope, **_kwargs):
        if event_type == "state_push":
            captured["envelope"] = envelope
            push_ready.set()

    socketio.emit.side_effect = _emit

    start = time.monotonic()
    await manager.route_event(
        NAMESPACE,
        "state_request",
        {
            "correlationId": "client-welcome",
            "ts": "2026-01-05T00:00:00.000Z",
            "data": {
                "context": None,  # welcome screen (no selected chat)
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
    assert isinstance(data["snapshot"], dict)
    validate_snapshot_schema_v1(data["snapshot"])
