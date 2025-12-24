from __future__ import annotations

import asyncio
import time
from collections import defaultdict, deque
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from typing import Any, Callable, Deque, Dict, Iterable, List, Optional, Set

import socketio
import uuid

from python.helpers.defer import DeferredTask
from python.helpers.print_style import PrintStyle
from python.helpers import runtime
from python.helpers.websocket import ConnectionNotFoundError, WebSocketHandler, WebSocketResult

BUFFER_MAX_SIZE = 100
BUFFER_TTL = timedelta(hours=1)


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


@dataclass
class BufferedEvent:
    event_type: str
    data: dict[str, Any]
    handler_id: str | None = None
    correlation_id: str | None = None
    timestamp: datetime = field(default_factory=_utcnow)


@dataclass
class ConnectionInfo:
    sid: str
    connected_at: datetime = field(default_factory=_utcnow)
    last_activity: datetime = field(default_factory=_utcnow)
    csrf_expires_at: float | None = None


@dataclass
class _HandlerExecution:
    handler: WebSocketHandler
    value: Any
    duration_ms: float | None


DIAGNOSTIC_EVENT = "ws_dev_console_event"
LIFECYCLE_CONNECT_EVENT = "ws_lifecycle_connect"
LIFECYCLE_DISCONNECT_EVENT = "ws_lifecycle_disconnect"


