"""Bounded site-challenge decisions and exact operation/turn origin grants.

This process-owned repository derives authority only from a current broker
operation, its exact owned lease, and an explicit protected-user decision.  It
does not persist URLs or page text, infer decisions from natural language, or
advertise Browser runtime readiness.
"""

from __future__ import annotations

import asyncio
from collections import deque
from dataclasses import dataclass, field
import hashlib
import json
import re
import threading
import time
from typing import Any, Awaitable, Callable
import uuid

from helpers.ws_principal import WsPrincipal
from plugins._a0_connector.helpers.browser_bridge_context import (
    BrowserBridgeContextRoute,
)
from plugins._a0_connector.helpers.browser_bridge_events import (
    SiteChallengeNotice,
)
from plugins._a0_connector.helpers.browser_bridge_operations import (
    BrokerCompletion,
    ControlTicket,
    OperationBinding,
    OperationTicket,
)
from plugins._a0_connector.helpers.browser_bridge_policy import (
    BrowserBridgePolicyError,
    normalize_site_origin,
)
from plugins._a0_connector.helpers.browser_bridge_selection import (
    selection_current as server_selection_current,
)
from plugins._a0_connector.helpers.browser_bridge_transport import (
    PRODUCTION_BROWSER_BRIDGE_TRANSPORT,
    BrowserBridgeTransportProfile,
    require_browser_bridge_transport_profile,
    require_transport_principal_identity,
)


SITE_AUTHORITY_CONTRACT = "a0.browser-bridge.site-authority.v1"
SITE_AUTHORITY_VERSION = 1
MAX_SITE_AUTHORITY_REQUEST_BYTES = 8 * 1024
MAX_SITE_CHALLENGE_TTL_MS = 120_000
MAX_TURN_GRANT_TTL_MS = 2 * 60 * 60 * 1_000
MAX_SITE_CHALLENGES = 128
MAX_SITE_DECISIONS = 128
MAX_SITE_GRANTS = 256
MAX_SITE_TOMBSTONES = 2_048
MAX_SITE_SUMMARY_BYTES = 512
DEFAULT_RESOLUTION_TIMEOUT_MS = 10_000

SITE_DECISIONS = frozenset({"deny", "allow_once", "allow_turn"})
SITE_OPTIONS = ("deny", "allow_once", "allow_turn")

_NATIVE_ID = re.compile(r"[A-Za-z0-9][A-Za-z0-9._:-]{0,255}")
_CORE_ID = re.compile(r"[A-Za-z0-9_-]{1,128}")
_DIGEST = re.compile(r"[a-f0-9]{64}")


class BrowserBridgeSiteAuthorityError(ValueError):
    """A site challenge, decision, or dependency value is invalid."""


class BrowserBridgeSiteAuthorityUnavailable(RuntimeError):
    """Exact current site authority cannot be established."""


@dataclass(frozen=True, slots=True)
class SiteChallenge:
    challenge_id: str
    server_instance_id: str
    route: BrowserBridgeContextRoute = field(repr=False)
    operation: OperationTicket = field(repr=False)
    origin: str
    canonical_parameter_hash: str
    target_fingerprint: str
    lease_id_digest: str = field(repr=False)
    browser_id_digest: str = field(repr=False)
    document_id: str | None = field(repr=False)
    document_epoch: int = field(repr=False)
    summary: str
    created_at_ms: int
    expires_at_ms: int
    event_hash: str = field(repr=False)

    def as_public_dict(self) -> dict[str, Any]:
        return {
            "challenge_id": self.challenge_id,
            "origin": self.origin,
            "action_class": "navigate",
            "summary": self.summary,
            "options": list(SITE_OPTIONS),
            "expires_at_ms": self.expires_at_ms,
        }


@dataclass(frozen=True, slots=True)
class SiteOriginGrant:
    origin_grant_id: str
    server_instance_id: str = field(repr=False)
    scope: str
    origin: str
    expires_at_ms: int
    principal: WsPrincipal = field(repr=False)
    connector_sid: str = field(repr=False)
    load_generation_id: str = field(repr=False)
    context_id: str = field(repr=False)
    browser_session_id: str = field(repr=False)
    turn_id: str = field(repr=False)
    op_id: str | None = field(default=None, repr=False)


@dataclass(frozen=True, slots=True)
class SiteDecision:
    challenge: SiteChallenge = field(repr=False)
    decision: str
    control_id: str
    decided_at_ms: int
    control_expires_at_ms: int
    grant: SiteOriginGrant | None = field(default=None, repr=False)
    saved_grant_id: str | None = field(default=None, repr=False)

    @property
    def challenge_id(self) -> str:
        return self.challenge.challenge_id

    def as_public_dict(self) -> dict[str, Any]:
        return {
            "challenge_id": self.challenge_id,
            "decision": self.decision,
            "control_id": self.control_id,
            "status": "accepted",
            "expires_at_ms": self.control_expires_at_ms,
        }

    def resolution(self) -> dict[str, Any]:
        challenge = self.challenge
        operation = challenge.operation
        grant = None
        if self.grant is not None:
            grant = {
                "origin_grant_id": self.grant.origin_grant_id,
                "scope": self.grant.scope,
                "origin": self.grant.origin,
                # The resolve control is authority only for the currently
                # waiting operation. Its wire grant never outlives that wait.
                "expires_at_ms": min(
                    self.control_expires_at_ms,
                    self.grant.expires_at_ms,
                ),
            }
        return {
            "challenge_id": challenge.challenge_id,
            "tab_handle": operation.target_tab_handle,
            "document_id": challenge.document_id,
            "document_epoch": challenge.document_epoch,
            "canonical_parameter_hash": challenge.canonical_parameter_hash,
            "target_fingerprint": challenge.target_fingerprint,
            "origin": challenge.origin,
            "action_class": "navigate",
            "decision": self.decision,
            "grant": grant,
        }


@dataclass(frozen=True, slots=True)
class SiteAuthorityInvalidationSummary:
    challenges: int
    decisions: int
    grants: int


