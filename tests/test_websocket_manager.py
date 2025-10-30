import asyncio
import sys
import threading
from pathlib import Path
from typing import Any
from unittest.mock import AsyncMock, patch

import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from python.helpers.websocket import WebSocketHandler, WebSocketResult
from python.helpers.websocket_manager import WebSocketManager, BUFFER_TTL


class FakeSocketIOServer:
    def __init__(self):
        self.emit = AsyncMock()
        self.disconnect = AsyncMock()


class DummyHandler(WebSocketHandler):
    def __init__(self, socketio, lock, results):
        super().__init__(socketio, lock)
        self.results = results

    @classmethod
    def get_event_types(cls) -> list[str]:
        return ["dummy"]

    async def process_event(self, event_type: str, data: dict[str, Any], sid: str):
        response = {"sid": sid, "data": data}
        self.results.append(response)
        return response


@pytest.mark.asyncio
async def test_connect_disconnect_updates_registry():
    socketio = FakeSocketIOServer()
    manager = WebSocketManager(socketio, threading.RLock())

    await manager.handle_connect("abc")
    assert "abc" in manager.connections

    await manager.handle_disconnect("abc")
    assert "abc" not in manager.connections


@pytest.mark.asyncio
async def test_server_restart_broadcast_emitted_when_enabled():
    socketio = FakeSocketIOServer()
    manager = WebSocketManager(socketio, threading.RLock())
    manager.set_server_restart_broadcast(True)

    await manager.handle_connect("sid-restart")

    socketio.emit.assert_awaited()
    args, kwargs = socketio.emit.await_args_list[0]
    assert args[0] == "server_restart"
    envelope = args[1]
    assert envelope["handlerId"] == manager._identifier  # noqa: SLF001
    assert envelope["data"]["runtimeId"]
    assert kwargs == {"to": "sid-restart"}


@pytest.mark.asyncio
async def test_server_restart_broadcast_skipped_when_disabled():
    socketio = FakeSocketIOServer()
    manager = WebSocketManager(socketio, threading.RLock())
    manager.set_server_restart_broadcast(False)

    await manager.handle_connect("sid-no-restart")

    assert socketio.emit.await_count == 0


@pytest.mark.asyncio
async def test_broadcast_performance_smoke(monkeypatch):
    socketio = FakeSocketIOServer()
    manager = WebSocketManager(socketio, threading.RLock())

    for idx in range(50):
        await manager.handle_connect(f"sid-{idx}")

    import time

    start = time.perf_counter()
    await manager.broadcast("perf_event", {"ok": True})
    duration_ms = (time.perf_counter() - start) * 1000

    assert socketio.emit.await_count == 50
    assert duration_ms < 300


@pytest.mark.asyncio
async def test_route_event_invokes_handler_and_ack():
    socketio = FakeSocketIOServer()
    manager = WebSocketManager(socketio, threading.RLock())

    results = []
    handler = DummyHandler(socketio, threading.RLock(), results)
    manager.register_handlers([handler])
    await manager.handle_connect("sid-1")

    response = await manager.route_event("dummy", {"foo": "bar"}, "sid-1")

    assert results[0]["sid"] == "sid-1"
    assert results[0]["data"]["foo"] == "bar"
    assert "correlationId" in results[0]["data"]

    assert isinstance(response, dict)
    assert "correlationId" in response
    assert isinstance(response["results"], list)
    entry = response["results"][0]
    assert entry["ok"] is True
    assert entry["data"]["sid"] == "sid-1"
    assert entry["data"]["data"]["foo"] == "bar"


@pytest.mark.asyncio
async def test_route_event_no_handler_returns_standard_error():
    socketio = FakeSocketIOServer()
    manager = WebSocketManager(socketio, threading.RLock())
    await manager.handle_connect("sid-1")

    response = await manager.route_event("missing", {}, "sid-1")

    assert len(response["results"]) == 1
    result = response["results"][0]
    assert result["handlerId"].endswith("WebSocketManager")
    assert result["ok"] is False
    assert result["error"]["code"] == "NO_HANDLERS"
    assert result["error"]["error"] == "No handler for 'missing'"