class WebSocketManager:
    def __init__(self, socketio: socketio.AsyncServer, lock) -> None:
        self.socketio = socketio
        self.lock = lock
        self.handlers: defaultdict[str, List[WebSocketHandler]] = defaultdict[str, List[WebSocketHandler]](list)
        self.connections: Dict[str, ConnectionInfo] = {}
        self.buffers: defaultdict[str, Deque[BufferedEvent]] = defaultdict[str, Deque[BufferedEvent]](deque)
        self._known_sids: Set[str] = set()
        self._identifier: str = f"{self.__class__.__module__}.{self.__class__.__name__}"
        # Session tracking (single-user default)
        self.user_to_sids: defaultdict[str, Set[str]] = defaultdict(set)
        self.sid_to_user: Dict[str, str | None] = {}
        self._ALL_USERS_BUCKET = "allUsers"
        self._server_restart_enabled: bool = False
        self._diagnostic_watchers: Set[str] = set()
        self._diagnostics_enabled: bool = runtime.is_development()
        self._dispatcher_loop: asyncio.AbstractEventLoop | None = None
        self._handler_worker: DeferredTask | None = None

    # Internal: development-only debug logging to avoid noise in production
    def _debug(self, message: str) -> None:
        if runtime.is_development():
            PrintStyle.debug(message)

    def _ensure_dispatcher_loop(self) -> None:
        if self._dispatcher_loop is None:
            try:
                self._dispatcher_loop = asyncio.get_running_loop()
            except RuntimeError:
                return

    def _get_handler_worker(self) -> DeferredTask:
        if self._handler_worker is None:
            self._handler_worker = DeferredTask(thread_name="WebSocketHandlers")
        return self._handler_worker

    async def _run_on_dispatcher_loop(self, coro: Any) -> Any:
        self._ensure_dispatcher_loop()
        dispatcher_loop = self._dispatcher_loop
        if dispatcher_loop is None:
            return await coro

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

    def _copy_diagnostic_watchers(self) -> list[str]:
        with self.lock:
            return list(self._diagnostic_watchers)

    def register_diagnostic_watcher(self, sid: str) -> bool:
        if not self._diagnostics_enabled:
            return False
        with self.lock:
            if sid not in self.connections:
                return False
            self._diagnostic_watchers.add(sid)
        return True

    def unregister_diagnostic_watcher(self, sid: str) -> None:
        with self.lock:
            self._diagnostic_watchers.discard(sid)

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

        async def _emit_to_watcher(sid: str) -> None:
            try:
                await self.emit_to(
                    sid,
                    DIAGNOSTIC_EVENT,
                    effective_payload,
                    handler_id=self._identifier,
                    diagnostic=True,
                )
            except ConnectionNotFoundError:
                self.unregister_diagnostic_watcher(sid)

        await asyncio.gather(*(_emit_to_watcher(sid) for sid in watchers))

    def _schedule_lifecycle_broadcast(self, event_type: str, payload: dict[str, Any]) -> None:
        async def _broadcast() -> None:
            try:
                await self.broadcast(
                    event_type,
                    payload,
                    diagnostic=True,
                )
            except Exception as exc:  # pragma: no cover - diagnostic
                self._debug(f"Failed to broadcast lifecycle event {event_type}: {exc}")

        asyncio.create_task(_broadcast())

    def _normalize_handler_filter(
        self, value: Any, field_name: str
    ) -> Set[str] | None:
        if value is None:
            return None
        if isinstance(value, str):
            return {value}
        try:
            iterator = iter(value)
        except TypeError as exc:  # pragma: no cover - defensive
            raise ValueError(f"{field_name} must be an array of handler identifiers") from exc

        normalized: Set[str] = set()
        for item in iterator:
            if not isinstance(item, str):
                raise ValueError(
                    f"{field_name} values must be handler identifier strings"
                )
            normalized.add(item)
        return normalized

    def _normalize_sid_filter(
        self, value: str | Iterable[str] | None
    ) -> Set[str]:
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
        event_type: str,
        *,
        include: Set[str] | None,
        exclude: Set[str] | None,
    ) -> tuple[list[WebSocketHandler], Set[str]]:
        registered = self.handlers.get(event_type, [])
        available_ids = {handler.identifier for handler in registered}

        if include is not None:
            unknown = include - available_ids
            if unknown:
                raise ValueError(
                    f"Unknown handler(s) in includeHandlers: {', '.join(sorted(unknown))}"
                )
        if exclude is not None:
            unknown = exclude - available_ids
            if unknown:
                raise ValueError(
                    f"Unknown handler(s) in excludeHandlers: {', '.join(sorted(unknown))}"
                )

        selected: list[WebSocketHandler] = []
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

    def register_handlers(self, handlers: Iterable[WebSocketHandler]) -> None:
        for handler in handlers:
            handler.bind_manager(self)
            declared = handler.get_event_types()
            try:
                validated_events = handler.validate_event_types(declared)
            except Exception as exc:
                PrintStyle.error(
                    f"Failed to register handler {handler.identifier}: {exc}"
                )
                raise

            PrintStyle.info(
                "Registered WebSocket handler %s for events: %s"
                % (handler.identifier, ", ".join(validated_events))
            )
            for event_type in validated_events:
                if event_type in self.handlers:
                    PrintStyle.warning(
                        f"Duplicate handler registration for event '{event_type}'"
                    )
                self.handlers[event_type].append(handler)
            self._debug(
                f"Registered handler {handler.identifier} for event '{event_type}'"
            )

    def iter_event_types(self) -> Iterable[str]:
        return list(self.handlers.keys())

    async def _invoke_handler(
        self,
        handler: WebSocketHandler,
        event_type: str,
        payload: dict[str, Any],
        sid: str,
    ) -> _HandlerExecution:
        instrument = self._diagnostics_active()
        start = time.perf_counter() if instrument else None
        try:
            value = await self._get_handler_worker().execute_inside(
                handler.process_event, event_type, payload, sid
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
        self, sid: str, csrf_expiry: float | None = None, user_id: str | None = None
    ) -> None:
        self._ensure_dispatcher_loop()
        user_bucket = user_id or "single_user"
        with self.lock:
            self.connections[sid] = ConnectionInfo(sid=sid, csrf_expires_at=csrf_expiry)
            self._known_sids.add(sid)
            self.sid_to_user[sid] = user_bucket
            self.user_to_sids[self._ALL_USERS_BUCKET].add(sid)
            self.user_to_sids[user_bucket].add(sid)
            connection_count = len(self.connections)
        PrintStyle.info(f"WebSocket connected: {sid}")
        await self._run_lifecycle(lambda h: h.on_connect(sid))
        await self._flush_buffer(sid)
        if self._server_restart_enabled:
            await self.emit_to(
                sid,
                "server_restart",
                {
                    "emittedAt": _utcnow()
                    .isoformat(timespec="milliseconds")
                    .replace("+00:00", "Z"),
                    "runtimeId": runtime.get_runtime_id(),
                },
                handler_id=self._identifier,
            )
            PrintStyle.info(f"server_restart broadcast emitted to {sid}")
        lifecycle_payload = {
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
        self._schedule_lifecycle_broadcast(LIFECYCLE_CONNECT_EVENT, lifecycle_payload)

    async def handle_disconnect(self, sid: str) -> None:
        self._ensure_dispatcher_loop()
        with self.lock:
            self.connections.pop(sid, None)
            # session tracking cleanup
            user_bucket = self.sid_to_user.pop(sid, None)
            if self._ALL_USERS_BUCKET in self.user_to_sids:
                self.user_to_sids[self._ALL_USERS_BUCKET].discard(sid)
                if not self.user_to_sids[self._ALL_USERS_BUCKET]:
                    self.user_to_sids.pop(self._ALL_USERS_BUCKET, None)
            if user_bucket and user_bucket in self.user_to_sids:
                self.user_to_sids[user_bucket].discard(sid)
                if not self.user_to_sids[user_bucket]:
                    self.user_to_sids.pop(user_bucket, None)
            connection_count = len(self.connections)
        self.unregister_diagnostic_watcher(sid)
        PrintStyle.info(f"WebSocket disconnected: {sid}")
        await self._run_lifecycle(lambda h: h.on_disconnect(sid))
        lifecycle_payload = {
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
            LIFECYCLE_DISCONNECT_EVENT, lifecycle_payload
        )

    async def route_event(
        self,
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
            f"Routing event '{event_type}' sid={sid} correlation={correlation_id}"
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
            error = self._build_error_result(
                handler_id=handler_id or self._identifier,
                code="INVALID_FILTER",
                message=str(exc),
                correlation_id=correlation_id,
            )
            if ack:
                ack({"correlationId": correlation_id, "results": [error]})
            return {"correlationId": correlation_id, "results": [error]}

        try:
            exclude_meta = self._normalize_handler_filter(
                exclude_meta_raw, "excludeHandlers"
            )
        except ValueError as exc:
            error = self._build_error_result(
                handler_id=handler_id or self._identifier,
                code="INVALID_FILTER",
                message=str(exc),
                correlation_id=correlation_id,
            )
            payload_error = {"correlationId": correlation_id, "results": [error]}
            if ack:
                ack(payload_error)
            return payload_error

        if exclude_meta_raw is not None and not allow_exclude:
            error = self._build_error_result(
                handler_id=handler_id or self._identifier,
                code="INVALID_FILTER",
                message="excludeHandlers is not supported for this operation",
                correlation_id=correlation_id,
            )
            if ack:
                ack({"correlationId": correlation_id, "results": [error]})
            return {"correlationId": correlation_id, "results": [error]}

        if include_handlers is not None and include_meta is not None:
            if include_handlers != include_meta:
                error = self._build_error_result(
                    handler_id=handler_id or self._identifier,
                    code="INVALID_FILTER",
                    message="Conflicting includeHandlers filters supplied",
                    correlation_id=correlation_id,
                )
                if ack:
                    ack({"correlationId": correlation_id, "results": [error]})
                return {"correlationId": correlation_id, "results": [error]}

        if allow_exclude and exclude_handlers is not None and exclude_meta is not None:
            if exclude_handlers != exclude_meta:
                error = self._build_error_result(
                    handler_id=handler_id or self._identifier,
                    code="INVALID_FILTER",
                    message="Conflicting excludeHandlers filters supplied",
                    correlation_id=correlation_id,
                )
                if ack:
                    ack({"correlationId": correlation_id, "results": [error]})
                return {"correlationId": correlation_id, "results": [error]}

        include = include_handlers or include_meta
        exclude = exclude_handlers or (exclude_meta if allow_exclude else None)

        registered = self.handlers.get(event_type, [])
        if not registered:
            PrintStyle.warning(f"No handlers registered for event '{event_type}'")
            error = self._build_error_result(
                handler_id=handler_id or self._identifier,
                code="NO_HANDLERS",
                message=f"No handler for '{event_type}'",
                correlation_id=correlation_id,
            )
            if ack:
                ack({"correlationId": correlation_id, "results": [error]})
            return {"correlationId": correlation_id, "results": [error]}

        try:
            selected_handlers, _ = self._select_handlers(
                event_type, include=include, exclude=exclude
            )
        except ValueError as exc:
            error = self._build_error_result(
                handler_id=handler_id or self._identifier,
                code="INVALID_FILTER",
                message=str(exc),
                correlation_id=correlation_id,
            )
            if ack:
                ack({"correlationId": correlation_id, "results": [error]})
            return {"correlationId": correlation_id, "results": [error]}

        if not selected_handlers:
            error = self._build_error_result(
                handler_id=handler_id or self._identifier,
                code="NO_HANDLERS",
                message=f"No handler for '{event_type}' after applying filters",
                correlation_id=correlation_id,
            )
            if ack:
                ack({"correlationId": correlation_id, "results": [error]})
            return {"correlationId": correlation_id, "results": [error]}

        with self.lock:
            info = self.connections.get(sid)
            if info:
                info.last_activity = _utcnow()

        executions = await asyncio.gather(
            *[
                self._invoke_handler(handler, event_type, dict(handler_payload), sid)
                for handler in selected_handlers
            ]
        )

        results: List[dict[str, Any]] = []
        for execution in executions:
            handler = execution.handler
            value = execution.value
            duration_ms = execution.duration_ms

            if isinstance(value, Exception):  # pragma: no cover - defensive logging
                PrintStyle.error(
                    f"Error in handler {handler.identifier} for '{event_type}' (correlation {correlation_id}): {value}"
                )
                results.append(
                    self._build_error_result(
                        handler_id=handler.identifier,
                        code="HANDLER_ERROR",
                        message="Internal server error",
                        details=str(value),
                        correlation_id=correlation_id,
                        duration_ms=duration_ms,
                    )
                )
                continue

            if isinstance(value, WebSocketResult):
                results.append(
                    value.as_result(
                        handler_id=handler.identifier,
                        fallback_correlation_id=correlation_id,
                        duration_ms=duration_ms,
                    )
                )
                continue

            if value is None:
                helper_result = WebSocketResult(ok=True)
            elif isinstance(value, dict):
                helper_result = WebSocketResult(ok=True, data=value)
            else:
                helper_result = WebSocketResult(ok=True, data={"result": value})

            results.append(
                helper_result.as_result(
                    handler_id=handler.identifier,
                    fallback_correlation_id=correlation_id,
                    duration_ms=duration_ms,
                )
            )

        await self._publish_diagnostic_event(
            lambda: {
                "kind": "inbound",
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
            f"Completed event '{event_type}' sid={sid} correlation={correlation_id}"
        )
        return response_payload

    async def request_for_sid(
        self,
        *,
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
            connected = sid in self.connections
        if not connected:
            return {
                "correlationId": correlation_id,
                "results": [
                    self._build_error_result(
                        handler_id=handler_id or self._identifier,
                        code="CONNECTION_NOT_FOUND",
                        message=f"Connection '{sid}' not found",
                        correlation_id=correlation_id,
                    )
                ],
            }

        async def _invoke() -> dict[str, Any]:
            return await self.route_event(
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
                            code="TIMEOUT",
                            message="Request timeout",
                            correlation_id=correlation_id,
                        )
                    ],
                }
        return await _invoke()

    async def route_event_all(
        self,
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
                    code="INVALID_FILTER",
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
                    code="INVALID_FILTER",
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
            f"Starting requestAll for '{event_type}' correlation={correlation_id}"
        )

        with self.lock:
            active_sids = list(self.connections.keys())
        if not active_sids:
            self._debug(
                f"No active connections for requestAll '{event_type}' correlation={correlation_id}"
            )
            return []

        timeout_seconds = timeout_ms / 1000 if timeout_ms and timeout_ms > 0 else None

        async def _invoke_for_sid(target_sid: str) -> dict[str, Any]:
            async def _dispatch() -> dict[str, Any]:
                return await self.route_event(
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
                return await asyncio.wait_for(_dispatch(), timeout=timeout_seconds)
            except asyncio.TimeoutError:
                PrintStyle.warning(
                    f"requestAll timeout for sid {target_sid} correlation={correlation_id}"
                )
                return {
                    "correlationId": correlation_id,
                    "results": [
                        self._build_error_result(
                            handler_id=handler_id or self._identifier,
                            code="TIMEOUT",
                            message="Request timeout",
                            correlation_id=correlation_id,
                        )
                    ],
                }

        tasks = {
            sid: asyncio.create_task(_invoke_for_sid(sid)) for sid in active_sids
        }

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
            f"Completed requestAll for '{event_type}' correlation={correlation_id}"
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
        ts = _utcnow().isoformat(timespec="milliseconds").replace("+00:00", "Z")
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

        with self.lock:
            connected = sid in self.connections
            known = sid in self._known_sids or sid in self.buffers

        if connected:
            self._debug(
                "Emit to sid=%s event=%s eventId=%s correlationId=%s handlerId=%s"
                % (
                    sid,
                    event_type,
                    envelope.get("eventId"),
                    envelope.get("correlationId"),
                    envelope.get("handlerId"),
                )
            )
            await self._run_on_dispatcher_loop(
                self.socketio.emit(event_type, envelope, to=sid)
            )
            delivered = True
        else:
            if not known:
                raise ConnectionNotFoundError(sid)
            with self.lock:
                self._buffer_event(
                    sid,
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
                    "sid": sid,
                    "correlationId": envelope["correlationId"],
                    "handlerId": envelope["handlerId"],
                    "timestamp": self._timestamp(),
                    "delivered": delivered,
                    "buffered": buffered,
                    "payloadSummary": self._summarize_payload(data),
                }
            )

    async def broadcast(
        self,
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
            current_sids = list(self.connections.keys())
        for sid in current_sids:
            if sid in excluded:
                continue
            targets.append(sid)
            await self.emit_to(
                sid,
                event_type,
                data,
                handler_id=handler_id,
                correlation_id=correlation_id,
                diagnostic=diagnostic,
            )

        if not diagnostic:
            await self._publish_diagnostic_event(
                lambda: {
                    "kind": "outbound",
                    "direction": "broadcast",
                    "eventType": event_type,
                    "targets": targets[:10],
                    "targetCount": len(targets),
                    "correlationId": correlation_id,
                    "handlerId": handler_id or self._identifier,
                    "timestamp": self._timestamp(),
                    "payloadSummary": self._summarize_payload(data),
                }
            )

    async def _run_lifecycle(self, fn: Callable[[WebSocketHandler], Any]) -> None:
        seen: Set[WebSocketHandler] = set()
        coros: list[Any] = []
        for handler_list in self.handlers.values():
            for handler in handler_list:
                if handler in seen:
                    continue
                seen.add(handler)
                coros.append(self._get_handler_worker().execute_inside(fn, handler))
        if coros:
            await asyncio.gather(*coros, return_exceptions=True)

    def _buffer_event(
        self,
        sid: str,
        event_type: str,
        data: dict[str, Any],
        handler_id: str | None,
        correlation_id: str | None,
    ) -> None:
        buffer = self.buffers[sid]
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
                f"Dropping buffered event '{dropped.event_type}' for sid {sid} (overflow)"
            )
        self._debug(
            f"Buffered event '{event_type}' for sid {sid} (queue length={len(buffer)})"
        )

    async def _flush_buffer(self, sid: str) -> None:
        self._ensure_dispatcher_loop()
        buffer = self.buffers.get(sid)
        if not buffer:
            return
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
                self.socketio.emit(event.event_type, envelope, to=sid)
            )
            delivered += 1
        if sid in self.buffers:
            self.buffers.pop(sid, None)
        if delivered:
            PrintStyle.info(
                f"Flushed {delivered} buffered event(s) to sid {sid}"
            )

    def update_csrf_expiry(self, sid: str, expiry: float) -> None:
        with self.lock:
            info = self.connections.get(sid)
            if info:
                info.csrf_expires_at = expiry

    async def validate_session(self, sid: str, now_ts: float) -> bool:
        self._ensure_dispatcher_loop()
        should_disconnect = False
        with self.lock:
            info = self.connections.get(sid)
            if not info:
                return False
            if info.csrf_expires_at is not None and info.csrf_expires_at <= now_ts:
                self.connections.pop(sid, None)
                should_disconnect = True
        if should_disconnect:
            PrintStyle.warning(f"Disconnecting {sid} due to CSRF expiry")
            await self._run_on_dispatcher_loop(self.socketio.disconnect(sid))
            return False
        return True

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

    # Session tracking helpers (single-user defaults)
    def get_sids_for_user(self, user: str | None = None) -> list[str]:
        """Return SIDs for a user; single-user default returns all active SIDs."""
        with self.lock:
            bucket = self._ALL_USERS_BUCKET if user is None else user
            return list(self.user_to_sids.get(bucket, set()))

    def get_user_for_sid(self, sid: str) -> str | None:
        """Return user identifier for a SID or None."""
        with self.lock:
            return self.sid_to_user.get(sid)

    def set_server_restart_broadcast(self, enabled: bool) -> None:
        """Enable or disable automatic server restart broadcasts."""

        self._server_restart_enabled = bool(enabled)
