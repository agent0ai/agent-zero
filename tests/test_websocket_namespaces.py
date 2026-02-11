import asyncio
import contextlib
import socket
import sys
import threading
from pathlib import Path
from typing import Any, AsyncIterator
from unittest.mock import AsyncMock

import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from python.helpers.state_monitor import StateMonitor
from python.helpers.websocket_manager import WebSocketManager


class FakeSocketIOServer:
    def __init__(self) -> None:
        self.emit = AsyncMock()
        self.disconnect = AsyncMock()


@contextlib.asynccontextmanager
async def _run_asgi_app(app: Any) -> AsyncIterator[str]:
    import uvicorn

    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    sock.bind(("127.0.0.1", 0))
    sock.listen(128)

    port = sock.getsockname()[1]

    config = uvicorn.Config(
        app,
        host="127.0.0.1",
        port=port,
        log_level="warning",
        access_log=False,
        lifespan="off",
    )
    server = uvicorn.Server(config)
    server.install_signal_handlers = lambda: None  # type: ignore[method-assign]

    task = asyncio.create_task(server.serve(sockets=[sock]))
    try:
        while not server.started:
            await asyncio.sleep(0.01)
        yield f"http://127.0.0.1:{port}"
    finally:
        server.should_exit = True
        try:
            await asyncio.wait_for(task, timeout=5)
        finally:
            sock.close()


@pytest.mark.asyncio
async def test_manager_identity_is_namespace_and_sid_allows_same_sid_across_namespaces() -> (
    None
):
    socketio = FakeSocketIOServer()
    manager = WebSocketManager(socketio, threading.RLock())
    # Avoid flakiness from lifecycle broadcasts scheduled via asyncio.create_task.
    manager._schedule_lifecycle_broadcast = lambda *_args, **_kwargs: None  # type: ignore[assignment]

    sid = "shared-sid"
    ns_a = "/a"
    ns_b = "/b"

    await manager.handle_connect(ns_a, sid)
    await manager.handle_connect(ns_b, sid)

    assert (ns_a, sid) in manager.connections
    assert (ns_b, sid) in manager.connections

    await manager.handle_disconnect(ns_a, sid)
    assert (ns_a, sid) not in manager.connections
    assert (ns_b, sid) in manager.connections

    await manager.emit_to(
        ns_a, sid, "test_event", {"value": 1}, correlation_id="corr-1"
    )

    assert (ns_a, sid) in manager.buffers
    assert (ns_b, sid) not in manager.buffers
    assert socketio.emit.await_count == 0


def test_state_monitor_tracks_two_identities_for_same_sid_across_namespaces() -> None:
    monitor = StateMonitor()
    sid = "shared-sid"
    monitor.register_sid("/a", sid)
    monitor.register_sid("/b", sid)

    debug = monitor._debug_state()
    assert ("/a", sid) in debug["identities"]
    assert ("/b", sid) in debug["identities"]


