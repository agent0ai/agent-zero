from __future__ import annotations

import re
import threading
from abc import ABC, abstractmethod
from urllib.parse import urlparse
from typing import Any, Iterable, Optional, TYPE_CHECKING

import socketio

if TYPE_CHECKING:  # pragma: no cover - hints only
    from python.helpers.websocket_manager import WebSocketManager

_EVENT_NAME_PATTERN = re.compile(r"^[a-z][a-z0-9_]*$")
_RESERVED_EVENT_NAMES: set[str] = {
    "connect",
    "disconnect",
    "error",
    "ping",
    "pong",
    "connect_error",
    "reconnect",
    "reconnect_attempt",
    "reconnect_error",
    "reconnect_failed",
}


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

    # Build candidate request host/port pairs. Prefer explicit Host header, fall back to
    # forwarded headers (reverse proxies) and finally SERVER_NAME.
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

    # Preserve the original mismatch semantics for debugging.
    if origin_host not in {host for host, _ in candidates}:
        return False, "origin_host_mismatch"
    return False, "origin_port_mismatch"


class SingletonInstantiationError(RuntimeError):
    """Raised when a WebSocketHandler subclass is instantiated directly.

    Handlers must be retrieved via ``get_instance`` to guarantee singleton
    semantics and consistent lifecycle behaviour.
    """


class ConnectionNotFoundError(RuntimeError):
    """Raised when attempting to emit to a non-existent WebSocket connection."""

    def __init__(self, sid: str, *, namespace: str | None = None) -> None:
        self.sid = sid
        self.namespace = namespace
        if namespace:
            super().__init__(f"Connection not found: namespace={namespace} sid={sid}")
        else:
            super().__init__(f"Connection not found: {sid}")


class WebSocketResult:
    """Helper wrapper for standardized handler results.

    Instances are converted to the canonical ``RequestResultItem`` shape by
    :class:`WebSocketManager`. Helper constructors enforce payload validation so
    handlers no longer need to hand‑craft dictionaries.
    """

    __slots__ = ("_ok", "_data", "_error", "_correlation_id", "_duration_ms")

    def __init__(
        self,
        ok: bool,
        data: dict[str, Any] | None = None,
        error: dict[str, Any] | None = None,
        correlation_id: str | None = None,
        duration_ms: float | None = None,
    ) -> None:
        if ok and error:
            raise ValueError("Cannot be both ok and have an error")
        if not ok and not error:
            raise ValueError("Must either be ok or have an error")
        if data is not None and not isinstance(data, dict):
            raise TypeError("Data payload must be a dictionary or None")
        if error is not None and not isinstance(error, dict):
            raise TypeError("Error payload must be a dictionary or None")
        if correlation_id is not None and not isinstance(correlation_id, str):
            raise TypeError("Correlation ID must be a string or None")
        if duration_ms is not None and not isinstance(duration_ms, (int, float)):
            raise TypeError("Duration must be a number or None")

        self._ok = bool(ok)
        self._data = dict(data) if data is not None else None
        self._error = dict(error) if error is not None else None
        self._correlation_id = correlation_id
        self._duration_ms = float(duration_ms) if duration_ms is not None else None

    @classmethod
    def ok(
        cls,
        data: dict[str, Any] | None = None,
        *,
        correlation_id: str | None = None,
        duration_ms: float | None = None,
    ) -> "WebSocketResult":
        if data is not None and not isinstance(data, dict):
            raise TypeError("WebSocketResult.ok data must be a dict or None")
        payload = dict(data) if data is not None else None
        return cls(
            ok=True,
            data=payload,
            correlation_id=correlation_id,
            duration_ms=duration_ms,
        )

    @classmethod
    def error(
        cls,
        *,
        code: str,
        message: str,
        details: Any | None = None,
        correlation_id: str | None = None,
        duration_ms: float | None = None,
    ) -> "WebSocketResult":
        if not isinstance(code, str) or not code.strip():
            raise ValueError("Error code must be a non-empty string")
        if not isinstance(message, str) or not message.strip():
            raise ValueError("Error message must be a non-empty string")

        error_payload: dict[str, Any] = {"code": code, "error": message}
        if details is not None:
            error_payload["details"] = details
        return cls(
            ok=False,
            error=error_payload,
            correlation_id=correlation_id,
            duration_ms=duration_ms,
        )

    def as_result(
        self,
        *,
        handler_id: str,
        fallback_correlation_id: str | None,
        duration_ms: float | None = None,
    ) -> dict[str, Any]:
        result: dict[str, Any] = {
            "handlerId": handler_id,
            "ok": self._ok,
        }

        effective_duration = (
            self._duration_ms if self._duration_ms is not None else duration_ms
        )
        if effective_duration is not None:
            result["durationMs"] = round(effective_duration, 4)

        correlation = (
            self._correlation_id
            if self._correlation_id is not None
            else fallback_correlation_id
        )
        if correlation is not None:
            result["correlationId"] = correlation

        if self._ok:
            result["data"] = dict(self._data) if self._data is not None else {}
        else:
            result["error"] = dict(self._error) if self._error is not None else {
                "code": "INTERNAL_ERROR",
                "error": "Internal server error",
            }
        return result


