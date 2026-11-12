"""Durable, sanitized lifecycle intent for the typed extension browser.

This module is deliberately transport-agnostic and inactive by default.  The
future activation path must inject both an exact route resolver and a sender
that delegates finalization to the restricted browser operation broker.
Neither persisted state nor Browser project configuration supplies authority.
"""

from __future__ import annotations

import asyncio
from collections import OrderedDict
from concurrent.futures import Future
from dataclasses import dataclass, replace
import json
import re
import threading
import time
from typing import Any, Awaitable, Callable, Mapping, Protocol
import uuid

from helpers.ws_principal import WsPrincipal
from plugins._a0_connector.helpers.browser_bridge_transport import (
    PRODUCTION_BROWSER_BRIDGE_TRANSPORT,
    BrowserBridgeTransportProfile,
    require_browser_bridge_transport_profile,
    require_transport_principal_identity,
)
from plugins._browser.helpers.config import (
    HOST_BROWSER_SELECTION_KEY,
    RUNTIME_BACKEND_KEY,
    get_browser_config,
    parse_extension_browser_selection,
)


SESSION_STORE_CONTRACT = "a0.browser-bridge.extension-sessions.v1"
SESSION_STORE_VERSION = 1
SESSION_STORE_KEY = "browser_extension_sessions_v1"
CONTROL_EVENT = "connector_browser_control"

MAX_IDENTIFIER_BYTES = 256
MAX_REASON_BYTES = 128
MAX_CONTEXTS = 128
MAX_TURNS_PER_SESSION = 64
MAX_DISPOSITIONS_PER_TURN = 256
MAX_STORE_BYTES = 512 * 1024
MAX_AGENT_TURN_BINDINGS = 1_024

TURN_ACTIVE = "active"
TURN_FINALIZATION_PENDING = "finalization_pending"
TURN_FINALIZED = "finalized"
TURN_OUTCOME_UNKNOWN = "outcome_unknown"
TURN_STATES = frozenset(
    {
        TURN_ACTIVE,
        TURN_FINALIZATION_PENDING,
        TURN_FINALIZED,
        TURN_OUTCOME_UNKNOWN,
    }
)
FINALIZATION_TERMINAL_STATES = frozenset({TURN_FINALIZED, TURN_OUTCOME_UNKNOWN})
LEASE_DISPOSITIONS = frozenset({"ephemeral", "deliverable", "handoff"})

_CORRELATION_ID_RE = re.compile(r"[A-Za-z0-9_-]{1,128}")
_GENERATION_ID_RE = re.compile(r"[A-Za-z0-9][A-Za-z0-9._:-]{0,255}")


class ExtensionSessionStateError(RuntimeError):
    """A lifecycle request or durable state failed closed."""

    def __init__(self, code: str, message: str) -> None:
        super().__init__(message)
        self.code = code


@dataclass(frozen=True, slots=True)
class ValidatedExtensionRoute:
    """Process-only current route; none of these fields are persisted."""

    bridge_id: str
    browser_id: str
    principal: WsPrincipal
    connector_sid: str
    load_generation_id: str
    transport_profile: BrowserBridgeTransportProfile = (
        PRODUCTION_BROWSER_BRIDGE_TRANSPORT
    )

    def __post_init__(self) -> None:
        bridge_id = _identifier(self.bridge_id, "bridge_id")
        profile = require_browser_bridge_transport_profile(
            self.transport_profile
        )
        browser_id = _browser_id(self.browser_id, bridge_id, profile)
        connector_sid = _identifier(self.connector_sid, "connector_sid")
        generation_id = _identifier(
            self.load_generation_id, "load_generation_id"
        )
        if not _GENERATION_ID_RE.fullmatch(generation_id):
            raise ExtensionSessionStateError(
                "INVALID_ROUTE", "The route generation ID is invalid"
            )
        principal = self.principal
        try:
            require_transport_principal_identity(principal, profile)
        except ValueError:
            raise ExtensionSessionStateError(
                "INVALID_ROUTE", "The route principal is not authorized for control"
            ) from None
        if (
            principal.principal_id != bridge_id
            or "browser.control" not in principal.scopes
            or not principal.permits_outbound(CONTROL_EVENT, profile.handler_id)
        ):
            raise ExtensionSessionStateError(
                "INVALID_ROUTE", "The route principal is not authorized for control"
            )
        object.__setattr__(self, "bridge_id", bridge_id)
        object.__setattr__(self, "browser_id", browser_id)
        object.__setattr__(self, "connector_sid", connector_sid)
        object.__setattr__(self, "load_generation_id", generation_id)


@dataclass(frozen=True, slots=True)
class ExtensionTurnIntent:
    turn_id: str
    state: str
    dispositions: tuple[tuple[str, str], ...]
    control_id: str | None
    reason: str | None
    started_at_ms: int
    finalization_requested_at_ms: int | None
    settled_at_ms: int | None


@dataclass(frozen=True, slots=True)
class ExtensionSessionIntent:
    context_id: str
    browser_session_id: str
    browser_id: str
    bridge_id: str
    turns: tuple[ExtensionTurnIntent, ...]
    last_acked_event_sequence: int
    created_at_ms: int
    updated_at_ms: int
    retire_requested: bool
    remove_requested: bool


@dataclass(frozen=True, slots=True)
class ActiveExtensionTurnBinding:
    """Sanitized active binding used by a future operation-binding factory."""

    context_id: str
    browser_session_id: str
    browser_id: str
    bridge_id: str
    turn_id: str


@dataclass(frozen=True, slots=True)
class ExtensionFinalizationIntent:
    control_id: str
    context_id: str
    browser_session_id: str
    browser_id: str
    bridge_id: str
    turn_id: str
    dispositions: tuple[tuple[str, str], ...]
    reason: str
    requested_at_ms: int
    contract_version: int = 1

    def disposition_mapping(self) -> dict[str, str]:
        return dict(self.dispositions)


class ExtensionSessionPersistence(Protocol):
    def load(self) -> Any: ...

    def save(self, value: Mapping[str, Any]) -> None: ...


class KvpExtensionSessionPersistence:
    """Small adapter over Agent Zero's atomic persistent KVP writes."""

    def __init__(self, key: str = SESSION_STORE_KEY) -> None:
        self._key = key

    def load(self) -> Any:
        from helpers import kvp

        return kvp.get_persistent(self._key, None)

    def save(self, value: Mapping[str, Any]) -> None:
        from helpers import kvp

        kvp.set_persistent(self._key, dict(value))