@pytest.mark.asyncio
async def test_route_event_all_returns_empty_when_no_connections():
    socketio = FakeSocketIOServer()
    manager = WebSocketManager(socketio, threading.RLock())

    results = await manager.route_event_all("event", {}, timeout_ms=1000)

    assert results == []


@pytest.mark.asyncio
async def test_route_event_all_aggregates_results():
    socketio = FakeSocketIOServer()
    manager = WebSocketManager(socketio, threading.RLock())

    class EchoHandler(WebSocketHandler):
        @classmethod
        def get_event_types(cls) -> list[str]:
            return ["multi"]

        async def process_event(self, event_type: str, data: dict[str, Any], sid: str):
            return {"sid": sid, "echo": data}

    handler = EchoHandler(socketio, threading.RLock())
    manager.register_handlers([handler])

    await manager.handle_connect("sid-1")
    await manager.handle_connect("sid-2")

    aggregated = await manager.route_event_all("multi", {"value": 42}, timeout_ms=1000)

    assert len(aggregated) == 2
    by_sid = {entry["sid"]: entry for entry in aggregated}
    assert by_sid["sid-1"]["results"][0]["ok"] is True
    payload_sid1 = by_sid["sid-1"]["results"][0]["data"]
    assert payload_sid1["sid"] == "sid-1"
    assert payload_sid1["echo"]["value"] == 42
    assert "correlationId" in payload_sid1["echo"]
    assert by_sid["sid-2"]["results"][0]["ok"] is True
    payload_sid2 = by_sid["sid-2"]["results"][0]["data"]
    assert payload_sid2["sid"] == "sid-2"
    assert payload_sid2["echo"]["value"] == 42
    assert by_sid["sid-1"]["correlationId"]


@pytest.mark.asyncio
async def test_route_event_all_timeout_marks_error():
    socketio = FakeSocketIOServer()
    manager = WebSocketManager(socketio, threading.RLock())

    class SlowHandler(WebSocketHandler):
        @classmethod
        def get_event_types(cls) -> list[str]:
            return ["slow"]

        async def process_event(self, event_type: str, data: dict[str, Any], sid: str):
            await asyncio.sleep(0.2)
            return {"status": "done"}

    handler = SlowHandler(socketio, threading.RLock())
    manager.register_handlers([handler])
    await manager.handle_connect("sid-1")

    aggregated = await manager.route_event_all("slow", {}, timeout_ms=50)

    assert len(aggregated) == 1
    first_entry = aggregated[0]
    result = first_entry["results"][0]
    assert result["ok"] is False
    assert result["error"] == {"code": "TIMEOUT", "error": "Request timeout"}
    assert first_entry["correlationId"]


@pytest.mark.asyncio
async def test_route_event_exception_standardizes_error_payload():
    socketio = FakeSocketIOServer()
    manager = WebSocketManager(socketio, threading.RLock())

    class FailingHandler(WebSocketHandler):
        @classmethod
        def get_event_types(cls) -> list[str]:
            return ["boom"]

        async def process_event(self, event_type: str, data: dict[str, Any], sid: str):
            raise RuntimeError("kaboom")

    handler = FailingHandler(socketio, threading.RLock())
    manager.register_handlers([handler])
    await manager.handle_connect("sid-1")

    response = await manager.route_event("boom", {}, "sid-1")

    assert len(response["results"]) == 1
    result = response["results"][0]
    assert result["handlerId"].endswith("FailingHandler")
    assert result["ok"] is False
    assert result["error"]["code"] == "HANDLER_ERROR"
    assert result["error"]["error"] == "Internal server error"
    assert "details" in result["error"]


@pytest.mark.asyncio
async def test_emit_to_unknown_sid_raises_error():
    socketio = FakeSocketIOServer()
    manager = WebSocketManager(socketio, threading.RLock())

    with pytest.raises(ValueError):
        await manager.emit_to("unknown", "event", {})


