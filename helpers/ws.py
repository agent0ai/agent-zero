import os
import threading
import uuid
from abc import abstractmethod
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable, Union, TYPE_CHECKING
from urllib.parse import urlparse

import socketio
from flask import Flask, session, request

from helpers import files, cache
from helpers.print_style import PrintStyle
from helpers.errors import format_error

if TYPE_CHECKING:
    from helpers.ws_manager import WsManager


# Shared types and utilities

from helpers.network import is_loopback_address

ConnectionIdentity = tuple[str, str]  # (namespace, sid)


def _ws_debug_enabled() -> bool:
    """Check A0_WS_DEBUG env var — lightweight, no heavy imports."""
    value = os.getenv("A0_WS_DEBUG", "").strip().lower()
    return value in {"1", "true", "yes", "on"}


def ws_debug(message: str) -> None:
    """Log *message* via :class:`PrintStyle` when ``A0_WS_DEBUG`` is active."""
    if _ws_debug_enabled():
        PrintStyle.debug(message)


class ConnectionNotFoundError(RuntimeError):
    """Raised when attempting to emit to a non-existent WebSocket connection."""

    def __init__(self, sid: str, *, namespace: str | None = None) -> None:
        self.sid = sid
        self.namespace = namespace
        if namespace:
            super().__init__(f"Connection not found: namespace={namespace} sid={sid}")
        else:
            super().__init__(f"Connection not found: {sid}")


def _default_port_for_scheme(scheme: str) -> int | None:
    if scheme == "http":
        return 80
    if scheme == "https":
        return 443
    return None


def normalize_origin(value: Any) -> str | None:
    """Normalize an Origin/Referer header value to scheme://host[:port]."""
    if not isinstance(value, str) or not value.strip():
        return None
    parsed = urlparse(value.strip())
    if not parsed.scheme or not parsed.hostname:
        return None
    origin = f"{parsed.scheme}://{parsed.hostname}"
    if parsed.port:
        origin += f":{parsed.port}"
    return origin


def _parse_host_header(value: Any) -> tuple[str | None, int | None]:
    if not isinstance(value, str) or not value.strip():
        return None, None
    parsed = urlparse(f"http://{value.strip()}")
    return parsed.hostname, parsed.port


def validate_ws_origin(environ: dict[str, Any]) -> tuple[bool, str | None]:
    """Validate the browser Origin during the Socket.IO handshake.

    This is the minimum baseline recommended by RFC 6455 (Origin considerations)
    and OWASP (CSWSH mitigation): reject cross-origin WebSocket handshakes when
    the server is intended for a specific web UI origin.
    """

    raw_origin = environ.get("HTTP_ORIGIN") or environ.get("HTTP_REFERER")
    origin = normalize_origin(raw_origin)
    if origin is None:
        return False, "missing_origin"

    origin_parsed = urlparse(origin)
    origin_host = origin_parsed.hostname.lower() if origin_parsed.hostname else None
    origin_port = origin_parsed.port or _default_port_for_scheme(origin_parsed.scheme)
    if origin_host is None or origin_port is None:
        return False, "invalid_origin"

    raw_host = environ.get("HTTP_HOST")
    req_host, req_port = _parse_host_header(raw_host)
    if not req_host:
        req_host = environ.get("SERVER_NAME")

    if req_port is None:
        server_port_raw = environ.get("SERVER_PORT")
        try:
            server_port = int(server_port_raw) if server_port_raw is not None else None
        except (TypeError, ValueError):
            server_port = None
        if server_port is not None and server_port > 0:
            req_port = server_port

    if req_host:
        req_host = req_host.lower()
    if req_port is None:
        req_port = origin_port

    forwarded_host_raw = environ.get("HTTP_X_FORWARDED_HOST")
    forwarded_host = None
    forwarded_port = None
    if isinstance(forwarded_host_raw, str) and forwarded_host_raw.strip():
        first = forwarded_host_raw.split(",")[0].strip()
        forwarded_host, forwarded_port = _parse_host_header(first)
        if forwarded_host:
            forwarded_host = forwarded_host.lower()

    forwarded_proto_raw = environ.get("HTTP_X_FORWARDED_PROTO")
    forwarded_scheme = None
    if isinstance(forwarded_proto_raw, str) and forwarded_proto_raw.strip():
        forwarded_scheme = forwarded_proto_raw.split(",")[0].strip().lower()
    forwarded_scheme = forwarded_scheme or origin_parsed.scheme
    forwarded_port = (
        forwarded_port
        if forwarded_port is not None
        else _default_port_for_scheme(forwarded_scheme) or origin_port
    )

    candidates: list[tuple[str, int]] = []
    if req_host:
        candidates.append((req_host, int(req_port)))
    if forwarded_host:
        candidates.append((forwarded_host, int(forwarded_port)))

    if not candidates:
        return False, "missing_host"

    for host, port in candidates:
        if origin_host == host and origin_port == port:
            return True, None

    if origin_host not in {host for host, _ in candidates}:
        return False, "origin_host_mismatch"
    return False, "origin_port_mismatch"


