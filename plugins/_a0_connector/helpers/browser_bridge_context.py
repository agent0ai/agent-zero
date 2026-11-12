"""Bridge-only context authorization and privacy-preserving log projection.

This module is intentionally separate from the legacy connector event bridge.
It does not subscribe sockets, send messages, emit events, or activate any
browser-bridge runtime surface.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
import math
import re
import threading
from typing import Any, Callable, Mapping, Protocol, Sequence

from helpers.ws_principal import WsPrincipal
from plugins._a0_connector.helpers.browser_bridge_transport import (
    PRODUCTION_BROWSER_BRIDGE_TRANSPORT,
    BrowserBridgeTransportProfile,
    require_browser_bridge_transport_profile,
    require_transport_principal_identity,
)


MAX_ADVERTISED_CONTEXTS = 64
MAX_CONTEXT_SUBSCRIPTIONS = 32
MAX_CONTEXT_PAGE_EVENTS = 50
MAX_CONTEXT_LABEL_BYTES = 256
MAX_CONTEXT_TEXT_BYTES = 8 * 1024
MAX_CONTEXT_IDENTIFIER_BYTES = 256
MAX_CONTEXT_CURSOR = 2**53 - 1

_NATIVE_IDENTIFIER = re.compile(r"[A-Za-z0-9][A-Za-z0-9._:-]{0,255}")
_MESSAGE_TYPES = {"input": "user", "user": "user", "response": "assistant"}
_ACTIVITY_TYPES: dict[str, tuple[str, str]] = {
    "agent": ("assistant_work", "working"),
    "browser": ("browser", "updated"),
    "code_exe": ("code", "updated"),
    "subagent": ("subagent", "updated"),
    "error": ("status", "failed"),
    "hint": ("status", "updated"),
    "info": ("status", "updated"),
    "progress": ("status", "working"),
    "tool": ("tool", "updated"),
    "mcp": ("tool", "updated"),
    "util": ("status", "updated"),
    "warning": ("status", "warning"),
}
_COMPLETION_STATUSES = frozenset({"completed", "canceled", "failed"})


class BrowserBridgeContextError(ValueError):
    """A context request or source value is invalid."""


class BrowserBridgeContextDenied(PermissionError):
    """The exact bridge route has no authority for the context operation."""

    def __init__(self, code: str) -> None:
        super().__init__(code)
        self.code = code


class BrowserBridgeContextUnavailable(RuntimeError):
    """Current route or read-only context state cannot be established safely."""


@dataclass(frozen=True, slots=True)
class BrowserBridgeContextRoute:
    principal: WsPrincipal
    connector_sid: str
    load_generation_id: str
    transport_profile: BrowserBridgeTransportProfile = (
        PRODUCTION_BROWSER_BRIDGE_TRANSPORT
    )

    def __post_init__(self) -> None:
        principal = self.principal
        try:
            profile = require_browser_bridge_transport_profile(
                self.transport_profile
            )
            require_transport_principal_identity(principal, profile)
            if type(principal.key_generation) is not int or principal.key_generation < 1:
                raise ValueError("invalid key generation")
        except ValueError:
            raise BrowserBridgeContextError("invalid bridge principal")
        _identifier(principal.principal_id, "bridge_id")
        _identifier(principal.subject_id, "subject_id")
        _identifier(self.connector_sid, "connector_sid")
        _native_identifier(self.load_generation_id, "load_generation_id")


@dataclass(frozen=True, slots=True)
class BrowserContextSourceSummary:
    context_id: str
    label: str
    kind: str
    status: str
    created_at_ms: int
    updated_at_ms: int


@dataclass(frozen=True, slots=True)
class BrowserContextSourcePage:
    entries: tuple[Any, ...]
    last_sequence: int
    complete: bool
    history_before: int | None = None
    has_more_history: bool | None = None


class BrowserContextDataSource(Protocol):
    def list_contexts(
        self,
        *,
        subject_id: str,
        limit: int,
    ) -> Sequence[BrowserContextSourceSummary]: ...

    def context_exists(self, *, subject_id: str, context_id: str) -> bool: ...

    def read_context(
        self,
        *,
        subject_id: str,
        context_id: str,
        from_sequence: int,
        history: str | None,
        history_before: int | None,
        limit: int,
    ) -> BrowserContextSourcePage | None: ...


@dataclass(slots=True)
class _RouteState:
    route: BrowserBridgeContextRoute
    advertised: frozenset[str]
    subscribed: set[str]


RouteAuthorizer = Callable[[BrowserBridgeContextRoute], bool]


class BrowserBridgeContextAccess:
    """Exact-route context advertisement, subscription, and projection seam."""

    def __init__(
        self,
        *,
        data_source: BrowserContextDataSource | None = None,
        route_authorizer: RouteAuthorizer | None = None,
        max_advertised_contexts: int = MAX_ADVERTISED_CONTEXTS,
        max_subscriptions: int = MAX_CONTEXT_SUBSCRIPTIONS,
        transport_profile: BrowserBridgeTransportProfile = (
            PRODUCTION_BROWSER_BRIDGE_TRANSPORT
        ),
    ) -> None:
        if min(max_advertised_contexts, max_subscriptions) < 1:
            raise ValueError("context authorization bounds must be positive")
        self._data_source = data_source or AgentContextDataSource()
        self._route_authorizer = route_authorizer or (lambda _route: False)
        self._transport_profile = require_browser_bridge_transport_profile(
            transport_profile
        )
        self._max_advertised_contexts = max_advertised_contexts
        self._max_subscriptions = max_subscriptions
        self._routes: dict[tuple[int, str, str], _RouteState] = {}
        self._lock = threading.RLock()

    @property
    def transport_profile(self) -> BrowserBridgeTransportProfile:
        return self._transport_profile

    def advertise_contexts(
        self,
        route: BrowserBridgeContextRoute,
        *,
        limit: int = MAX_ADVERTISED_CONTEXTS,
    ) -> tuple[dict[str, Any], ...]:
        route = _route(route)
        limit = _bounded_limit(limit, self._max_advertised_contexts, "context list")
        self._require_current(route, "context.list")
        try:
            source_items = self._data_source.list_contexts(
                subject_id=route.principal.subject_id,
                limit=limit,
            )
        except Exception as error:
            raise BrowserBridgeContextUnavailable("context source unavailable") from error
        self._require_current(route, "context.list")
        if not isinstance(source_items, Sequence) or isinstance(
            source_items, (str, bytes, bytearray)
        ):
            raise BrowserBridgeContextUnavailable("invalid context source")
        if len(source_items) > limit:
            raise BrowserBridgeContextUnavailable("context source exceeded limit")
        projected = tuple(_project_summary(item) for item in source_items)
        context_ids = [item["context_id"] for item in projected]
        if len(set(context_ids)) != len(context_ids):
            raise BrowserBridgeContextUnavailable("duplicate context source identity")
        self._require_current(route, "context.list")
        key = _route_key(route)
        with self._lock:
            prior = self._routes.get(key)
            subscriptions = (
                prior.subscribed & set(context_ids)
                if prior is not None and _same_route(prior.route, route)
                else set()
            )
            self._routes[key] = _RouteState(
                route=route,
                advertised=frozenset(context_ids),
                subscribed=subscriptions,
            )
        self._require_current(route, "context.list")
        return projected

    def subscribe(
        self,
        route: BrowserBridgeContextRoute,
        *,
        context_id: Any,
    ) -> None:
        route = _route(route)
        context_id = _identifier(context_id, "context_id")
        self._require_current(route, "context.read")
        self._require_advertised(route, context_id)
        if not self._context_exists(route, context_id, "context.read"):
            raise BrowserBridgeContextDenied("CONTEXT_NOT_FOUND")
        self._require_current(route, "context.read")
        with self._lock:
            state = self._state_for_route_locked(route)
            if context_id not in state.advertised:
                raise BrowserBridgeContextDenied("CONTEXT_NOT_ADVERTISED")
            if (
                context_id not in state.subscribed
                and len(state.subscribed) >= self._max_subscriptions
            ):
                raise BrowserBridgeContextDenied("CONTEXT_SUBSCRIPTION_LIMIT")
            state.subscribed.add(context_id)
        self._require_current(route, "context.read")

    def unsubscribe(
        self,
        route: BrowserBridgeContextRoute,
        *,
        context_id: Any,
    ) -> None:
        route = _route(route)
        context_id = _identifier(context_id, "context_id")
        self._require_current(route, "context.read")
        with self._lock:
            state = self._state_for_route_locked(route)
            if context_id not in state.advertised:
                raise BrowserBridgeContextDenied("CONTEXT_NOT_ADVERTISED")
            state.subscribed.discard(context_id)

    def authorize_message_target(
        self,
        route: BrowserBridgeContextRoute,
        *,
        context_id: Any,
    ) -> None:
        route = _route(route)
        context_id = _identifier(context_id, "context_id")
        self._require_current(route, "context.message")
        self._require_advertised(route, context_id)
        if not self._context_exists(route, context_id, "context.message"):
            raise BrowserBridgeContextDenied("CONTEXT_NOT_FOUND")
        self._require_current(route, "context.message")
        self._require_advertised(route, context_id)

    def project_snapshot(
        self,
        route: BrowserBridgeContextRoute,
        *,
        context_id: Any,
        from_sequence: int = 0,
        history: str | None = None,
        history_before: int | None = None,
        limit: int = MAX_CONTEXT_PAGE_EVENTS,
    ) -> dict[str, Any]:
        route = _route(route)
        context_id = _identifier(context_id, "context_id")
        from_sequence = _cursor(from_sequence, "from_sequence")
        history = _history_mode(history)
        if history_before is not None:
            history_before = _cursor(history_before, "history_before")
        limit = _bounded_limit(limit, MAX_CONTEXT_PAGE_EVENTS, "context page")
        self._require_current(route, "context.read")
        self._require_subscribed(route, context_id)
        try:
            page = self._data_source.read_context(
                subject_id=route.principal.subject_id,
                context_id=context_id,
                from_sequence=from_sequence,
                history=history,
                history_before=history_before,
                limit=limit,
            )
        except Exception as error:
            raise BrowserBridgeContextUnavailable("context source unavailable") from error
        self._require_current(route, "context.read")
        self._require_subscribed(route, context_id)
        if page is None:
            raise BrowserBridgeContextDenied("CONTEXT_NOT_FOUND")
        projected_page = _project_page(
            page,
            context_id,
            limit,
            minimum_cursor=(
                from_sequence
                if history is None and history_before is None
                else None
            ),
            require_history_pagination=(
                history == "tail" or history_before is not None
            ),
        )
        self._require_current(route, "context.read")
        self._require_subscribed(route, context_id)
        return projected_page

    def project_event(
        self,
        route: BrowserBridgeContextRoute,
        *,
        context_id: Any,
        entry: Any,
    ) -> dict[str, Any] | None:
        route = _route(route)
        context_id = _identifier(context_id, "context_id")
        self._require_current(route, "context.read")
        self._require_subscribed(route, context_id)
        projected = _project_log_entry(entry, context_id)
        self._require_current(route, "context.read")
        self._require_subscribed(route, context_id)
        return projected

    def project_completion(
        self,
        route: BrowserBridgeContextRoute,
        *,
        context_id: Any,
        status: Any,
    ) -> dict[str, str]:
        route = _route(route)
        context_id = _identifier(context_id, "context_id")
        if status not in _COMPLETION_STATUSES:
            raise BrowserBridgeContextError("invalid completion status")
        self._require_current(route, "context.read")
        self._require_subscribed(route, context_id)
        return {"context_id": context_id, "status": status}

    def disconnect(
        self,
        *,
        principal: WsPrincipal,
        connector_sid: Any,
        load_generation_id: Any,
    ) -> bool:
        if not isinstance(principal, WsPrincipal):
            raise BrowserBridgeContextError("invalid bridge principal")
        sid = _identifier(connector_sid, "connector_sid")
        generation = _native_identifier(load_generation_id, "load_generation_id")
        key = (id(principal), sid, generation)
        with self._lock:
            state = self._routes.get(key)
            if state is None or state.route.principal is not principal:
                return False
            self._routes.pop(key, None)
            return True

    def _context_exists(
        self,
        route: BrowserBridgeContextRoute,
        context_id: str,
        scope: str,
    ) -> bool:
        try:
            exists = self._data_source.context_exists(
                subject_id=route.principal.subject_id,
                context_id=context_id,
            )
        except Exception as error:
            raise BrowserBridgeContextUnavailable("context source unavailable") from error
        self._require_current(route, scope)
        return exists is True

    def _require_current(self, route: BrowserBridgeContextRoute, scope: str) -> None:
        if (
            route.transport_profile is not self._transport_profile
            or scope not in route.principal.scopes
        ):
            raise BrowserBridgeContextDenied("SCOPE_DENIED")
        try:
            current = self._route_authorizer(route)
        except Exception:
            current = False
        if current is not True:
            self._drop_route(route)
            raise BrowserBridgeContextDenied("STALE_BRIDGE_ROUTE")

    def _require_advertised(
        self,
        route: BrowserBridgeContextRoute,
        context_id: str,
    ) -> None:
        with self._lock:
            state = self._state_for_route_locked(route)
            if context_id not in state.advertised:
                raise BrowserBridgeContextDenied("CONTEXT_NOT_ADVERTISED")

    def _require_subscribed(
        self,
        route: BrowserBridgeContextRoute,
        context_id: str,
    ) -> None:
        with self._lock:
            state = self._state_for_route_locked(route)
            if context_id not in state.subscribed:
                raise BrowserBridgeContextDenied("CONTEXT_NOT_SUBSCRIBED")

    def _state_for_route_locked(
        self,
        route: BrowserBridgeContextRoute,
    ) -> _RouteState:
        state = self._routes.get(_route_key(route))
        if state is None or not _same_route(state.route, route):
            raise BrowserBridgeContextDenied("CONTEXTS_NOT_ADVERTISED")
        return state

    def _drop_route(self, route: BrowserBridgeContextRoute) -> None:
        key = _route_key(route)
        with self._lock:
            state = self._routes.get(key)
            if state is not None and _same_route(state.route, route):
                self._routes.pop(key, None)


class AgentContextDataSource:
    """Read-only adapter over the current in-process AgentContext/log contract."""

    def list_contexts(
        self,
        *,
        subject_id: str,
        limit: int,
    ) -> Sequence[BrowserContextSourceSummary]:
        if subject_id != "single_user":
            return ()
        from agent import AgentContext

        contexts = [
            context for context in AgentContext.all() if _is_visible_context(context)
        ]
        contexts.sort(
            key=lambda context: _datetime_to_ms(getattr(context, "last_message", None)),
            reverse=True,
        )
        return tuple(_source_summary(context) for context in contexts[:limit])

    def context_exists(self, *, subject_id: str, context_id: str) -> bool:
        if subject_id != "single_user":
            return False
        from agent import AgentContext

        return _is_visible_context(AgentContext.get(context_id))

    def read_context(
        self,
        *,
        subject_id: str,
        context_id: str,
        from_sequence: int,
        history: str | None,
        history_before: int | None,
        limit: int,
    ) -> BrowserContextSourcePage | None:
        if subject_id != "single_user":
            return None
        from agent import AgentContext

        context = AgentContext.get(context_id)
        if not _is_visible_context(context):
            return None
        log = getattr(context, "log", None)
        if log is None or not callable(getattr(log, "output", None)):
            return None
        lock = getattr(log, "_lock", None)
        updates = getattr(log, "updates", None)
        if isinstance(updates, list):
            if lock is not None:
                with lock:
                    total = len(updates)
            else:
                total = len(updates)
        else:
            total = int(log.output().end)

        page_history_before: int | None = None
        has_more_history: bool | None = None
        if history_before is not None:
            before = min(history_before, total)
            start = max(before - limit, 0)
            end = before
            page_history_before = start
            has_more_history = bool(start)
        elif history == "tail":
            start = max(total - limit, 0)
            end = total
            page_history_before = start
            has_more_history = bool(start)
        else:
            start = min(from_sequence, total)
            end = min(start + limit, total)
        output = log.output(start=start, end=end)
        return BrowserContextSourcePage(
            entries=tuple(output.items),
            last_sequence=int(output.end),
            complete=not bool(context.is_running()),
            history_before=page_history_before,
            has_more_history=has_more_history,
        )


def _project_summary(value: Any) -> dict[str, Any]:
    if not isinstance(value, BrowserContextSourceSummary):
        raise BrowserBridgeContextUnavailable("invalid context summary")
    context_id = _identifier(value.context_id, "context_id")
    label = _truncate_text(value.label, MAX_CONTEXT_LABEL_BYTES)
    if not label:
        label = "Untitled task"
    if value.kind not in {"chat", "task"} or value.status not in {
        "idle",
        "running",
        "paused",
    }:
        raise BrowserBridgeContextUnavailable("invalid context summary")
    created = _timestamp(value.created_at_ms)
    updated = _timestamp(value.updated_at_ms)
    if updated < created:
        raise BrowserBridgeContextUnavailable("invalid context summary")
    return {
        "context_id": context_id,
        "label": label,
        "kind": value.kind,
        "status": value.status,
        "created_at_ms": created,
        "updated_at_ms": updated,
    }


def _project_page(
    page: Any,
    context_id: str,
    limit: int,
    *,
    minimum_cursor: int | None,
    require_history_pagination: bool,
) -> dict[str, Any]:
    if (
        not isinstance(page, BrowserContextSourcePage)
        or not isinstance(page.entries, tuple)
        or len(page.entries) > limit
        or not isinstance(page.complete, bool)
    ):
        raise BrowserBridgeContextUnavailable("invalid context page")
    last_sequence = _cursor(page.last_sequence, "last_sequence")
    if (
        page.entries
        and minimum_cursor is not None
        and last_sequence <= minimum_cursor
    ):
        raise BrowserBridgeContextUnavailable("context page did not advance")
    if require_history_pagination and (
        page.history_before is None or not isinstance(page.has_more_history, bool)
    ):
        raise BrowserBridgeContextUnavailable("missing context pagination")
    result: dict[str, Any] = {
        "context_id": context_id,
        "events": [
            projected
            for entry in page.entries
            if (projected := _project_log_entry(entry, context_id)) is not None
        ],
        "last_sequence": last_sequence,
        "complete": page.complete,
    }
    if page.history_before is not None or page.has_more_history is not None:
        if page.history_before is None or not isinstance(page.has_more_history, bool):
            raise BrowserBridgeContextUnavailable("invalid context pagination")
        history_before = _cursor(page.history_before, "history_before")
        if history_before > last_sequence:
            raise BrowserBridgeContextUnavailable("invalid context pagination")
        if page.entries and last_sequence <= history_before:
            raise BrowserBridgeContextUnavailable("context page did not advance")
        result["history_before"] = history_before
        result["has_more_history"] = page.has_more_history
    return result


def _project_log_entry(entry: Any, context_id: str) -> dict[str, Any] | None:
    if not isinstance(entry, Mapping):
        return None
    item_no = entry.get("no")
    if (
        isinstance(item_no, bool)
        or not isinstance(item_no, int)
        or not 0 <= item_no < MAX_CONTEXT_CURSOR
    ):
        return None
    entry_type = entry.get("type")
    if not isinstance(entry_type, str):
        return None
    event: str
    data: dict[str, str]
    role = _MESSAGE_TYPES.get(entry_type)
    if role is not None:
        text = _truncate_text(entry.get("content"), MAX_CONTEXT_TEXT_BYTES)
        if not text:
            return None
        event = "message"
        data = {"role": role, "text": text}
    else:
        activity = _ACTIVITY_TYPES.get(entry_type)
        if activity is None:
            return None
        event = "activity"
        data = {"activity": activity[0], "status": activity[1]}
    projected: dict[str, Any] = {
        "context_id": context_id,
        "sequence": item_no + 1,
        "event": event,
        "data": data,
    }
    timestamp_ms = _source_timestamp_ms(entry.get("timestamp"))
    if timestamp_ms is not None:
        projected["timestamp_ms"] = timestamp_ms
    correlation_id = entry.get("id")
    try:
        if correlation_id is not None:
            projected["correlation_id"] = _native_identifier(
                correlation_id,
                "correlation_id",
            )
    except BrowserBridgeContextError:
        pass
    return projected


def _source_summary(context: Any) -> BrowserContextSourceSummary:
    context_type = getattr(getattr(context, "type", None), "value", "user")
    if bool(getattr(context, "paused", False)):
        status = "paused"
    elif bool(context.is_running()):
        status = "running"
    else:
        status = "idle"
    return BrowserContextSourceSummary(
        context_id=str(getattr(context, "id", "")),
        label=str(getattr(context, "name", "") or "Untitled task"),
        kind="task" if context_type == "task" else "chat",
        status=status,
        created_at_ms=_datetime_to_ms(getattr(context, "created_at", None)),
        updated_at_ms=_datetime_to_ms(getattr(context, "last_message", None)),
    )


def _is_visible_context(context: Any) -> bool:
    if context is None:
        return False
    return getattr(getattr(context, "type", None), "value", None) != "background"


def _datetime_to_ms(value: Any) -> int:
    if not isinstance(value, datetime):
        return 0
    try:
        timestamp = value.timestamp()
    except (OSError, OverflowError, ValueError):
        return 0
    if not math.isfinite(timestamp) or timestamp < 0:
        return 0
    return int(timestamp * 1_000)


def _source_timestamp_ms(value: Any) -> int | None:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        return None
    if not math.isfinite(value) or value < 0:
        return None
    timestamp = int(value * 1_000)
    return timestamp if timestamp <= MAX_CONTEXT_CURSOR else None


def _truncate_text(value: Any, max_bytes: int) -> str:
    if not isinstance(value, str) or not value:
        return ""
    try:
        encoded = value.encode("utf-8")
    except UnicodeError:
        return ""
    if len(encoded) <= max_bytes:
        return value
    marker = "\n\n[Text truncated]"
    budget = max_bytes - len(marker.encode("utf-8"))
    clipped = encoded[: max(budget, 0)]
    while clipped:
        try:
            return clipped.decode("utf-8") + marker
        except UnicodeDecodeError:
            clipped = clipped[:-1]
    return marker if len(marker.encode("utf-8")) <= max_bytes else ""


def _route(value: Any) -> BrowserBridgeContextRoute:
    if not isinstance(value, BrowserBridgeContextRoute):
        raise BrowserBridgeContextError("invalid bridge context route")
    return value


def _route_key(route: BrowserBridgeContextRoute) -> tuple[int, str, str]:
    return id(route.principal), route.connector_sid, route.load_generation_id


def _same_route(
    expected: BrowserBridgeContextRoute,
    candidate: BrowserBridgeContextRoute,
) -> bool:
    return (
        expected.principal is candidate.principal
        and expected.connector_sid == candidate.connector_sid
        and expected.load_generation_id == candidate.load_generation_id
    )


def _identifier(value: Any, field_name: str) -> str:
    if (
        not isinstance(value, str)
        or not value
        or value != value.strip()
        or not value.isprintable()
    ):
        raise BrowserBridgeContextError(f"invalid {field_name}")
    try:
        size = len(value.encode("utf-8"))
    except UnicodeError:
        raise BrowserBridgeContextError(f"invalid {field_name}") from None
    if size > MAX_CONTEXT_IDENTIFIER_BYTES:
        raise BrowserBridgeContextError(f"invalid {field_name}")
    return value


def _native_identifier(value: Any, field_name: str) -> str:
    value = _identifier(value, field_name)
    if _NATIVE_IDENTIFIER.fullmatch(value) is None:
        raise BrowserBridgeContextError(f"invalid {field_name}")
    return value


def _timestamp(value: Any) -> int:
    if (
        isinstance(value, bool)
        or not isinstance(value, int)
        or not 0 <= value <= MAX_CONTEXT_CURSOR
    ):
        raise BrowserBridgeContextUnavailable("invalid context timestamp")
    return value


def _cursor(value: Any, field_name: str) -> int:
    if (
        isinstance(value, bool)
        or not isinstance(value, int)
        or not 0 <= value <= MAX_CONTEXT_CURSOR
    ):
        raise BrowserBridgeContextError(f"invalid {field_name}")
    return value


def _bounded_limit(value: Any, maximum: int, subject: str) -> int:
    if (
        isinstance(value, bool)
        or not isinstance(value, int)
        or not 1 <= value <= maximum
    ):
        raise BrowserBridgeContextError(f"invalid {subject} limit")
    return value


def _history_mode(value: Any) -> str | None:
    if value in (None, ""):
        return None
    if value != "tail":
        raise BrowserBridgeContextError("invalid history mode")
    return "tail"


_access: BrowserBridgeContextAccess | None = None
_access_lock = threading.Lock()


def get_browser_bridge_context_access() -> BrowserBridgeContextAccess:
    global _access
    if _access is None:
        with _access_lock:
            if _access is None:
                _access = BrowserBridgeContextAccess()
    return _access