@pytest.mark.asyncio
async def test_namespace_isolation_state_sync_vs_dev_websocket_test() -> None:
    """
    CONTRACT.INVARIANT.NS.ISOLATION: no cross-namespace delivery for application events.

    Acceptance proof for `/state_sync` vs `/dev_websocket_test` namespaces.
    """

    import socketio
    from flask import Flask

    from python.helpers.websocket import WebSocketHandler
    from python.helpers.websocket_manager import WebSocketManager
    from run_ui import configure_websocket_namespaces

    class StateHandler(WebSocketHandler):
        @classmethod
        def requires_auth(cls) -> bool:
            return False

        @classmethod
        def requires_csrf(cls) -> bool:
            return False

        @classmethod
        def get_event_types(cls) -> list[str]:
            return ["state_request"]

        async def process_event(self, event_type: str, data: dict[str, Any], sid: str):
            await self.emit_to(sid, "state_push", {"source": "state_sync"})
            return {"ok": True}

    class DevHandler(WebSocketHandler):
        @classmethod
        def requires_auth(cls) -> bool:
            return False

        @classmethod
        def requires_csrf(cls) -> bool:
            return False

        @classmethod
        def get_event_types(cls) -> list[str]:
            return ["ws_tester_emit"]

        async def process_event(self, event_type: str, data: dict[str, Any], sid: str):
            await self.broadcast(
                "ws_tester_broadcast", {"source": "dev_websocket_test"}
            )
            return None

    StateHandler._reset_instance_for_testing()
    DevHandler._reset_instance_for_testing()

    webapp = Flask("test_namespace_isolation")
    webapp.secret_key = "test-secret"

    sio = socketio.AsyncServer(
        async_mode="asgi", cors_allowed_origins="*", namespaces="*"
    )
    lock = threading.RLock()
    manager = WebSocketManager(sio, lock)

    configure_websocket_namespaces(
        webapp=webapp,
        socketio_server=sio,
        websocket_manager=manager,
        handlers_by_namespace={
            "/state_sync": [StateHandler.get_instance(sio, lock)],
            "/dev_websocket_test": [DevHandler.get_instance(sio, lock)],
        },
    )

    asgi_app = socketio.ASGIApp(sio)

    async with _run_asgi_app(asgi_app) as base_url:
        client = socketio.AsyncClient()

        state_push_state = asyncio.Event()
        state_push_dev = asyncio.Event()
        tester_broadcast_dev = asyncio.Event()
        tester_broadcast_state = asyncio.Event()

        async def _on_state_push_state(_payload: Any) -> None:
            state_push_state.set()

        async def _on_state_push_dev(_payload: Any) -> None:
            state_push_dev.set()

        async def _on_tester_broadcast_dev(_payload: Any) -> None:
            tester_broadcast_dev.set()

        async def _on_tester_broadcast_state(_payload: Any) -> None:
            tester_broadcast_state.set()

        client.on("state_push", _on_state_push_state, namespace="/state_sync")
        client.on("state_push", _on_state_push_dev, namespace="/dev_websocket_test")
        client.on(
            "ws_tester_broadcast",
            _on_tester_broadcast_dev,
            namespace="/dev_websocket_test",
        )
        client.on(
            "ws_tester_broadcast", _on_tester_broadcast_state, namespace="/state_sync"
        )

        await client.connect(
            base_url,
            namespaces=["/state_sync", "/dev_websocket_test"],
            headers={"Origin": base_url},
            wait_timeout=2,
        )
        try:
            await client.call(
                "state_request", {"context": None}, namespace="/state_sync", timeout=2
            )
            await asyncio.wait_for(state_push_state.wait(), timeout=2)
            await asyncio.sleep(0.05)
            assert state_push_dev.is_set() is False

            await client.emit(
                "ws_tester_emit", {"message": "hi"}, namespace="/dev_websocket_test"
            )
            await asyncio.wait_for(tester_broadcast_dev.wait(), timeout=2)
            await asyncio.sleep(0.05)
            assert tester_broadcast_state.is_set() is False
        finally:
            await client.disconnect()


@pytest.mark.asyncio
async def test_diagnostics_include_source_namespace_and_deliver_on_dev_namespace_only() -> (
    None
):
    """
    CONTRACT.Diagnostics: dev console diagnostics are delivered on `/dev_websocket_test`,
    but must include `sourceNamespace` identifying the origin namespace.
    """

    from python.helpers.websocket import WebSocketHandler
    from python.helpers.websocket_manager import DIAGNOSTIC_EVENT, WebSocketManager

    class DummyHandler(WebSocketHandler):
        @classmethod
        def get_event_types(cls) -> list[str]:
            return ["dummy_event"]

        async def process_event(self, event_type: str, data: dict[str, Any], sid: str):
            return {"ok": True}

    DummyHandler._reset_instance_for_testing()

    socketio = FakeSocketIOServer()
    manager = WebSocketManager(socketio, threading.RLock())
    manager._schedule_lifecycle_broadcast = lambda *_args, **_kwargs: None  # type: ignore[assignment]

    ns_state = "/state_sync"
    ns_dev = "/dev_websocket_test"

    handler = DummyHandler.get_instance(socketio, threading.RLock())
    manager.register_handlers({ns_state: [handler]})

    await manager.handle_connect(ns_dev, "sid-watcher")
    await manager.handle_connect(ns_state, "sid-client")
    assert manager.register_diagnostic_watcher(ns_dev, "sid-watcher") is True

    socketio.emit.reset_mock()

    await manager.route_event(ns_state, "dummy_event", {"payload": True}, "sid-client")

    calls = [(call.args, call.kwargs) for call in socketio.emit.await_args_list]
    diagnostic = next((c for c in calls if c[0] and c[0][0] == DIAGNOSTIC_EVENT), None)
    assert diagnostic is not None

    args, kwargs = diagnostic
    envelope = args[1]
    assert kwargs == {"to": "sid-watcher", "namespace": ns_dev}
    assert envelope["data"]["sourceNamespace"] == ns_state


def test_namespace_discovery_maps_core_handlers_to_expected_namespaces() -> None:
    """
    US1 regression: ensure discovery assigns core handlers to their dedicated namespaces
    (no cross-registration).
    """

    from python.helpers.websocket_namespace_discovery import (
        discover_websocket_namespaces,
    )

    discoveries = discover_websocket_namespaces(
        handlers_folder="python/websocket_handlers",
        include_root_default=True,
    )
    by_namespace = {entry.namespace: entry for entry in discoveries}

    assert "/state_sync" in by_namespace
    assert "/dev_websocket_test" in by_namespace

    state_cls_names = [
        cls.__name__ for cls in by_namespace["/state_sync"].handler_classes
    ]
    dev_cls_names = [
        cls.__name__ for cls in by_namespace["/dev_websocket_test"].handler_classes
    ]

    assert state_cls_names == ["StateSyncHandler"]
    assert dev_cls_names == ["DevWebsocketTestHandler"]