@pytest.mark.asyncio
async def test_emit_to_known_disconnected_sid_buffers():
    socketio = FakeSocketIOServer()
    manager = WebSocketManager(socketio, threading.RLock())
    await manager.handle_connect("sid-1")
    await manager.handle_disconnect("sid-1")

    await manager.emit_to("sid-1", "event", {"a": 1}, correlation_id="corr-1")

    assert "sid-1" in manager.buffers
    buffered = list(manager.buffers["sid-1"])
    assert len(buffered) == 1
    assert buffered[0].event_type == "event"
    assert buffered[0].data == {"a": 1}
    assert buffered[0].correlation_id == "corr-1"


@pytest.mark.asyncio
async def test_buffer_overflow_drops_oldest(monkeypatch):
    socketio = FakeSocketIOServer()
    manager = WebSocketManager(socketio, threading.RLock())

    await manager.handle_connect("offline")
    await manager.handle_disconnect("offline")

    monkeypatch.setattr("python.helpers.websocket_manager.BUFFER_MAX_SIZE", 2)

    await manager.emit_to("offline", "event", {"idx": 0})
    await manager.emit_to("offline", "event", {"idx": 1})
    await manager.emit_to("offline", "event", {"idx": 2})

    buffer = manager.buffers["offline"]
    assert len(buffer) == 2
    assert buffer[0].data["idx"] == 1
    assert buffer[1].data["idx"] == 2


@pytest.mark.asyncio
async def test_expired_buffer_entries_are_discarded(monkeypatch):
    socketio = FakeSocketIOServer()
    manager = WebSocketManager(socketio, threading.RLock())

    await manager.handle_connect("sid-expired")
    await manager.handle_disconnect("sid-expired")

    from datetime import timedelta, timezone, datetime

    past = datetime.now(timezone.utc) - (BUFFER_TTL + timedelta(seconds=5))
    future = past + BUFFER_TTL + timedelta(seconds=10)

    await manager.emit_to("sid-expired", "event", {"a": 1})
    manager.buffers["sid-expired"][0].timestamp = past

    socketio.emit.reset_mock()

    monkeypatch.setattr(
        "python.helpers.websocket_manager._utcnow",
        lambda: future,
    )
    await manager.handle_connect("sid-expired")

    assert socketio.emit.await_count == 0
    assert "sid-expired" not in manager.buffers


@pytest.mark.asyncio
async def test_flush_buffer_delivers_and_logs(monkeypatch):
    socketio = FakeSocketIOServer()
    manager = WebSocketManager(socketio, threading.RLock())
    await manager.handle_connect("sid-1")
    await manager.handle_disconnect("sid-1")

    await manager.emit_to("sid-1", "event", {"a": 1})

    await manager.handle_connect("sid-1")

    assert len(socketio.emit.await_args_list) == 1
    awaited_call = socketio.emit.await_args_list[0]
    assert awaited_call.args[0] == "event"
    envelope = awaited_call.args[1]
    assert envelope["data"] == {"a": 1}
    assert "eventId" in envelope and "handlerId" in envelope and "ts" in envelope
    assert awaited_call.kwargs == {"to": "sid-1"}
    assert "sid-1" not in manager.buffers


@pytest.mark.asyncio
async def test_broadcast_excludes_multiple_sids():
    socketio = FakeSocketIOServer()
    manager = WebSocketManager(socketio, threading.RLock())

    for sid in ("sid-1", "sid-2", "sid-3"):
        await manager.handle_connect(sid)

    await manager.broadcast(
        "event",
        {"foo": "bar"},
        exclude_sids={"sid-1", "sid-3"},
        handler_id="custom.broadcast",
        correlation_id="corr-b",
    )

    assert len(socketio.emit.await_args_list) == 1
    awaited_call = socketio.emit.await_args_list[0]
    assert awaited_call.args[0] == "event"
    envelope = awaited_call.args[1]
    assert envelope["data"] == {"foo": "bar"}
    assert envelope["handlerId"] == "custom.broadcast"
    assert envelope["correlationId"] == "corr-b"
    assert "eventId" in envelope and "ts" in envelope
    assert awaited_call.kwargs == {"to": "sid-2"}


