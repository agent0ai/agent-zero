import sys
import threading
from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from python.helpers.websocket import WebSocketHandler, WebSocketResult


class _FakeSocketIO:
    async def emit(self, *_args, **_kwargs):  # pragma: no cover - helper stub
        return None

    async def disconnect(self, *_args, **_kwargs):  # pragma: no cover - helper stub
        return None


class _TestHandler(WebSocketHandler):
    @classmethod
    def get_event_types(cls) -> list[str]:
        return ["test_event"]

    async def process_event(self, event_type: str, data: dict, sid: str) -> None:
        return None


def _make_handler() -> _TestHandler:
    return _TestHandler(_FakeSocketIO(), threading.RLock())


def test_websocket_result_ok_clones_payload():
    payload = {"value": 1}
    result = WebSocketResult.ok(payload)

    assert result.as_result(
        handler_id="handler",
        fallback_correlation_id="corr",
    )["data"] == payload

    payload["value"] = 2
    assert result.as_result(
        handler_id="handler",
        fallback_correlation_id="corr",
    )["data"] == {"value": 1}


def test_websocket_result_error_contains_metadata():
    result = WebSocketResult.error(
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


def test_websocket_result_applies_fallback_correlation_and_duration():
    result = WebSocketResult.ok(duration_ms=5.4321)
    payload = result.as_result(
        handler_id="handler",
        fallback_correlation_id="corr-fallback",
    )
    assert payload["correlationId"] == "corr-fallback"
    assert payload["durationMs"] == pytest.approx(5.4321, rel=1e-3)


def test_handler_result_helpers_return_websocket_result_instances():
    handler = _make_handler()

    ok_result = handler.result_ok({"foo": "bar"}, correlation_id="cid")
    assert isinstance(ok_result, WebSocketResult)
    ok_payload = ok_result.as_result(
        handler_id="handler",
        fallback_correlation_id=None,
    )
    assert ok_payload["ok"] is True
    assert ok_payload["data"] == {"foo": "bar"}
    assert ok_payload["correlationId"] == "cid"

    err_result = handler.result_error(
        code="E_BAD",
        message="boom",
        details="missing",
        correlation_id="err",
    )
    assert isinstance(err_result, WebSocketResult)
    err_payload = err_result.as_result(
        handler_id="handler",
        fallback_correlation_id=None,
    )
    assert err_payload["ok"] is False
    assert err_payload["error"] == {
        "code": "E_BAD",
        "error": "boom",
        "details": "missing",
    }
    assert err_payload["correlationId"] == "err"


def test_result_error_requires_error_payload():
    with pytest.raises(ValueError):
        WebSocketResult(ok=False)

    with pytest.raises(ValueError):
        WebSocketResult.error(code="", message="boom")
