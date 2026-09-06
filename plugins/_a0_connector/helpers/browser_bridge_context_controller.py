"""Exact-route controller for the Browser bridge context event surface.

This is a presentation transport only.  Its polling tasks read the existing
AgentContext projection and may be cancelled independently; they never own,
cancel, reset, remove, or otherwise alter an AgentContext task.
"""

from __future__ import annotations

import asyncio
import json
from dataclasses import dataclass
import re
from typing import Any, Callable

from helpers.ws_principal import WsPrincipal, restricted_correlation_id
from plugins._a0_connector.helpers.browser_bridge_context import (
    MAX_ADVERTISED_CONTEXTS,
    MAX_CONTEXT_CURSOR,
    MAX_CONTEXT_PAGE_EVENTS,
    BrowserBridgeContextAccess,
    BrowserBridgeContextRoute,
)
from plugins._a0_connector.helpers.browser_bridge_messages import (
    BrowserBridgeMessageDispatcher,
)
from plugins._a0_connector.helpers.browser_bridge_transport import (
    PRODUCTION_BROWSER_BRIDGE_TRANSPORT,
    BrowserBridgeTransportProfile,
    require_browser_bridge_transport_profile,
)


CONTRACT_VERSION = 1
WS_NAMESPACE = PRODUCTION_BROWSER_BRIDGE_TRANSPORT.namespace
RESTRICTED_HANDLER_ID = PRODUCTION_BROWSER_BRIDGE_TRANSPORT.handler_id
CONTEXT_LIST_EVENT = "connector_context_list"
CONTEXT_SUBSCRIBE_EVENT = "connector_subscribe_context"
CONTEXT_UNSUBSCRIBE_EVENT = "connector_unsubscribe_context"
CONTEXT_SEND_MESSAGE_EVENT = "connector_send_message"
CONTEXT_SNAPSHOT_EVENT = "connector_context_snapshot"
CONTEXT_EVENT = "connector_context_event"
CONTEXT_COMPLETE_EVENT = "connector_context_complete"
CONTEXT_QUEUE_EVENT = "connector_message_queue_updated"

_INBOUND_EVENTS = frozenset(
    {
        CONTEXT_LIST_EVENT,
        CONTEXT_SUBSCRIBE_EVENT,
        CONTEXT_UNSUBSCRIBE_EVENT,
        CONTEXT_SEND_MESSAGE_EVENT,
    }
)
_OUTBOUND_EVENTS = frozenset(
    {CONTEXT_SNAPSHOT_EVENT, CONTEXT_EVENT, CONTEXT_COMPLETE_EVENT, CONTEXT_QUEUE_EVENT}
)
_IDENTIFIER = re.compile(r"[A-Za-z0-9][A-Za-z0-9._:-]{0,255}")

MAX_PRESENTATION_STREAMS = 32
MIN_POLL_INTERVAL_SECONDS = 0.01
MAX_POLL_INTERVAL_SECONDS = 5.0
DEFAULT_POLL_INTERVAL_SECONDS = 0.25
MAX_CANCEL_WAIT_SECONDS = 1.0
MAX_EMIT_TIMEOUT_SECONDS = 10.0
DEFAULT_EMIT_TIMEOUT_SECONDS = 5.0


class BrowserBridgeContextControllerError(ValueError):
    """A context controller request or dependency is invalid."""

    def __init__(self, code: str) -> None:
        super().__init__(code)
        self.code = code


class BrowserBridgeContextControllerDenied(PermissionError):
    """The exact current route cannot use the context event surface."""

    def __init__(self, code: str) -> None:
        super().__init__(code)
        self.code = code


@dataclass(slots=True)
class _PresentationStream:
    route: BrowserBridgeContextRoute
    context_id: str
    cursor: int
    completion_reported: bool
    task: asyncio.Task[None] | None = None
    queue_signature: str | None = None


RouteAuthorizer = Callable[[BrowserBridgeContextRoute], bool]