CurrentOperation = Callable[..., OperationTicket | None]
RemainingOperation = Callable[[OperationTicket], int]
LeaseResolver = Callable[[Any, str], Any | None]
RouteVerifier = Callable[[BrowserBridgeContextRoute], bool]
TurnCurrent = Callable[[OperationBinding], bool]
BeginResolution = Callable[..., Awaitable[ControlTicket]]
WaitControl = Callable[[ControlTicket], Awaitable[BrokerCompletion]]


class BrowserBridgeSiteAuthorityRepository:
    """Register exact site challenges and mint no broader than requested."""

    def __init__(
        self,
        *,
        current_operation: CurrentOperation | None = None,
        remaining_operation_ms: RemainingOperation | None = None,
        lease_for: LeaseResolver | None = None,
        route_verifier: RouteVerifier | None = None,
        turn_current: TurnCurrent | None = None,
        selection_current: Callable[[str, str], bool] | None = None,
        saved_origin_grant: Callable[[OperationBinding, str], str | None] | None = None,
        begin_resolution: BeginResolution | None = None,
        wait_control: WaitControl | None = None,
        server_instance_id: Callable[[], str] | None = None,
        clock_ms: Callable[[], int] | None = None,
        control_id_factory: Callable[[], str] | None = None,
        grant_id_factory: Callable[[], str] | None = None,
        max_challenges: int = MAX_SITE_CHALLENGES,
        max_decisions: int = MAX_SITE_DECISIONS,
        max_grants: int = MAX_SITE_GRANTS,
        max_tombstones: int = MAX_SITE_TOMBSTONES,
        transport_profile: BrowserBridgeTransportProfile = (
            PRODUCTION_BROWSER_BRIDGE_TRANSPORT
        ),
    ) -> None:
        for value, maximum, name in (
            (max_challenges, MAX_SITE_CHALLENGES, "challenge"),
            (max_decisions, MAX_SITE_DECISIONS, "decision"),
            (max_grants, MAX_SITE_GRANTS, "grant"),
            (max_tombstones, MAX_SITE_TOMBSTONES, "tombstone"),
        ):
            if type(value) is not int or not 1 <= value <= maximum:
                raise ValueError(f"invalid site {name} bound")
        self._current_operation = current_operation or _no_operation
        self._transport_profile = require_browser_bridge_transport_profile(
            transport_profile
        )
        self._remaining_operation_ms = remaining_operation_ms or (
            lambda _operation: 0
        )
        self._lease_for = lease_for or (lambda _binding, _handle: None)
        self._route_verifier = route_verifier or (lambda _route: False)
        self._turn_current = turn_current or (lambda _binding: False)
        self._selection_current = selection_current or server_selection_current
        self._saved_origin_grant = saved_origin_grant
        self._begin_resolution = begin_resolution or _resolution_unavailable
        self._wait_control = wait_control or _wait_unavailable
        self._server_instance_id = server_instance_id or _server_unavailable
        self._clock_ms = clock_ms or (lambda: time.time_ns() // 1_000_000)
        self._control_id_factory = control_id_factory or (
            lambda: uuid.uuid4().hex
        )
        self._grant_id_factory = grant_id_factory or (lambda: str(uuid.uuid4()))
        self._max_challenges = max_challenges
        self._max_decisions = max_decisions
        self._max_grants = max_grants
        self._max_tombstones = max_tombstones
        self._challenges: dict[str, SiteChallenge] = {}
        self._decisions: dict[str, SiteDecision] = {}
        self._decision_outcomes: dict[str, str] = {}
        self._operation_challenges: dict[tuple[Any, ...], str] = {}
        self._operation_grants: dict[str, SiteOriginGrant] = {}
        self._turn_grants: dict[tuple[Any, ...], SiteOriginGrant] = {}
        self._tombstones: dict[str, str] = {}
        self._tombstone_order: deque[str] = deque()
        self._tasks: dict[str, asyncio.Task[None]] = {}
        self._closed = False
        self._lock = threading.RLock()

    @property
    def pending_count(self) -> int:
        with self._lock:
            return len(self._challenges)

    @property
    def resolution_task_count(self) -> int:
        with self._lock:
            return len(self._tasks)

    def register_event(self, notice: SiteChallengeNotice) -> None:
        self.register_challenge(notice)

    def register_challenge(self, notice: SiteChallengeNotice) -> SiteChallenge:
        _validate_notice(notice, self._transport_profile)
        now = self._now()
        event_hash = _notice_hash(notice)
        with self._lock:
            self._ensure_open_locked()
            self._expire_locked(now)
            existing = self._challenges.get(notice.challenge_id)
            if existing is not None:
                if existing.event_hash == event_hash and self._challenge_current(
                    existing
                ):
                    return existing
                self._invalidate_challenge_locked(existing, "mismatch")
                raise BrowserBridgeSiteAuthorityUnavailable(
                    "site challenge mismatch"
                )
            decision = self._decisions.get(notice.challenge_id)
            if decision is not None:
                if (
                    decision.challenge.event_hash == event_hash
                    and self._challenge_current(decision.challenge)
                ):
                    return decision.challenge
                raise BrowserBridgeSiteAuthorityUnavailable(
                    "site challenge is terminal"
                )
            if notice.challenge_id in self._tombstones:
                raise BrowserBridgeSiteAuthorityUnavailable(
                    "site challenge is terminal"
                )
            if len(self._challenges) >= self._max_challenges:
                raise BrowserBridgeSiteAuthorityUnavailable(
                    "site challenge limit reached"
                )
            operation, remaining = self._resolve_notice(notice)
            if notice.expires_at_ms <= now or (
                notice.expires_at_ms - now > MAX_SITE_CHALLENGE_TTL_MS
            ):
                raise BrowserBridgeSiteAuthorityUnavailable(
                    "site challenge expired"
                )
            operation_key = _operation_key(operation)
            if operation_key in self._operation_challenges:
                raise BrowserBridgeSiteAuthorityUnavailable(
                    "operation already has a site challenge"
                )
            expires_at_ms = min(notice.expires_at_ms, now + remaining)
            if expires_at_ms <= now:
                raise BrowserBridgeSiteAuthorityUnavailable(
                    "site challenge expired"
                )
            challenge = SiteChallenge(
                challenge_id=notice.challenge_id,
                server_instance_id=self._server_id(),
                route=BrowserBridgeContextRoute(
                    notice.principal,
                    notice.connector_sid,
                    notice.load_generation_id,
                    self._transport_profile,
                ),
                operation=operation,
                origin=notice.origin,
                canonical_parameter_hash=notice.canonical_parameter_hash,
                target_fingerprint=notice.target_fingerprint,
                lease_id_digest=notice.lease_id_digest,
                browser_id_digest=notice.browser_id_digest,
                document_id=notice.document_id,
                document_epoch=notice.document_epoch,
                summary=_safe_summary(notice.origin),
                created_at_ms=now,
                expires_at_ms=expires_at_ms,
                event_hash=event_hash,
            )
            self._challenges[challenge.challenge_id] = challenge
            self._operation_challenges[operation_key] = challenge.challenge_id
            grant = self._turn_grant_locked(
                operation.binding, challenge.origin, now
            )
            saved_grant = self._saved_grant_for(challenge)
            if grant is not None:
                self._start_decision_locked(
                    challenge,
                    "allow_turn",
                    now=now,
                    grant=grant,
                )
            elif saved_grant is not None:
                self._start_decision_locked(challenge, "allow_once", now=now,
                    saved_grant_id=saved_grant)
            return challenge

    def list_pending(
        self,
        *,
        subject_id: Any,
        context_id: Any | None = None,
        bridge_id: Any | None = None,
    ) -> tuple[dict[str, Any], ...]:
        subject = _identifier(subject_id, "subject_id")
        context, bridge = _list_scope(context_id, bridge_id)
        now = self._now()
        with self._lock:
            self._ensure_open_locked()
            self._expire_locked(now)
            result: list[dict[str, Any]] = []
            for challenge in tuple(self._challenges.values()):
                if challenge.route.principal.subject_id != subject:
                    continue
                binding = challenge.operation.binding
                if context is not None and (
                    binding.context_id != context or binding.bridge_id != bridge
                ):
                    continue
                if not self._challenge_current(challenge):
                    self._invalidate_challenge_locked(challenge, "invalidated")
                    continue
                result.append(challenge.as_public_dict())
            result.sort(key=lambda item: (item["expires_at_ms"], item["challenge_id"]))
            return tuple(result)

    async def decide(
        self,
        *,
        subject_id: Any,
        challenge_id: Any,
        decision: Any,
        expected_route: BrowserBridgeContextRoute | None = None,
    ) -> SiteDecision:
        subject = _identifier(subject_id, "subject_id")
        challenge_key = _identifier(challenge_id, "challenge_id")
        if not isinstance(decision, str) or decision not in SITE_DECISIONS:
            raise BrowserBridgeSiteAuthorityError("invalid site decision")
        now = self._now()
        with self._lock:
            self._ensure_open_locked()
            self._expire_locked(now)
            existing = self._decisions.get(challenge_key)
            retained = existing.challenge if existing is not None else self._challenges.get(challenge_key)
            if expected_route is not None and (
                retained is None
                or retained.route.principal is not expected_route.principal
                or retained.route.connector_sid != expected_route.connector_sid
                or retained.route.load_generation_id != expected_route.load_generation_id
                or retained.route.transport_profile is not expected_route.transport_profile
                or not self._challenge_current(retained)
            ):
                raise BrowserBridgeSiteAuthorityUnavailable("site challenge unavailable")
            if existing is not None:
                if (
                    existing.challenge.route.principal.subject_id == subject
                    and existing.decision == decision
                    and self._selected(existing.challenge.operation.binding)
                ):
                    return existing
                raise BrowserBridgeSiteAuthorityUnavailable(
                    "site challenge already decided"
                )
            challenge = self._challenges.get(challenge_key)
            if (
                challenge is None
                or challenge.route.principal.subject_id != subject
                or not self._challenge_current(challenge)
            ):
                if challenge is not None:
                    self._invalidate_challenge_locked(challenge, "invalidated")
                raise BrowserBridgeSiteAuthorityUnavailable(
                    "site challenge unavailable"
                )
            return self._start_decision_locked(
                challenge,
                decision,
                now=now,
            )

    def turn_grant_for(
        self,
        binding: OperationBinding,
        *,
        origin: Any,
    ) -> SiteOriginGrant | None:
        """Return only a current exact-turn grant before dispatching a new op."""

        if not isinstance(binding, OperationBinding):
            raise BrowserBridgeSiteAuthorityError("invalid browser operation binding")
        try:
            canonical_origin = normalize_site_origin(origin)
        except BrowserBridgePolicyError as error:
            raise BrowserBridgeSiteAuthorityError("invalid site origin") from error
        now = self._now()
        with self._lock:
            self._ensure_open_locked()
            self._expire_locked(now)
            return self._turn_grant_locked(binding, canonical_origin, now)

    def grant_for_operation(
        self,
        operation: OperationTicket,
        *,
        origin: Any,
    ) -> SiteOriginGrant | None:
        if not isinstance(operation, OperationTicket):
            raise BrowserBridgeSiteAuthorityError("invalid browser operation")
        try:
            canonical_origin = normalize_site_origin(origin)
        except BrowserBridgePolicyError as error:
            raise BrowserBridgeSiteAuthorityError("invalid site origin") from error
        try:
            server_id = self._server_id()
        except BrowserBridgeSiteAuthorityUnavailable:
            return None
        now = self._now()
        with self._lock:
            self._ensure_open_locked()
            self._expire_locked(now)
            selected = self._selected(operation.binding)
            if (
                not selected
                or self._current_ticket(operation) is not operation
                or operation.action != "navigate"
                or operation.destination_origin != canonical_origin
            ):
                if not selected:
                    self._operation_grants = {
                        challenge_id: grant
                        for challenge_id, grant in self._operation_grants.items()
                        if grant.op_id != operation.binding.op_id
                    }
                    self._turn_grants.pop(
                        _turn_binding_key(operation.binding, canonical_origin),
                        None,
                    )
                return None
            for challenge_id, grant in tuple(self._operation_grants.items()):
                decision = self._decisions.get(challenge_id)
                if decision is None:
                    self._operation_grants.pop(challenge_id, None)
                    continue
                if (
                    decision.challenge.operation is operation
                    and grant.server_instance_id == server_id
                    and grant.origin == canonical_origin
                    and grant.expires_at_ms > now
                    and self._decision_outcomes.get(challenge_id) == "resolved"
                ):
                    return grant
            return self._turn_grant_locked(
                operation.binding,
                canonical_origin,
                now,
                server_id=server_id,
            )

    def cancel_operation(
        self, operation: OperationTicket
    ) -> SiteAuthorityInvalidationSummary:
        if not isinstance(operation, OperationTicket):
            raise BrowserBridgeSiteAuthorityError("invalid browser operation")
        return self._invalidate_matching(
            lambda challenge: challenge.operation is operation,
            lambda grant: grant.op_id == operation.binding.op_id,
        )

    def finalize_turn(
        self,
        *,
        principal: WsPrincipal,
        connector_sid: Any,
        load_generation_id: Any,
        context_id: Any,
        browser_session_id: Any,
        turn_id: Any,
    ) -> SiteAuthorityInvalidationSummary:
        values = _lifecycle_values(
            principal,
            connector_sid,
            load_generation_id,
            context_id,
            browser_session_id,
            turn_id,
        )
        return self._invalidate_matching(
            lambda challenge: _challenge_turn(challenge) == values,
            lambda grant: _grant_turn(grant) == values,
        )

    def disconnect(
        self,
        *,
        principal: WsPrincipal,
        connector_sid: Any,
        load_generation_id: Any,
    ) -> SiteAuthorityInvalidationSummary:
        if not isinstance(principal, WsPrincipal):
            raise BrowserBridgeSiteAuthorityError("invalid bridge principal")
        sid = _identifier(connector_sid, "connector_sid")
        generation = _identifier(load_generation_id, "load_generation_id")
        return self._invalidate_matching(
            lambda challenge: (
                challenge.route.principal is principal
                and challenge.route.connector_sid == sid
                and challenge.route.load_generation_id == generation
            ),
            lambda grant: (
                grant.principal is principal
                and grant.connector_sid == sid
                and grant.load_generation_id == generation
            ),
        )

    def finalize_context(
        self, *, context_id: Any
    ) -> SiteAuthorityInvalidationSummary:
        """Withdraw only pending/turn authority owned by one context."""

        context = _identifier(context_id, "context_id")
        return self._invalidate_matching(
            lambda challenge: challenge.operation.binding.context_id == context,
            lambda grant: grant.context_id == context,
        )

    def revoke_bridge(
        self,
        *,
        server_instance_id: Any,
        bridge_id: Any,
        subject_id: Any,
    ) -> SiteAuthorityInvalidationSummary:
        server = _identifier(server_instance_id, "server_instance_id")
        bridge = _identifier(bridge_id, "bridge_id")
        subject = _identifier(subject_id, "subject_id")
        return self._invalidate_matching(
            lambda challenge: (
                challenge.server_instance_id == server
                and challenge.route.principal.principal_id == bridge
                and challenge.route.principal.subject_id == subject
            ),
            lambda grant: (
                grant.server_instance_id == server
                and grant.principal.principal_id == bridge
                and grant.principal.subject_id == subject
            ),
        )

    def expire(
        self, now_ms: int | None = None
    ) -> SiteAuthorityInvalidationSummary:
        now = self._now() if now_ms is None else _timestamp(now_ms)
        with self._lock:
            return self._expire_locked(now)

    async def close(self) -> SiteAuthorityInvalidationSummary:
        with self._lock:
            if self._closed:
                return SiteAuthorityInvalidationSummary(0, 0, 0)
            self._closed = True
            summary = self._invalidate_all_locked("closed")
            tasks = tuple(self._tasks.values())
            self._tasks.clear()
            for task in tasks:
                task.cancel()
        if tasks:
            await asyncio.gather(*tasks, return_exceptions=True)
        return summary

    async def _resolve_decision(self, decision: SiteDecision) -> None:
        try:
            timeout_ms = min(
                DEFAULT_RESOLUTION_TIMEOUT_MS,
                self._remaining(decision.challenge.operation),
                max(0, decision.control_expires_at_ms - self._now()),
            )
            if timeout_ms <= 0:
                raise BrowserBridgeSiteAuthorityUnavailable(
                    "site resolution expired"
                )
            ticket = await self._begin_resolution(
                decision.challenge.operation,
                control_id=decision.control_id,
                resolution=decision.resolution(),
                authorization_current=lambda: self._decision_current(decision),
                timeout_ms=timeout_ms,
            )
            if not isinstance(ticket, ControlTicket):
                raise BrowserBridgeSiteAuthorityUnavailable(
                    "site resolution unavailable"
                )
            completion = await self._wait_control(ticket)
            if not _matching_completion(decision, completion):
                raise BrowserBridgeSiteAuthorityUnavailable(
                    "site resolution failed"
                )
            with self._lock:
                if not self._decision_current_locked(decision):
                    return
                self._decision_outcomes[decision.challenge_id] = "resolved"
                if decision.grant is not None:
                    if self._grant_count_locked() >= self._max_grants:
                        self._decision_outcomes[decision.challenge_id] = "failed"
                        return
                    if decision.grant.scope == "operation":
                        self._operation_grants[
                            decision.challenge_id
                        ] = decision.grant
                    else:
                        self._turn_grants[
                            _grant_key(decision.grant)
                        ] = decision.grant
        except asyncio.CancelledError:
            raise
        except Exception:
            with self._lock:
                if self._decisions.get(decision.challenge_id) is decision:
                    self._decision_outcomes[decision.challenge_id] = "failed"

    def _start_decision_locked(
        self,
        challenge: SiteChallenge,
        decision: str,
        *,
        now: int,
        grant: SiteOriginGrant | None = None,
        saved_grant_id: str | None = None,
    ) -> SiteDecision:
        if len(self._decisions) >= self._max_decisions:
            raise BrowserBridgeSiteAuthorityUnavailable(
                "site decision limit reached"
            )
        remaining = self._remaining(challenge.operation)
        control_expires_at_ms = min(
            challenge.expires_at_ms,
            now + remaining,
        )
        if control_expires_at_ms <= now:
            self._invalidate_challenge_locked(challenge, "expired")
            raise BrowserBridgeSiteAuthorityUnavailable(
                "site challenge expired"
            )
        control_id = self._fresh_id(
            self._control_id_factory, "control_id", core=True
        )
        if grant is None:
            grant = self._grant_for_decision(
                challenge,
                decision,
                now=now,
                control_expires_at_ms=control_expires_at_ms,
            )
        result = SiteDecision(
            challenge=challenge,
            decision=decision,
            control_id=control_id,
            decided_at_ms=now,
            control_expires_at_ms=control_expires_at_ms,
            grant=grant,
            saved_grant_id=saved_grant_id,
        )
        self._challenges.pop(challenge.challenge_id, None)
        self._decisions[challenge.challenge_id] = result
        self._decision_outcomes[challenge.challenge_id] = "resolving"
        task = asyncio.create_task(
            self._resolve_decision(result),
            name=f"browser-bridge-site:{challenge.challenge_id}",
        )
        self._tasks[challenge.challenge_id] = task
        task.add_done_callback(self._resolution_finished)
        return result

    def _turn_grant_locked(
        self,
        binding: OperationBinding,
        origin: str,
        now: int,
        *,
        server_id: str | None = None,
    ) -> SiteOriginGrant | None:
        if not _operation_binding_valid(binding, self._transport_profile):
            return None
        try:
            current_server = server_id or self._server_id()
            route = BrowserBridgeContextRoute(
                binding.principal,
                binding.connector_sid,
                binding.load_generation_id,
                self._transport_profile,
            )
            current_turn = self._turn_current(binding) is True
            selected = self._selected(binding)
        except Exception:
            return None
        grant_key = _turn_binding_key(binding, origin)
        if not selected:
            self._turn_grants.pop(grant_key, None)
            return None
        if (
            not current_turn
            or not self._route_current(route)
        ):
            return None
        grant = self._turn_grants.get(grant_key)
        if (
            grant is None
            or grant.server_instance_id != current_server
            or grant.principal is not binding.principal
            or grant.connector_sid != binding.connector_sid
            or grant.load_generation_id != binding.load_generation_id
            or grant.context_id != binding.context_id
            or grant.browser_session_id != binding.browser_session_id
            or grant.turn_id != binding.turn_id
            or grant.origin != origin
            or grant.expires_at_ms <= now
        ):
            return None
        return grant

    def _resolution_finished(self, task: asyncio.Task[None]) -> None:
        with self._lock:
            for challenge_id, current in tuple(self._tasks.items()):
                if current is task:
                    self._tasks.pop(challenge_id, None)
                    break
        try:
            task.exception()
        except asyncio.CancelledError:
            pass

    def _resolve_notice(
        self, notice: SiteChallengeNotice
    ) -> tuple[OperationTicket, int]:
        route = BrowserBridgeContextRoute(
            notice.principal,
            notice.connector_sid,
            notice.load_generation_id,
            self._transport_profile,
        )
        if not self._route_current(route):
            raise BrowserBridgeSiteAuthorityUnavailable("site route unavailable")
        operation = self._lookup_operation(notice)
        if not isinstance(operation, OperationTicket):
            raise BrowserBridgeSiteAuthorityUnavailable(
                "site operation unavailable"
            )
        binding = operation.binding
        if (
            binding.principal is not notice.principal
            or binding.connector_sid != notice.connector_sid
            or binding.load_generation_id != notice.load_generation_id
            or binding.context_id != notice.context_id
            or binding.browser_session_id != notice.browser_session_id
            or binding.turn_id != notice.turn_id
            or binding.action_id != notice.action_id
            or binding.op_id != notice.op_id
            or operation.action != "navigate"
            or not operation.target_tab_handle
            or operation.canonical_parameter_hash
            != notice.canonical_parameter_hash
            or operation.destination_origin != notice.origin
            or _target_fingerprint(notice) != notice.target_fingerprint
            or not self._selected(binding)
        ):
            raise BrowserBridgeSiteAuthorityUnavailable(
                "site operation mismatch"
            )
        remaining = self._remaining(operation)
        if remaining <= 0:
            raise BrowserBridgeSiteAuthorityUnavailable(
                "site operation expired"
            )
        lease = self._lease_for(binding, operation.target_tab_handle)
        if (
            lease is None
            or getattr(lease, "tab_handle", None) != operation.target_tab_handle
            or _hash_identifier(getattr(lease, "lease_id", None))
            != notice.lease_id_digest
            or _hash_identifier(getattr(lease, "tab_handle", None))
            != notice.browser_id_digest
        ):
            raise BrowserBridgeSiteAuthorityUnavailable("site lease mismatch")
        return operation, remaining

    def _challenge_current(self, challenge: SiteChallenge) -> bool:
        try:
            if self._server_id() != challenge.server_instance_id:
                return False
            route = challenge.route
            if (
                not self._route_current(route)
                or not self._selected(challenge.operation.binding)
            ):
                return False
            operation = self._current_ticket(challenge.operation)
            if operation is not challenge.operation or self._remaining(operation) <= 0:
                return False
            lease = self._lease_for(
                operation.binding, operation.target_tab_handle
            )
            return bool(
                lease is not None
                and getattr(lease, "tab_handle", None)
                == operation.target_tab_handle
                and _hash_identifier(getattr(lease, "lease_id", None))
                == challenge.lease_id_digest
                and _hash_identifier(getattr(lease, "tab_handle", None))
                == challenge.browser_id_digest
            )
        except Exception:
            return False

    def _selected(self, binding: OperationBinding) -> bool:
        try:
            return self._selection_current(
                binding.context_id, binding.bridge_id
            ) is True
        except Exception:
            return False

    def _decision_current(self, decision: SiteDecision) -> bool:
        with self._lock:
            return self._decision_current_locked(decision)

    def _decision_current_locked(self, decision: SiteDecision) -> bool:
        now = self._now()
        return bool(
            not self._closed
            and self._decisions.get(decision.challenge_id) is decision
            and self._decision_outcomes.get(decision.challenge_id)
            == "resolving"
            and now < decision.control_expires_at_ms
            and (
                decision.grant is None
                or now < decision.grant.expires_at_ms
            )
            and self._challenge_current(decision.challenge)
            and (decision.saved_grant_id is None or self._saved_grant_for(decision.challenge) == decision.saved_grant_id)
        )

    def _saved_grant_for(self, challenge: SiteChallenge) -> str | None:
        if self._transport_profile is not PRODUCTION_BROWSER_BRIDGE_TRANSPORT or self._saved_origin_grant is None:
            return None
        try:
            value = self._saved_origin_grant(challenge.operation.binding, challenge.origin)
            return _identifier(value, "grant_id") if value is not None else None
        except Exception:
            return None

    def _lookup_operation(
        self, notice: SiteChallengeNotice
    ) -> OperationTicket | None:
        try:
            return self._current_operation(
                principal=notice.principal,
                connector_sid=notice.connector_sid,
                load_generation_id=notice.load_generation_id,
                op_id=notice.op_id,
            )
        except Exception:
            return None

    def _current_ticket(
        self, operation: OperationTicket
    ) -> OperationTicket | None:
        binding = operation.binding
        try:
            return self._current_operation(
                principal=binding.principal,
                connector_sid=binding.connector_sid,
                load_generation_id=binding.load_generation_id,
                op_id=binding.op_id,
            )
        except Exception:
            return None

    def _remaining(self, operation: OperationTicket) -> int:
        try:
            value = self._remaining_operation_ms(operation)
        except Exception:
            return 0
        if type(value) is not int or not 0 <= value <= MAX_SITE_CHALLENGE_TTL_MS:
            return 0
        return value

    def _route_current(self, route: BrowserBridgeContextRoute) -> bool:
        try:
            return self._route_verifier(route) is True
        except Exception:
            return False

    def _server_id(self) -> str:
        try:
            return _identifier(self._server_instance_id(), "server_instance_id")
        except Exception:
            raise BrowserBridgeSiteAuthorityUnavailable(
                "site server unavailable"
            ) from None

    def _grant_for_decision(
        self,
        challenge: SiteChallenge,
        decision: str,
        *,
        now: int,
        control_expires_at_ms: int,
    ) -> SiteOriginGrant | None:
        if decision == "deny":
            return None
        grant_id = self._fresh_id(
            self._grant_id_factory, "origin_grant_id", core=False
        )
        binding = challenge.operation.binding
        scope = "operation" if decision == "allow_once" else "turn"
        expires_at_ms = (
            control_expires_at_ms
            if scope == "operation"
            else now + MAX_TURN_GRANT_TTL_MS
        )
        return SiteOriginGrant(
            origin_grant_id=grant_id,
            server_instance_id=challenge.server_instance_id,
            scope=scope,
            origin=challenge.origin,
            expires_at_ms=expires_at_ms,
            principal=binding.principal,
            connector_sid=binding.connector_sid,
            load_generation_id=binding.load_generation_id,
            context_id=binding.context_id,
            browser_session_id=binding.browser_session_id,
            turn_id=binding.turn_id,
            op_id=binding.op_id if scope == "operation" else None,
        )

    def _fresh_id(
        self,
        factory: Callable[[], str],
        field: str,
        *,
        core: bool,
    ) -> str:
        try:
            value = _core_identifier(factory(), field) if core else _identifier(
                factory(), field
            )
        except Exception:
            raise BrowserBridgeSiteAuthorityUnavailable(
                "site identity unavailable"
            ) from None
        used = {
            decision.control_id for decision in self._decisions.values()
        } | {
            decision.grant.origin_grant_id
            for decision in self._decisions.values()
            if decision.grant is not None
        } | {
            grant.origin_grant_id
            for grant in self._operation_grants.values()
        } | {
            grant.origin_grant_id for grant in self._turn_grants.values()
        }
        if value in used:
            raise BrowserBridgeSiteAuthorityUnavailable(
                "site identity collision"
            )
        return value

    def _invalidate_matching(
        self,
        challenge_match: Callable[[SiteChallenge], bool],
        grant_match: Callable[[SiteOriginGrant], bool],
    ) -> SiteAuthorityInvalidationSummary:
        with self._lock:
            challenges = [
                challenge
                for challenge in self._challenges.values()
                if challenge_match(challenge)
            ]
            decisions = [
                decision
                for decision in self._decisions.values()
                if challenge_match(decision.challenge)
            ]
            for challenge in challenges:
                self._invalidate_challenge_locked(challenge, "invalidated")
            for decision in decisions:
                self._invalidate_decision_locked(decision, "invalidated")
            before = self._grant_count_locked()
            self._operation_grants = {
                key: grant
                for key, grant in self._operation_grants.items()
                if not grant_match(grant)
            }
            self._turn_grants = {
                key: grant
                for key, grant in self._turn_grants.items()
                if not grant_match(grant)
            }
            return SiteAuthorityInvalidationSummary(
                len(challenges), len(decisions), before - self._grant_count_locked()
            )

    def _expire_locked(self, now: int) -> SiteAuthorityInvalidationSummary:
        challenges = [
            challenge
            for challenge in self._challenges.values()
            if challenge.expires_at_ms <= now
        ]
        decisions = [
            decision
            for decision in self._decisions.values()
            if decision.control_expires_at_ms <= now
        ]
        for challenge in challenges:
            self._invalidate_challenge_locked(challenge, "expired")
        for decision in decisions:
            self._invalidate_decision_locked(decision, "expired")
        before = self._grant_count_locked()
        self._operation_grants = {
            key: grant
            for key, grant in self._operation_grants.items()
            if grant.expires_at_ms > now
        }
        self._turn_grants = {
            key: grant
            for key, grant in self._turn_grants.items()
            if grant.expires_at_ms > now
        }
        return SiteAuthorityInvalidationSummary(
            len(challenges), len(decisions), before - self._grant_count_locked()
        )

    def _invalidate_challenge_locked(
        self, challenge: SiteChallenge, reason: str
    ) -> None:
        if self._challenges.get(challenge.challenge_id) is not challenge:
            return
        self._challenges.pop(challenge.challenge_id, None)
        self._operation_challenges.pop(_operation_key(challenge.operation), None)
        self._remember_locked(challenge.challenge_id, reason)

    def _invalidate_decision_locked(
        self, decision: SiteDecision, reason: str
    ) -> None:
        if self._decisions.get(decision.challenge_id) is not decision:
            return
        self._decisions.pop(decision.challenge_id, None)
        self._decision_outcomes.pop(decision.challenge_id, None)
        self._operation_grants.pop(decision.challenge_id, None)
        self._operation_challenges.pop(
            _operation_key(decision.challenge.operation), None
        )
        self._remember_locked(decision.challenge_id, reason)

    def _invalidate_all_locked(
        self, reason: str
    ) -> SiteAuthorityInvalidationSummary:
        challenges = tuple(self._challenges.values())
        decisions = tuple(self._decisions.values())
        grants = self._grant_count_locked()
        for challenge in challenges:
            self._invalidate_challenge_locked(challenge, reason)
        for decision in decisions:
            self._invalidate_decision_locked(decision, reason)
        self._operation_grants.clear()
        self._turn_grants.clear()
        return SiteAuthorityInvalidationSummary(
            len(challenges), len(decisions), grants
        )

    def _remember_locked(self, challenge_id: str, reason: str) -> None:
        if challenge_id in self._tombstones:
            return
        self._tombstones[challenge_id] = reason
        self._tombstone_order.append(challenge_id)
        while len(self._tombstone_order) > self._max_tombstones:
            self._tombstones.pop(self._tombstone_order.popleft(), None)

    def _grant_count_locked(self) -> int:
        return len(self._operation_grants) + len(self._turn_grants)

    def _ensure_open_locked(self) -> None:
        if self._closed:
            raise BrowserBridgeSiteAuthorityUnavailable(
                "site authority closed"
            )

    def _now(self) -> int:
        return _timestamp(self._clock_ms())


def _matching_completion(
    decision: SiteDecision, completion: BrokerCompletion
) -> bool:
    return bool(
        isinstance(completion, BrokerCompletion)
        and completion.ok is True
        and completion.result
        == {
            "contract_version": SITE_AUTHORITY_VERSION,
            "control_id": decision.control_id,
            "challenge_id": decision.challenge_id,
            "status": "resolved",
            "decision": decision.decision,
        }
    )


def _operation_key(operation: OperationTicket) -> tuple[Any, ...]:
    binding = operation.binding
    return (
        id(binding.principal),
        binding.connector_sid,
        binding.load_generation_id,
        binding.context_id,
        binding.browser_session_id,
        binding.turn_id,
        binding.action_id,
        binding.op_id,
    )


def _turn_key(operation: OperationTicket, origin: str) -> tuple[Any, ...]:
    return _turn_binding_key(operation.binding, origin)


def _turn_binding_key(
    binding: OperationBinding, origin: str
) -> tuple[Any, ...]:
    return (
        id(binding.principal),
        binding.connector_sid,
        binding.load_generation_id,
        binding.context_id,
        binding.browser_session_id,
        binding.turn_id,
        origin,
    )


def _operation_binding_valid(
    binding: OperationBinding,
    transport_profile: BrowserBridgeTransportProfile,
) -> bool:
    principal = binding.principal
    try:
        require_transport_principal_identity(principal, transport_profile)
    except ValueError:
        return False
    if (
        not {"browser.operate", "browser.control", "browser.approval"}
        <= principal.scopes
    ):
        return False
    try:
        for field in (
            "connector_sid",
            "load_generation_id",
            "context_id",
            "browser_session_id",
            "turn_id",
            "action_id",
            "op_id",
        ):
            _identifier(getattr(binding, field), field)
    except BrowserBridgeSiteAuthorityError:
        return False
    return True


def _grant_key(grant: SiteOriginGrant) -> tuple[Any, ...]:
    return (
        id(grant.principal),
        grant.connector_sid,
        grant.load_generation_id,
        grant.context_id,
        grant.browser_session_id,
        grant.turn_id,
        grant.origin,
    )


def _challenge_turn(challenge: SiteChallenge) -> tuple[Any, ...]:
    binding = challenge.operation.binding
    return (
        id(binding.principal),
        binding.connector_sid,
        binding.load_generation_id,
        binding.context_id,
        binding.browser_session_id,
        binding.turn_id,
    )


def _grant_turn(grant: SiteOriginGrant) -> tuple[Any, ...]:
    return (
        id(grant.principal),
        grant.connector_sid,
        grant.load_generation_id,
        grant.context_id,
        grant.browser_session_id,
        grant.turn_id,
    )


def _lifecycle_values(
    principal: WsPrincipal,
    connector_sid: Any,
    load_generation_id: Any,
    context_id: Any,
    browser_session_id: Any,
    turn_id: Any,
) -> tuple[Any, ...]:
    if not isinstance(principal, WsPrincipal):
        raise BrowserBridgeSiteAuthorityError("invalid bridge principal")
    return (
        id(principal),
        _identifier(connector_sid, "connector_sid"),
        _identifier(load_generation_id, "load_generation_id"),
        _identifier(context_id, "context_id"),
        _identifier(browser_session_id, "browser_session_id"),
        _identifier(turn_id, "turn_id"),
    )


def _notice_hash(notice: SiteChallengeNotice) -> str:
    values = (
        id(notice.principal),
        notice.connector_sid,
        notice.load_generation_id,
        notice.context_id,
        notice.browser_session_id,
        notice.turn_id,
        notice.action_id,
        notice.op_id,
        notice.challenge_id,
        notice.origin,
        notice.canonical_parameter_hash,
        notice.target_fingerprint,
        notice.lease_id_digest,
        notice.browser_id_digest,
        notice.document_id,
        notice.document_epoch,
        hashlib.sha256(_utf8(notice.summary)).hexdigest(),
        notice.expires_at_ms,
    )
    return hashlib.sha256(repr(values).encode("utf-8")).hexdigest()


def _validate_notice(
    notice: Any,
    transport_profile: BrowserBridgeTransportProfile,
) -> SiteChallengeNotice:
    if not isinstance(notice, SiteChallengeNotice):
        raise BrowserBridgeSiteAuthorityError("invalid site challenge")
    principal = notice.principal
    try:
        require_transport_principal_identity(principal, transport_profile)
    except ValueError:
        raise BrowserBridgeSiteAuthorityError("invalid bridge principal") from None
    if (
        not {"browser.operate", "browser.control", "browser.approval"}
        <= principal.scopes
    ):
        raise BrowserBridgeSiteAuthorityError("invalid bridge principal")
    for field in (
        "connector_sid",
        "load_generation_id",
        "context_id",
        "browser_session_id",
        "turn_id",
        "action_id",
        "op_id",
        "challenge_id",
    ):
        _identifier(getattr(notice, field), field)
    if notice.document_id is not None:
        _identifier(notice.document_id, "document_id")
    for field in (
        "canonical_parameter_hash",
        "target_fingerprint",
        "lease_id_digest",
        "browser_id_digest",
    ):
        value = getattr(notice, field)
        if not isinstance(value, str) or _DIGEST.fullmatch(value) is None:
            raise BrowserBridgeSiteAuthorityError(f"invalid {field}")
    try:
        origin = normalize_site_origin(notice.origin)
    except BrowserBridgePolicyError as error:
        raise BrowserBridgeSiteAuthorityError("invalid site origin") from error
    if origin != notice.origin:
        raise BrowserBridgeSiteAuthorityError("invalid site origin")
    if (
        not isinstance(notice.summary, str)
        or not notice.summary
        or not notice.summary.isprintable()
        or len(_utf8(notice.summary)) > MAX_SITE_SUMMARY_BYTES
        or isinstance(notice.document_epoch, bool)
        or not isinstance(notice.document_epoch, int)
        or not 0 <= notice.document_epoch <= 2**53 - 1
    ):
        raise BrowserBridgeSiteAuthorityError("invalid site challenge")
    _timestamp(notice.expires_at_ms)
    return notice


def _hash_identifier(value: Any) -> str | None:
    if not isinstance(value, str) or _NATIVE_ID.fullmatch(value) is None:
        return None
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def _target_fingerprint(notice: SiteChallengeNotice) -> str:
    value = {
        "action_class": "navigate",
        "browser_id_digest": notice.browser_id_digest,
        "document_epoch": notice.document_epoch,
        "document_id": notice.document_id,
        "lease_id_digest": notice.lease_id_digest,
        "load_generation_id": notice.load_generation_id,
        "origin": notice.origin,
    }
    encoded = json.dumps(
        value, ensure_ascii=False, sort_keys=True, separators=(",", ":")
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def _safe_summary(origin: str) -> str:
    value = f"Allow navigation to {origin}?"
    if len(_utf8(value)) > MAX_SITE_SUMMARY_BYTES:
        raise BrowserBridgeSiteAuthorityUnavailable("site summary unavailable")
    return value


def _utf8(value: str) -> bytes:
    try:
        return value.encode("utf-8")
    except UnicodeError:
        raise BrowserBridgeSiteAuthorityError("invalid site text") from None


def _identifier(value: Any, field: str) -> str:
    if not isinstance(value, str) or _NATIVE_ID.fullmatch(value) is None:
        raise BrowserBridgeSiteAuthorityError(f"invalid {field}")
    return value


def _list_scope(
    context_id: Any | None, bridge_id: Any | None
) -> tuple[str | None, str | None]:
    if context_id is None and bridge_id is None:
        return None, None
    if context_id is None or bridge_id is None:
        raise BrowserBridgeSiteAuthorityError("incomplete site list scope")
    return (
        _identifier(context_id, "context_id"),
        _identifier(bridge_id, "bridge_id"),
    )


def _core_identifier(value: Any, field: str) -> str:
    if not isinstance(value, str) or _CORE_ID.fullmatch(value) is None:
        raise BrowserBridgeSiteAuthorityError(f"invalid {field}")
    return value


def _timestamp(value: Any) -> int:
    if (
        isinstance(value, bool)
        or not isinstance(value, int)
        or not 0 <= value <= 2**53 - 1
    ):
        raise BrowserBridgeSiteAuthorityUnavailable(
            "site authority clock unavailable"
        )
    return value


def _no_operation(**_kwargs: Any) -> None:
    return None


async def _resolution_unavailable(*_args: Any, **_kwargs: Any) -> ControlTicket:
    raise BrowserBridgeSiteAuthorityUnavailable("site resolution unavailable")


async def _wait_unavailable(_ticket: ControlTicket) -> BrokerCompletion:
    raise BrowserBridgeSiteAuthorityUnavailable("site resolution unavailable")


def _server_unavailable() -> str:
    raise BrowserBridgeSiteAuthorityUnavailable("site server unavailable")


_repository: BrowserBridgeSiteAuthorityRepository | None = None
_repository_lock = threading.Lock()


def bind_browser_bridge_site_authority_repository(
    repository: BrowserBridgeSiteAuthorityRepository | None,
) -> None:
    """Install or clear the server-owned repository for the protected API."""

    if repository is not None and not isinstance(
        repository, BrowserBridgeSiteAuthorityRepository
    ):
        raise BrowserBridgeSiteAuthorityError("invalid site authority repository")
    global _repository
    with _repository_lock:
        _repository = repository


def get_browser_bridge_site_authority_repository(
) -> BrowserBridgeSiteAuthorityRepository:
    with _repository_lock:
        repository = _repository
    if repository is None:
        raise BrowserBridgeSiteAuthorityUnavailable(
            "site authority repository unavailable"
        )
    return repository
