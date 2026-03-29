import asyncio
import sys
import threading
import time
from pathlib import Path
from typing import Any
from unittest.mock import AsyncMock, patch

import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from helpers.ws import ConnectionNotFoundError, WsHandler
from helpers.ws_manager import (
    WsManager,
    WsResult,
    BUFFER_TTL,
    DIAGNOSTIC_EVENT,
    LIFECYCLE_CONNECT_EVENT,
    LIFECYCLE_DISCONNECT_EVENT,
)

NAMESPACE = "/test"


class FakeSocketIOServer:
    def __init__(self):
        self.emit = AsyncMock()
        self.disconnect = AsyncMock()


class DummyHandler(WsHandler):
    def __init__(self, socketio, lock, results=None):
        super().__init__(socketio, lock)
        self.results = results if results is not None else []

    async def process(self, event: str, data: dict[str, Any], sid: str):
        response = {"sid": sid, "data": data}
        self.results.append(response)
        return response


@pytest.mark.asyncio
async def test_connect_disconnect_updates_registry():
    socketio = FakeSocketIOServer()
    manager = WsManager(socketio, threading.RLock())

    await manager.handle_connect(NAMESPACE, "abc")
    assert (NAMESPACE, "abc") in manager.connections

    await manager.handle_disconnect(NAMESPACE, "abc")
    assert (NAMESPACE, "abc") not in manager.connections


@pytest.mark.asyncio
async def test_server_restart_broadcast_emitted_when_enabled():
    socketio = FakeSocketIOServer()
    manager = WsManager(socketio, threading.RLock())
    manager.set_server_restart_broadcast(True)

    await manager.handle_connect(NAMESPACE, "sid-restart")

    socketio.emit.assert_awaited()
    args, kwargs = socketio.emit.await_args_list[0]
    assert args[0] == "server_restart"
    envelope = args[1]
    assert envelope["handlerId"] == manager._identifier  # noqa: SLF001
    assert envelope["data"]["runtimeId"]
    assert kwargs == {"to": "sid-restart", "namespace": NAMESPACE}


@pytest.mark.asyncio
async def test_server_restart_broadcast_skipped_when_disabled():
    socketio = FakeSocketIOServer()
    manager = WsManager(socketio, threading.RLock())
    manager.set_server_restart_broadcast(False)

    await manager.handle_connect(NAMESPACE, "sid-no-restart")

    assert socketio.emit.await_count == 0


@pytest.mark.asyncio
async def test_broadcast_performance_smoke(monkeypatch):
    socketio = FakeSocketIOServer()
    manager = WsManager(socketio, threading.RLock())

    for idx in range(50):
        await manager.handle_connect(NAMESPACE, f"sid-{idx}")

    # Drain lifecycle broadcast tasks queued by handle_connect and reset the
    # mock so we only measure the explicit broadcast below.
    for _ in range(55):
        await asyncio.sleep(0)
    socketio.emit.reset_mock()

    import time

    start = time.perf_counter()
    await manager.broadcast(NAMESPACE, "perf_event", {"ok": True})
    duration_ms = (time.perf_counter() - start) * 1000

    assert socketio.emit.await_count == 50
    assert duration_ms < 300


@pytest.mark.asyncio
async def test_route_event_invokes_handler_and_ack():
    socketio = FakeSocketIOServer()
    manager = WsManager(socketio, threading.RLock())

    results = []
    handler = DummyHandler(socketio, threading.RLock(), results)
    manager.register_handlers({NAMESPACE: [handler]})
    await manager.handle_connect(NAMESPACE, "sid-1")

    response = await manager.route_event(NAMESPACE, "dummy", {"foo": "bar"}, "sid-1")

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
    manager = WsManager(socketio, threading.RLock())
    await manager.handle_connect(NAMESPACE, "sid-1")

    response = await manager.route_event(NAMESPACE, "missing", {}, "sid-1")

    assert len(response["results"]) == 1
    result = response["results"][0]
    assert result["handlerId"].endswith("WsManager")
    assert result["ok"] is False
    assert result["error"]["code"] == "NO_HANDLERS"
    assert (
        result["error"]["error"]
        == f"No handler for namespace '{NAMESPACE}'"
    )