class BrowserBridgeContextController:
    """Dispatch strict bridge context requests and own bounded live views."""

    def __init__(
        self,
        *,
        access: BrowserBridgeContextAccess,
        messages: BrowserBridgeMessageDispatcher,
        manager: Any,
        route_authorizer: RouteAuthorizer | None = None,
        queue_projection: Callable | None = None,
        max_streams: int = MAX_PRESENTATION_STREAMS,
        poll_interval_seconds: float = DEFAULT_POLL_INTERVAL_SECONDS,
        cancel_wait_seconds: float = MAX_CANCEL_WAIT_SECONDS,
        emit_timeout_seconds: float = DEFAULT_EMIT_TIMEOUT_SECONDS,
        transport_profile: BrowserBridgeTransportProfile = (
            PRODUCTION_BROWSER_BRIDGE_TRANSPORT
        ),
    ) -> None:
        if not isinstance(access, BrowserBridgeContextAccess):
            raise BrowserBridgeContextControllerError("INVALID_CONTEXT_ACCESS")
        if not isinstance(messages, BrowserBridgeMessageDispatcher):
            raise BrowserBridgeContextControllerError("INVALID_MESSAGE_DISPATCHER")
        if getattr(messages, "_access", None) is not access:
            raise BrowserBridgeContextControllerError("INVALID_MESSAGE_DISPATCHER")
        if not callable(getattr(manager, "emit_to", None)):
            raise BrowserBridgeContextControllerError("INVALID_WEBSOCKET_MANAGER")
        if isinstance(max_streams, bool) or not 1 <= max_streams <= MAX_PRESENTATION_STREAMS:
            raise BrowserBridgeContextControllerError("INVALID_STREAM_LIMIT")
        if (
            isinstance(poll_interval_seconds, bool)
            or not isinstance(poll_interval_seconds, (int, float))
            or not MIN_POLL_INTERVAL_SECONDS
            <= float(poll_interval_seconds)
            <= MAX_POLL_INTERVAL_SECONDS
        ):
            raise BrowserBridgeContextControllerError("INVALID_POLL_INTERVAL")
        if (
            isinstance(cancel_wait_seconds, bool)
            or not isinstance(cancel_wait_seconds, (int, float))
            or not 0 < float(cancel_wait_seconds) <= MAX_CANCEL_WAIT_SECONDS
        ):
            raise BrowserBridgeContextControllerError("INVALID_CANCEL_WAIT")
        if (
            isinstance(emit_timeout_seconds, bool)
            or not isinstance(emit_timeout_seconds, (int, float))
            or not 0 < float(emit_timeout_seconds) <= MAX_EMIT_TIMEOUT_SECONDS
        ):
            raise BrowserBridgeContextControllerError("INVALID_EMIT_TIMEOUT")
        self._access = access
        self._messages = messages
        self._manager = manager
        self._transport_profile = require_browser_bridge_transport_profile(
            transport_profile
        )
        if access.transport_profile is not self._transport_profile:
            raise BrowserBridgeContextControllerError("INVALID_CONTEXT_ACCESS")
        if messages.transport_profile is not self._transport_profile:
            raise BrowserBridgeContextControllerError("INVALID_MESSAGE_DISPATCHER")
        self._route_authorizer = route_authorizer or (lambda _route: False)
        self._queue_projection = queue_projection
        self._max_streams = max_streams
        self._poll_interval_seconds = float(poll_interval_seconds)
        self._cancel_wait_seconds = float(cancel_wait_seconds)
        self._emit_timeout_seconds = float(emit_timeout_seconds)
        self._streams: dict[
            tuple[int, str, str, str], _PresentationStream
        ] = {}
        # Public lifecycle mutations are serialized.  Pollers never acquire
        # this lock and instead compare their exact retained stream object.
        self._dispatch_lock = asyncio.Lock()

    @property
    def stream_count(self) -> int:
        return len(self._streams)

    async def dispatch(
        self,
        event: str,
        route: BrowserBridgeContextRoute,
        document: Any,
    ) -> dict[str, Any]:
        if event not in _INBOUND_EVENTS:
            raise BrowserBridgeContextControllerDenied("EVENT_NOT_ALLOWED")
        route = _route(route)
        request = _request_document(document)
        self._require_current(route)
        if event == CONTEXT_LIST_EVENT:
            return await self._list(route, request)
        if event == CONTEXT_SUBSCRIBE_EVENT:
            return await self._subscribe(route, request)
        if event == CONTEXT_UNSUBSCRIBE_EVENT:
            return await self._unsubscribe(route, request)
        _exact_keys(
            request,
            required={"contract_version", "context_id", "client_message_id", "text"},
            optional={"artifact_ids", "tab_candidates"},
        )
        _contract(request)
        for name in ("artifact_ids", "tab_candidates"):
            if name in request:
                value = request.pop(name)
                if not isinstance(value, list) or value:
                    raise BrowserBridgeContextControllerDenied(
                        "ATTACHMENT_AUTHORITY_UNAVAILABLE"
                    )
        # The purpose-built dispatcher owns durable idempotency and performs
        # its own exact-route check immediately before the log/model effect.
        return self._messages.send(route, request)

    async def disconnect(
        self,
        *,
        principal: WsPrincipal,
        connector_sid: Any,
        load_generation_id: Any,
    ) -> bool:
        sid = _identifier(connector_sid, "connector_sid")
        generation = _identifier(load_generation_id, "load_generation_id")
        if not isinstance(principal, WsPrincipal):
            raise BrowserBridgeContextControllerError("INVALID_ROUTE")
        prefix = (id(principal), sid, generation)
        async with self._dispatch_lock:
            streams = [
                self._streams.pop(key)
                for key in tuple(self._streams)
                if key[:3] == prefix
            ]
            await self._cancel_streams(streams)
            removed = self._access.disconnect(
                principal=principal,
                connector_sid=sid,
                load_generation_id=generation,
            )
        return bool(streams) or removed

    async def _list(
        self,
        route: BrowserBridgeContextRoute,
        request: dict[str, Any],
    ) -> dict[str, Any]:
        _exact_keys(
            request,
            required={"contract_version"},
            optional={"limit"},
        )
        _contract(request)
        limit = request.get("limit", MAX_ADVERTISED_CONTEXTS)
        if isinstance(limit, bool) or not isinstance(limit, int) or not 1 <= limit <= MAX_ADVERTISED_CONTEXTS:
            raise BrowserBridgeContextControllerError("INVALID_STATE")
        async with self._dispatch_lock:
            contexts = self._access.advertise_contexts(route, limit=limit)
            advertised = {item["context_id"] for item in contexts}
            stale = [
                self._streams.pop(key)
                for key in tuple(self._streams)
                if key[:3] == _route_prefix(route) and key[3] not in advertised
            ]
            await self._cancel_streams(stale)
        self._require_current(route)
        return {"contract_version": CONTRACT_VERSION, "contexts": list(contexts)}

    async def _subscribe(
        self,
        route: BrowserBridgeContextRoute,
        request: dict[str, Any],
    ) -> dict[str, Any]:
        _exact_keys(
            request,
            required={"contract_version", "context_id"},
            optional={"from", "history", "history_before"},
        )
        _contract(request)
        context_id = _identifier(request["context_id"], "context_id")
        from_sequence = _cursor(request.get("from", 0), "from")
        history = request.get("history")
        if history is not None and history not in {"tail", "all"}:
            raise BrowserBridgeContextControllerError("INVALID_STATE")
        history_before = request.get("history_before")
        if history_before is not None:
            history_before = _cursor(history_before, "history_before")
        key = _stream_key(route, context_id)
        async with self._dispatch_lock:
            previous = self._streams.pop(key, None)
            await self._cancel_streams([previous] if previous is not None else [])
            if len(self._streams) >= self._max_streams:
                raise BrowserBridgeContextControllerDenied("CONTEXT_STREAM_LIMIT")
            subscribed = False
            try:
                self._access.subscribe(route, context_id=context_id)
                subscribed = True
                snapshot = self._access.project_snapshot(
                    route,
                    context_id=context_id,
                    from_sequence=from_sequence,
                    history=history,
                    history_before=history_before,
                    limit=MAX_CONTEXT_PAGE_EVENTS,
                )
                stream = _PresentationStream(
                    route=route,
                    context_id=context_id,
                    cursor=snapshot["last_sequence"],
                    completion_reported=bool(snapshot["complete"]),
                )
                # Register before emission so unsubscribe/disconnect can make
                # an in-flight frame stale.  Shared emit_to independently pins
                # the exact ConnectionInfo principal at dispatcher delivery.
                self._streams[key] = stream
                await self._emit(route, CONTEXT_SNAPSHOT_EVENT, snapshot)
                await self._queue_update(stream)
                if snapshot["complete"]:
                    completion = self._access.project_completion(
                        route, context_id=context_id, status="completed"
                    )
                    await self._emit(route, CONTEXT_COMPLETE_EVENT, completion)
                task = asyncio.create_task(
                    self._poll(stream),
                    name=f"browser-bridge-context:{context_id}",
                )
                stream.task = task
            except Exception:
                self._streams.pop(key, None)
                if subscribed:
                    try:
                        self._access.unsubscribe(route, context_id=context_id)
                    except Exception:
                        pass
                raise
        result: dict[str, Any] = {
            "contract_version": CONTRACT_VERSION,
            "context_id": context_id,
            "subscribed": True,
            "last_sequence": snapshot["last_sequence"],
        }
        if "history_before" in snapshot:
            result["history_before"] = snapshot["history_before"]
            result["has_more_history"] = snapshot["has_more_history"]
        return result

    async def _unsubscribe(
        self,
        route: BrowserBridgeContextRoute,
        request: dict[str, Any],
    ) -> dict[str, Any]:
        _exact_keys(request, required={"contract_version", "context_id"})
        _contract(request)
        context_id = _identifier(request["context_id"], "context_id")
        key = _stream_key(route, context_id)
        async with self._dispatch_lock:
            stream = self._streams.pop(key, None)
            await self._cancel_streams([stream] if stream is not None else [])
            self._access.unsubscribe(route, context_id=context_id)
        return {
            "contract_version": CONTRACT_VERSION,
            "context_id": context_id,
            "unsubscribed": True,
        }

    async def _poll(self, stream: _PresentationStream) -> None:
        key = _stream_key(stream.route, stream.context_id)
        try:
            while True:
                if not self._stream_is_current(key, stream):
                    return
                await asyncio.sleep(self._poll_interval_seconds)
                if not self._stream_is_current(key, stream):
                    return
                self._require_current(stream.route)
                await self._queue_update(stream)
                snapshot = self._access.project_snapshot(
                    stream.route,
                    context_id=stream.context_id,
                    from_sequence=stream.cursor,
                    limit=MAX_CONTEXT_PAGE_EVENTS,
                )
                if not self._stream_is_current(key, stream):
                    return
                prior_cursor = stream.cursor
                page_cursor = snapshot["last_sequence"]
                stream.cursor = page_cursor
                events = snapshot["events"]
                for index, event in enumerate(events):
                    if not self._stream_is_current(key, stream):
                        return
                    # Do not expose the page-end cursor until the last visible
                    # event has been delivered.  If transport drops mid-page,
                    # replay starts from the prior source cursor and stable item
                    # sequences are safely upserted instead of skipping frames.
                    event_cursor = (
                        page_cursor if index == len(events) - 1 else prior_cursor
                    )
                    await self._emit(
                        stream.route,
                        CONTEXT_EVENT,
                        {**event, "last_sequence": event_cursor},
                    )
                complete = bool(snapshot["complete"])
                if complete and (not stream.completion_reported or bool(events)):
                    if not self._stream_is_current(key, stream):
                        return
                    completion = self._access.project_completion(
                        stream.route,
                        context_id=stream.context_id,
                        status="completed",
                    )
                    await self._emit(
                        stream.route, CONTEXT_COMPLETE_EVENT, completion
                    )
                stream.completion_reported = complete
        except asyncio.CancelledError:
            raise
        except Exception:
            # Source/route/transport loss terminates only this presentation
            # reader.  Raw source or transport errors are never reflected.
            return
        finally:
            if self._streams.get(key) is stream:
                self._streams.pop(key, None)
                try:
                    self._access.unsubscribe(
                        stream.route, context_id=stream.context_id
                    )
                except Exception:
                    pass

    async def _queue_update(self, stream: _PresentationStream) -> None:
        if self._queue_projection is None:
            return
        self._require_current(stream.route)
        payload = self._queue_projection(stream.route, stream.context_id)
        if not isinstance(payload, dict) or set(payload) != {"contract_version", "context_id", "message_queue"}:
            raise BrowserBridgeContextControllerError("INVALID_QUEUE_PROJECTION")
        items = payload["message_queue"]
        if type(payload["contract_version"]) is not int or payload["contract_version"] != 1 or payload["context_id"] != stream.context_id or not isinstance(items, list) or len(items) > 32:
            raise BrowserBridgeContextControllerError("INVALID_QUEUE_PROJECTION")
        identifiers = set()
        for item in items:
            if not isinstance(item, dict) or set(item) != {"id", "text", "attachments", "attachment_count"}:
                raise BrowserBridgeContextControllerError("INVALID_QUEUE_PROJECTION")
            item_id = _identifier(item["id"], "item_id")
            if item_id in identifiers or not isinstance(item["text"], str) or len(item["text"]) > 100 or item["attachments"] != [] or type(item["attachment_count"]) is not int or item["attachment_count"] != 0:
                raise BrowserBridgeContextControllerError("INVALID_QUEUE_PROJECTION")
            identifiers.add(item_id)
        signature = json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
        self._require_current(stream.route)
        if signature == stream.queue_signature:
            return
        await self._emit(stream.route, CONTEXT_QUEUE_EVENT, payload)
        stream.queue_signature = signature

    async def _emit(
        self,
        route: BrowserBridgeContextRoute,
        event: str,
        payload: dict[str, Any],
    ) -> None:
        if event not in _OUTBOUND_EVENTS:
            raise BrowserBridgeContextControllerDenied("EVENT_NOT_ALLOWED")
        self._require_current(route)
        data = {"contract_version": CONTRACT_VERSION, **payload}
        await asyncio.wait_for(
            self._manager.emit_to(
                self._transport_profile.namespace,
                route.connector_sid,
                event,
                data,
                handler_id=self._transport_profile.handler_id,
                correlation_id=restricted_correlation_id(None),
                expected_principal=route.principal,
            ),
            timeout=self._emit_timeout_seconds,
        )
        self._require_current(route)

    async def _cancel_streams(
        self, streams: list[_PresentationStream]
    ) -> None:
        tasks = [stream.task for stream in streams if stream.task is not None]
        for task in tasks:
            task.cancel()
        if not tasks:
            return
        done, _pending = await asyncio.wait(
            tasks, timeout=self._cancel_wait_seconds
        )
        # Retrieve terminal exceptions without waiting on a cancellation-hostile
        # dependency.  Removed stream identities prevent any future emission.
        for task in done:
            try:
                task.exception()
            except asyncio.CancelledError:
                pass

    def _stream_is_current(
        self,
        key: tuple[int, str, str, str],
        stream: _PresentationStream,
    ) -> bool:
        return self._streams.get(key) is stream and self._is_current(stream.route)

    def _require_current(self, route: BrowserBridgeContextRoute) -> None:
        if not self._is_current(route):
            raise BrowserBridgeContextControllerDenied("STALE_BRIDGE_ROUTE")

    def _is_current(self, route: BrowserBridgeContextRoute) -> bool:
        if route.transport_profile is not self._transport_profile:
            return False
        try:
            return self._route_authorizer(route) is True
        except Exception:
            return False