# Constants

ThreadLockType = Union[threading.Lock, threading.RLock]

NAMESPACE = "/ws"
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
    """Base class for WebSocket handlers loaded from api/ directories.

    Mirrors ApiHandler conventions: declarative security flags, dynamic file-
    based loading, and a ``process(event, data, sid)`` entry point.  Handlers
    are activated per-connection based on the ``auth.handlers`` list sent by the
    client during the Socket.IO connect handshake.
    """

    def __init__(
        self,
        socketio_server: socketio.AsyncServer,
        lock: ThreadLockType,
        *,
        manager: "WsManager | None" = None,
        namespace: str = NAMESPACE,
    ):
        self.socketio = socketio_server
        self.lock = lock
        self._manager = manager
        self._namespace = namespace

    # Properties

    @property
    def namespace(self) -> str:
        return self._namespace

    @property
    def manager(self) -> "WsManager":
        if self._manager is None:
            raise RuntimeError("WsHandler has no WsManager bound")
        return self._manager

    @property
    def identifier(self) -> str:
        return f"{self.__class__.__module__}.{self.__class__.__name__}"

    def bind_manager(
        self, manager: "WsManager", *, namespace: str | None = None
    ) -> None:
        """Late-bind (or rebind) the manager and optionally the namespace."""
        self._manager = manager
        if namespace is not None:
            self._namespace = namespace

    # Security flags (mirror ApiHandler)

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

    # Lifecycle hooks

    async def on_connect(self, sid: str) -> None:
        pass

    async def on_disconnect(self, sid: str) -> None:
        pass

    # Event processing

    @abstractmethod
    async def process(self, event: str, data: dict, sid: str) -> dict | None:
        """Handle an incoming event.

        Return a dict to include in the acknowledgement, or ``None`` for
        fire-and-forget semantics.
        """

    # Emit helpers (delegate to WsManager for envelope wrapping)

    async def emit_to(
        self,
        sid: str,
        event: str,
        data: dict,
        *,
        correlation_id: str | None = None,
    ) -> None:
        await self.manager.emit_to(
            self._namespace, sid, event, data,
            handler_id=self.identifier,
            correlation_id=correlation_id,
        )

    async def broadcast(
        self,
        event: str,
        data: dict,
        *,
        exclude_sids: str | Iterable[str] | None = None,
        correlation_id: str | None = None,
    ) -> None:
        await self.manager.broadcast(
            self._namespace, event, data,
            exclude_sids=exclude_sids,
            handler_id=self.identifier,
            correlation_id=correlation_id,
        )

    # Aggregation helper

    async def dispatch_to_all_sids(
        self,
        event: str,
        data: dict,
        *,
        correlation_id: str | None = None,
    ) -> list[dict[str, Any]]:
        """Dispatch *event* to every connected sid's activated handlers and
        aggregate the results.

        Returns a list of ``{sid, correlationId, results}`` dicts – one per
        connected sid.  This mirrors the shape produced by
        ``WsManager.route_event_all`` so that existing frontend
        assertions remain valid.
        """
        cid = correlation_id or uuid.uuid4().hex

        with _contexts_lock:
            snapshot = {
                sid: dict(handlers)
                for sid, handlers in _active_handlers.items()
            }
            contexts_snapshot = dict(_ws_contexts)

        mgr = self._manager
        aggregated: list[dict[str, Any]] = []
        for sid, handlers in snapshot.items():
            ctx = contexts_snapshot.get(sid)
            # Skip sids whose security context was removed (concurrent disconnect).
            if ctx is None:
                continue
            security_errors: list[dict[str, Any]] = []
            passing: list[WsHandler] = []
            for _path, instance in handlers.items():
                error = _check_security(type(instance), ctx)
                if error is not None:
                    security_errors.append({
                        "handlerId": instance.identifier,
                        "ok": False,
                        "correlationId": cid,
                        "error": error,
                    })
                    continue
                passing.append(instance)

            if mgr is not None and passing:
                result = await mgr.process_client_event(
                    self._namespace, event,
                    dict(data, correlationId=cid), sid,
                    handlers=passing,
                )
                sid_results = security_errors + result.get("results", [])
            else:
                # Fallback: inline processing
                sid_results = list(security_errors)
                for _path, instance in handlers.items():
                    if instance not in passing:
                        continue
                    try:
                        result = await instance.process(
                            event, dict(data, correlationId=cid), sid,
                        )
                        if result is not None:
                            sid_results.append({
                                "handlerId": instance.identifier,
                                "ok": True,
                                "correlationId": cid,
                                "data": result,
                            })
                    except Exception as e:
                        sid_results.append({
                            "handlerId": instance.identifier,
                            "ok": False,
                            "correlationId": cid,
                            "error": {"code": "HANDLER_ERROR", "error": str(e)},
                        })
            aggregated.append({
                "sid": sid,
                "correlationId": cid,
                "results": sid_results,
            })
        return aggregated

    # Context helper (shared with ApiHandler)

    def use_context(self, ctxid: str, create_if_not_exists: bool = True):
        from helpers.context_utils import use_context as _use_context
        return _use_context(self.lock, ctxid, create_if_not_exists)