@pytest.mark.asyncio
async def test_emit_to_wraps_envelope_with_metadata():
    socketio = FakeSocketIOServer()
    manager = WebSocketManager(socketio, threading.RLock())
    await manager.handle_connect("sid-meta")

    await manager.emit_to(
        "sid-meta",
        "meta_event",
        {"payload": True},
        handler_id="custom.handler",
        correlation_id="corr-meta",
    )

    socketio.emit.assert_awaited_once()
    args, kwargs = socketio.emit.await_args_list[0]
    assert args[0] == "meta_event"
    envelope = args[1]
    assert envelope["handlerId"] == "custom.handler"
    assert envelope["correlationId"] == "corr-meta"
    assert envelope["data"] == {"payload": True}
    assert kwargs == {"to": "sid-meta"}


@pytest.mark.asyncio
async def test_timestamps_are_timezone_aware():
    socketio = FakeSocketIOServer()
    manager = WebSocketManager(socketio, threading.RLock())

    await manager.handle_connect("sid-utc")
    info = manager.connections["sid-utc"]

    assert info.connected_at.tzinfo is not None
    assert info.last_activity.tzinfo is not None

    with patch("python.helpers.websocket_manager._utcnow") as mocked_now:
        mocked_now.return_value = info.last_activity
        await manager.route_event("unknown", {}, "sid-utc")
        assert info.last_activity.tzinfo is not None


@pytest.mark.asyncio
async def test_update_csrf_expiry_and_validate_session_disconnects():
    socketio = FakeSocketIOServer()
    manager = WebSocketManager(socketio, threading.RLock())

    await manager.handle_connect("sid-csrf")

    now_ts = 1000.0
    manager.update_csrf_expiry("sid-csrf", now_ts + 10)
    assert manager.connections["sid-csrf"].csrf_expires_at == now_ts + 10

    assert await manager.validate_session("sid-csrf", now_ts + 5) is True
    assert socketio.disconnect.await_count == 0

    assert await manager.validate_session("sid-csrf", now_ts + 15) is False
    socketio.disconnect.assert_awaited_once_with("sid-csrf")


class DuplicateHandler(WebSocketHandler):
    @classmethod
    def get_event_types(cls) -> list[str]:
        return ["dup_event"]

    async def process_event(self, event_type: str, data: dict[str, Any], sid: str):
        return {"handledBy": self.identifier}


class AnotherDuplicateHandler(WebSocketHandler):
    @classmethod
    def get_event_types(cls) -> list[str]:
        return ["dup_event"]

    async def process_event(self, event_type: str, data: dict[str, Any], sid: str):
        return {"handledBy": self.identifier}


def test_register_handlers_warns_on_duplicates(monkeypatch):
    socketio = FakeSocketIOServer()
    manager = WebSocketManager(socketio, threading.RLock())

    warnings: list[str] = []

    def capture_warning(message: str) -> None:
        warnings.append(message)

    monkeypatch.setattr(
        "python.helpers.print_style.PrintStyle.warning", staticmethod(capture_warning)
    )

    handler_a = DuplicateHandler(socketio, threading.RLock())
    handler_b = AnotherDuplicateHandler(socketio, threading.RLock())

    manager.register_handlers([handler_a, handler_b])

    assert any("Duplicate handler registration" in msg for msg in warnings)


class NonDictHandler(WebSocketHandler):
    @classmethod
    def get_event_types(cls) -> list[str]:
        return ["non_dict"]

    async def process_event(self, event_type: str, data: dict[str, Any], sid: str):
        return "raw-value"


@pytest.mark.asyncio
async def test_route_event_standardizes_success_payload():
    socketio = FakeSocketIOServer()
    manager = WebSocketManager(socketio, threading.RLock())

    handler = NonDictHandler(socketio, threading.RLock())
    manager.register_handlers([handler])

    response = await manager.route_event("non_dict", {}, "sid-123")

    assert len(response["results"]) == 1
    assert response["results"][0]["ok"] is True
    assert response["results"][0]["data"] == {"result": "raw-value"}