def test_run_ui_builds_namespace_handler_map_without_cross_registration() -> None:
    from run_ui import _build_websocket_handlers_by_namespace

    handlers_by_namespace = _build_websocket_handlers_by_namespace(
        object(), threading.RLock()
    )

    assert "/state_sync" in handlers_by_namespace
    assert "/dev_websocket_test" in handlers_by_namespace

    assert all(
        handler.__class__.__name__ != "DevWebsocketTestHandler"
        for handler in handlers_by_namespace["/state_sync"]
    )
    assert all(
        handler.__class__.__name__ != "StateSyncHandler"
        for handler in handlers_by_namespace["/dev_websocket_test"]
    )


@pytest.mark.asyncio
async def test_route_event_dispatches_only_within_connected_namespace_and_results_are_scoped() -> (
    None
):
    """
    CONTRACT.NS.ROUTING: inbound routing is restricted to handlers in the connected namespace.
    """

    from python.helpers.websocket import WebSocketHandler

    socketio = FakeSocketIOServer()
    manager = WebSocketManager(socketio, threading.RLock())
    manager._schedule_lifecycle_broadcast = lambda *_args, **_kwargs: None  # type: ignore[assignment]

    ns_state = "/state_sync"
    ns_dev = "/dev_websocket_test"

    calls: list[str] = []

    class StatePingHandler(WebSocketHandler):
        @classmethod
        def get_event_types(cls) -> list[str]:
            return ["route_test"]

        async def process_event(self, event_type: str, data: dict[str, Any], sid: str):
            calls.append(f"state:{sid}")
            return {"ns": "state"}

    class DevPingHandler(WebSocketHandler):
        @classmethod
        def get_event_types(cls) -> list[str]:
            return ["route_test"]

        async def process_event(self, event_type: str, data: dict[str, Any], sid: str):
            calls.append(f"dev:{sid}")
            return {"ns": "dev"}

    StatePingHandler._reset_instance_for_testing()
    DevPingHandler._reset_instance_for_testing()

    state_handler = StatePingHandler.get_instance(socketio, threading.RLock())
    dev_handler = DevPingHandler.get_instance(socketio, threading.RLock())

    manager.register_handlers({ns_state: [state_handler], ns_dev: [dev_handler]})
    await manager.handle_connect(ns_state, "sid-state")
    await manager.handle_connect(ns_dev, "sid-dev")

    res_state = await manager.route_event(ns_state, "route_test", {"x": 1}, "sid-state")
    assert {item["handlerId"] for item in res_state["results"]} == {
        state_handler.identifier
    }
    assert res_state["results"][0]["data"]["ns"] == "state"

    res_dev = await manager.route_event(ns_dev, "route_test", {"x": 2}, "sid-dev")
    assert {item["handlerId"] for item in res_dev["results"]} == {
        dev_handler.identifier
    }
    assert res_dev["results"][0]["data"]["ns"] == "dev"

    assert calls == ["state:sid-state", "dev:sid-dev"]


@pytest.mark.asyncio
async def test_lifecycle_broadcasts_deliver_only_within_the_namespace() -> None:
    """
    CONTRACT.NS.DELIVERY: lifecycle broadcasts are namespace-scoped.
    """

    from python.helpers.websocket_manager import (
        LIFECYCLE_CONNECT_EVENT,
        LIFECYCLE_DISCONNECT_EVENT,
    )

    socketio = FakeSocketIOServer()
    manager = WebSocketManager(socketio, threading.RLock())

    ns_state = "/state_sync"
    ns_dev = "/dev_websocket_test"

    # Connect events should broadcast only within their namespace.
    await manager.handle_connect(ns_state, "sid-state-1")
    await asyncio.sleep(0)
    state_connect_calls = [
        call
        for call in socketio.emit.await_args_list
        if call.args and call.args[0] == LIFECYCLE_CONNECT_EVENT
    ]
    assert state_connect_calls
    assert all(call.kwargs.get("namespace") == ns_state for call in state_connect_calls)

    socketio.emit.reset_mock()
    await manager.handle_connect(ns_dev, "sid-dev-1")
    await asyncio.sleep(0)
    dev_connect_calls = [
        call
        for call in socketio.emit.await_args_list
        if call.args and call.args[0] == LIFECYCLE_CONNECT_EVENT
    ]
    assert dev_connect_calls
    assert all(call.kwargs.get("namespace") == ns_dev for call in dev_connect_calls)

    # Disconnect broadcasts go to remaining peers in that namespace only.
    socketio.emit.reset_mock()
    await manager.handle_connect(ns_state, "sid-state-2")
    await manager.handle_connect(ns_dev, "sid-dev-2")
    socketio.emit.reset_mock()

    await manager.handle_disconnect(ns_state, "sid-state-2")
    await asyncio.sleep(0)
    state_disconnect_calls = [
        call
        for call in socketio.emit.await_args_list
        if call.args and call.args[0] == LIFECYCLE_DISCONNECT_EVENT
    ]
    assert state_disconnect_calls
    assert all(
        call.kwargs.get("namespace") == ns_state for call in state_disconnect_calls
    )
    assert all(
        call.kwargs.get("to") == "sid-state-1" for call in state_disconnect_calls
    )