@pytest.mark.asyncio
async def test_route_event_all_returns_empty_when_no_connections():
    socketio = FakeSocketIOServer()
    manager = WsManager(socketio, threading.RLock())

    results = await manager.route_event_all(NAMESPACE, "event", {}, timeout_ms=1000)

    assert results == []


@pytest.mark.asyncio
async def test_route_event_all_aggregates_results():
    socketio = FakeSocketIOServer()
    manager = WsManager(socketio, threading.RLock())

    class EchoHandler(WsHandler):
        async def process(self, event: str, data: dict[str, Any], sid: str):
            return {"sid": sid, "echo": data}

    handler = EchoHandler(socketio, threading.RLock())
    manager.register_handlers({NAMESPACE: [handler]})

    await manager.handle_connect(NAMESPACE, "sid-1")
    await manager.handle_connect(NAMESPACE, "sid-2")

    aggregated = await manager.route_event_all(
        NAMESPACE, "multi", {"value": 42}, timeout_ms=1000
    )

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
    manager = WsManager(socketio, threading.RLock())

    class SlowHandler(WsHandler):
        async def process(self, event: str, data: dict[str, Any], sid: str):
            await asyncio.sleep(0.2)
            return {"status": "done"}

    handler = SlowHandler(socketio, threading.RLock())
    manager.register_handlers({NAMESPACE: [handler]})
    await manager.handle_connect(NAMESPACE, "sid-1")

    aggregated = await manager.route_event_all(NAMESPACE, "slow", {}, timeout_ms=50)

    assert len(aggregated) == 1
    first_entry = aggregated[0]
    result = first_entry["results"][0]
    assert result["ok"] is False
    assert result["error"] == {"code": "TIMEOUT", "error": "Request timeout"}
    assert first_entry["correlationId"]


@pytest.mark.asyncio
async def test_route_event_exception_standardizes_error_payload():
    socketio = FakeSocketIOServer()
    manager = WsManager(socketio, threading.RLock())

    class FailingHandler(WsHandler):
        async def process(self, event: str, data: dict[str, Any], sid: str):
            raise RuntimeError("kaboom")

    handler = FailingHandler(socketio, threading.RLock())
    manager.register_handlers({NAMESPACE: [handler]})
    await manager.handle_connect(NAMESPACE, "sid-1")

    response = await manager.route_event(NAMESPACE, "boom", {}, "sid-1")

    assert len(response["results"]) == 1
    result = response["results"][0]
    assert result["handlerId"].endswith("FailingHandler")
    assert result["ok"] is False
    assert result["error"]["code"] == "HANDLER_ERROR"
    assert result["error"]["error"] == "Internal server error"
    assert "details" in result["error"]


@pytest.mark.asyncio
async def test_route_event_offloads_blocking_handlers():
    socketio = FakeSocketIOServer()
    manager = WsManager(socketio, threading.RLock())

    class BlockingHandler(WsHandler):
        async def process(self, event: str, data: dict[str, Any], sid: str):
            time.sleep(0.2)
            return {"status": "done"}

    handler = BlockingHandler(socketio, threading.RLock())
    manager.register_handlers({NAMESPACE: [handler]})
    await manager.handle_connect(NAMESPACE, "sid-1")

    route_task = asyncio.create_task(
        manager.route_event(NAMESPACE, "block", {}, "sid-1")
    )
    await asyncio.sleep(0)

    t0 = time.perf_counter()
    await asyncio.sleep(0.05)
    elapsed = time.perf_counter() - t0
    assert elapsed < 0.15

    response = await route_task
    assert response["results"]


@pytest.mark.asyncio
async def test_route_event_unwraps_ts_data_envelope_and_preserves_correlation_id():
    socketio = FakeSocketIOServer()
    manager = WsManager(socketio, threading.RLock())

    results: list[dict[str, Any]] = []
    handler = DummyHandler(socketio, threading.RLock(), results)
    manager.register_handlers({NAMESPACE: [handler]})
    await manager.handle_connect(NAMESPACE, "sid-1")

    response = await manager.route_event(
        NAMESPACE,
        "dummy",
        {
            "correlationId": "client-1",
            "ts": "2025-10-29T12:00:00.000Z",
            "data": {"value": 123},
        },
        "sid-1",
    )

    assert response["correlationId"] == "client-1"
    assert len(results) == 1
    handler_payload = results[0]["data"]
    assert handler_payload["value"] == 123
    assert handler_payload["correlationId"] == "client-1"
    assert "ts" not in handler_payload
    assert "data" not in handler_payload


