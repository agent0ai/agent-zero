import threading
from abc import abstractmethod
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Union

import socketio
from flask import Flask, session, request

from agent import AgentContext
from initialize import initialize_agent
from helpers import files, cache
from helpers.api import is_loopback_address
from helpers.print_style import PrintStyle
from helpers.errors import format_error
from helpers.websocket import validate_ws_origin

ThreadLockType = Union[threading.Lock, threading.RLock]

CACHE_AREA = "ws_handlers(api)(plugins)"
cache.toggle_area(CACHE_AREA, False)  # cache off for now


@dataclass
class _SecurityContext:
    auth_hash: str | None
    csrf_token: str | None
    client_csrf_token: str | None
    csrf_cookie: str | None
    remote_addr: str | None
    api_key: str | None


_ws_contexts: dict[str, _SecurityContext] = {}
_active_handlers: dict[str, dict[str, "WsHandler"]] = {}
_contexts_lock = threading.Lock()


class WsHandler:
    def __init__(self, socketio_server: socketio.AsyncServer, lock: ThreadLockType):
        self.socketio = socketio_server
        self.lock = lock

    @classmethod
    def requires_loopback(cls) -> bool:
        return False

    @classmethod
    def requires_api_key(cls) -> bool:
        return False

    @classmethod
    def requires_auth(cls) -> bool:
        return True

    @classmethod
    def requires_csrf(cls) -> bool:
        return cls.requires_auth()

    @abstractmethod
    async def process(self, data: dict, sid: str) -> dict | None:
        pass

    async def on_connect(self, sid: str) -> dict | None:
        return None

    async def on_disconnect(self, sid: str) -> None:
        pass

    def use_context(self, ctxid: str, create_if_not_exists: bool = True):
        with self.lock:
            if not ctxid:
                first = AgentContext.first()
                if first:
                    AgentContext.use(first.id)
                    return first
                context = AgentContext(config=initialize_agent(), set_current=True)
                return context
            got = AgentContext.use(ctxid)
            if got:
                return got
            if create_if_not_exists:
                context = AgentContext(config=initialize_agent(), id=ctxid, set_current=True)
                return context
            else:
                raise Exception(f"Context {ctxid} not found")


def _check_security(handler_cls: type[WsHandler], ctx: _SecurityContext) -> dict[str, Any] | None:
    if handler_cls.requires_loopback():
        if not ctx.remote_addr or not is_loopback_address(ctx.remote_addr):
            return {"ok": False, "error": "Access denied", "code": 403}

    if handler_cls.requires_auth():
        from helpers import login
        user_pass_hash = login.get_credentials_hash()
        if user_pass_hash and ctx.auth_hash != user_pass_hash:
            return {"ok": False, "error": "Authentication required", "code": 401}

    if handler_cls.requires_csrf():
        if not ctx.csrf_token:
            return {"ok": False, "error": "CSRF token not initialised", "code": 403}
        if not ctx.client_csrf_token or ctx.client_csrf_token != ctx.csrf_token:
            return {"ok": False, "error": "CSRF token missing or invalid", "code": 403}
        if ctx.csrf_cookie != ctx.csrf_token:
            return {"ok": False, "error": "CSRF cookie mismatch", "code": 403}

    if handler_cls.requires_api_key():
        from helpers.settings import get_settings
        valid_key = get_settings().get("mcp_server_token")
        if not ctx.api_key or ctx.api_key != valid_key:
            return {"ok": False, "error": "API key required", "code": 401}

    return None