# Security check (aligned with api.py decorators)

def _check_security(handler_cls: type[WsHandler], ctx: _SecurityContext) -> dict[str, Any] | None:
    """Return an error payload dict if the check fails, or ``None`` on success."""

    if handler_cls.requires_loopback():
        if not ctx.remote_addr or not is_loopback_address(ctx.remote_addr):
            return {"code": "FORBIDDEN", "error": "Access denied"}

    if handler_cls.requires_auth():
        from helpers import login
        user_pass_hash = login.get_credentials_hash()
        if user_pass_hash and ctx.auth_hash != user_pass_hash:
            return {"code": "AUTH_REQUIRED", "error": "Authentication required"}

    if handler_cls.requires_csrf():
        if not ctx.csrf_token:
            return {"code": "CSRF_MISSING", "error": "CSRF token not initialised"}
        if not ctx.client_csrf_token or ctx.client_csrf_token != ctx.csrf_token:
            return {"code": "CSRF_INVALID", "error": "CSRF token missing or invalid"}
        if ctx.csrf_cookie != ctx.csrf_token:
            return {"code": "CSRF_COOKIE", "error": "CSRF cookie mismatch"}

    if handler_cls.requires_api_key():
        from helpers.settings import get_settings
        valid_key = get_settings().get("mcp_server_token")
        if not ctx.api_key or ctx.api_key != valid_key:
            return {"code": "API_KEY_REQUIRED", "error": "API key required"}

    return None


# Namespace registration

