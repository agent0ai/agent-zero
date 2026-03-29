from __future__ import annotations

import asyncio, os
import re
import time
import threading
from collections import defaultdict, deque
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from typing import Any, Callable, Deque, Dict, Iterable, List, Optional, Set

import socketio
import uuid

from helpers.defer import DeferredTask
from helpers.print_style import PrintStyle
from helpers import runtime
from helpers.ws import ConnectionIdentity, ConnectionNotFoundError, WsHandler, _ws_debug_enabled, ws_debug


# Event validation

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


# WsResult – standardized handler return value

class WsResult:
    """Helper wrapper for standardized handler results.

    Instances are converted to the canonical ``RequestResultItem`` shape by
    :class:`WsManager`.  Helper constructors enforce payload validation
    so handlers no longer need to hand-craft dictionaries.
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
    ) -> "WsResult":
        if data is not None and not isinstance(data, dict):
            raise TypeError("WsResult.ok data must be a dict or None")
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
    ) -> "WsResult":
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


def validate_event_type(event_type: str) -> str:
    """Validate an event name: must be lowercase_snake_case and not reserved."""
    if not isinstance(event_type, str):
        raise TypeError("Event type must be a string")
    if not _EVENT_NAME_PATTERN.fullmatch(event_type):
        raise ValueError(
            f"Invalid event type '{event_type}' – must match lowercase_snake_case"
        )
    if event_type in _RESERVED_EVENT_NAMES:
        raise ValueError(
            f"Event type '{event_type}' is reserved by Socket.IO and cannot be used"
        )
    return event_type


BUFFER_MAX_SIZE = 100
BUFFER_TTL = timedelta(hours=1)
_shared_ws_manager: WsManager | None = None


async def send_data(
    event_type: str,
    data: dict[str, Any],
    *,
    endpoint_name: str = "/ws",
    connection_id: str | None = None,
) -> None:
    """Convenience wrapper around :pymeth:`WsManager.send_data`.

    All optional parameters are keyword-only to match the instance method's
    ``(endpoint_name, event_type, data, connection_id)`` order and avoid
    positional confusion between the two signatures.
    """
    manager = get_shared_ws_manager()
    await manager.send_data(endpoint_name, event_type, data, connection_id)


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def set_shared_ws_manager(manager: "WsManager") -> None:
    global _shared_ws_manager
    _shared_ws_manager = manager


def get_shared_ws_manager() -> "WsManager":
    manager = _shared_ws_manager
    if manager is None:
        raise RuntimeError("Shared WsManager has not been initialized")
    return manager


@dataclass
class BufferedEvent:
    event_type: str
    data: dict[str, Any]
    handler_id: str | None = None
    correlation_id: str | None = None
    timestamp: datetime = field(default_factory=_utcnow)


@dataclass
class ConnectionInfo:
    namespace: str
    sid: str
    connected_at: datetime = field(default_factory=_utcnow)
    last_activity: datetime = field(default_factory=_utcnow)


@dataclass
class _HandlerExecution:
    handler: WsHandler
    value: Any
    duration_ms: float | None


DIAGNOSTIC_EVENT = "ws_dev_console_event"
LIFECYCLE_CONNECT_EVENT = "ws_lifecycle_connect"
LIFECYCLE_DISCONNECT_EVENT = "ws_lifecycle_disconnect"
STATE_PUSH_EVENT = "state_push"
SERVER_RESTART_EVENT = "server_restart"

# Error codes returned by _build_error_result
ERR_NO_HANDLERS = "NO_HANDLERS"
ERR_HANDLER_ERROR = "HANDLER_ERROR"
ERR_INVALID_FILTER = "INVALID_FILTER"
ERR_INVALID_EVENT = "INVALID_EVENT"
ERR_CONNECTION_NOT_FOUND = "CONNECTION_NOT_FOUND"
ERR_TIMEOUT = "TIMEOUT"


class WsManager:
    def __init__(self, socketio: socketio.AsyncServer, lock) -> None:
        self.socketio = socketio
        self.lock = lock
        self.handlers: defaultdict[str, List[WsHandler]] = defaultdict(list)
        self.connections: Dict[ConnectionIdentity, ConnectionInfo] = {}
        self.buffers: defaultdict[ConnectionIdentity, Deque[BufferedEvent]] = (
            defaultdict(deque)
        )
        self._known_sids: Set[ConnectionIdentity] = set()
        self._disconnect_times: Dict[ConnectionIdentity, datetime] = {}
        self._identifier: str = f"{self.__class__.__module__}.{self.__class__.__name__}"
        # Session tracking (single-user default)
        self.user_to_sids: defaultdict[str, Set[ConnectionIdentity]] = defaultdict(set)
        self.sid_to_user: Dict[ConnectionIdentity, str | None] = {}
        self._ALL_USERS_BUCKET = "allUsers"
        self._server_restart_enabled: bool = False
        self._diagnostic_watchers: Set[ConnectionIdentity] = set()
        self._diagnostics_enabled: bool = runtime.is_development()
        self._dispatcher_loop: asyncio.AbstractEventLoop | None = None
        self._handler_worker: DeferredTask | None = None
        self._lifecycle_tasks: Set[asyncio.Task] = set()

    # Internal: development-only debug logging to avoid noise in production
    def _debug(self, message: str) -> None:
        ws_debug(message)

    def _ensure_dispatcher_loop(self) -> None:
        if self._dispatcher_loop is None:
            try:
                self._dispatcher_loop = asyncio.get_running_loop()
            except RuntimeError:
                return

    def _get_handler_worker(self) -> DeferredTask:
        if self._handler_worker is None:
            self._handler_worker = DeferredTask(thread_name="WsHandlers")
        return self._handler_worker

    async def _run_on_dispatcher_loop(self, coro: Any) -> Any:
        self._ensure_dispatcher_loop()
        dispatcher_loop = self._dispatcher_loop
        if dispatcher_loop is None:
            return await coro
        if dispatcher_loop.is_closed():
            try:
                coro.close()
            except Exception:  # pragma: no cover - best-effort cleanup
                pass
            raise RuntimeError("Dispatcher event loop is closed")

        try:
            running_loop = asyncio.get_running_loop()
        except RuntimeError:
            running_loop = None

        if running_loop is dispatcher_loop:
            return await coro

        future = asyncio.run_coroutine_threadsafe(coro, dispatcher_loop)
        return await asyncio.wrap_future(future)

    def _diagnostics_active(self) -> bool:
        if not self._diagnostics_enabled:
            return False
        with self.lock:
            return bool(self._diagnostic_watchers)

    def _copy_diagnostic_watchers(self) -> list[ConnectionIdentity]:
        with self.lock:
            return list(self._diagnostic_watchers)

    def register_diagnostic_watcher(self, namespace: str, sid: str) -> bool:
        if not self._diagnostics_enabled:
            return False
        identity: ConnectionIdentity = (namespace, sid)
        with self.lock:
            if identity not in self.connections:
                return False
            self._diagnostic_watchers.add(identity)
        return True

    def unregister_diagnostic_watcher(self, namespace: str, sid: str) -> None:
        identity: ConnectionIdentity = (namespace, sid)
        with self.lock:
            self._diagnostic_watchers.discard(identity)

    def _timestamp(self) -> str:
        return _utcnow().isoformat(timespec="milliseconds").replace("+00:00", "Z")

    def _summarize_payload(self, payload: dict[str, Any] | None) -> dict[str, Any]:
        if not isinstance(payload, dict):
            return {}
        summary: dict[str, Any] = {}
        for key in list(payload.keys())[:5]:
            value = payload[key]
            if isinstance(value, (str, int, float, bool)) or value is None:
                preview = value
            elif isinstance(value, dict):
                preview = f"dict({len(value)})"
            elif isinstance(value, list):
                preview = f"list({len(value)})"
            else:
                preview = value.__class__.__name__
            summary[key] = preview
        summary["__sizeBytes__"] = len(str(payload).encode("utf-8"))
        return summary

    def _summarize_results(self, results: List[dict[str, Any]]) -> dict[str, Any]:
        summary = {"ok": 0, "error": 0, "handlers": []}
        for result in results:
            handler_id = result.get("handlerId")
            ok = bool(result.get("ok"))
            if ok:
                summary["ok"] += 1
            else:
                summary["error"] += 1
            summary["handlers"].append(
                {
                    "handlerId": handler_id,
                    "ok": ok,
                    "errorCode": (result.get("error") or {}).get("code"),
                    "durationMs": result.get("durationMs"),
                }
            )
        summary["handlerCount"] = len(summary["handlers"])
        return summary

    async def _publish_diagnostic_event(
        self, payload: dict[str, Any] | Callable[[], dict[str, Any]]
    ) -> None:
        if not self._diagnostics_enabled:
            return
        watchers = self._copy_diagnostic_watchers()
        if not watchers:
            return
        effective_payload = payload() if callable(payload) else payload
        if (
            isinstance(effective_payload, dict)
            and "sourceNamespace" not in effective_payload
        ):
            origin = effective_payload.get("namespace")
            if isinstance(origin, str) and origin.strip():
                effective_payload = {
                    **effective_payload,
                    "sourceNamespace": origin.strip(),
                }

        async def _emit_to_watcher(identity: ConnectionIdentity) -> None:
            namespace, sid = identity
            try:
                await self.emit_to(
                    namespace,
                    sid,
                    DIAGNOSTIC_EVENT,
                    effective_payload,
                    handler_id=self._identifier,
                    diagnostic=True,
                )
            except ConnectionNotFoundError:
                self.unregister_diagnostic_watcher(namespace, sid)

        await asyncio.gather(*(_emit_to_watcher(identity) for identity in watchers))

    def _schedule_lifecycle_broadcast(
        self, namespace: str, event_type: str, payload: dict[str, Any]
    ) -> None:
        async def _broadcast() -> None:
            try:
                await self.broadcast(
                    namespace,
                    event_type,
                    payload,
                    diagnostic=True,
                )
            except Exception as exc:  # pragma: no cover - diagnostic
                self._debug(f"Failed to broadcast lifecycle event {event_type}: {exc}")

        task = asyncio.create_task(_broadcast())
        self._lifecycle_tasks.add(task)
        task.add_done_callback(self._lifecycle_tasks.discard)

    def _sweep_stale_sids(self) -> None:
        """Remove _known_sids entries whose disconnect exceeds BUFFER_TTL."""
        now = _utcnow()
        with self.lock:
            stale = [
                identity
                for identity, dt in self._disconnect_times.items()
                if identity not in self.connections and (now - dt) > BUFFER_TTL
            ]
            for identity in stale:
                self._known_sids.discard(identity)
                self._disconnect_times.pop(identity, None)
                self.buffers.pop(identity, None)

    def _normalize_handler_filter(self, value: Any, field_name: str) -> Set[str] | None:
        if value is None:
            return None
        if isinstance(value, str):
            return {value}
        try:
            iterator = iter(value)
        except TypeError as exc:  # pragma: no cover - defensive
            raise ValueError(
                f"{field_name} must be an array of handler identifiers"
            ) from exc

        normalized: Set[str] = set()
        for item in iterator:
            if not isinstance(item, str):
                raise ValueError(
                    f"{field_name} values must be handler identifier strings"
                )
            normalized.add(item)
        return normalized

    def _normalize_sid_filter(self, value: str | Iterable[str] | None) -> Set[str]:
        if value is None:
            return set()
        if isinstance(value, str):
            return {value}
        normalized: Set[str] = set()
        for item in value:
            normalized.add(str(item))
        return normalized

    def _select_handlers(
        self,
        namespace: str,
        *,
        include: Set[str] | None,
        exclude: Set[str] | None,
    ) -> tuple[list[WsHandler], Set[str]]:
        registered = self.handlers.get(namespace, [])
        available_ids = {handler.identifier for handler in registered}

        if include is not None:
            unknown = include - available_ids
            if unknown:
                raise ValueError(
                    f"Unknown handler(s) in includeHandlers for namespace '{namespace}': "
                    f"{', '.join(sorted(unknown))}"
                )
        if exclude is not None:
            unknown = exclude - available_ids
            if unknown:
                raise ValueError(
                    f"Unknown handler(s) in excludeHandlers for namespace '{namespace}': "
                    f"{', '.join(sorted(unknown))}"
                )

        selected: list[WsHandler] = []
        for handler in registered:
            ident = handler.identifier
            if include is not None and ident not in include:
                continue
            if exclude is not None and ident in exclude:
                continue
            selected.append(handler)

        return selected, available_ids

    def _resolve_correlation_id(self, payload: dict[str, Any]) -> str:
        value = payload.get("correlationId")
        if isinstance(value, str) and value.strip():
            correlation_id = value.strip()
        else:
            correlation_id = uuid.uuid4().hex
            payload["correlationId"] = correlation_id
        return correlation_id

    def register_handlers(
        self, handlers_by_namespace: dict[str, Iterable[WsHandler]]
    ) -> None:
        for namespace, handlers in handlers_by_namespace.items():
            for handler in handlers:
                handler.bind_manager(self, namespace=namespace)
                if _ws_debug_enabled():
                    PrintStyle.info(
                        "Registered WebSocket handler %s namespace=%s"
                        % (handler.identifier, namespace)
                    )
                existing = self.handlers.get(namespace, [])
                if handler in existing:
                    PrintStyle.warning(
                        f"Duplicate handler registration for namespace '{namespace}'"
                    )
                self.handlers[namespace].append(handler)
                self._debug(
                    f"Registered handler {handler.identifier} namespace={namespace}"
                )

    def iter_namespaces(self) -> list[str]:
        return list(self.handlers.keys())

    async def process_client_event(
        self,
        namespace: str,
        event_type: str,
        data: dict[str, Any],
        sid: str,
        *,
        handlers: list[WsHandler],
    ) -> dict[str, Any]:
        """Process a client-originated event through provided handler instances.

        Unlike ``route_event`` which selects from globally registered handlers,
        this accepts pre-selected instances (e.g. per-connection activated
        handlers that have already passed security checks).
        """
        self._ensure_dispatcher_loop()
        incoming = dict(data or {})
        correlation_id = self._resolve_correlation_id(incoming)

        if "data" in incoming and isinstance(incoming.get("data"), dict):
            handler_payload = dict(incoming["data"])
            if "excludeSids" in incoming:
                handler_payload["excludeSids"] = incoming["excludeSids"]
        else:
            handler_payload = dict(incoming)
        handler_payload["correlationId"] = correlation_id

        if not handlers:
            return self._ack_error(
                handler_id=self._identifier,
                code=ERR_NO_HANDLERS,
                message="No handlers available after security filtering",
                correlation_id=correlation_id,
            )

        with self.lock:
            info = self.connections.get((namespace, sid))
            if info:
                info.last_activity = _utcnow()

        executions = await asyncio.gather(
            *[
                self._invoke_handler(handler, event_type, dict(handler_payload), sid)
                for handler in handlers
            ]
        )

        results = self._collect_results(
            executions, event_type, correlation_id, skip_none=True,
        )

        await self._publish_diagnostic_event(
            lambda: {
                "kind": "inbound",
                "sourceNamespace": namespace,
                "namespace": namespace,
                "eventType": event_type,
                "sid": sid,
                "correlationId": correlation_id,
                "timestamp": self._timestamp(),
                "handlerCount": len(handlers),
                "durationMs": sum(
                    (exec.duration_ms or 0.0) for exec in executions
                ),
                "resultSummary": self._summarize_results(results),
                "payloadSummary": self._summarize_payload(handler_payload),
            }
        )

        response = {"correlationId": correlation_id, "results": results}
        self._debug(
            f"Completed client event namespace={namespace} '{event_type}' "
            f"sid={sid} correlation={correlation_id}"
        )
        return response

    def _collect_results(
        self,
        executions: list[_HandlerExecution],
        event_type: str,
        correlation_id: str,
        *,
        skip_none: bool = False,
    ) -> List[dict[str, Any]]:
        """Build a result list from handler executions.

        Args:
            skip_none: When ``True``, handlers that return ``None`` are omitted
                from the results (fire-and-forget / opt-out semantics used by
                ``process_client_event``).  When ``False``, ``None`` is converted
                to ``WsResult(ok=True)`` (default ``route_event`` behaviour).
        """
        results: List[dict[str, Any]] = []
        for execution in executions:
            handler = execution.handler
            value = execution.value
            duration_ms = execution.duration_ms

            if isinstance(value, Exception):
                PrintStyle.error(
                    f"Error in handler {handler.identifier} for '{event_type}' "
                    f"(correlation {correlation_id}): {value}"
                )
                results.append(
                    self._build_error_result(
                        handler_id=handler.identifier,
                        code=ERR_HANDLER_ERROR,
                        message="Internal server error",
                        details=str(value),
                        correlation_id=correlation_id,
                        duration_ms=duration_ms,
                    )
                )
                continue

            if isinstance(value, WsResult):
                results.append(
                    value.as_result(
                        handler_id=handler.identifier,
                        fallback_correlation_id=correlation_id,
                        duration_ms=duration_ms,
                    )
                )
                continue

            if value is None:
                if skip_none:
                    continue
                helper_result = WsResult(ok=True)
            elif isinstance(value, dict):
                helper_result = WsResult(ok=True, data=value)
            else:
                helper_result = WsResult(ok=True, data={"result": value})

            results.append(
                helper_result.as_result(
                    handler_id=handler.identifier,
                    fallback_correlation_id=correlation_id,
                    duration_ms=duration_ms,
                )
            )
        return results

    async def _invoke_handler(
        self,
        handler: WsHandler,
        event_type: str,
        payload: dict[str, Any],
        sid: str,
    ) -> _HandlerExecution:
        instrument = self._diagnostics_active()
        start = time.perf_counter() if instrument else None
        try:
            value = await self._get_handler_worker().execute_inside(
                handler.process, event_type, payload, sid
            )
        except Exception as exc:  # pragma: no cover - handled by caller
            duration_ms = (
                (time.perf_counter() - start) * 1000 if start is not None else None
            )
            return _HandlerExecution(handler, exc, duration_ms)
        duration_ms = (
            (time.perf_counter() - start) * 1000 if start is not None else None
        )
        return _HandlerExecution(handler, value, duration_ms)

    async def handle_connect(
        self, namespace: str, sid: str, user_id: str | None = None
    ) -> None:
        self._ensure_dispatcher_loop()
        user_bucket = user_id or "single_user"
        identity: ConnectionIdentity = (namespace, sid)
        with self.lock:
            self.connections[identity] = ConnectionInfo(namespace=namespace, sid=sid)
            self._known_sids.add(identity)
            self._disconnect_times.pop(identity, None)
            self.sid_to_user[identity] = user_bucket
            self.user_to_sids[self._ALL_USERS_BUCKET].add(identity)
            self.user_to_sids[user_bucket].add(identity)
            connection_count = sum(
                1 for conn_identity in self.connections if conn_identity[0] == namespace
            )
        if _ws_debug_enabled():
            PrintStyle.info(f"WebSocket connected: namespace={namespace} sid={sid}")
        await self._run_lifecycle(namespace, lambda h: h.on_connect(sid))
        await self._flush_buffer(identity)
        if self._server_restart_enabled:
            await self.emit_to(
                namespace,
                sid,
                SERVER_RESTART_EVENT,
                {
                    "emittedAt": self._timestamp(),
                    "runtimeId": runtime.get_runtime_id(),
                },
                handler_id=self._identifier,
            )
            if _ws_debug_enabled():
                PrintStyle.info(
                    f"server_restart broadcast emitted to namespace={namespace} sid={sid}"
                )
        lifecycle_payload = {
            "namespace": namespace,
            "sid": sid,
            "connectionCount": connection_count,
            "timestamp": self._timestamp(),
        }
        await self._publish_diagnostic_event(
            {
                "kind": "lifecycle",
                "event": "connect",
                **lifecycle_payload,
            }
        )
        self._schedule_lifecycle_broadcast(
            namespace, LIFECYCLE_CONNECT_EVENT, lifecycle_payload
        )

    async def handle_disconnect(self, namespace: str, sid: str) -> None:
        self._ensure_dispatcher_loop()
        identity: ConnectionIdentity = (namespace, sid)
        with self.lock:
            self.connections.pop(identity, None)
            # Keep identity in _known_sids so emit_to buffers instead of raising;
            # record disconnect time for TTL-based cleanup
            self._disconnect_times[identity] = _utcnow()
            # session tracking cleanup
            user_bucket = self.sid_to_user.pop(identity, None)
            if self._ALL_USERS_BUCKET in self.user_to_sids:
                self.user_to_sids[self._ALL_USERS_BUCKET].discard(identity)
                if not self.user_to_sids[self._ALL_USERS_BUCKET]:
                    self.user_to_sids.pop(self._ALL_USERS_BUCKET, None)
            if user_bucket and user_bucket in self.user_to_sids:
                self.user_to_sids[user_bucket].discard(identity)
                if not self.user_to_sids[user_bucket]:
                    self.user_to_sids.pop(user_bucket, None)
            connection_count = sum(
                1 for conn_identity in self.connections if conn_identity[0] == namespace
            )
        self.unregister_diagnostic_watcher(namespace, sid)
        PrintStyle.info(f"WebSocket disconnected: namespace={namespace} sid={sid}")
        await self._run_lifecycle(namespace, lambda h: h.on_disconnect(sid))
        lifecycle_payload = {
            "namespace": namespace,
            "sid": sid,
            "connectionCount": connection_count,
            "timestamp": self._timestamp(),
        }
        await self._publish_diagnostic_event(
            {
                "kind": "lifecycle",
                "event": "disconnect",
                **lifecycle_payload,
            }
        )
        self._schedule_lifecycle_broadcast(
            namespace, LIFECYCLE_DISCONNECT_EVENT, lifecycle_payload
        )
        self._sweep_stale_sids()

    async def route_event(
        self,
        namespace: str,
        event_type: str,
        data: dict[str, Any],
        sid: str,
        ack: Optional[Callable[[Any], None]] = None,
        *,
        include_handlers: Set[str] | None = None,
        exclude_handlers: Set[str] | None = None,
        allow_exclude: bool = False,
        handler_id: str | None = None,
    ) -> dict[str, Any]:
        self._ensure_dispatcher_loop()
        incoming = dict(data or {})
        correlation_id = self._resolve_correlation_id(incoming)
        self._debug(
            f"Routing event namespace={namespace} '{event_type}' sid={sid} correlation={correlation_id}"
        )

        include_meta_raw = incoming.pop("includeHandlers", None)
        exclude_meta_raw = incoming.pop("excludeHandlers", None)

        if "data" in incoming and isinstance(incoming.get("data"), dict):
            handler_payload = dict(incoming.get("data") or {})
            if "excludeSids" in incoming:
                handler_payload["excludeSids"] = incoming.get("excludeSids")
        else:
            handler_payload = dict(incoming)

        handler_payload["correlationId"] = correlation_id

        try:
            include_meta = self._normalize_handler_filter(
                include_meta_raw, "includeHandlers"
            )
        except ValueError as exc:
            return self._ack_error(
                handler_id=handler_id or self._identifier,
                code=ERR_INVALID_FILTER,
                message=str(exc),
                correlation_id=correlation_id,
                ack=ack,
            )

        try:
            exclude_meta = self._normalize_handler_filter(
                exclude_meta_raw, "excludeHandlers"
            )
        except ValueError as exc:
            return self._ack_error(
                handler_id=handler_id or self._identifier,
                code=ERR_INVALID_FILTER,
                message=str(exc),
                correlation_id=correlation_id,
                ack=ack,
            )

        if exclude_meta_raw is not None and not allow_exclude:
            return self._ack_error(
                handler_id=handler_id or self._identifier,
                code=ERR_INVALID_FILTER,
                message="excludeHandlers is not supported for this operation",
                correlation_id=correlation_id,
                ack=ack,
            )

        if include_handlers is not None and include_meta is not None:
            if include_handlers != include_meta:
                return self._ack_error(
                    handler_id=handler_id or self._identifier,
                    code=ERR_INVALID_FILTER,
                    message="Conflicting includeHandlers filters supplied",
                    correlation_id=correlation_id,
                    ack=ack,
                )

        if allow_exclude and exclude_handlers is not None and exclude_meta is not None:
            if exclude_handlers != exclude_meta:
                return self._ack_error(
                    handler_id=handler_id or self._identifier,
                    code=ERR_INVALID_FILTER,
                    message="Conflicting excludeHandlers filters supplied",
                    correlation_id=correlation_id,
                    ack=ack,
                )

        include = include_handlers or include_meta
        exclude = exclude_handlers or (exclude_meta if allow_exclude else None)

        try:
            validate_event_type(event_type)
        except (TypeError, ValueError) as exc:
            return self._ack_error(
                handler_id=handler_id or self._identifier,
                code=ERR_INVALID_EVENT,
                message=str(exc),
                correlation_id=correlation_id,
                ack=ack,
            )

        registered = self.handlers.get(namespace, [])
        if not registered:
            PrintStyle.warning(f"No handlers registered for namespace '{namespace}'")
            return self._ack_error(
                handler_id=handler_id or self._identifier,
                code=ERR_NO_HANDLERS,
                message=f"No handler for namespace '{namespace}'",
                correlation_id=correlation_id,
                ack=ack,
            )

        try:
            selected_handlers, _ = self._select_handlers(
                namespace, include=include, exclude=exclude
            )
        except ValueError as exc:
            return self._ack_error(
                handler_id=handler_id or self._identifier,
                code=ERR_INVALID_FILTER,
                message=str(exc),
                correlation_id=correlation_id,
                ack=ack,
            )

        if not selected_handlers:
            return self._ack_error(
                handler_id=handler_id or self._identifier,
                code=ERR_NO_HANDLERS,
                message=f"No handler for '{event_type}' after applying filters",
                correlation_id=correlation_id,
                ack=ack,
            )

        with self.lock:
            info = self.connections.get((namespace, sid))
            if info:
                info.last_activity = _utcnow()

        executions = await asyncio.gather(
            *[
                self._invoke_handler(handler, event_type, dict(handler_payload), sid)
                for handler in selected_handlers
            ]
        )

        # NOTE: skip_none=False here — route_event converts None to ok=True,
        # unlike process_client_event which skips None (fire-and-forget).
        # This is intentional: route_event is server-initiated and callers
        # expect a result entry for every handler.
        results = self._collect_results(
            executions, event_type, correlation_id, skip_none=False,
        )

        await self._publish_diagnostic_event(
            lambda: {
                "kind": "inbound",
                "sourceNamespace": namespace,
                "namespace": namespace,
                "eventType": event_type,
                "sid": sid,
                "correlationId": correlation_id,
                "timestamp": self._timestamp(),
                "handlerCount": len(selected_handlers),
                "durationMs": sum((exec.duration_ms or 0.0) for exec in executions),
                "resultSummary": self._summarize_results(results),
                "payloadSummary": self._summarize_payload(handler_payload),
            }
        )

        response_payload = {"correlationId": correlation_id, "results": results}
        if ack:
            ack(response_payload)
        self._debug(
            f"Completed event namespace={namespace} '{event_type}' sid={sid} correlation={correlation_id}"
        )
        return response_payload

    async def request_for_sid(
        self,
        *,
        namespace: str,
        sid: str,
        event_type: str,
        data: dict[str, Any],
        timeout_ms: int = 0,
        handler_id: str | None = None,
        include_handlers: Set[str] | None = None,
    ) -> dict[str, Any]:
        payload = dict(data or {})
        correlation_id = self._resolve_correlation_id(payload)

        with self.lock:
            connected = (namespace, sid) in self.connections
        if not connected:
            return {
                "correlationId": correlation_id,
                "results": [
                    self._build_error_result(
                        handler_id=handler_id or self._identifier,
                        code=ERR_CONNECTION_NOT_FOUND,
                        message=f"Connection '{sid}' not found in namespace '{namespace}'",
                        correlation_id=correlation_id,
                    )
                ],
            }

        async def _invoke() -> dict[str, Any]:
            return await self.route_event(
                namespace,
                event_type,
                payload,
                sid,
                include_handlers=include_handlers,
                handler_id=handler_id,
            )

        if timeout_ms and timeout_ms > 0:
            try:
                return await asyncio.wait_for(_invoke(), timeout=timeout_ms / 1000)
            except asyncio.TimeoutError:
                PrintStyle.warning(
                    f"request timeout for sid {sid} event '{event_type}'"
                )
                return {
                    "correlationId": correlation_id,
                    "results": [
                        self._build_error_result(
                            handler_id=handler_id or self._identifier,
                            code=ERR_TIMEOUT,
                            message="Request timeout",
                            correlation_id=correlation_id,
                        )
                    ],
                }
        return await _invoke()

    async def route_event_all(
        self,
        namespace: str,
        event_type: str,
        data: dict[str, Any],
        *,
        timeout_ms: int = 0,
        exclude_handlers: Set[str] | None = None,
        handler_id: str | None = None,
    ) -> list[dict[str, Any]]:
        """Fan-out a request to all active connections and aggregate responses."""

        base_payload = dict(data or {})
        exclude_meta_raw = base_payload.pop("excludeHandlers", None)
        exclude_combined: Set[str] | None = exclude_handlers
        correlation_id = self._resolve_correlation_id(base_payload)

        if exclude_meta_raw is not None:
            try:
                exclude_meta = self._normalize_handler_filter(
                    exclude_meta_raw, "excludeHandlers"
                )
            except ValueError as exc:
                error = self._build_error_result(
                    handler_id=handler_id or self._identifier,
                    code=ERR_INVALID_FILTER,
                    message=str(exc),
                    correlation_id=correlation_id,
                )
                return [
                    {
                        "sid": "__invalid__",
                        "correlationId": correlation_id,
                        "results": [error],
                    }
                ]

            if exclude_combined is None:
                exclude_combined = exclude_meta
            elif exclude_meta is not None and exclude_combined != exclude_meta:
                error = self._build_error_result(
                    handler_id=handler_id or self._identifier,
                    code=ERR_INVALID_FILTER,
                    message="Conflicting excludeHandlers filters supplied",
                    correlation_id=correlation_id,
                )
                return [
                    {
                        "sid": "__invalid__",
                        "correlationId": correlation_id,
                        "results": [error],
                    }
                ]

        self._debug(
            f"Starting requestAll namespace={namespace} for '{event_type}' correlation={correlation_id}"
        )

        with self.lock:
            active_sids = [
                conn_identity[1]
                for conn_identity in self.connections.keys()
                if conn_identity[0] == namespace
            ]
        if not active_sids:
            self._debug(
                f"No active connections for requestAll namespace={namespace} '{event_type}' correlation={correlation_id}"
            )
            return []

        timeout_seconds = timeout_ms / 1000 if timeout_ms and timeout_ms > 0 else None

        async def _invoke_for_sid(target_sid: str) -> dict[str, Any]:
            async def _dispatch() -> dict[str, Any]:
                return await self.route_event(
                    namespace,
                    event_type,
                    base_payload,
                    target_sid,
                    allow_exclude=True,
                    exclude_handlers=exclude_combined,
                    handler_id=handler_id,
                )

            if timeout_seconds is None:
                return await _dispatch()

            try:
                task = asyncio.create_task(_dispatch())
                return await asyncio.wait_for(
                    asyncio.shield(task), timeout=timeout_seconds
                )
            except asyncio.TimeoutError:
                PrintStyle.warning(
                    f"requestAll timeout for sid {target_sid} correlation={correlation_id}"
                )
                # Ensure any late exceptions are observed so asyncio does not log
                # "Task exception was never retrieved".
                try:
                    task.add_done_callback(lambda t: t.exception())  # type: ignore[arg-type]
                except Exception:  # pragma: no cover - defensive
                    pass
                return {
                    "correlationId": correlation_id,
                    "results": [
                        self._build_error_result(
                            handler_id=handler_id or self._identifier,
                            code=ERR_TIMEOUT,
                            message="Request timeout",
                            correlation_id=correlation_id,
                        )
                    ],
                }

        tasks = {sid: asyncio.create_task(_invoke_for_sid(sid)) for sid in active_sids}

        aggregated: list[dict[str, Any]] = []
        for sid, task in tasks.items():
            result = await task
            if isinstance(result, dict):
                aggregated.append(
                    {
                        "sid": sid,
                        "correlationId": result.get("correlationId", correlation_id),
                        "results": result.get("results", []),
                    }
                )
            else:
                aggregated.append(
                    {
                        "sid": sid,
                        "correlationId": correlation_id,
                        "results": result,
                    }
                )

        self._debug(
            f"Completed requestAll namespace={namespace} for '{event_type}' correlation={correlation_id}"
        )
        return aggregated

    def _wrap_envelope(
        self,
        handler_id: str | None,
        data: dict[str, Any],
        *,
        correlation_id: str | None = None,
    ) -> dict[str, Any]:
        hid = handler_id or self._identifier
        ts = self._timestamp()
        event_id = str(uuid.uuid4())
        correlation = correlation_id or str(uuid.uuid4())
        return {
            "handlerId": hid,
            "eventId": event_id,
            "correlationId": correlation,
            "ts": ts,
            "data": data or {},
        }

    async def emit_to(
        self,
        namespace: str,
        sid: str,
        event_type: str,
        data: dict[str, Any],
        *,
        handler_id: str | None = None,
        correlation_id: str | None = None,
        diagnostic: bool = False,
    ) -> None:
        envelope = self._wrap_envelope(
            handler_id,
            data,
            correlation_id=correlation_id,
        )
        delivered = False
        buffered = False
        identity: ConnectionIdentity = (namespace, sid)

        with self.lock:
            connected = identity in self.connections
            known = identity in self._known_sids or identity in self.buffers
            # Evict if disconnect has exceeded BUFFER_TTL
            if not connected and known:
                dt = self._disconnect_times.get(identity)
                if dt is not None and (_utcnow() - dt) > BUFFER_TTL:
                    self._known_sids.discard(identity)
                    self._disconnect_times.pop(identity, None)
                    self.buffers.pop(identity, None)
                    known = False

        if connected:
            self._debug(
                "Emit to namespace=%s sid=%s event=%s eventId=%s correlationId=%s handlerId=%s"
                % (
                    namespace,
                    sid,
                    event_type,
                    envelope.get("eventId"),
                    envelope.get("correlationId"),
                    envelope.get("handlerId"),
                )
            )
            await self._run_on_dispatcher_loop(
                self.socketio.emit(event_type, envelope, to=sid, namespace=namespace)
            )
            delivered = True
        else:
            if not known:
                raise ConnectionNotFoundError(sid, namespace=namespace)
            with self.lock:
                self._buffer_event(
                    identity,
                    event_type,
                    data,
                    handler_id,
                    envelope["correlationId"],
                )
            buffered = True

        if not diagnostic:
            await self._publish_diagnostic_event(
                lambda: {
                    "kind": "outbound",
                    "direction": "emit_to",
                    "eventType": event_type,
                    "namespace": namespace,
                    "sid": sid,
                    "correlationId": envelope["correlationId"],
                    "handlerId": envelope["handlerId"],
                    "timestamp": self._timestamp(),
                    "delivered": delivered,
                    "buffered": buffered,
                    "payloadSummary": self._summarize_payload(data),
                }
            )

    async def send_data(
        self,
        endpoint_name: str,
        event_type: str,
        data: dict[str, Any],
        connection_id: str | None = None,
    ) -> None:
        if connection_id is not None:
            await self.emit_to(endpoint_name, connection_id, event_type, data)
            return
        await self.broadcast(endpoint_name, event_type, data)

    async def broadcast(
        self,
        namespace: str,
        event_type: str,
        data: dict[str, Any],
        *,
        exclude_sids: str | Iterable[str] | None = None,
        handler_id: str | None = None,
        correlation_id: str | None = None,
        diagnostic: bool = False,
    ) -> None:
        excluded = self._normalize_sid_filter(exclude_sids)

        targets: list[str] = []
        with self.lock:
            current_identities = list(self.connections.keys())
        for conn_identity in current_identities:
            if conn_identity[0] != namespace:
                continue
            sid = conn_identity[1]
            if sid in excluded:
                continue
            targets.append(sid)

        if targets:
            envelope = self._wrap_envelope(
                handler_id,
                data,
                correlation_id=correlation_id,
            )
            coros = [
                self._run_on_dispatcher_loop(
                    self.socketio.emit(event_type, envelope, to=sid, namespace=namespace)
                )
                for sid in targets
            ]
            await asyncio.gather(*coros)

        if not diagnostic:
            await self._publish_diagnostic_event(
                lambda: {
                    "kind": "outbound",
                    "direction": "broadcast",
                    "eventType": event_type,
                    "namespace": namespace,
                    "targets": targets[:10],
                    "targetCount": len(targets),
                    "correlationId": correlation_id,
                    "handlerId": handler_id or self._identifier,
                    "timestamp": self._timestamp(),
                    "payloadSummary": self._summarize_payload(data),
                }
            )

    async def _run_lifecycle(
        self, namespace: str, fn: Callable[[WsHandler], Any]
    ) -> None:
        seen: Set[WsHandler] = set()
        coros: list[Any] = []
        for handler in self.handlers.get(namespace, []):
            if handler in seen:
                continue
            seen.add(handler)
            coros.append(self._get_handler_worker().execute_inside(fn, handler))
        if coros:
            await asyncio.gather(*coros, return_exceptions=True)

    def _buffer_event(
        self,
        identity: ConnectionIdentity,
        event_type: str,
        data: dict[str, Any],
        handler_id: str | None,
        correlation_id: str | None,
    ) -> None:
        namespace, sid = identity
        buffer = self.buffers[identity]
        buffer.append(
            BufferedEvent(
                event_type=event_type,
                data=data,
                handler_id=handler_id,
                correlation_id=correlation_id,
            )
        )
        while len(buffer) > BUFFER_MAX_SIZE:
            dropped = buffer.popleft()
            PrintStyle.warning(
                f"Dropping buffered event '{dropped.event_type}' for namespace={namespace} sid={sid} (overflow)"
            )
        self._debug(
            f"Buffered event namespace={namespace} '{event_type}' sid={sid} (queue length={len(buffer)})"
        )

    async def _flush_buffer(self, identity: ConnectionIdentity) -> None:
        self._ensure_dispatcher_loop()
        buffer = self.buffers.get(identity)
        if not buffer:
            return
        namespace, sid = identity
        now = _utcnow()
        delivered = 0
        while buffer:
            event = buffer.popleft()
            if now - event.timestamp > BUFFER_TTL:
                self._debug(
                    f"Discarding expired buffered event '{event.event_type}' for sid {sid}"
                )
                continue
            envelope = self._wrap_envelope(
                event.handler_id,
                event.data,
                correlation_id=event.correlation_id,
            )
            self._debug(
                "Flush to sid=%s event=%s eventId=%s correlationId=%s handlerId=%s"
                % (
                    sid,
                    event.event_type,
                    envelope.get("eventId"),
                    envelope.get("correlationId"),
                    envelope.get("handlerId"),
                )
            )
            await self._run_on_dispatcher_loop(
                self.socketio.emit(
                    event.event_type, envelope, to=sid, namespace=namespace
                )
            )
            delivered += 1
        if identity in self.buffers:
            self.buffers.pop(identity, None)
        if delivered:
            PrintStyle.info(
                f"Flushed {delivered} buffered event(s) to namespace={namespace} sid={sid}"
            )

    def _build_error_result(
        self,
        *,
        handler_id: str | None = None,
        code: str,
        message: str,
        details: str | None = None,
        correlation_id: str | None = None,
        duration_ms: float | None = None,
    ) -> dict[str, Any]:
        error_payload = {"code": code, "error": message}
        if details:
            error_payload["details"] = details
        result: dict[str, Any] = {
            "handlerId": handler_id or self._identifier,
            "ok": False,
            "error": error_payload,
        }
        if correlation_id is not None:
            result["correlationId"] = correlation_id
        if duration_ms is not None:
            result["durationMs"] = round(duration_ms, 4)
        return result

    def _ack_error(
        self,
        *,
        handler_id: str | None = None,
        code: str,
        message: str,
        correlation_id: str | None = None,
        ack: Callable | None = None,
    ) -> dict[str, Any]:
        """Build an error response, optionally invoke the ack callback, and return."""
        error = self._build_error_result(
            handler_id=handler_id,
            code=code,
            message=message,
            correlation_id=correlation_id,
        )
        response = {"correlationId": correlation_id, "results": [error]}
        if ack:
            ack(response)
        return response

    # Session tracking helpers (single-user defaults)
    def get_sids_for_user(self, user: str | None = None) -> list[ConnectionIdentity]:
        """Return connection identities for a user; single-user default returns all."""
        with self.lock:
            bucket = self._ALL_USERS_BUCKET if user is None else user
            return list(self.user_to_sids.get(bucket, set()))

    def get_user_for_sid(self, namespace: str, sid: str) -> str | None:
        """Return user identifier for a connection or None."""
        identity: ConnectionIdentity = (namespace, sid)
        with self.lock:
            return self.sid_to_user.get(identity)

    def set_server_restart_broadcast(self, enabled: bool) -> None:
        """Enable or disable automatic server restart broadcasts."""

        self._server_restart_enabled = bool(enabled)