class ErrorHandler(WebSocketHandler):
    @classmethod
    def get_event_types(cls) -> list[str]:
        return ["boom"]

    async def process_event(self, event_type: str, data: dict[str, Any], sid: str):
        raise RuntimeError("BOOM")


class ResultHandler(WebSocketHandler):
    @classmethod
    def get_event_types(cls) -> list[str]:  # pragma: no cover - simple declaration
        return ["result_event", "result_error"]

    async def process_event(self, event_type: str, data: dict[str, Any], sid: str):
        if event_type == "result_event":
            return WebSocketResult.ok({"sid": sid}, correlation_id="explicit", duration_ms=1.234)
        return WebSocketResult.error(
            code="E_RESULT",
            message="boom",
            details="test",
        )


@pytest.mark.asyncio
async def test_route_event_standardizes_error_payload():
    socketio = FakeSocketIOServer()
    manager = WebSocketManager(socketio, threading.RLock())

    handler = ErrorHandler(socketio, threading.RLock())
    manager.register_handlers([handler])

    response = await manager.route_event("boom", {}, "sid-123")

    assert len(response["results"]) == 1
    payload = response["results"][0]
    assert payload["ok"] is False
    assert payload["error"]["code"] == "HANDLER_ERROR"
    assert payload["error"]["error"] == "Internal server error"


@pytest.mark.asyncio
async def test_route_event_accepts_websocket_result_instances():
    socketio = FakeSocketIOServer()
    manager = WebSocketManager(socketio, threading.RLock())

    handler = ResultHandler(socketio, threading.RLock())
    manager.register_handlers([handler])

    response = await manager.route_event("result_event", {}, "sid-123")

    assert response["results"]
    payload = response["results"][0]
    assert payload["ok"] is True
    assert payload["data"] == {"sid": "sid-123"}
    assert payload["correlationId"] == "explicit"
    assert payload["durationMs"] == pytest.approx(1.234, rel=1e-3)


@pytest.mark.asyncio
async def test_route_event_preserves_websocket_result_errors():
    socketio = FakeSocketIOServer()
    manager = WebSocketManager(socketio, threading.RLock())

    handler = ResultHandler(socketio, threading.RLock())
    manager.register_handlers([handler])

    response = await manager.route_event("result_error", {}, "sid-123")

    payload = response["results"][0]
    assert payload["ok"] is False
    assert payload["error"] == {"code": "E_RESULT", "error": "boom", "details": "test"}


class AlphaFilterHandler(WebSocketHandler):
    @classmethod
    def get_event_types(cls) -> list[str]:
        return ["filter_event"]

    async def process_event(self, event_type: str, data: dict[str, Any], sid: str):
        return {"handledBy": self.identifier, "sid": sid}


class BetaFilterHandler(WebSocketHandler):
    @classmethod
    def get_event_types(cls) -> list[str]:
        return ["filter_event"]

    async def process_event(self, event_type: str, data: dict[str, Any], sid: str):
        return {"handledBy": self.identifier, "sid": sid}


@pytest.mark.asyncio
async def test_route_event_include_handlers_filters_results():
    socketio = FakeSocketIOServer()
    manager = WebSocketManager(socketio, threading.RLock())

    alpha = AlphaFilterHandler(socketio, threading.RLock())
    beta = BetaFilterHandler(socketio, threading.RLock())
    manager.register_handlers([alpha, beta])
    await manager.handle_connect("sid-filter")

    response = await manager.route_event(
        "filter_event",
        {
            "includeHandlers": [alpha.identifier],
            "payload": True,
        },
        "sid-filter",
    )

    assert response["correlationId"]
    results = response["results"]
    assert len(results) == 1
    assert results[0]["handlerId"] == alpha.identifier
    assert results[0]["data"]["handledBy"] == alpha.identifier