@pytest.mark.asyncio
async def test_emit_to_unknown_sid_raises_error():
    socketio = FakeSocketIOServer()
    manager = WsManager(socketio, threading.RLock())

    with pytest.raises(ConnectionNotFoundError):
        await manager.emit_to(NAMESPACE, "unknown", "event", {})


@pytest.mark.asyncio
async def test_emit_to_known_disconnected_sid_buffers():
    socketio = FakeSocketIOServer()
    manager = WsManager(socketio, threading.RLock())
    await manager.handle_connect(NAMESPACE, "sid-1")
    await manager.handle_disconnect(NAMESPACE, "sid-1")

    await manager.emit_to(
        NAMESPACE, "sid-1", "event", {"a": 1}, correlation_id="corr-1"
    )

    assert (NAMESPACE, "sid-1") in manager.buffers
    buffered = list(manager.buffers[(NAMESPACE, "sid-1")])
    assert len(buffered) == 1
    assert buffered[0].event_type == "event"
    assert buffered[0].data == {"a": 1}
    assert buffered[0].correlation_id == "corr-1"


@pytest.mark.asyncio
async def test_buffer_overflow_drops_oldest(monkeypatch):
    socketio = FakeSocketIOServer()
    manager = WsManager(socketio, threading.RLock())

    await manager.handle_connect(NAMESPACE, "offline")
    await manager.handle_disconnect(NAMESPACE, "offline")

    monkeypatch.setattr("helpers.ws_manager.BUFFER_MAX_SIZE", 2)

    await manager.emit_to(NAMESPACE, "offline", "event", {"idx": 0})
    await manager.emit_to(NAMESPACE, "offline", "event", {"idx": 1})
    await manager.emit_to(NAMESPACE, "offline", "event", {"idx": 2})

    buffer = manager.buffers[(NAMESPACE, "offline")]
    assert len(buffer) == 2
    assert buffer[0].data["idx"] == 1
    assert buffer[1].data["idx"] == 2


@pytest.mark.asyncio
async def test_expired_buffer_entries_are_discarded(monkeypatch):
    socketio = FakeSocketIOServer()
    manager = WsManager(socketio, threading.RLock())

    await manager.handle_connect(NAMESPACE, "sid-expired")
    await manager.handle_disconnect(NAMESPACE, "sid-expired")

    from datetime import timedelta, timezone, datetime

    past = datetime.now(timezone.utc) - (BUFFER_TTL + timedelta(seconds=5))
    future = past + BUFFER_TTL + timedelta(seconds=10)

    await manager.emit_to(NAMESPACE, "sid-expired", "event", {"a": 1})
    manager.buffers[(NAMESPACE, "sid-expired")][0].timestamp = past

    socketio.emit.reset_mock()

    monkeypatch.setattr(
        "helpers.ws_manager._utcnow",
        lambda: future,
    )
    await manager.handle_connect(NAMESPACE, "sid-expired")

    assert socketio.emit.await_count == 0
    assert (NAMESPACE, "sid-expired") not in manager.buffers


@pytest.mark.asyncio
async def test_flush_buffer_delivers_and_logs(monkeypatch):
    socketio = FakeSocketIOServer()
    manager = WsManager(socketio, threading.RLock())
    await manager.handle_connect(NAMESPACE, "sid-1")
    await manager.handle_disconnect(NAMESPACE, "sid-1")

    await manager.emit_to(NAMESPACE, "sid-1", "event", {"a": 1})

    await manager.handle_connect(NAMESPACE, "sid-1")

    assert len(socketio.emit.await_args_list) == 1
    awaited_call = socketio.emit.await_args_list[0]
    assert awaited_call.args[0] == "event"
    envelope = awaited_call.args[1]
    assert envelope["data"] == {"a": 1}
    assert "eventId" in envelope and "handlerId" in envelope and "ts" in envelope
    assert awaited_call.kwargs == {"to": "sid-1", "namespace": NAMESPACE}
    assert (NAMESPACE, "sid-1") not in manager.buffers