@pytest.mark.asyncio
async def test_request_semantics_no_handlers_and_timeouts_are_namespace_scoped_and_order_insensitive() -> (
    None
):
    """
    CONTRACT.REQUEST.RESULTS + CONTRACT.REQUEST.RESULTS.ORDERING + CONTRACT.NS.ROUTING.
    """

    from python.helpers.websocket import WebSocketHandler

    socketio = FakeSocketIOServer()
    manager = WebSocketManager(socketio, threading.RLock())
    manager._schedule_lifecycle_broadcast = lambda *_args, **_kwargs: None  # type: ignore[assignment]

    ns_state = "/state_sync"
    ns_dev = "/dev_websocket_test"

    class Alpha(WebSocketHandler):
        @classmethod
        def get_event_types(cls) -> list[str]:
            return ["multi", "slow"]

        async def process_event(self, event_type: str, data: dict[str, Any], sid: str):
            if event_type == "slow":
                await asyncio.sleep(0.2)
                return {"alpha": True}
            return {"alpha": True}

    class Beta(WebSocketHandler):
        @classmethod
        def get_event_types(cls) -> list[str]:
            return ["multi"]

        async def process_event(self, event_type: str, data: dict[str, Any], sid: str):
            return {"beta": True}

    Alpha._reset_instance_for_testing()
    Beta._reset_instance_for_testing()
    alpha = Alpha.get_instance(socketio, threading.RLock())
    beta = Beta.get_instance(socketio, threading.RLock())

    manager.register_handlers({ns_state: [alpha, beta]})
    await manager.handle_connect(ns_state, "sid-a")
    await manager.handle_connect(ns_state, "sid-b")
    await manager.handle_connect(ns_dev, "sid-dev")

    # Unknown event name -> NO_HANDLERS (no hang), scoped to the namespace.
    no_handler = await manager.route_event(ns_dev, "missing_event", {"x": 1}, "sid-dev")
    assert no_handler["results"][0]["ok"] is False
    assert no_handler["results"][0]["error"]["code"] == "NO_HANDLERS"
    assert ns_dev in no_handler["results"][0]["error"]["error"]

    # Unknown event name in a namespace that *does* have other handlers -> NO_HANDLERS.
    unhandled_in_state = await manager.route_event(
        ns_state, "unknown_event", {"x": 1}, "sid-a"
    )
    assert unhandled_in_state["results"][0]["ok"] is False
    assert unhandled_in_state["results"][0]["error"]["code"] == "NO_HANDLERS"
    assert ns_state in unhandled_in_state["results"][0]["error"]["error"]

    # Known event name in the wrong namespace -> NO_HANDLERS (no cross-namespace fallback).
    wrong_namespace = await manager.route_event(ns_dev, "multi", {"x": 1}, "sid-dev")
    assert wrong_namespace["results"][0]["ok"] is False
    assert wrong_namespace["results"][0]["error"]["code"] == "NO_HANDLERS"
    assert ns_dev in wrong_namespace["results"][0]["error"]["error"]

    # Order-insensitive results[]: both handlers must be present regardless of ordering.
    multi = await manager.route_event(ns_state, "multi", {"x": 1}, "sid-a")
    handler_ids = {item["handlerId"] for item in multi["results"]}
    assert handler_ids == {alpha.identifier, beta.identifier}

    # Timeout results are represented as TIMEOUT items and scoped to the namespace.
    aggregated = await manager.route_event_all(
        ns_state, "slow", {"x": 1}, timeout_ms=50
    )
    assert len(aggregated) == 2  # only state namespace connections
    assert {entry["sid"] for entry in aggregated} == {"sid-a", "sid-b"}
    for entry in aggregated:
        assert entry["results"]
        assert entry["results"][0]["ok"] is False
        assert entry["results"][0]["error"]["code"] == "TIMEOUT"

    # Allow the underlying slow route_event coroutines to complete so pytest's event loop
    # teardown does not cancel them mid-flight (avoids noisy InvalidStateError callbacks).
    await asyncio.sleep(0.3)