def register_ws_namespace(
    socketio_server: socketio.AsyncServer,
    webapp: Flask,
    lock: ThreadLockType,
) -> None:
    from helpers.modules import load_classes_from_file
    from helpers import plugins, runtime

    def _resolve_handler(path: str) -> type[WsHandler] | None:
        handler_cls: type[WsHandler] | None = None

        # Check built-in api/<path>.py
        builtin_file = files.get_abs_path(f"api/{path}.py")
        if files.is_in_dir(builtin_file, files.get_abs_path("api")) and files.exists(builtin_file):
            classes = load_classes_from_file(builtin_file, WsHandler)
            if classes:
                handler_cls = classes[0]

        # Check plugin api/<handler>.py — path format: plugins/<plugin_name>/<handler>
        if handler_cls is None and path.startswith("plugins/"):
            parts = path.split("/", 2)
            if len(parts) == 3:
                _, plugin_name, handler_name = parts
                plugin_dir = plugins.find_plugin_dir(plugin_name)
                if plugin_dir:
                    plugin_file = Path(plugin_dir) / "api" / f"{handler_name}.py"
                    if plugin_file.is_file():
                        classes = load_classes_from_file(str(plugin_file), WsHandler)
                        if classes:
                            handler_cls = classes[0]

        return handler_cls

    def _resolve_cached(path: str) -> type[WsHandler] | None:
        cached = cache.get(CACHE_AREA, path)
        if cached is not None:
            return cached
        handler_cls = _resolve_handler(path)
        if handler_cls is not None:
            cache.add(CACHE_AREA, path, handler_cls)
        return handler_cls

    @socketio_server.on("connect", namespace="/ws") # type: ignore
    async def _on_connect(sid, environ, auth):
        with webapp.request_context(environ):
            origin_ok, origin_reason = validate_ws_origin(environ)
            if not origin_ok:
                PrintStyle.warning(
                    f"WS /ws connect rejected for {sid}: {origin_reason or 'invalid'}"
                )
                return False

            ctx = _SecurityContext(
                auth_hash=session.get("authentication"),
                csrf_token=session.get("csrf_token"),
                client_csrf_token=(
                    (auth.get("csrf_token") or auth.get("csrfToken"))
                    if isinstance(auth, dict) else None
                ),
                csrf_cookie=request.cookies.get(
                    f"csrf_token_{runtime.get_runtime_id()}"
                ),
                remote_addr=str(request.remote_addr) if request.remote_addr else None,
                api_key=(
                    (auth.get("api_key") or auth.get("apiKey"))
                    if isinstance(auth, dict) else None
                ),
            )
            with _contexts_lock:
                _ws_contexts[sid] = ctx

        # Activate handlers declared in auth.handlers
        handler_paths = []
        if isinstance(auth, dict):
            raw = auth.get("handlers")
            if isinstance(raw, list):
                handler_paths = [p for p in raw if isinstance(p, str)]

        activated: dict[str, WsHandler] = {}
        for path in handler_paths:
            try:
                handler_cls = _resolve_cached(path)
                if handler_cls is None:
                    continue
                error = _check_security(handler_cls, ctx)
                if error is not None:
                    continue
                instance = handler_cls(socketio_server, lock)
                await instance.on_connect(sid)
                activated[path] = instance
            except Exception as e:
                PrintStyle.error(f"WS on_connect error ({path}): {format_error(e)}")

        with _contexts_lock:
            _active_handlers[sid] = activated

        return True

    @socketio_server.on("disconnect", namespace="/ws") # type: ignore
    async def _on_disconnect(sid):
        with _contexts_lock:
            activated = _active_handlers.pop(sid, {})
            _ws_contexts.pop(sid, None)

        for path, instance in activated.items():
            try:
                await instance.on_disconnect(sid)
            except Exception as e:
                PrintStyle.error(f"WS on_disconnect error ({path}): {format_error(e)}")

    @socketio_server.on("*", namespace="/ws") # type: ignore
    async def _dispatch(event, sid, data):
        path = event
        payload = data if isinstance(data, dict) else {}

        try:
            with _contexts_lock:
                ctx = _ws_contexts.get(sid)
                activated = _active_handlers.get(sid, {})
            if ctx is None:
                return {"ok": False, "error": "No security context", "code": 401}

            instance = activated.get(path)
            if instance is None:
                return {"ok": False, "error": f"WS endpoint not activated: {path}", "code": 404}

            # Security check
            error = _check_security(type(instance), ctx)
            if error is not None:
                return error

            # Use cached instance and process
            return await instance.process(payload, sid)

        except Exception as e:
            error_text = format_error(e)
            PrintStyle.error(f"WS handler error ({path}): {error_text}")
            return {"ok": False, "error": error_text, "code": 500}