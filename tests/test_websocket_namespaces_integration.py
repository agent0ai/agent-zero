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
async def test_unregistered_namespace_connection_fails_with_unknown_namespace_connect_error() -> None:
    """
    US5 integration: unregistered namespace connections fail deterministically with a structured
    connect_error payload (UNKNOWN_NAMESPACE), independent of python-socketio defaults.
    """

    from flask import Flask
    import socketio

    from python.helpers.websocket import WebSocketHandler
    from python.helpers.websocket_manager import WebSocketManager
    from run_ui import configure_websocket_namespaces

    class OpenHandler(WebSocketHandler):
        @classmethod
        def requires_auth(cls) -> bool:
            return False

        @classmethod
        def requires_csrf(cls) -> bool:
            return False

        @classmethod
        def get_event_types(cls) -> list[str]:
            return ["open_ping"]

        async def process_event(self, event_type: str, data: dict[str, Any], sid: str):
            return {"ok": True}

    OpenHandler._reset_instance_for_testing()

    webapp = Flask("test_ws_namespaces_integration")
    webapp.secret_key = "test-secret"

    sio = socketio.AsyncServer(async_mode="asgi", cors_allowed_origins="*", namespaces="*")
    lock = __import__("threading").RLock()
    manager = WebSocketManager(sio, lock)

    configure_websocket_namespaces(
        webapp=webapp,
        socketio_server=sio,
        websocket_manager=manager,
        handlers_by_namespace={"/open": [OpenHandler.get_instance(sio, lock)]},
    )

    asgi_app = socketio.ASGIApp(sio)

    async with _run_asgi_app(asgi_app) as base_url:
        client = socketio.AsyncClient()
        connect_error_fut: asyncio.Future[Any] = asyncio.get_running_loop().create_future()

        async def _on_connect_error(data: Any) -> None:
            if not connect_error_fut.done():
                connect_error_fut.set_result(data)

        client.on("connect_error", _on_connect_error, namespace="/unknown")

        try:
            with pytest.raises(socketio.exceptions.ConnectionError):
                await client.connect(base_url, namespaces=["/unknown"])

            err = await asyncio.wait_for(connect_error_fut, timeout=2)
            assert err["message"] == "UNKNOWN_NAMESPACE"
            assert err["data"] == {"code": "UNKNOWN_NAMESPACE", "namespace": "/unknown"}
        finally:
            try:
                await client.disconnect()
            except Exception:
                pass