class ExtensionSessionRegistry:
    """Concurrency-safe bounded registry for durable lifecycle intent."""

    def __init__(
        self,
        *,
        persistence: ExtensionSessionPersistence | None = None,
        clock_ms: Callable[[], int] | None = None,
        id_factory: Callable[[], str] | None = None,
        max_contexts: int = MAX_CONTEXTS,
        max_turns_per_session: int = MAX_TURNS_PER_SESSION,
        max_dispositions_per_turn: int = MAX_DISPOSITIONS_PER_TURN,
        max_store_bytes: int = MAX_STORE_BYTES,
        transport_profile: BrowserBridgeTransportProfile = (
            PRODUCTION_BROWSER_BRIDGE_TRANSPORT
        ),
    ) -> None:
        if min(
            max_contexts,
            max_turns_per_session,
            max_dispositions_per_turn,
            max_store_bytes,
        ) < 1:
            raise ValueError("Extension session bounds must be positive")
        self._persistence = persistence or KvpExtensionSessionPersistence()
        self._transport_profile = require_browser_bridge_transport_profile(
            transport_profile
        )
        self._clock_ms = clock_ms or (lambda: time.time_ns() // 1_000_000)
        self._id_factory = id_factory or (lambda: uuid.uuid4().hex)
        self._max_contexts = max_contexts
        self._max_turns = max_turns_per_session
        self._max_dispositions = max_dispositions_per_turn
        self._max_store_bytes = max_store_bytes
        self._lock = threading.RLock()

    @property
    def transport_profile(self) -> BrowserBridgeTransportProfile:
        return self._transport_profile

    def sessions(self) -> tuple[ExtensionSessionIntent, ...]:
        with self._lock:
            sessions = self._load_locked()
            return tuple(sessions[key] for key in sorted(sessions))

    def session(self, context_id: str) -> ExtensionSessionIntent | None:
        context_id = _identifier(context_id, "context_id")
        with self._lock:
            return self._load_locked().get(context_id)

    def begin_turn(
        self, *, context_id: str, browser_id: str, bridge_id: str
    ) -> tuple[ExtensionSessionIntent, ExtensionTurnIntent]:
        context_id = _identifier(context_id, "context_id")
        bridge_id = _identifier(bridge_id, "bridge_id")
        browser_id = _browser_id(browser_id, bridge_id, self._transport_profile)
        with self._lock:
            sessions = self._load_locked()
            now = _timestamp(self._clock_ms(), "clock")
            current = sessions.get(context_id)
            if current is None:
                if len(sessions) >= self._max_contexts:
                    raise ExtensionSessionStateError(
                        "REGISTRY_FULL", "The extension session registry is full"
                    )
                current = ExtensionSessionIntent(
                    context_id=context_id,
                    browser_session_id=self._fresh_session_id(sessions),
                    browser_id=browser_id,
                    bridge_id=bridge_id,
                    turns=(),
                    last_acked_event_sequence=0,
                    created_at_ms=now,
                    updated_at_ms=now,
                    retire_requested=False,
                    remove_requested=False,
                )
            elif current.browser_id != browser_id or current.bridge_id != bridge_id:
                raise ExtensionSessionStateError(
                    "BRIDGE_PIN_CONFLICT",
                    "A browser session cannot migrate to another bridge",
                )
            elif current.retire_requested or current.remove_requested:
                raise ExtensionSessionStateError(
                    "SESSION_RETIRING", "The browser session is retiring"
                )

            turns = list(current.turns)
            while len(turns) >= self._max_turns and turns[0].state == TURN_FINALIZED:
                turns.pop(0)
            if len(turns) >= self._max_turns:
                raise ExtensionSessionStateError(
                    "TURN_REGISTRY_FULL", "The extension turn registry is full"
                )
            turn = ExtensionTurnIntent(
                turn_id=self._fresh_turn_id(turns),
                state=TURN_ACTIVE,
                dispositions=(),
                control_id=None,
                reason=None,
                started_at_ms=now,
                finalization_requested_at_ms=None,
                settled_at_ms=None,
            )
            turns.append(turn)
            current = replace(current, turns=tuple(turns), updated_at_ms=now)
            sessions[context_id] = current
            self._save_locked(sessions)
            return current, turn

    def active_turn_binding(
        self, *, context_id: str, turn_id: str
    ) -> ActiveExtensionTurnBinding | None:
        context_id = _identifier(context_id, "context_id")
        turn_id = _identifier(turn_id, "turn_id")
        with self._lock:
            session = self._load_locked().get(context_id)
            if session is None:
                return None
            turns = list(session.turns)
            try:
                turn = turns[_turn_index(turns, turn_id)]
            except ExtensionSessionStateError:
                return None
            if turn.state != TURN_ACTIVE:
                return None
            return ActiveExtensionTurnBinding(
                context_id=session.context_id,
                browser_session_id=session.browser_session_id,
                browser_id=session.browser_id,
                bridge_id=session.bridge_id,
                turn_id=turn.turn_id,
            )

    def record_disposition(
        self,
        *,
        context_id: str,
        browser_session_id: str,
        turn_id: str,
        lease_id: str,
        disposition: str,
    ) -> ExtensionTurnIntent:
        """Record only a lease ID and disposition, never remote tab metadata."""

        context_id = _identifier(context_id, "context_id")
        browser_session_id = _identifier(browser_session_id, "browser_session_id")
        turn_id = _identifier(turn_id, "turn_id")
        lease_id = _identifier(lease_id, "lease_id")
        if disposition not in LEASE_DISPOSITIONS:
            raise ExtensionSessionStateError(
                "INVALID_DISPOSITION", "The lease disposition is invalid"
            )
        with self._lock:
            sessions = self._load_locked()
            session = _require_session(sessions, context_id, browser_session_id)
            turns = list(session.turns)
            index = _turn_index(turns, turn_id)
            turn = turns[index]
            if turn.state != TURN_ACTIVE:
                raise ExtensionSessionStateError(
                    "TURN_FINALIZING", "The turn no longer accepts dispositions"
                )
            dispositions = dict(turn.dispositions)
            if lease_id not in dispositions and len(dispositions) >= self._max_dispositions:
                raise ExtensionSessionStateError(
                    "DISPOSITION_REGISTRY_FULL", "The turn disposition registry is full"
                )
            dispositions[lease_id] = disposition
            turn = replace(turn, dispositions=tuple(sorted(dispositions.items())))
            turns[index] = turn
            now = _timestamp(self._clock_ms(), "clock")
            sessions[context_id] = replace(
                session, turns=tuple(turns), updated_at_ms=now
            )
            self._save_locked(sessions)
            return turn

    def stage_finalize(
        self,
        *,
        context_id: str,
        turn_id: str | None = None,
        reason: str,
        retire: bool = False,
        remove: bool = False,
    ) -> tuple[ExtensionFinalizationIntent, ...]:
        context_id = _identifier(context_id, "context_id")
        if turn_id is not None:
            turn_id = _identifier(turn_id, "turn_id")
        reason = _reason(reason)
        with self._lock:
            sessions = self._load_locked()
            session = sessions.get(context_id)
            if session is None:
                return ()
            now = _timestamp(self._clock_ms(), "clock")
            turns = list(session.turns)
            target_indexes = (
                [_turn_index(turns, turn_id)]
                if turn_id is not None
                else list(range(len(turns)))
            )
            intents: list[ExtensionFinalizationIntent] = []
            allocated_control_ids = {
                candidate.control_id
                for candidate_session in sessions.values()
                for candidate in candidate_session.turns
                if candidate.control_id is not None
            }
            for index in target_indexes:
                turn = turns[index]
                if turn.state == TURN_ACTIVE:
                    control_id = self._fresh_unique(
                        allocated_control_ids, "control_id", correlation=True
                    )
                    allocated_control_ids.add(control_id)
                    turn = replace(
                        turn,
                        state=TURN_FINALIZATION_PENDING,
                        control_id=control_id,
                        reason=reason,
                        finalization_requested_at_ms=now,
                    )
                    turns[index] = turn
                if turn.state == TURN_FINALIZATION_PENDING:
                    intents.append(_finalization_intent(session, turn))

            updated = replace(
                session,
                turns=tuple(turns),
                updated_at_ms=now,
                retire_requested=session.retire_requested or retire or remove,
                remove_requested=session.remove_requested or remove,
            )
            if _can_delete(updated):
                sessions.pop(context_id, None)
            else:
                sessions[context_id] = updated
            self._save_locked(sessions)
            return tuple(intents)

    def pending_finalizations(self) -> tuple[ExtensionFinalizationIntent, ...]:
        with self._lock:
            intents: list[ExtensionFinalizationIntent] = []
            sessions = self._load_locked()
            for context_id in sorted(sessions):
                session = sessions[context_id]
                for turn in session.turns:
                    if turn.state == TURN_FINALIZATION_PENDING:
                        intents.append(_finalization_intent(session, turn))
            return tuple(intents)

    def settle_finalization(
        self,
        intent: ExtensionFinalizationIntent,
        status: str,
    ) -> str:
        if status not in FINALIZATION_TERMINAL_STATES:
            raise ExtensionSessionStateError(
                "INVALID_SETTLEMENT", "The finalization settlement is invalid"
            )
        with self._lock:
            sessions = self._load_locked()
            session = sessions.get(intent.context_id)
            if session is None:
                return "not_found"
            if (
                session.browser_session_id != intent.browser_session_id
                or session.browser_id != intent.browser_id
                or session.bridge_id != intent.bridge_id
            ):
                return "mismatch"
            turns = list(session.turns)
            try:
                index = _turn_index(turns, intent.turn_id)
            except ExtensionSessionStateError:
                return "not_found"
            turn = turns[index]
            if turn.state in FINALIZATION_TERMINAL_STATES:
                return "duplicate"
            if (
                turn.state != TURN_FINALIZATION_PENDING
                or turn.control_id != intent.control_id
                or turn.reason != intent.reason
                or turn.dispositions != intent.dispositions
                or turn.finalization_requested_at_ms != intent.requested_at_ms
            ):
                return "mismatch"
            now = _timestamp(self._clock_ms(), "clock")
            turns[index] = replace(turn, state=status, settled_at_ms=now)
            updated = replace(session, turns=tuple(turns), updated_at_ms=now)
            if _can_delete(updated):
                sessions.pop(intent.context_id, None)
            else:
                sessions[intent.context_id] = updated
            self._save_locked(sessions)
            return "settled"

    def update_event_cursor(
        self,
        *,
        context_id: str,
        browser_session_id: str,
        sequence: int,
    ) -> ExtensionSessionIntent:
        context_id = _identifier(context_id, "context_id")
        browser_session_id = _identifier(browser_session_id, "browser_session_id")
        sequence = _nonnegative_int(sequence, "sequence")
        with self._lock:
            sessions = self._load_locked()
            session = _require_session(sessions, context_id, browser_session_id)
            if sequence < session.last_acked_event_sequence:
                raise ExtensionSessionStateError(
                    "STALE_EVENT_CURSOR", "The event cursor cannot move backwards"
                )
            now = _timestamp(self._clock_ms(), "clock")
            session = replace(
                session, last_acked_event_sequence=sequence, updated_at_ms=now
            )
            sessions[context_id] = session
            self._save_locked(sessions)
            return session

    def _fresh_id(self, field: str) -> str:
        return _identifier(self._id_factory(), field)

    def _fresh_correlation_id(self, field: str) -> str:
        value = self._fresh_id(field)
        if not _CORRELATION_ID_RE.fullmatch(value):
            raise ExtensionSessionStateError(
                "INVALID_IDENTIFIER", f"Generated {field} is not a safe correlation ID"
            )
        return value

    def _fresh_session_id(
        self, sessions: Mapping[str, ExtensionSessionIntent]
    ) -> str:
        existing = {session.browser_session_id for session in sessions.values()}
        return self._fresh_unique(existing, "browser_session_id", correlation=False)

    def _fresh_turn_id(self, turns: list[ExtensionTurnIntent]) -> str:
        return self._fresh_unique(
            {turn.turn_id for turn in turns}, "turn_id", correlation=True
        )

    def _fresh_unique(
        self, existing: set[str], field: str, *, correlation: bool
    ) -> str:
        for _attempt in range(8):
            value = (
                self._fresh_correlation_id(field)
                if correlation
                else self._fresh_id(field)
            )
            if value not in existing:
                return value
        raise ExtensionSessionStateError(
            "IDENTIFIER_COLLISION", f"Could not allocate a fresh {field}"
        )

    def _load_locked(self) -> dict[str, ExtensionSessionIntent]:
        try:
            raw = self._persistence.load()
        except Exception:
            raise ExtensionSessionStateError(
                "STORE_UNAVAILABLE", "The extension session store is unavailable"
            ) from None
        if raw is None:
            return {}
        return _decode_store(
            raw,
            max_contexts=self._max_contexts,
            max_turns=self._max_turns,
            max_dispositions=self._max_dispositions,
            transport_profile=self._transport_profile,
        )

    def _save_locked(self, sessions: Mapping[str, ExtensionSessionIntent]) -> None:
        document = _encode_store(sessions)
        encoded = json.dumps(
            document, ensure_ascii=False, separators=(",", ":"), sort_keys=True
        ).encode("utf-8")
        if len(encoded) > self._max_store_bytes:
            raise ExtensionSessionStateError(
                "STORE_FULL", "The extension session store exceeds its byte bound"
            )
        try:
            self._persistence.save(document)
        except Exception:
            raise ExtensionSessionStateError(
                "STORE_UNAVAILABLE", "The extension session store is unavailable"
            ) from None


RouteResolver = Callable[[str, str], ValidatedExtensionRoute | None]
FinalizationSender = Callable[
    [ExtensionFinalizationIntent, ValidatedExtensionRoute], Awaitable[str]
]
CoroutineSubmitter = Callable[[Awaitable[None]], Future[Any]]


class ProcessFinalizationDispatcher:
    """Process-owned delivery whose futures outlive any requesting agent task."""

    def __init__(
        self,
        *,
        registry: ExtensionSessionRegistry,
        route_resolver: RouteResolver,
        sender: FinalizationSender,
        submitter: CoroutineSubmitter | None = None,
        max_inflight: int = 128,
    ) -> None:
        if max_inflight < 1:
            raise ValueError("max_inflight must be positive")
        self._registry = registry
        self._route_resolver = route_resolver
        self._sender = sender
        self._submitter = submitter or _background_submitter
        self._max_inflight = max_inflight
        self._inflight: dict[str, Future[Any]] = {}
        self._lock = threading.RLock()

    @property
    def inflight_count(self) -> int:
        with self._lock:
            return len(self._inflight)

    def schedule(
        self, intents: tuple[ExtensionFinalizationIntent, ...]
    ) -> tuple[str, ...]:
        scheduled: list[str] = []
        for intent in intents:
            with self._lock:
                if intent.control_id in self._inflight:
                    continue
                if len(self._inflight) >= self._max_inflight:
                    break
                if self._resolve_route(intent) is None:
                    continue
                coroutine = self._dispatch(intent)
                try:
                    future = self._submitter(coroutine)
                except Exception:
                    if asyncio.iscoroutine(coroutine):
                        coroutine.close()
                    continue
                self._inflight[intent.control_id] = future
            future.add_done_callback(
                lambda _future, control_id=intent.control_id: self._finished(control_id)
            )
            scheduled.append(intent.control_id)
        return tuple(scheduled)

    def replay_pending(self) -> tuple[str, ...]:
        return self.schedule(self._registry.pending_finalizations())

    def _resolve_route(
        self, intent: ExtensionFinalizationIntent
    ) -> ValidatedExtensionRoute | None:
        try:
            route = self._route_resolver(intent.context_id, intent.bridge_id)
        except Exception:
            return None
        if not isinstance(route, ValidatedExtensionRoute):
            return None
        if route.bridge_id != intent.bridge_id or route.browser_id != intent.browser_id:
            return None
        return route

    async def _dispatch(
        self,
        intent: ExtensionFinalizationIntent,
    ) -> None:
        # Route/SID/generation are live process authority. Re-resolve after the
        # thread handoff so a schedule-to-send race cannot use a captured SID.
        route = self._resolve_route(intent)
        if route is None:
            return
        try:
            result = await self._sender(intent, route)
        except asyncio.CancelledError:
            # Process shutdown is not evidence that a control did or did not apply.
            raise
        except Exception:
            result = TURN_OUTCOME_UNKNOWN
        status = TURN_FINALIZED if result == TURN_FINALIZED else TURN_OUTCOME_UNKNOWN
        self._registry.settle_finalization(intent, status)

    def _finished(self, control_id: str) -> None:
        with self._lock:
            self._inflight.pop(control_id, None)


class ExtensionSessionLifecycle:
    """Narrow hook-facing adapter, unconfigured and effect-free by default."""

    def __init__(
        self,
        *,
        registry: ExtensionSessionRegistry | None = None,
        config_loader: Callable[[Any], Mapping[str, Any]] | None = None,
        max_agent_bindings: int = MAX_AGENT_TURN_BINDINGS,
        transport_profile: BrowserBridgeTransportProfile = (
            PRODUCTION_BROWSER_BRIDGE_TRANSPORT
        ),
    ) -> None:
        if max_agent_bindings < 1:
            raise ValueError("max_agent_bindings must be positive")
        self._transport_profile = require_browser_bridge_transport_profile(
            transport_profile
        )
        self.registry = registry or ExtensionSessionRegistry(
            transport_profile=self._transport_profile
        )
        if self.registry.transport_profile is not self._transport_profile:
            raise ValueError("Extension lifecycle transport mismatch")
        self._config_loader = config_loader or get_browser_config
        self._max_agent_bindings = max_agent_bindings
        self._route_resolver: RouteResolver | None = None
        self._dispatcher: ProcessFinalizationDispatcher | None = None
        self._configuration_owner: object | None = None
        self._configuration_retiring = False
        self._agent_turns: OrderedDict[tuple[str, int], str] = OrderedDict()
        self._synthetic_turns: OrderedDict[
            tuple[str, int], ActiveExtensionTurnBinding
        ] = OrderedDict()
        self._lock = threading.RLock()

    @property
    def transport_profile(self) -> BrowserBridgeTransportProfile:
        return self._transport_profile

    @property
    def configured(self) -> bool:
        with self._lock:
            return (
                self._configuration_owner is not None
                and not self._configuration_retiring
                and self._dispatcher is not None
                and self._route_resolver is not None
            )

    def configured_for(self, owner: object) -> bool:
        with self._lock:
            return (
                owner is not None
                and self._configuration_owner is owner
                and not self._configuration_retiring
                and self._dispatcher is not None
                and self._route_resolver is not None
            )

    def configure(
        self,
        *,
        route_resolver: RouteResolver,
        sender: FinalizationSender,
        submitter: CoroutineSubmitter | None = None,
        max_inflight: int = 128,
        owner: object | None = None,
    ) -> tuple[str, ...]:
        configuration_owner = _legacy_lifecycle_owner if owner is None else owner
        with self._lock:
            if (
                self._configuration_owner is not None
                or self._configuration_retiring
                or self._dispatcher is not None
                or self._route_resolver is not None
            ):
                raise ExtensionSessionStateError(
                    "ALREADY_CONFIGURED",
                    "The extension session lifecycle is already configured",
                )
            dispatcher = ProcessFinalizationDispatcher(
                registry=self.registry,
                route_resolver=route_resolver,
                sender=sender,
                submitter=submitter,
                max_inflight=max_inflight,
            )
            self._configuration_owner = configuration_owner
            self._configuration_retiring = False
            self._route_resolver = route_resolver
            self._dispatcher = dispatcher
        return dispatcher.replay_pending()

    def unconfigure(self, *, owner: object) -> tuple[str, ...]:
        """Withdraw one exact owner and durably finalize its tracked turns.

        Existing process-owned sends are not cancelled or relabelled.  New hook
        calls become inert before the tracked bindings are detached.  The
        established ``restarted`` wire reason is used for reload/owner retire;
        no private lifecycle reason is sent to the extension.
        """

        if owner is None:
            raise ExtensionSessionStateError(
                "OWNER_MISMATCH", "The extension session lifecycle owner is invalid"
            )
        with self._lock:
            if (
                self._configuration_owner is not owner
                or self._configuration_retiring
            ):
                raise ExtensionSessionStateError(
                    "OWNER_MISMATCH",
                    "The extension session lifecycle is owned by another component",
                )
            dispatcher = self._dispatcher
            self._configuration_retiring = True
            agent_turns = tuple(
                (context_id, turn_id)
                for (context_id, _agent_id), turn_id in self._agent_turns.items()
            )
            synthetic_turns = tuple(
                (binding.context_id, binding.turn_id)
                for binding in self._synthetic_turns.values()
            )

        intents: list[ExtensionFinalizationIntent] = []
        seen: set[tuple[str, str]] = set()
        for context_id, turn_id in (*agent_turns, *synthetic_turns):
            key = (context_id, turn_id)
            if key in seen:
                continue
            seen.add(key)
            try:
                staged = self.registry.stage_finalize(
                    context_id=context_id,
                    turn_id=turn_id,
                    reason="restarted",
                )
            except Exception:
                with self._lock:
                    if self._configuration_owner is owner:
                        self._configuration_retiring = False
                raise
            intents.extend(staged)
        with self._lock:
            if self._configuration_owner is not owner:
                self._configuration_retiring = False
                raise ExtensionSessionStateError(
                    "OWNER_MISMATCH",
                    "The extension session lifecycle owner changed during retirement",
                )
            self._configuration_owner = None
            self._configuration_retiring = False
            self._route_resolver = None
            self._dispatcher = None
            self._agent_turns.clear()
            self._synthetic_turns.clear()
        if dispatcher is None:
            return ()
        return dispatcher.schedule(tuple(intents))

    def begin_agent_turn(self, agent: Any) -> ExtensionTurnIntent | None:
        selection = self._validated_selection(agent, require_route=True)
        if selection is None:
            return None
        context_id, browser_id, bridge_id = selection
        key = (context_id, id(agent))
        with self._lock:
            if key in self._synthetic_turns:
                return None
            existing_turn = self._agent_turns.pop(key, None)
            if (
                existing_turn is None
                and len(self._agent_turns) + len(self._synthetic_turns)
                >= self._max_agent_bindings
            ):
                return None
        if existing_turn is not None:
            self._stage_and_dispatch(
                context_id=context_id,
                turn_id=existing_turn,
                reason="restarted",
            )
        try:
            _session, turn = self.registry.begin_turn(
                context_id=context_id,
                browser_id=browser_id,
                bridge_id=bridge_id,
            )
        except ExtensionSessionStateError:
            return None
        conflicting_owner = False
        configuration_lost = False
        with self._lock:
            if self._configuration_owner is None or self._configuration_retiring:
                configuration_lost = True
            elif key in self._agent_turns or key in self._synthetic_turns:
                conflicting_owner = True
            elif (
                len(self._agent_turns) + len(self._synthetic_turns)
                >= self._max_agent_bindings
            ):
                conflicting_owner = True
            else:
                self._agent_turns[key] = turn.turn_id
                self._agent_turns.move_to_end(key)
        if configuration_lost or conflicting_owner:
            self._stage_and_dispatch(
                context_id=context_id,
                turn_id=turn.turn_id,
                reason="restarted" if configuration_lost else "superseded",
            )
            return None
        self._attach_task_done_finalizer(agent, context_id, turn.turn_id)
        return turn

    def finalize_agent_turn(self, agent: Any, *, reason: str) -> tuple[str, ...]:
        context_id = str(getattr(getattr(agent, "context", None), "id", "") or "")
        try:
            context_id = _identifier(context_id, "context_id")
        except ExtensionSessionStateError:
            return ()
        key = (context_id, id(agent))
        with self._lock:
            turn_id = self._agent_turns.pop(key, None)
        if turn_id is None:
            return ()
        return self._stage_and_dispatch(
            context_id=context_id, turn_id=turn_id, reason=reason
        )

    def finalize_tracked_agent_turn(
        self, agent: Any, *, turn_id: str, reason: str
    ) -> tuple[str, ...]:
        """Finalize a callback's exact turn without touching a replacement."""

        context_id = str(getattr(getattr(agent, "context", None), "id", "") or "")
        key = (context_id, id(agent))
        with self._lock:
            if self._agent_turns.get(key) != turn_id:
                return ()
            self._agent_turns.pop(key, None)
        return self._stage_and_dispatch(
            context_id=context_id, turn_id=turn_id, reason=reason
        )

    def active_agent_turn(self, agent: Any) -> ActiveExtensionTurnBinding | None:
        """Return only an exact, currently routed active turn for this agent."""

        selection = self._validated_selection(agent, require_route=True)
        if selection is None:
            return None
        context_id, browser_id, bridge_id = selection
        key = (context_id, id(agent))
        with self._lock:
            turn_id = self._agent_turns.get(key)
        if turn_id is None:
            return None
        try:
            binding = self.registry.active_turn_binding(
                context_id=context_id, turn_id=turn_id
            )
        except ExtensionSessionStateError:
            return None
        if (
            binding is None
            or binding.browser_id != browser_id
            or binding.bridge_id != bridge_id
        ):
            return None
        return binding

    def is_current_turn(
        self, agent: Any, binding: ActiveExtensionTurnBinding
    ) -> bool:
        """Revalidate exact real or synthetic ownership immediately before send."""

        if not isinstance(binding, ActiveExtensionTurnBinding):
            return False
        selection = self._validated_selection(agent, require_route=True)
        if selection is None:
            return False
        context_id, browser_id, bridge_id = selection
        if (
            binding.context_id != context_id
            or binding.browser_id != browser_id
            or binding.bridge_id != bridge_id
        ):
            return False
        key = (context_id, id(agent))
        with self._lock:
            owned = (
                self._agent_turns.get(key) == binding.turn_id
                or self._synthetic_turns.get(key) == binding
            )
        if not owned:
            return False
        try:
            current = self.registry.active_turn_binding(
                context_id=context_id, turn_id=binding.turn_id
            )
        except ExtensionSessionStateError:
            return False
        return current == binding

    def begin_synthetic_turn(self, agent: Any) -> ActiveExtensionTurnBinding | None:
        """Allocate one direct-call turn without changing monologue ownership."""

        selection = self._validated_selection(agent, require_route=True)
        if selection is None:
            return None
        context_id, browser_id, bridge_id = selection
        key = (context_id, id(agent))
        with self._lock:
            if (
                key in self._agent_turns
                or key in self._synthetic_turns
                or len(self._agent_turns) + len(self._synthetic_turns)
                >= self._max_agent_bindings
            ):
                return None
        try:
            session, turn = self.registry.begin_turn(
                context_id=context_id,
                browser_id=browser_id,
                bridge_id=bridge_id,
            )
        except ExtensionSessionStateError:
            return None
        binding = ActiveExtensionTurnBinding(
            context_id=context_id,
            browser_session_id=session.browser_session_id,
            browser_id=browser_id,
            bridge_id=bridge_id,
            turn_id=turn.turn_id,
        )
        conflicting_owner = False
        configuration_lost = False
        with self._lock:
            # A concurrent owner cannot be safely replaced. Finalize the turn we
            # just allocated and preserve the existing exact owner.
            if self._configuration_owner is None or self._configuration_retiring:
                configuration_lost = True
            elif (
                key in self._agent_turns
                or key in self._synthetic_turns
                or len(self._agent_turns) + len(self._synthetic_turns)
                >= self._max_agent_bindings
            ):
                conflicting_owner = True
            else:
                self._synthetic_turns[key] = binding
        if configuration_lost or conflicting_owner:
            self._stage_and_dispatch(
                context_id=context_id,
                turn_id=turn.turn_id,
                reason="restarted" if configuration_lost else "superseded",
            )
            return None
        return binding

    def finalize_synthetic_turn(
        self,
        agent: Any,
        binding: ActiveExtensionTurnBinding,
        *,
        reason: str = "direct",
    ) -> tuple[str, ...]:
        """Finalize only the exact synthetic binding returned to this caller."""

        if not isinstance(binding, ActiveExtensionTurnBinding):
            return ()
        context_id = str(getattr(getattr(agent, "context", None), "id", "") or "")
        key = (context_id, id(agent))
        with self._lock:
            current = self._synthetic_turns.get(key)
            if current != binding:
                return ()
            self._synthetic_turns.pop(key, None)
        return self._stage_and_dispatch(
            context_id=binding.context_id,
            turn_id=binding.turn_id,
            reason=reason,
        )

    def finalize_context(
        self,
        context: Any,
        *,
        reason: str,
        retire: bool = False,
        remove: bool = False,
    ) -> tuple[str, ...]:
        with self._lock:
            if self._configuration_owner is None or self._configuration_retiring:
                return ()
        context_id = str(getattr(context, "id", "") or "")
        try:
            context_id = _identifier(context_id, "context_id")
            if self.registry.session(context_id) is None:
                return ()
        except ExtensionSessionStateError:
            return ()
        with self._lock:
            for key in tuple(self._agent_turns):
                if key[0] == context_id:
                    self._agent_turns.pop(key, None)
            for key in tuple(self._synthetic_turns):
                if key[0] == context_id:
                    self._synthetic_turns.pop(key, None)
        return self._stage_and_dispatch(
            context_id=context_id,
            turn_id=None,
            reason=reason,
            retire=retire,
            remove=remove,
        )

    def replay_pending(self) -> tuple[str, ...]:
        with self._lock:
            dispatcher = self._dispatcher
        return () if dispatcher is None else dispatcher.replay_pending()

    def _attach_task_done_finalizer(
        self, agent: Any, context_id: str, turn_id: str
    ) -> None:
        task = getattr(getattr(agent, "context", None), "task", None)
        add_done_callback = getattr(task, "add_done_callback", None)
        if not callable(add_done_callback):
            return

        def finalize_after_task(_future: Any) -> None:
            self.finalize_tracked_agent_turn(
                agent, turn_id=turn_id, reason="task_done"
            )

        try:
            add_done_callback(finalize_after_task)
        except Exception:
            return

    def _validated_selection(
        self, agent: Any, *, require_route: bool
    ) -> tuple[str, str, str] | None:
        if agent is None:
            return None
        with self._lock:
            route_resolver = self._route_resolver
            dispatcher = self._dispatcher
            retiring = self._configuration_retiring
        if retiring or route_resolver is None or dispatcher is None:
            return None
        context_id = str(getattr(getattr(agent, "context", None), "id", "") or "")
        try:
            context_id = _identifier(context_id, "context_id")
            config = self._config_loader(agent)
            if (
                not isinstance(config, Mapping)
                or config.get(RUNTIME_BACKEND_KEY) != "host_required"
            ):
                return None
            selection = parse_extension_browser_selection(
                config.get(HOST_BROWSER_SELECTION_KEY)
            )
        except Exception:
            return None
        if selection is None:
            return None
        if require_route:
            try:
                route = route_resolver(context_id, selection.bridge_id)
            except Exception:
                return None
            if (
                not isinstance(route, ValidatedExtensionRoute)
                or route.bridge_id != selection.bridge_id
                or route.browser_id != selection.value
            ):
                return None
        return context_id, selection.value, selection.bridge_id

    def _stage_and_dispatch(
        self,
        *,
        context_id: str,
        turn_id: str | None,
        reason: str,
        retire: bool = False,
        remove: bool = False,
    ) -> tuple[str, ...]:
        with self._lock:
            dispatcher = self._dispatcher
        try:
            intents = self.registry.stage_finalize(
                context_id=context_id,
                turn_id=turn_id,
                reason=reason,
                retire=retire,
                remove=remove,
            )
        except ExtensionSessionStateError:
            return ()
        return () if dispatcher is None else dispatcher.schedule(intents)


_legacy_lifecycle_owner = object()
_lifecycle = ExtensionSessionLifecycle()


def get_extension_session_lifecycle() -> ExtensionSessionLifecycle:
    """Return the hook-owned singleton for explicit production composition."""

    return _lifecycle


def configure_extension_session_lifecycle(
    *,
    route_resolver: RouteResolver,
    sender: FinalizationSender,
    submitter: CoroutineSubmitter | None = None,
    max_inflight: int = 128,
) -> tuple[str, ...]:
    """Inject the future restricted broker seam and replay durable controls."""

    return _lifecycle.configure(
        route_resolver=route_resolver,
        sender=sender,
        submitter=submitter,
        max_inflight=max_inflight,
    )


def replay_extension_finalizations() -> tuple[str, ...]:
    """Retry durable pending controls after a trusted route becomes current."""

    return _lifecycle.replay_pending()


def begin_extension_monologue(agent: Any) -> ExtensionTurnIntent | None:
    return _lifecycle.begin_agent_turn(agent)


def finalize_extension_monologue(agent: Any, *, reason: str) -> tuple[str, ...]:
    return _lifecycle.finalize_agent_turn(agent, reason=reason)


def get_active_extension_turn(agent: Any) -> ActiveExtensionTurnBinding | None:
    """Resolve the current turn from the hook-owned production lifecycle."""

    return _lifecycle.active_agent_turn(agent)


def is_current_extension_turn(
    agent: Any, binding: ActiveExtensionTurnBinding
) -> bool:
    """Revalidate an exact turn for a broker dispatch preflight."""

    return _lifecycle.is_current_turn(agent, binding)


def begin_extension_synthetic_turn(agent: Any) -> ActiveExtensionTurnBinding | None:
    """Begin a direct Browser-call scope when no monologue turn owns the agent."""

    return _lifecycle.begin_synthetic_turn(agent)


def finalize_extension_synthetic_turn(
    agent: Any,
    binding: ActiveExtensionTurnBinding,
    *,
    reason: str = "direct",
) -> tuple[str, ...]:
    """Finalize a matching direct-call scope from the caller's ``finally`` block."""

    return _lifecycle.finalize_synthetic_turn(agent, binding, reason=reason)


def finalize_extension_context(
    context: Any,
    *,
    reason: str,
    retire: bool = False,
    remove: bool = False,
) -> tuple[str, ...]:
    return _lifecycle.finalize_context(
        context, reason=reason, retire=retire, remove=remove,
    )


def _background_submitter(coroutine: Awaitable[None]) -> Future[Any]:
    from helpers.defer import EventLoopThread

    return EventLoopThread("BrowserExtensionFinalization").run_coroutine(coroutine)


def _identifier(value: Any, field: str) -> str:
    if (
        not isinstance(value, str)
        or not value
        or value != value.strip()
        or len(value.encode("utf-8")) > MAX_IDENTIFIER_BYTES
        or any(ord(character) < 0x20 or ord(character) == 0x7F for character in value)
    ):
        raise ExtensionSessionStateError(
            "INVALID_IDENTIFIER", f"The {field} is invalid"
        )
    return value


def _browser_id(
    value: Any,
    bridge_id: str,
    transport_profile: BrowserBridgeTransportProfile = (
        PRODUCTION_BROWSER_BRIDGE_TRANSPORT
    ),
) -> str:
    browser_id = _identifier(value, "browser_id")
    require_browser_bridge_transport_profile(transport_profile)
    try:
        selection = parse_extension_browser_selection(browser_id)
    except ValueError:
        selection = None
    if selection is None or selection.bridge_id != bridge_id:
        raise ExtensionSessionStateError(
            "INVALID_BROWSER_ID", "The browser ID does not match the bridge"
        )
    return browser_id


def _reason(value: Any) -> str:
    reason = _identifier(value, "reason")
    if len(reason.encode("utf-8")) > MAX_REASON_BYTES:
        raise ExtensionSessionStateError(
            "INVALID_REASON", "The finalization reason is too long"
        )
    return reason


def _timestamp(value: Any, field: str) -> int:
    if type(value) is not int or value < 0:
        raise ExtensionSessionStateError("INVALID_STATE", f"The {field} is invalid")
    return value


def _nonnegative_int(value: Any, field: str) -> int:
    return _timestamp(value, field)


def _optional_timestamp(value: Any, field: str) -> int | None:
    return None if value is None else _timestamp(value, field)


def _turn_index(turns: list[ExtensionTurnIntent], turn_id: str) -> int:
    for index, turn in enumerate(turns):
        if turn.turn_id == turn_id:
            return index
    raise ExtensionSessionStateError("TURN_NOT_FOUND", "The extension turn was not found")


def _require_session(
    sessions: Mapping[str, ExtensionSessionIntent],
    context_id: str,
    browser_session_id: str,
) -> ExtensionSessionIntent:
    session = sessions.get(context_id)
    if session is None or session.browser_session_id != browser_session_id:
        raise ExtensionSessionStateError(
            "SESSION_NOT_FOUND", "The extension session was not found"
        )
    return session


def _finalization_intent(
    session: ExtensionSessionIntent, turn: ExtensionTurnIntent
) -> ExtensionFinalizationIntent:
    if (
        turn.control_id is None
        or turn.reason is None
        or turn.finalization_requested_at_ms is None
    ):
        raise ExtensionSessionStateError(
            "INVALID_STATE", "The pending finalization is incomplete"
        )
    return ExtensionFinalizationIntent(
        control_id=turn.control_id,
        context_id=session.context_id,
        browser_session_id=session.browser_session_id,
        browser_id=session.browser_id,
        bridge_id=session.bridge_id,
        turn_id=turn.turn_id,
        dispositions=turn.dispositions,
        reason=turn.reason,
        requested_at_ms=turn.finalization_requested_at_ms,
    )


def _can_delete(session: ExtensionSessionIntent) -> bool:
    if not (session.retire_requested or session.remove_requested):
        return False
    return all(turn.state == TURN_FINALIZED for turn in session.turns)


def _encode_store(
    sessions: Mapping[str, ExtensionSessionIntent],
) -> dict[str, Any]:
    return {
        "contract": SESSION_STORE_CONTRACT,
        "schema_version": SESSION_STORE_VERSION,
        "sessions": [_encode_session(sessions[key]) for key in sorted(sessions)],
    }


def _encode_session(session: ExtensionSessionIntent) -> dict[str, Any]:
    return {
        "context_id": session.context_id,
        "browser_session_id": session.browser_session_id,
        "browser_id": session.browser_id,
        "bridge_id": session.bridge_id,
        "turns": [_encode_turn(turn) for turn in session.turns],
        "last_acked_event_sequence": session.last_acked_event_sequence,
        "created_at_ms": session.created_at_ms,
        "updated_at_ms": session.updated_at_ms,
        "retire_requested": session.retire_requested,
        "remove_requested": session.remove_requested,
    }


def _encode_turn(turn: ExtensionTurnIntent) -> dict[str, Any]:
    return {
        "turn_id": turn.turn_id,
        "state": turn.state,
        "dispositions": dict(turn.dispositions),
        "control_id": turn.control_id,
        "reason": turn.reason,
        "started_at_ms": turn.started_at_ms,
        "finalization_requested_at_ms": turn.finalization_requested_at_ms,
        "settled_at_ms": turn.settled_at_ms,
    }


def _decode_store(
    value: Any,
    *,
    max_contexts: int,
    max_turns: int,
    max_dispositions: int,
    transport_profile: BrowserBridgeTransportProfile = (
        PRODUCTION_BROWSER_BRIDGE_TRANSPORT
    ),
) -> dict[str, ExtensionSessionIntent]:
    if not isinstance(value, Mapping) or set(value) != {
        "contract",
        "schema_version",
        "sessions",
    }:
        raise ExtensionSessionStateError("CORRUPT_STORE", "Invalid session store")
    if (
        value.get("contract") != SESSION_STORE_CONTRACT
        or value.get("schema_version") != SESSION_STORE_VERSION
    ):
        raise ExtensionSessionStateError("CORRUPT_STORE", "Unsupported session store")
    raw_sessions = value.get("sessions")
    if not isinstance(raw_sessions, list) or len(raw_sessions) > max_contexts:
        raise ExtensionSessionStateError("CORRUPT_STORE", "Invalid session records")
    sessions: dict[str, ExtensionSessionIntent] = {}
    browser_session_ids: set[str] = set()
    control_ids: set[str] = set()
    for raw in raw_sessions:
        session = _decode_session(
            raw,
            max_turns=max_turns,
            max_dispositions=max_dispositions,
            transport_profile=transport_profile,
        )
        if session.context_id in sessions:
            raise ExtensionSessionStateError("CORRUPT_STORE", "Duplicate context record")
        if session.browser_session_id in browser_session_ids:
            raise ExtensionSessionStateError("CORRUPT_STORE", "Duplicate browser session")
        browser_session_ids.add(session.browser_session_id)
        for turn in session.turns:
            if turn.control_id is not None:
                if turn.control_id in control_ids:
                    raise ExtensionSessionStateError(
                        "CORRUPT_STORE", "Duplicate finalization control"
                    )
                control_ids.add(turn.control_id)
        sessions[session.context_id] = session
    return sessions


def _decode_session(
    value: Any,
    *,
    max_turns: int,
    max_dispositions: int,
    transport_profile: BrowserBridgeTransportProfile = (
        PRODUCTION_BROWSER_BRIDGE_TRANSPORT
    ),
) -> ExtensionSessionIntent:
    expected = {
        "context_id",
        "browser_session_id",
        "browser_id",
        "bridge_id",
        "turns",
        "last_acked_event_sequence",
        "created_at_ms",
        "updated_at_ms",
        "retire_requested",
        "remove_requested",
    }
    if not isinstance(value, Mapping) or set(value) != expected:
        raise ExtensionSessionStateError("CORRUPT_STORE", "Invalid session record")
    context_id = _identifier(value.get("context_id"), "context_id")
    bridge_id = _identifier(value.get("bridge_id"), "bridge_id")
    browser_id = _browser_id(
        value.get("browser_id"), bridge_id, transport_profile
    )
    raw_turns = value.get("turns")
    if not isinstance(raw_turns, list) or len(raw_turns) > max_turns:
        raise ExtensionSessionStateError("CORRUPT_STORE", "Invalid turn records")
    turns = tuple(
        _decode_turn(raw, max_dispositions=max_dispositions) for raw in raw_turns
    )
    if len({turn.turn_id for turn in turns}) != len(turns):
        raise ExtensionSessionStateError("CORRUPT_STORE", "Duplicate turn record")
    created = _timestamp(value.get("created_at_ms"), "created_at_ms")
    updated = _timestamp(value.get("updated_at_ms"), "updated_at_ms")
    if updated < created:
        raise ExtensionSessionStateError("CORRUPT_STORE", "Invalid session timestamps")
    if type(value.get("retire_requested")) is not bool or type(
        value.get("remove_requested")
    ) is not bool:
        raise ExtensionSessionStateError("CORRUPT_STORE", "Invalid session flags")
    if value["remove_requested"] and not value["retire_requested"]:
        raise ExtensionSessionStateError("CORRUPT_STORE", "Invalid removal state")
    return ExtensionSessionIntent(
        context_id=context_id,
        browser_session_id=_identifier(
            value.get("browser_session_id"), "browser_session_id"
        ),
        browser_id=browser_id,
        bridge_id=bridge_id,
        turns=turns,
        last_acked_event_sequence=_nonnegative_int(
            value.get("last_acked_event_sequence"), "last_acked_event_sequence"
        ),
        created_at_ms=created,
        updated_at_ms=updated,
        retire_requested=value["retire_requested"],
        remove_requested=value["remove_requested"],
    )


def _decode_turn(value: Any, *, max_dispositions: int) -> ExtensionTurnIntent:
    expected = {
        "turn_id",
        "state",
        "dispositions",
        "control_id",
        "reason",
        "started_at_ms",
        "finalization_requested_at_ms",
        "settled_at_ms",
    }
    if not isinstance(value, Mapping) or set(value) != expected:
        raise ExtensionSessionStateError("CORRUPT_STORE", "Invalid turn record")
    state = value.get("state")
    if state not in TURN_STATES:
        raise ExtensionSessionStateError("CORRUPT_STORE", "Invalid turn state")
    raw_dispositions = value.get("dispositions")
    if not isinstance(raw_dispositions, Mapping) or len(
        raw_dispositions
    ) > max_dispositions:
        raise ExtensionSessionStateError("CORRUPT_STORE", "Invalid dispositions")
    dispositions: list[tuple[str, str]] = []
    for raw_lease_id, raw_disposition in raw_dispositions.items():
        lease_id = _identifier(raw_lease_id, "lease_id")
        if raw_disposition not in LEASE_DISPOSITIONS:
            raise ExtensionSessionStateError("CORRUPT_STORE", "Invalid disposition")
        dispositions.append((lease_id, raw_disposition))
    control_id = value.get("control_id")
    reason = value.get("reason")
    requested = _optional_timestamp(
        value.get("finalization_requested_at_ms"), "finalization_requested_at_ms"
    )
    settled = _optional_timestamp(value.get("settled_at_ms"), "settled_at_ms")
    if state == TURN_ACTIVE:
        if (
            control_id is not None
            or reason is not None
            or requested is not None
            or settled is not None
        ):
            raise ExtensionSessionStateError("CORRUPT_STORE", "Invalid active turn")
    else:
        control_id = _identifier(control_id, "control_id")
        if not _CORRELATION_ID_RE.fullmatch(control_id):
            raise ExtensionSessionStateError("CORRUPT_STORE", "Invalid control ID")
        reason = _reason(reason)
        if requested is None:
            raise ExtensionSessionStateError("CORRUPT_STORE", "Missing request timestamp")
        if state == TURN_FINALIZATION_PENDING and settled is not None:
            raise ExtensionSessionStateError("CORRUPT_STORE", "Pending turn is settled")
        if state in FINALIZATION_TERMINAL_STATES and settled is None:
            raise ExtensionSessionStateError("CORRUPT_STORE", "Terminal turn is unsettled")
    started = _timestamp(value.get("started_at_ms"), "started_at_ms")
    if requested is not None and requested < started:
        raise ExtensionSessionStateError("CORRUPT_STORE", "Invalid turn timestamps")
    if settled is not None and (requested is None or settled < requested):
        raise ExtensionSessionStateError("CORRUPT_STORE", "Invalid turn timestamps")
    return ExtensionTurnIntent(
        turn_id=_identifier(value.get("turn_id"), "turn_id"),
        state=state,
        dispositions=tuple(sorted(dispositions)),
        control_id=control_id,
        reason=reason,
        started_at_ms=started,
        finalization_requested_at_ms=requested,
        settled_at_ms=settled,
    )