@pytest.mark.asyncio
async def test_route_event_rejects_exclude_handlers_without_permission():
    socketio = FakeSocketIOServer()
    manager = WebSocketManager(socketio, threading.RLock())

    handler = AlphaFilterHandler(socketio, threading.RLock())
    manager.register_handlers([handler])
    await manager.handle_connect("sid-exclude")

    response = await manager.route_event(
        "filter_event",
        {"excludeHandlers": [handler.identifier]},
        "sid-exclude",
    )

    result = response["results"][0]
    assert result["error"]["code"] == "INVALID_FILTER"
    assert "excludeHandlers" in result["error"]["error"]


@pytest.mark.asyncio
async def test_route_event_all_respects_exclude_handlers():
    socketio = FakeSocketIOServer()
    manager = WebSocketManager(socketio, threading.RLock())

    alpha = AlphaFilterHandler(socketio, threading.RLock())
    beta = BetaFilterHandler(socketio, threading.RLock())
    manager.register_handlers([alpha, beta])

    await manager.handle_connect("sid-a")
    await manager.handle_connect("sid-b")

    aggregated = await manager.route_event_all(
        "filter_event",
        {"excludeHandlers": [beta.identifier]},
        handler_id="test.manager",
    )

    assert aggregated
    for entry in aggregated:
        assert entry["correlationId"]
        assert entry["results"]
        assert all(result["handlerId"] == alpha.identifier for result in entry["results"])


@pytest.mark.asyncio
async def test_route_event_preserves_correlation_id():
    socketio = FakeSocketIOServer()
    manager = WebSocketManager(socketio, threading.RLock())

    results = []
    handler = DummyHandler(socketio, threading.RLock(), results)
    manager.register_handlers([handler])
    await manager.handle_connect("sid-correlation")

    response = await manager.route_event(
        "dummy",
        {"foo": "bar", "correlationId": "manual-correlation"},
        "sid-correlation",
    )

    assert response["correlationId"] == "manual-correlation"
    result = response["results"][0]
    assert result["correlationId"] == "manual-correlation"


@pytest.mark.asyncio
async def test_request_preserves_explicit_correlation_id():
    socketio = FakeSocketIOServer()
    manager = WebSocketManager(socketio, threading.RLock())

    handler = DummyHandler(socketio, threading.RLock(), [])
    manager.register_handlers([handler])
    await manager.handle_connect("sid-request")

    response = await manager.request_for_sid(
        sid="sid-request",
        event_type="dummy",
        data={"payload": True, "correlationId": "req-correlation"},
        handler_id="tester",
    )

    assert response["correlationId"] == "req-correlation"
    result = response["results"][0]
    assert result["correlationId"] == "req-correlation"


@pytest.mark.asyncio
async def test_request_all_entries_include_correlation_id():
    socketio = FakeSocketIOServer()
    manager = WebSocketManager(socketio, threading.RLock())

    handler = DummyHandler(socketio, threading.RLock(), [])
    manager.register_handlers([handler])

    await manager.handle_connect("sid-1")
    await manager.handle_connect("sid-2")

    aggregated = await manager.route_event_all(
        "dummy",
        {"value": 1, "correlationId": "agg-correlation"},
    )

    assert aggregated
    for entry in aggregated:
        assert entry["correlationId"] == "agg-correlation"
        assert entry["results"]
        assert entry["results"][0]["correlationId"] == "agg-correlation"


def test_debug_logging_respects_runtime_flag(monkeypatch):
    socketio = FakeSocketIOServer()
    manager = WebSocketManager(socketio, threading.RLock())

    logs: list[str] = []

    def capture(message: str) -> None:
        logs.append(message)

    monkeypatch.setattr("python.helpers.print_style.PrintStyle.debug", staticmethod(capture))
    monkeypatch.setattr("python.helpers.websocket_manager.runtime.is_development", lambda: False)

    manager._debug("should-not-log")  # noqa: SLF001
    assert logs == []

    monkeypatch.setattr("python.helpers.websocket_manager.runtime.is_development", lambda: True)
    manager._debug("should-log")  # noqa: SLF001
    assert logs == ["should-log"]
