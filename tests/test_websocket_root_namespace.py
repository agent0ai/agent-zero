import asyncio
import contextlib
import socket
from typing import Any, AsyncIterator

import pytest


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
async def test_root_namespace_request_style_calls_resolve_with_no_handlers() -> None:
    """
    CONTRACT.INVARIANT.NS.ROOT.UNHANDLED: root (`/`) is reserved and unhandled for application
    events by default, but request-style calls must not hang (NO_HANDLERS).
    """

    import socketio
    from flask import Flask

    from python.helpers.websocket import WebSocketHandler
    from python.helpers.websocket_manager import WebSocketManager
    from run_ui import configure_websocket_namespaces

    app = Flask("test_ws_root_namespace")
    app.secret_key = "test-secret"

    calls: list[str] = []

    class HelloHandler(WebSocketHandler):
        @classmethod
        def requires_auth(cls) -> bool:
            return False

        @classmethod
        def requires_csrf(cls) -> bool:
            return False

        @classmethod
        def get_event_types(cls) -> list[str]:
            return ["hello_request"]

        async def process_event(self, event_type: str, data: dict[str, Any], sid: str):
            calls.append(sid)
            return {"hello": True}

    HelloHandler._reset_instance_for_testing()

    sio = socketio.AsyncServer(
        async_mode="asgi", cors_allowed_origins="*", namespaces="*"
    )
    lock = __import__("threading").RLock()
    manager = WebSocketManager(sio, lock)

    configure_websocket_namespaces(
        webapp=app,
        socketio_server=sio,
        websocket_manager=manager,
        handlers_by_namespace={
            "/state_sync": [HelloHandler.get_instance(sio, lock)],
        },
    )

    asgi_app = socketio.ASGIApp(sio)

    async with _run_asgi_app(asgi_app) as base_url:
        client = socketio.AsyncClient()
        await client.connect(
            base_url,
            namespaces=["/"],
            headers={"Origin": base_url},
            wait_timeout=2,
        )
        try:
            res_unknown = await client.call(
                "unknown_event", {"x": 1}, namespace="/", timeout=2
            )
            assert res_unknown["results"][0]["ok"] is False
            assert res_unknown["results"][0]["error"]["code"] == "NO_HANDLERS"

            res_known_elsewhere = await client.call(
                "hello_request", {"name": "x"}, namespace="/", timeout=2
            )
            assert res_known_elsewhere["results"][0]["ok"] is False
            assert res_known_elsewhere["results"][0]["error"]["code"] == "NO_HANDLERS"
            assert calls == []
        finally:
            await client.disconnect()


@pytest.mark.asyncio
async def test_root_namespace_fire_and_forget_does_not_invoke_application_handlers() -> (
    None
):
    """
    Fire-and-forget emits on `/` must not invoke any application handler.
    """

    import socketio
    from flask import Flask

    from python.helpers.websocket import WebSocketHandler
    from python.helpers.websocket_manager import WebSocketManager
    from run_ui import configure_websocket_namespaces

    app = Flask("test_ws_root_fire_and_forget")
    app.secret_key = "test-secret"

    calls: list[str] = []

    class SideEffectHandler(WebSocketHandler):
        @classmethod
        def requires_auth(cls) -> bool:
            return False

        @classmethod
        def requires_csrf(cls) -> bool:
            return False

        @classmethod
        def get_event_types(cls) -> list[str]:
            return ["hello_request"]

        async def process_event(self, event_type: str, data: dict[str, Any], sid: str):
            calls.append(sid)
            return {"ok": True}

    SideEffectHandler._reset_instance_for_testing()

    sio = socketio.AsyncServer(
        async_mode="asgi", cors_allowed_origins="*", namespaces="*"
    )
    lock = __import__("threading").RLock()
    manager = WebSocketManager(sio, lock)

    configure_websocket_namespaces(
        webapp=app,
        socketio_server=sio,
        websocket_manager=manager,
        handlers_by_namespace={
            "/state_sync": [SideEffectHandler.get_instance(sio, lock)],
        },
    )

    asgi_app = socketio.ASGIApp(sio)

    async with _run_asgi_app(asgi_app) as base_url:
        client = socketio.AsyncClient()
        await client.connect(
            base_url,
            namespaces=["/"],
            headers={"Origin": base_url},
            wait_timeout=2,
        )
        try:
            await client.emit("hello_request", {"name": "x"}, namespace="/")
            await asyncio.sleep(0.1)
            assert calls == []
        finally:
            await client.disconnect()