def register_ws_namespace(
    socketio_server: socketio.AsyncServer,
    webapp: Flask,
    lock: ThreadLockType,
    manager: "WsManager | None" = None,
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

        # Check user api/<path>.py
        if handler_cls is None:
            user_file = files.get_abs_path(files.USER_DIR, f"api/{path}.py")
            if files.exists(user_file):
                classes = load_classes_from_file(user_file, WsHandler)
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

    @socketio_server.on("connect", namespace=NAMESPACE)  # type: ignore
    async def _on_connect(sid, environ, auth):
        with webapp.request_context(environ):
            origin_ok, origin_reason = validate_ws_origin(environ)
            if not origin_ok:
                PrintStyle.warning(
                    f"WS connect rejected for {sid}: {origin_reason or 'invalid'}"
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
            user_id = session.get("user_id") or "single_user"

            with _contexts_lock:
                _ws_contexts[sid] = ctx

        # Register with WsManager first so that the dispatcher loop and
        # connection tracking are available before handler on_connect runs
        # (extensions like StateSync depend on manager._dispatcher_loop).
        if manager is not None:
            await manager.handle_connect(NAMESPACE, sid, user_id=user_id)

        # Activate handlers declared in auth.handlers
        handler_paths: list[str] = []
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
                instance = handler_cls(
                    socketio_server, lock,
                    manager=manager, namespace=NAMESPACE,
                )
                await instance.on_connect(sid)
                activated[path] = instance
            except Exception as e:
                PrintStyle.error(f"WS on_connect error ({path}): {format_error(e)}")

        with _contexts_lock:
            _active_handlers[sid] = activated

        return True

    @socketio_server.on("disconnect", namespace=NAMESPACE)  # type: ignore
    async def _on_disconnect(sid):
        with _contexts_lock:
            activated = _active_handlers.pop(sid, {})
            _ws_contexts.pop(sid, None)

        for path, instance in activated.items():
            try:
                await instance.on_disconnect(sid)
            except Exception as e:
                PrintStyle.error(f"WS on_disconnect error ({path}): {format_error(e)}")

        if manager is not None:
            await manager.handle_disconnect(NAMESPACE, sid)

    @socketio_server.on("*", namespace=NAMESPACE)  # type: ignore
    async def _dispatch(event, sid, data):
        incoming = data if isinstance(data, dict) else {}

        try:
            with _contexts_lock:
                ctx = _ws_contexts.get(sid)
                activated = dict(_active_handlers.get(sid, {}))

            correlation_id = incoming.get("correlationId") or uuid.uuid4().hex

            if ctx is None:
                return _error_response("AUTH_REQUIRED",
                                       "No security context", correlation_id)
            if not activated:
                return _error_response("NO_HANDLERS",
                                       "No handlers activated", correlation_id)

            # Pre-filter handlers through security checks
            passing_handlers: list[WsHandler] = []
            security_errors: list[dict[str, Any]] = []
            for path, instance in activated.items():
                error = _check_security(type(instance), ctx)
                if error is not None:
                    security_errors.append({
                        "handlerId": instance.identifier,
                        "ok": False,
                        "correlationId": correlation_id,
                        "error": error,
                    })
                else:
                    passing_handlers.append(instance)

            # Delegate to WsManager for unified processing pipeline
            # (worker thread isolation, diagnostic events, WsResult support)
            if manager is not None and passing_handlers:
                result = await manager.process_client_event(
                    NAMESPACE, event, incoming, sid,
                    handlers=passing_handlers,
                )
                if security_errors:
                    result["results"] = security_errors + result.get("results", [])
                return result

            # All handlers failed security or no manager — return collected errors
            if not passing_handlers:
                return {"correlationId": correlation_id, "results": security_errors}

            # Fallback: inline processing (no manager — should not happen in practice)
            handler_payload: dict[str, Any]
            if "data" in incoming and isinstance(incoming.get("data"), dict):
                handler_payload = dict(incoming["data"])
            else:
                handler_payload = dict(incoming)
            handler_payload["correlationId"] = correlation_id

            results: list[dict[str, Any]] = list(security_errors)
            for path, instance in activated.items():
                if instance not in passing_handlers:
                    continue
                try:
                    result = await instance.process(event, handler_payload, sid)
                    if result is not None:
                        results.append({
                            "handlerId": instance.identifier,
                            "ok": True,
                            "correlationId": correlation_id,
                            "data": result,
                        })
                except Exception as e:
                    error_text = format_error(e)
                    PrintStyle.error(f"WS handler error ({path}/{event}): {error_text}")
                    results.append({
                        "handlerId": instance.identifier,
                        "ok": False,
                        "correlationId": correlation_id,
                        "error": {"code": "HANDLER_ERROR", "error": "Internal server error"},
                    })

            return {"correlationId": correlation_id, "results": results}

        except Exception as e:
            error_text = format_error(e)
            PrintStyle.error(f"WS dispatch error ({event}): {error_text}")
            return _error_response(
                "INTERNAL_ERROR", "Internal server error",
                incoming.get("correlationId", ""),
            )


def _error_response(code: str, message: str,
                    correlation_id: str) -> dict[str, Any]:
    return {
        "correlationId": correlation_id,
        "results": [{
            "handlerId": "ws.dispatch",
            "ok": False,
            "error": {"code": code, "error": message},
        }],
    }