@pytest.mark.asyncio
async def test_known_sid_expires_after_buffer_ttl(monkeypatch):
    """After BUFFER_TTL, a disconnected sid is swept from _known_sids and emit_to raises."""
    socketio = FakeSocketIOServer()
    manager = WsManager(socketio, threading.RLock())

    await manager.handle_connect(NAMESPACE, "sid-stale")
    await manager.handle_disconnect(NAMESPACE, "sid-stale")

    # Immediately after disconnect, buffering still works
    await manager.emit_to(NAMESPACE, "sid-stale", "event", {"x": 1})
    assert (NAMESPACE, "sid-stale") in manager.buffers

    from datetime import timedelta, timezone, datetime

    future = datetime.now(timezone.utc) + BUFFER_TTL + timedelta(seconds=10)
    monkeypatch.setattr("helpers.ws_manager._utcnow", lambda: future)

    # After TTL, emit_to should raise because the sid is no longer known
    with pytest.raises(ConnectionNotFoundError):
        await manager.emit_to(NAMESPACE, "sid-stale", "event", {"x": 2})

    # _known_sids and buffers should be cleaned
    assert (NAMESPACE, "sid-stale") not in manager._known_sids
    assert (NAMESPACE, "sid-stale") not in manager.buffers
    assert (NAMESPACE, "sid-stale") not in manager._disconnect_times


@pytest.mark.asyncio
async def test_sweep_cleans_stale_sids_on_disconnect(monkeypatch):
    """_sweep_stale_sids runs during handle_disconnect and cleans expired entries."""
    socketio = FakeSocketIOServer()
    manager = WsManager(socketio, threading.RLock())

    await manager.handle_connect(NAMESPACE, "old-sid")
    await manager.handle_disconnect(NAMESPACE, "old-sid")

    from datetime import timedelta, timezone, datetime

    future = datetime.now(timezone.utc) + BUFFER_TTL + timedelta(seconds=10)
    monkeypatch.setattr("helpers.ws_manager._utcnow", lambda: future)

    # A new connect/disconnect triggers sweep which cleans old-sid
    await manager.handle_connect(NAMESPACE, "new-sid")
    await manager.handle_disconnect(NAMESPACE, "new-sid")

    assert (NAMESPACE, "old-sid") not in manager._known_sids
    assert (NAMESPACE, "old-sid") not in manager._disconnect_times


