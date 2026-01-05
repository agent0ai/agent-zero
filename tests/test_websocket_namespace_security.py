import asyncio
import contextlib
import socket
import sys
import threading
from pathlib import Path
from typing import Any, AsyncIterator

import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


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


def _make_session_cookie(app: Any, data: dict[str, Any]) -> str:
    from flask.sessions import SecureCookieSessionInterface

    serializer = SecureCookieSessionInterface().get_signing_serializer(app)
    assert serializer is not None
    return serializer.dumps(data)


@pytest.mark.asyncio
async def test_connect_security_is_computed_per_namespace_and_enforced(monkeypatch) -> None:
    from flask import Flask
    import socketio

    from python.helpers.websocket import WebSocketHandler
    from python.helpers.websocket_manager import WebSocketManager
    from python.helpers import runtime
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

        async def process_event(self, event_type: str, data: dict[str, Any], sid: str) -> dict[str, Any]:
            return {"ok": True}

    class SecureHandler(WebSocketHandler):
        @classmethod
        def get_event_types(cls) -> list[str]:
            return ["secure_ping"]

        async def process_event(self, event_type: str, data: dict[str, Any], sid: str) -> dict[str, Any]:
            return {"ok": True}

    OpenHandler._reset_instance_for_testing()
    SecureHandler._reset_instance_for_testing()

    monkeypatch.setattr("python.helpers.login.get_credentials_hash", lambda: "hash")

    webapp = Flask("test_websocket_namespace_security")
    webapp.secret_key = "test-secret"

    sio = socketio.AsyncServer(async_mode="asgi", cors_allowed_origins="*", namespaces="*")
    lock = threading.RLock()
    manager = WebSocketManager(sio, lock)
    handlers_by_namespace = {
        "/open": [OpenHandler.get_instance(sio, lock)],
        "/secure": [SecureHandler.get_instance(sio, lock)],
    }

    configure_websocket_namespaces(
        webapp=webapp,
        socketio_server=sio,
        websocket_manager=manager,
        handlers_by_namespace=handlers_by_namespace,
    )

    asgi_app = socketio.ASGIApp(sio)

    async with _run_asgi_app(asgi_app) as base_url:
        # Open namespace should not require auth/csrf (but Origin validation is always enforced).
        open_client = socketio.AsyncClient()
        await open_client.connect(
            base_url,
            namespaces=["/open"],
            headers={"Origin": base_url},
            wait_timeout=2,
        )
        try:
            res = await open_client.call("open_ping", {}, namespace="/open", timeout=2)
            assert isinstance(res, dict)
            assert res.get("results")
            res_unhandled = await open_client.call("unhandled_event", {"x": 1}, namespace="/open", timeout=2)
            assert res_unhandled["results"]
            assert res_unhandled["results"][0]["ok"] is False
            assert res_unhandled["results"][0]["error"]["code"] == "NO_HANDLERS"
        finally:
            await open_client.disconnect()

        # Secure namespace rejects without valid session+csrf when credentials are configured.
        secure_client = socketio.AsyncClient()
        with pytest.raises(socketio.exceptions.ConnectionError):
            await secure_client.connect(
                base_url,
                namespaces=["/secure"],
                headers={"Origin": base_url},
                wait_timeout=2,
            )
        await secure_client.disconnect()

        # Secure namespace accepts valid session + auth csrf_token + runtime-scoped csrf cookie.
        csrf_token = "csrf-1"
        session_cookie = _make_session_cookie(
            webapp,
            {
                "authentication": "hash",
                "csrf_token": csrf_token,
                "user_id": "u1",
            },
        )
        session_cookie_name = webapp.config.get("SESSION_COOKIE_NAME", "session")
        csrf_cookie_name = f"csrf_token_{runtime.get_runtime_id()}"
        cookie_header = f"{session_cookie_name}={session_cookie}; {csrf_cookie_name}={csrf_token}"

        secure_client_ok = socketio.AsyncClient()
        await secure_client_ok.connect(
            base_url,
            namespaces=["/secure"],
            headers={"Origin": base_url, "Cookie": cookie_header},
            auth={"csrf_token": csrf_token},
            wait_timeout=2,
        )
        try:
            res2 = await secure_client_ok.call("secure_ping", {}, namespace="/secure", timeout=2)
            assert isinstance(res2, dict)
            assert res2.get("results")
        finally:
            await secure_client_ok.disconnect()


@pytest.mark.asyncio
async def test_unknown_namespace_rejected_with_deterministic_connect_error_payload() -> None:
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

        async def process_event(self, event_type: str, data: dict[str, Any], sid: str) -> dict[str, Any]:
            return {"ok": True}

    OpenHandler._reset_instance_for_testing()

    webapp = Flask("test_unknown_namespace_rejection")
    webapp.secret_key = "test-secret"

    sio = socketio.AsyncServer(async_mode="asgi", cors_allowed_origins="*", namespaces="*")
    lock = threading.RLock()
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