def _request_document(value: Any) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise BrowserBridgeContextControllerError("INVALID_STATE")
    result = dict(value)
    # WsManager injects this already-sanitized envelope value into handler data;
    # it is transport metadata and never part of a native method document.
    result.pop("correlationId", None)
    return result


def _exact_keys(
    value: dict[str, Any],
    *,
    required: set[str],
    optional: set[str] | None = None,
) -> None:
    optional = optional or set()
    keys = set(value)
    if not required <= keys or not keys <= required | optional:
        raise BrowserBridgeContextControllerError("INVALID_STATE")


def _contract(value: dict[str, Any]) -> None:
    version = value.get("contract_version")
    if isinstance(version, bool) or not isinstance(version, int) or version != CONTRACT_VERSION:
        raise BrowserBridgeContextControllerError("INVALID_STATE")


def _route(value: Any) -> BrowserBridgeContextRoute:
    if not isinstance(value, BrowserBridgeContextRoute):
        raise BrowserBridgeContextControllerError("INVALID_ROUTE")
    return value


def _identifier(value: Any, name: str) -> str:
    if not isinstance(value, str) or _IDENTIFIER.fullmatch(value) is None:
        raise BrowserBridgeContextControllerError(f"INVALID_{name.upper()}")
    return value


def _cursor(value: Any, name: str) -> int:
    if (
        isinstance(value, bool)
        or not isinstance(value, int)
        or not 0 <= value <= MAX_CONTEXT_CURSOR
    ):
        raise BrowserBridgeContextControllerError(f"INVALID_{name.upper()}")
    return value


def _route_prefix(route: BrowserBridgeContextRoute) -> tuple[int, str, str]:
    return (id(route.principal), route.connector_sid, route.load_generation_id)


def _stream_key(
    route: BrowserBridgeContextRoute, context_id: str
) -> tuple[int, str, str, str]:
    return (*_route_prefix(route), context_id)