@pytest.mark.asyncio
async def test_broadcast_excludes_multiple_sids():
    socketio = FakeSocketIOServer()
    manager = WsManager(socketio, threading.RLock())

    for sid in ("sid-1", "sid-2", "sid-3"):
        await manager.handle_connect(NAMESPACE, sid)

    # Drain lifecycle broadcast tasks from handle_connect
    for _ in range(10):
        await asyncio.sleep(0)
    socketio.emit.reset_mock()

    await manager.broadcast(
        NAMESPACE,
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
    assert awaited_call.kwargs == {"to": "sid-2", "namespace": NAMESPACE}


@pytest.mark.asyncio
async def test_emit_to_wraps_envelope_with_metadata():
    socketio = FakeSocketIOServer()
    manager = WsManager(socketio, threading.RLock())
    await manager.handle_connect(NAMESPACE, "sid-meta")

    await manager.emit_to(
        NAMESPACE,
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
    assert kwargs == {"to": "sid-meta", "namespace": NAMESPACE}


@pytest.mark.asyncio
async def test_timestamps_are_timezone_aware():
    socketio = FakeSocketIOServer()
    manager = WsManager(socketio, threading.RLock())

    await manager.handle_connect(NAMESPACE, "sid-utc")
    info = manager.connections[(NAMESPACE, "sid-utc")]

    assert info.connected_at.tzinfo is not None
    assert info.last_activity.tzinfo is not None

    with patch("helpers.ws_manager._utcnow") as mocked_now:
        mocked_now.return_value = info.last_activity
        await manager.route_event(NAMESPACE, "unknown", {}, "sid-utc")
        assert info.last_activity.tzinfo is not None

class DuplicateHandler(WsHandler):
    async def process(self, event: str, data: dict[str, Any], sid: str):
        return {"handledBy": self.identifier}


class AnotherDuplicateHandler(WsHandler):
    async def process(self, event: str, data: dict[str, Any], sid: str):
        return {"handledBy": self.identifier}


def test_register_handlers_warns_on_duplicates(monkeypatch):
    socketio = FakeSocketIOServer()
    manager = WsManager(socketio, threading.RLock())

    warnings: list[str] = []

    def capture_warning(message: str) -> None:
        warnings.append(message)

    monkeypatch.setattr(
        "helpers.print_style.PrintStyle.warning", staticmethod(capture_warning)
    )

    handler_a = DuplicateHandler(socketio, threading.RLock())

    manager.register_handlers({NAMESPACE: [handler_a, handler_a]})

    assert any("Duplicate handler registration" in msg for msg in warnings)


class NonDictHandler(WsHandler):
    async def process(self, event: str, data: dict[str, Any], sid: str):
        return "raw-value"


@pytest.mark.asyncio
async def test_route_event_standardizes_success_payload():
    socketio = FakeSocketIOServer()
    manager = WsManager(socketio, threading.RLock())

    handler = NonDictHandler(socketio, threading.RLock())
    manager.register_handlers({NAMESPACE: [handler]})

    response = await manager.route_event(NAMESPACE, "non_dict", {}, "sid-123")

    assert len(response["results"]) == 1
    assert response["results"][0]["ok"] is True
    assert response["results"][0]["data"] == {"result": "raw-value"}


class ErrorHandler(WsHandler):
    async def process(self, event: str, data: dict[str, Any], sid: str):
        raise RuntimeError("BOOM")


class ResultHandler(WsHandler):
    async def process(self, event: str, data: dict[str, Any], sid: str):
        if event == "result_event":
            return WsResult.ok({"sid": sid}, correlation_id="explicit", duration_ms=1.234)
        return WsResult.error(
            code="E_RESULT",
            message="boom",
            details="test",
        )


@pytest.mark.asyncio
async def test_route_event_standardizes_error_payload():
    socketio = FakeSocketIOServer()
    manager = WsManager(socketio, threading.RLock())

    handler = ErrorHandler(socketio, threading.RLock())
    manager.register_handlers({NAMESPACE: [handler]})

    response = await manager.route_event(NAMESPACE, "boom", {}, "sid-123")

    assert len(response["results"]) == 1
    payload = response["results"][0]
    assert payload["ok"] is False
    assert payload["error"]["code"] == "HANDLER_ERROR"
    assert payload["error"]["error"] == "Internal server error"


@pytest.mark.asyncio
async def test_route_event_accepts_websocket_result_instances():
    socketio = FakeSocketIOServer()
    manager = WsManager(socketio, threading.RLock())

    handler = ResultHandler(socketio, threading.RLock())
    manager.register_handlers({NAMESPACE: [handler]})

    response = await manager.route_event(NAMESPACE, "result_event", {}, "sid-123")

    assert response["results"]
    payload = response["results"][0]
    assert payload["ok"] is True
    assert payload["data"] == {"sid": "sid-123"}
    assert payload["correlationId"] == "explicit"
    assert payload["durationMs"] == pytest.approx(1.234, rel=1e-3)


@pytest.mark.asyncio
async def test_route_event_preserves_websocket_result_errors():
    socketio = FakeSocketIOServer()
    manager = WsManager(socketio, threading.RLock())

    handler = ResultHandler(socketio, threading.RLock())
    manager.register_handlers({NAMESPACE: [handler]})

    response = await manager.route_event(NAMESPACE, "result_error", {}, "sid-123")

    payload = response["results"][0]
    assert payload["ok"] is False
    assert payload["error"] == {"code": "E_RESULT", "error": "boom", "details": "test"}


class AlphaFilterHandler(WsHandler):
    async def process(self, event: str, data: dict[str, Any], sid: str):
        return {"handledBy": self.identifier, "sid": sid}


class BetaFilterHandler(WsHandler):
    async def process(self, event: str, data: dict[str, Any], sid: str):
        return {"handledBy": self.identifier, "sid": sid}


@pytest.mark.asyncio
async def test_route_event_include_handlers_filters_results():
    socketio = FakeSocketIOServer()
    manager = WsManager(socketio, threading.RLock())

    alpha = AlphaFilterHandler(socketio, threading.RLock())
    beta = BetaFilterHandler(socketio, threading.RLock())
    manager.register_handlers({NAMESPACE: [alpha, beta]})
    await manager.handle_connect(NAMESPACE, "sid-filter")

    response = await manager.route_event(
        NAMESPACE,
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
    manager = WsManager(socketio, threading.RLock())

    handler = AlphaFilterHandler(socketio, threading.RLock())
    manager.register_handlers({NAMESPACE: [handler]})
    await manager.handle_connect(NAMESPACE, "sid-exclude")

    response = await manager.route_event(
        NAMESPACE,
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
    manager = WsManager(socketio, threading.RLock())

    alpha = AlphaFilterHandler(socketio, threading.RLock())
    beta = BetaFilterHandler(socketio, threading.RLock())
    manager.register_handlers({NAMESPACE: [alpha, beta]})

    await manager.handle_connect(NAMESPACE, "sid-a")
    await manager.handle_connect(NAMESPACE, "sid-b")

    aggregated = await manager.route_event_all(
        NAMESPACE,
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
    manager = WsManager(socketio, threading.RLock())

    results = []
    handler = DummyHandler(socketio, threading.RLock(), results)
    manager.register_handlers({NAMESPACE: [handler]})
    await manager.handle_connect(NAMESPACE, "sid-correlation")

    response = await manager.route_event(
        NAMESPACE,
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
    manager = WsManager(socketio, threading.RLock())

    handler = DummyHandler(socketio, threading.RLock())
    manager.register_handlers({NAMESPACE: [handler]})
    await manager.handle_connect(NAMESPACE, "sid-request")

    response = await manager.request_for_sid(
        namespace=NAMESPACE,
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
    manager = WsManager(socketio, threading.RLock())

    handler = DummyHandler(socketio, threading.RLock())
    manager.register_handlers({NAMESPACE: [handler]})

    await manager.handle_connect(NAMESPACE, "sid-1")
    await manager.handle_connect(NAMESPACE, "sid-2")

    aggregated = await manager.route_event_all(
        NAMESPACE,
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
    manager = WsManager(socketio, threading.RLock())

    logs: list[str] = []

    def capture(message: str) -> None:
        logs.append(message)

    monkeypatch.setattr("helpers.print_style.PrintStyle.debug", staticmethod(capture))
    monkeypatch.setenv("A0_WS_DEBUG", "")

    manager._debug("should-not-log")  # noqa: SLF001
    assert logs == []

    monkeypatch.setenv("A0_WS_DEBUG", "1")
    manager._debug("should-log")  # noqa: SLF001
    assert logs == ["should-log"]


@pytest.mark.asyncio
async def test_diagnostic_event_emitted_for_inbound():
    socketio = FakeSocketIOServer()
    manager = WsManager(socketio, threading.RLock())

    results: list[dict[str, Any]] = []
    handler = DummyHandler(socketio, threading.RLock(), results)
    manager.register_handlers({NAMESPACE: [handler]})

    await manager.handle_connect(NAMESPACE, "observer")
    assert manager.register_diagnostic_watcher(NAMESPACE, "observer") is True
    await manager.handle_connect(NAMESPACE, "sid-client")

    await manager.route_event(NAMESPACE, "dummy", {"payload": "value"}, "sid-client")

    emitted_events = [call.args[0] for call in socketio.emit.await_args_list]
    assert DIAGNOSTIC_EVENT in emitted_events


@pytest.mark.asyncio
async def test_lifecycle_events_broadcast(monkeypatch):
    socketio = FakeSocketIOServer()
    manager = WsManager(socketio, threading.RLock())

    broadcast_mock = AsyncMock()
    monkeypatch.setattr(manager, "broadcast", broadcast_mock)

    await manager.handle_connect(NAMESPACE, "sid-life")
    await asyncio.sleep(0)
    await manager.handle_disconnect(NAMESPACE, "sid-life")
    await asyncio.sleep(0)

    events = [call.args[1] for call in broadcast_mock.await_args_list]
    assert LIFECYCLE_CONNECT_EVENT in events
    assert LIFECYCLE_DISCONNECT_EVENT in events
