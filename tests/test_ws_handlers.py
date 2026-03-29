import sys
import threading
from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from helpers.ws_manager import WsResult


class _FakeSocketIO:
    async def emit(self, *_args, **_kwargs):  # pragma: no cover - helper stub
        return None

    async def disconnect(self, *_args, **_kwargs):  # pragma: no cover - helper stub
        return None


def test_ws_result_ok_clones_payload():
    payload = {"value": 1}
    result = WsResult.ok(payload)

    assert result.as_result(
        handler_id="handler",
        fallback_correlation_id="corr",
    )["data"] == payload

    payload["value"] = 2
    assert result.as_result(
        handler_id="handler",
        fallback_correlation_id="corr",
    )["data"] == {"value": 1}


def test_ws_result_error_contains_metadata():
    result = WsResult.error(
        code="E_TEST",
        message="failure",
        details="additional",
        correlation_id="corr",
        duration_ms=12.5,
    )

    as_payload = result.as_result(handler_id="handler", fallback_correlation_id=None)
    assert as_payload["ok"] is False
    assert as_payload["error"] == {
        "code": "E_TEST",
        "error": "failure",
        "details": "additional",
    }
    assert as_payload["correlationId"] == "corr"
    assert as_payload["durationMs"] == pytest.approx(12.5, rel=1e-3)


def test_ws_result_applies_fallback_correlation_and_duration():
    result = WsResult.ok(duration_ms=5.4321)
    payload = result.as_result(
        handler_id="handler",
        fallback_correlation_id="corr-fallback",
    )
    assert payload["correlationId"] == "corr-fallback"
    assert payload["durationMs"] == pytest.approx(5.4321, rel=1e-3)


def test_result_error_requires_error_payload():
    with pytest.raises(ValueError):
        WsResult(ok=False)

    with pytest.raises(ValueError):
        WsResult.error(code="", message="boom")


@pytest.mark.asyncio
async def test_state_sync_handler_registers_and_routes_state_request():
    from helpers.ws_manager import WsManager
    from api.ws_webui import WsWebui
    from helpers.state_monitor import _reset_state_monitor_for_testing

    _reset_state_monitor_for_testing()

    socketio = _FakeSocketIO()
    lock = threading.RLock()
    manager = WsManager(socketio, lock)

    namespace = "/ws"
    handler = WsWebui(socketio, lock, manager=manager, namespace=namespace)

    # Register connection with manager (sets up dispatcher loop)
    await manager.handle_connect(namespace, "sid-1")
    # Trigger StateMonitor binding via extension
    await handler.on_connect("sid-1")

    result = await handler.process(
        "state_request",
        {
            "correlationId": "smoke-1",
            "context": None,
            "log_from": 0,
            "notifications_from": 0,
            "timezone": "UTC",
        },
        "sid-1",
    )

    assert result is not None
    assert "runtime_epoch" in result
    assert result.get("seq_base") == 1

    await handler.on_disconnect("sid-1")
    await manager.handle_disconnect(namespace, "sid-1")
