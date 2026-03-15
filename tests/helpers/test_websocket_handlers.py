import sys
import threading
from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from python.helpers.websocket import (
    WebSocketHandler,
    WebSocketResult,
    SingletonInstantiationError,
)


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
    _TestHandler._reset_instance_for_testing()
    return _TestHandler.get_instance(_FakeSocketIO(), threading.RLock())


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


def test_handler_direct_instantiation_disallowed():
    with pytest.raises(SingletonInstantiationError):
        _TestHandler(_FakeSocketIO(), threading.RLock())


def test_get_instance_returns_singleton():
    _TestHandler._reset_instance_for_testing()
    socketio = _FakeSocketIO()
    lock = threading.RLock()
    first = _TestHandler.get_instance(socketio, lock)
    second = _TestHandler.get_instance(None, None)
    assert first is second


@pytest.mark.asyncio
async def test_state_sync_handler_registers_and_routes_state_request():
    from python.helpers.websocket_manager import WebSocketManager
    from python.websocket_handlers.state_sync_handler import StateSyncHandler
    from python.helpers.state_monitor import _reset_state_monitor_for_testing

    _reset_state_monitor_for_testing()
    StateSyncHandler._reset_instance_for_testing()

    socketio = _FakeSocketIO()
    lock = threading.RLock()
    manager = WebSocketManager(socketio, lock)
    handler = StateSyncHandler.get_instance(socketio, lock)
    namespace = "/state_sync"
    manager.register_handlers({namespace: [handler]})
    await manager.handle_connect(namespace, "sid-1")

    response = await manager.route_event(
        namespace,
        "state_request",
        {
            "correlationId": "smoke-1",
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

    assert response["correlationId"] == "smoke-1"
    assert response["results"] and response["results"][0]["ok"] is True
    await manager.handle_disconnect(namespace, "sid-1")


# --- RootDefaultHandler (_default.py) ---


@pytest.mark.asyncio
async def test_root_default_handler_requires_no_auth_or_csrf():
    from python.websocket_handlers._default import RootDefaultHandler

    assert RootDefaultHandler.requires_auth() is False
    assert RootDefaultHandler.requires_csrf() is False


@pytest.mark.asyncio
async def test_root_default_handler_processes_ws_root_echo():
    from python.helpers.websocket_manager import WebSocketManager
    from python.websocket_handlers._default import RootDefaultHandler

    RootDefaultHandler._reset_instance_for_testing()
    socketio = _FakeSocketIO()
    lock = threading.RLock()
    manager = WebSocketManager(socketio, lock)
    handler = RootDefaultHandler.get_instance(socketio, lock)
    manager.register_handlers({"/": [handler]})
    await manager.handle_connect("/", "sid-root")

    response = await manager.route_event(
        "/",
        "ws_root_echo",
        {"payload": "test-data", "nested": {"a": 1}},
        "sid-root",
    )

    assert response["results"]
    first = response["results"][0]
    assert first["ok"] is True
    data = first["data"]
    assert data["ok"] is True
    assert data["namespace"] == "/"
    assert data["sid"] == "sid-root"
    echo = data["echo"]
    assert echo["payload"] == "test-data"
    assert echo["nested"] == {"a": 1}


# --- HelloHandler (hello_handler.py) ---


@pytest.mark.asyncio
async def test_hello_handler_processes_hello_request():
    from python.helpers.websocket_manager import WebSocketManager
    from python.websocket_handlers.hello_handler import HelloHandler

    HelloHandler._reset_instance_for_testing()
    socketio = _FakeSocketIO()
    lock = threading.RLock()
    manager = WebSocketManager(socketio, lock)
    handler = HelloHandler.get_instance(socketio, lock)
    manager.register_handlers({"/hello": [handler]})
    await manager.handle_connect("/hello", "sid-hello")

    response = await manager.route_event(
        "/hello",
        "hello_request",
        {"name": "Alice"},
        "sid-hello",
    )

    assert response["results"]
    first = response["results"][0]
    assert first["ok"] is True
    data = first["data"]
    assert data["message"] == "Hello, Alice!"
    assert "handler" in data


@pytest.mark.asyncio
async def test_hello_handler_defaults_to_stranger_when_no_name():
    from python.helpers.websocket_manager import WebSocketManager
    from python.websocket_handlers.hello_handler import HelloHandler

    HelloHandler._reset_instance_for_testing()
    socketio = _FakeSocketIO()
    lock = threading.RLock()
    manager = WebSocketManager(socketio, lock)
    handler = HelloHandler.get_instance(socketio, lock)
    manager.register_handlers({"/hello": [handler]})
    await manager.handle_connect("/hello", "sid-hello")

    response = await manager.route_event(
        "/hello",
        "hello_request",
        {},
        "sid-hello",
    )

    assert response["results"][0]["data"]["message"] == "Hello, stranger!"


# --- DevWebsocketTestHandler (dev_websocket_test_handler.py) ---


@pytest.mark.asyncio
async def test_dev_websocket_test_handler_ws_tester_request():
    from python.helpers.websocket_manager import WebSocketManager
    from python.websocket_handlers.dev_websocket_test_handler import DevWebsocketTestHandler

    DevWebsocketTestHandler._reset_instance_for_testing()
    socketio = _FakeSocketIO()
    lock = threading.RLock()
    manager = WebSocketManager(socketio, lock)
    manager._schedule_lifecycle_broadcast = lambda *_args, **_kwargs: None
    handler = DevWebsocketTestHandler.get_instance(socketio, lock)
    manager.register_handlers({"/dev_websocket_test": [handler]})
    await manager.handle_connect("/dev_websocket_test", "sid-dev")

    response = await manager.route_event(
        "/dev_websocket_test",
        "ws_tester_request",
        {"value": 42, "correlationId": "cid-1"},
        "sid-dev",
    )

    assert response["results"]
    first = response["results"][0]
    assert first["ok"] is True
    assert first["data"]["echo"] == 42
    assert first["data"]["status"] == "ok"


@pytest.mark.asyncio
async def test_dev_websocket_test_handler_ws_tester_request_delayed():
    from python.helpers.websocket_manager import WebSocketManager
    from python.websocket_handlers.dev_websocket_test_handler import DevWebsocketTestHandler

    DevWebsocketTestHandler._reset_instance_for_testing()
    socketio = _FakeSocketIO()
    lock = threading.RLock()
    manager = WebSocketManager(socketio, lock)
    manager._schedule_lifecycle_broadcast = lambda *_args, **_kwargs: None
    handler = DevWebsocketTestHandler.get_instance(socketio, lock)
    manager.register_handlers({"/dev_websocket_test": [handler]})
    await manager.handle_connect("/dev_websocket_test", "sid-dev")

    response = await manager.route_event(
        "/dev_websocket_test",
        "ws_tester_request_delayed",
        {"delay_ms": 10, "correlationId": "cid-delayed"},
        "sid-dev",
    )

    assert response["results"][0]["ok"] is True
    assert response["results"][0]["data"]["status"] == "delayed"
    assert response["results"][0]["data"]["delay_ms"] == 10


@pytest.mark.asyncio
async def test_dev_websocket_test_handler_unknown_event_returns_error():
    from python.helpers.websocket_manager import WebSocketManager
    from python.websocket_handlers.dev_websocket_test_handler import DevWebsocketTestHandler

    DevWebsocketTestHandler._reset_instance_for_testing()
    socketio = _FakeSocketIO()
    lock = threading.RLock()
    manager = WebSocketManager(socketio, lock)
    manager._schedule_lifecycle_broadcast = lambda *_args, **_kwargs: None
    handler = DevWebsocketTestHandler.get_instance(socketio, lock)
    manager.register_handlers({"/dev_websocket_test": [handler]})
    await manager.handle_connect("/dev_websocket_test", "sid-dev")

    response = await manager.route_event(
        "/dev_websocket_test",
        "unknown_event_type",
        {},
        "sid-dev",
    )

    assert response["results"][0]["ok"] is False
    assert response["results"][0]["error"]["code"] == "HARNESS_UNKNOWN_EVENT"