class WebSocketHandler(ABC):
    """Base class for WebSocket event handlers.

    The interface mirrors :class:`python.helpers.api.ApiHandler` with declarative
    security configuration and lifecycle hooks while enforcing event-naming
    conventions.
    """

    _instances: dict[type["WebSocketHandler"], "WebSocketHandler"] = {}
    _construction_tokens: dict[type["WebSocketHandler"], bool] = {}
    _singleton_lock = threading.RLock()

    def __init__(self, socketio: socketio.AsyncServer, lock: threading.RLock) -> None:
        """Create a handler bound to the shared Socket.IO instance."""

        cls = self.__class__
        if not WebSocketHandler._construction_tokens.get(cls):
            raise SingletonInstantiationError(
                f"{cls.__name__} must be instantiated via {cls.__name__}.get_instance()"
            )

        self.socketio: socketio.AsyncServer = socketio
        self.lock: threading.RLock = lock
        self._manager: Optional[WebSocketManager] = None
        self._namespace: str | None = None

    @classmethod
    def get_instance(
        cls,
        socketio: socketio.AsyncServer | None = None,
        lock: threading.RLock | None = None,
        *args: Any,
        **kwargs: Any,
    ) -> "WebSocketHandler":
        """Return the singleton instance for ``cls``.

        Args:
            socketio: Shared AsyncServer instance (required on first call).
            lock: Shared threading lock (required on first call).
            *args: Optional subclass-specific constructor args.
            **kwargs: Optional subclass-specific constructor kwargs.
        """

        if cls is WebSocketHandler:
            raise TypeError("WebSocketHandler must be subclassed before use")

        with WebSocketHandler._singleton_lock:
            instance = WebSocketHandler._instances.get(cls)
            if instance is not None:
                return instance

            if socketio is None or lock is None:
                raise ValueError(
                    f"{cls.__name__}.get_instance() requires socketio and lock on first call"
                )

            WebSocketHandler._construction_tokens[cls] = True
            try:
                instance = cls(socketio, lock, *args, **kwargs)
            finally:
                WebSocketHandler._construction_tokens.pop(cls, None)

            WebSocketHandler._instances[cls] = instance
            return instance

    @classmethod
    def _reset_instance_for_testing(cls) -> None:
        """Reset the cached singleton instance (testing helper)."""

        with WebSocketHandler._singleton_lock:
            WebSocketHandler._instances.pop(cls, None)
            WebSocketHandler._construction_tokens.pop(cls, None)

    @classmethod
    @abstractmethod
    def get_event_types(cls) -> list[str]:
        """Return the list of event types this handler subscribes to."""

    @classmethod
    def validate_event_types(cls, event_types: Iterable[str]) -> list[str]:
        """Validate event type declarations.

        Ensures that every event name follows ``lowercase_snake_case`` naming,
        does not collide with Socket.IO reserved events, and that the handler
        does not declare duplicates.
        """

        validated: list[str] = []
        seen: set[str] = set()
        for event in event_types:
            if not isinstance(event, str):
                raise TypeError("Event type declarations must be strings")
            if not _EVENT_NAME_PATTERN.fullmatch(event):
                raise ValueError(
                    f"Invalid event type '{event}' – must match lowercase_snake_case"
                )
            if event in _RESERVED_EVENT_NAMES:
                raise ValueError(
                    f"Event type '{event}' is reserved by Socket.IO and cannot be used"
                )
            if event in seen:
                raise ValueError(f"Duplicate event type '{event}' declared in handler")
            seen.add(event)
            validated.append(event)
        if not validated:
            raise ValueError("Handlers must declare at least one event type")
        return validated

    @classmethod
    def requires_auth(cls) -> bool:
        """Return whether an authenticated Flask session is required."""

        return True

    @classmethod
    def requires_csrf(cls) -> bool:
        """Return whether CSRF validation is required for the handler.

        This mirrors ApiHandler.requires_csrf(): by default, authenticated
        WebSocket handlers also require CSRF validation during the Socket.IO
        connect step.
        """

        return cls.requires_auth()

    async def on_connect(self, sid: str) -> None:
        """Lifecycle hook invoked when a client connects."""

        return None

    async def on_disconnect(self, sid: str) -> None:
        """Lifecycle hook invoked when a client disconnects."""

        return None

    @abstractmethod
    async def process_event(
        self,
        event_type: str,
        data: dict[str, Any],
        sid: str,
    ) -> dict[str, Any] | WebSocketResult | None:
        """Process an incoming event dispatched to the handler.

        Returning ``None`` indicates fire-and-forget semantics. Returning a
        dictionary includes the payload in the Socket.IO acknowledgement.
        """

    def bind_manager(self, manager: WebSocketManager, *, namespace: str) -> None:
        """Associate this handler instance with the shared WebSocket manager."""

        self._manager = manager
        self._namespace = namespace

    @property
    def namespace(self) -> str:
        if not self._namespace:
            raise RuntimeError("WebSocketHandler is missing namespace binding")
        return self._namespace

    @property
    def manager(self) -> WebSocketManager:
        """Return the bound WebSocket manager.

        Raises:
            RuntimeError: If the handler has not been registered yet.
        """

        if not self._manager:
            raise RuntimeError("WebSocketHandler is not registered with a manager")
        return self._manager

    @property
    def identifier(self) -> str:
        """Return a stable identifier used in aggregated responses."""

        return f"{self.__class__.__module__}.{self.__class__.__name__}"

    async def emit_to(
        self,
        sid: str,
        event_type: str,
        data: dict[str, Any],
        *,
        correlation_id: str | None = None,
    ) -> None:
        """Emit an event to a specific connection or buffer it if offline."""
        await self.manager.emit_to(
            self.namespace,
            sid,
            event_type,
            data,
            handler_id=self.identifier,
            correlation_id=correlation_id,
        )

    async def broadcast(
        self,
        event_type: str,
        data: dict[str, Any],
        *,
        exclude_sids: str | Iterable[str] | None = None,
        correlation_id: str | None = None,
    ) -> None:
        """Broadcast an event to all connections, optionally excluding one."""
        await self.manager.broadcast(
            self.namespace,
            event_type,
            data,
            exclude_sids=exclude_sids,
            handler_id=self.identifier,
            correlation_id=correlation_id,
        )

    # ------------------------------------------------------------------
    # Convenience wrappers for standardized result helpers
    # ------------------------------------------------------------------

    @staticmethod
    def result_ok(
        data: dict[str, Any] | None = None,
        *,
        correlation_id: str | None = None,
        duration_ms: float | None = None,
    ) -> WebSocketResult:
        """Return a standardized success result."""

        return WebSocketResult.ok(
            data=data,
            correlation_id=correlation_id,
            duration_ms=duration_ms,
        )

    @staticmethod
    def result_error(
        *,
        code: str,
        message: str,
        details: Any | None = None,
        correlation_id: str | None = None,
        duration_ms: float | None = None,
    ) -> WebSocketResult:
        """Return a standardized error result."""

        return WebSocketResult.error(
            code=code,
            message=message,
            details=details,
            correlation_id=correlation_id,
            duration_ms=duration_ms,
        )

    async def request(
        self,
        sid: str,
        event_type: str,
        data: dict[str, Any],
        *,
        timeout_ms: int = 0,
        include_handlers: Iterable[str] | None = None,
    ) -> dict[str, Any]:
        """Send a request-response event to a specific connection and aggregate results.

        Returns a payload shaped as ``{"correlationId": str, "results": RequestResultItem[]}``.
        """

        return await self.manager.request_for_sid(
            namespace=self.namespace,
            sid=sid,
            event_type=event_type,
            data=data,
            timeout_ms=timeout_ms,
            handler_id=self.identifier,
            include_handlers=set(include_handlers) if include_handlers else None,
        )

    async def request_all(
        self,
        event_type: str,
        data: dict[str, Any],
        *,
        timeout_ms: int = 0,
        exclude_handlers: Iterable[str] | None = None,
    ) -> list[dict[str, Any]]:
        """Fan a request out to every active connection and aggregate responses.

        Each entry in the returned list is ``{"sid": str, "correlationId": str, "results": RequestResultItem[]}``.
        """

        return await self.manager.route_event_all(
            self.namespace,
            event_type=event_type,
            data=data,
            timeout_ms=timeout_ms,
            exclude_handlers=set(exclude_handlers) if exclude_handlers else None,
            handler_id=self.identifier,
        )
