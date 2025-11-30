import sys
from pathlib import Path
import time

import pytest
from flask import Flask, request, session

import threading
import asyncio

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from python.api.csrf_token import GetCsrfToken
from python.helpers import login, runtime
from python.helpers.print_style import PrintStyle
from python.helpers.websocket import (
    WS_CSRF_TTL_SECONDS,
    WebSocketHandler,
    set_ws_csrf_flag,
    validate_ws_csrf_flag,
)
from python.helpers.websocket_manager import WebSocketManager
import socketio


class DummyHandler(WebSocketHandler):
    @classmethod
    def get_event_types(cls) -> list[str]:
        return ["dummy"]

    @classmethod
    def requires_auth(cls) -> bool:
        return True

    @classmethod
    def requires_csrf(cls) -> bool:
        return True

    async def process_event(self, event_type: str, data: dict, sid: str):
        return {"echo": data}


@pytest.fixture()
def app_context(monkeypatch):
    monkeypatch.setenv("AUTH_LOGIN", "admin")
    monkeypatch.setenv("AUTH_PASSWORD", "secret")

    app = Flask("ws-test")
    app.secret_key = "test-secret"
    sio = socketio.AsyncServer(async_mode="asgi", cors_allowed_origins=[])
    lock = threading.RLock()
    manager = WebSocketManager(sio, lock)

    monkeypatch.setattr(runtime, "get_runtime_id", lambda: "test-runtime", raising=False)

    DummyHandler._reset_instance_for_testing()
    handler = DummyHandler.get_instance(sio, lock)
    manager.register_handlers([handler])

    csrf_handler = GetCsrfToken(app, lock)

    @app.route("/csrf_token", methods=["GET", "POST"])
    async def csrf_token_route():
        return await csrf_handler.handle_request(request)

    websocket_handlers = [handler]

    async def perform_handshake():
        sid = "test-sid"
        requires_auth = any(h.requires_auth() for h in websocket_handlers)
        if requires_auth:
            credentials_hash = login.get_credentials_hash()
            if credentials_hash:
                if session.get("authentication") != credentials_hash:
                    PrintStyle.warning(
                        f"WebSocket authentication failed for {sid}: session not valid"
                    )
                    return False
        csrf_expiry = None
        requires_csrf = any(h.requires_csrf() for h in websocket_handlers)
        if requires_csrf:
            now_ts = time.time()
            ok, reason, expiry = validate_ws_csrf_flag(session, now_ts)
            if not ok:
                PrintStyle.warning(
                    f"WebSocket CSRF validation failed for {sid}: {reason or 'invalid'}"
                )
                return False
            csrf_expiry = expiry
        await manager.handle_connect(sid, csrf_expiry)
        await manager.handle_disconnect(sid)
        return True

    yield app, manager, perform_handshake

    with manager.lock:
        manager.connections.clear()
        manager.handlers.clear()


@pytest.mark.asyncio
async def test_websocket_connect_with_valid_preflight(app_context):
    app, _, perform_handshake = app_context

    with app.test_request_context("/"):
        session["authentication"] = login.get_credentials_hash()
        set_ws_csrf_flag(session, time.time(), WS_CSRF_TTL_SECONDS)
        assert await perform_handshake() is True


@pytest.mark.asyncio
async def test_websocket_connect_fails_after_ttl_expired(app_context):
    app, _, perform_handshake = app_context

    with app.test_request_context("/"):
        session["authentication"] = login.get_credentials_hash()
        set_ws_csrf_flag(session, time.time() - WS_CSRF_TTL_SECONDS - 1, WS_CSRF_TTL_SECONDS)
        assert await perform_handshake() is False


@pytest.mark.asyncio
async def test_websocket_reconnect_after_refresh(app_context):
    app, _, perform_handshake = app_context

    with app.test_request_context("/"):
        session["authentication"] = login.get_credentials_hash()
        set_ws_csrf_flag(session, time.time() - WS_CSRF_TTL_SECONDS - 1, WS_CSRF_TTL_SECONDS)
        assert await perform_handshake() is False

    with app.test_request_context("/"):
        session["authentication"] = login.get_credentials_hash()
        set_ws_csrf_flag(session, time.time(), WS_CSRF_TTL_SECONDS)
        assert await perform_handshake() is True
