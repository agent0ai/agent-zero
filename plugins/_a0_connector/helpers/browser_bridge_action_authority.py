"""Once-only consequential-action authority for exact pending Browser clicks.

The extension may report a locally detected action risk, but that report grants
nothing.  This controller validates the event against Core's retained operation,
owned lease and semantic-document projection, records only an explicit protected
user choice, consumes one exact receipt, and owns the correlated resolution task.
"""

from __future__ import annotations

import asyncio
from collections import deque
from dataclasses import dataclass, field
import hashlib
import re
import threading
import time
from typing import Any, Awaitable, Callable, Mapping
import uuid

from helpers.ws_principal import WsPrincipal
from plugins._a0_connector.helpers.browser_bridge_approval import (
    MAX_APPROVAL_TTL_MS,
    ApprovalConsumeStatus,
    ApprovalDecisionStatus,
    BrowserActionDataClassification,
    BrowserApprovalBinding,
    BrowserApprovalRoute,
    BrowserBridgeApprovalRepository,
    NO_ACTION_DATA_CLASSIFICATION,
)
from plugins._a0_connector.helpers.browser_bridge_context import (
    BrowserBridgeContextRoute,
)
from plugins._a0_connector.helpers.browser_bridge_events import (
    ActionChallengeNotice,
    TYPE_CHALLENGE_SUMMARY,
    UPLOAD_CHALLENGE_SUMMARY,
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


ACTION_AUTHORITY_CONTRACT = "a0.browser-bridge.approval.v1"
ACTION_AUTHORITY_VERSION = 1
MAX_ACTION_CHALLENGES = 128
MAX_ACTION_DECISIONS = 128
MAX_ACTION_TOMBSTONES = 2_048
DEFAULT_ACTION_RESOLUTION_TIMEOUT_MS = 10_000

ACTION_CHOICES = frozenset({"decline", "approve_once"})
ACTION_OPTIONS = ("decline", "approve_once")
ACTION_CLASSES = frozenset(
    {"sensitive_input", "external_side_effect", "unknown"}
)

_NATIVE_ID = re.compile(r"[A-Za-z0-9][A-Za-z0-9._:-]{0,255}")
_CORE_ID = re.compile(r"[A-Za-z0-9_-]{1,128}")
_DIGEST = re.compile(r"[a-f0-9]{64}")


class BrowserBridgeActionAuthorityError(ValueError):
    """An action challenge, choice, or dependency value is invalid."""


class BrowserBridgeActionAuthorityUnavailable(RuntimeError):
    """Exact current consequential-action authority cannot be established."""


@dataclass(frozen=True, slots=True)
class ActionDocumentBinding:
    """Safe server-owned semantic document identity for one leased tab."""

    document_id: str
    document_epoch: int
    refs: frozenset[str]

    def __post_init__(self) -> None:
        _identifier(self.document_id, "document_id")
        if not _safe_integer(self.document_epoch):
            raise BrowserBridgeActionAuthorityError("invalid document_epoch")
        refs = frozenset(self.refs)
        if not refs or len(refs) > 20_000:
            raise BrowserBridgeActionAuthorityError("invalid document refs")
        for ref in refs:
            _identifier(ref, "ref")
        object.__setattr__(self, "refs", refs)


@dataclass(frozen=True, slots=True)
class ActionChallenge:
    challenge_id: str
    server_instance_id: str
    route: BrowserBridgeContextRoute = field(repr=False)
    operation: OperationTicket = field(repr=False)
    approval_binding: BrowserApprovalBinding = field(repr=False)
    origin: str
    action_class: str
    data_classification: BrowserActionDataClassification = field(repr=False)
    canonical_parameter_hash: str = field(repr=False)
    target_fingerprint: str = field(repr=False)
    lease_id_digest: str = field(repr=False)
    browser_id_digest: str = field(repr=False)
    document_id: str = field(repr=False)
    document_epoch: int = field(repr=False)
    created_at_ms: int
    expires_at_ms: int
    event_hash: str = field(repr=False)

    def as_public_dict(self) -> dict[str, Any]:
        return {
            "challenge_id": self.challenge_id,
            "action": self.operation.action,
            "origin": self.origin,
            "action_class": self.action_class,
            "options": list(ACTION_OPTIONS),
            "expires_at_ms": self.expires_at_ms,
        }


@dataclass(frozen=True, slots=True)
class ActionDecision:
    challenge: ActionChallenge = field(repr=False)
    choice: str
    control_id: str
    action_grant_id: str | None = field(default=None, repr=False)
    receipt_id: str | None = field(default=None, repr=False)
    decided_at_ms: int = 0
    control_expires_at_ms: int = 0

    @property
    def challenge_id(self) -> str:
        return self.challenge.challenge_id

    @property
    def decision(self) -> str:
        return "approved" if self.choice == "approve_once" else "declined"

    def as_public_dict(self) -> dict[str, Any]:
        return {
            "challenge_id": self.challenge_id,
            "decision": self.decision,
            "control_id": self.control_id,
            "status": "accepted",
        }

    def resolution(self) -> dict[str, Any]:
        challenge = self.challenge
        operation = challenge.operation
        grant = None
        if self.choice == "approve_once":
            grant = {
                "action_grant_id": self.action_grant_id,
                "scope": "operation",
                "origin": challenge.origin,
                "action_class": challenge.action_class,
                "canonical_parameter_hash": challenge.canonical_parameter_hash,
                "target_fingerprint": challenge.target_fingerprint,
                "data_classification": (
                    challenge.data_classification.as_wire_value()
                ),
                "expires_at_ms": self.control_expires_at_ms,
            }
        return {
            "challenge_id": challenge.challenge_id,
            "tab_handle": operation.target_tab_handle,
            "document_id": challenge.document_id,
            "document_epoch": challenge.document_epoch,
            "canonical_parameter_hash": challenge.canonical_parameter_hash,
            "target_fingerprint": challenge.target_fingerprint,
            "origin": challenge.origin,
            "action_class": challenge.action_class,
            "data_classification": challenge.data_classification.as_wire_value(),
            "decision": self.choice,
            "grant": grant,
        }


@dataclass(frozen=True, slots=True)
class ActionAuthorityInvalidationSummary:
    challenges: int
    decisions: int


CurrentOperation = Callable[..., OperationTicket | None]
RemainingOperation = Callable[[OperationTicket], int]
LeaseResolver = Callable[[OperationBinding, str], Any | None]
DocumentResolver = Callable[
    [OperationBinding, str], ActionDocumentBinding | Any | None
]
RouteVerifier = Callable[[BrowserBridgeContextRoute], bool]
BeginResolution = Callable[..., Awaitable[ControlTicket]]
WaitControl = Callable[[ControlTicket], Awaitable[BrokerCompletion]]


class BrowserBridgeActionAuthority:
    """Validate action challenges and resolve one exact pending operation."""

    def __init__(
        self,
        *,
        current_operation: CurrentOperation | None = None,
        remaining_operation_ms: RemainingOperation | None = None,
        lease_for: LeaseResolver | None = None,
        document_for: DocumentResolver | None = None,
        route_verifier: RouteVerifier | None = None,
        turn_current: Callable[[OperationBinding], bool] | None = None,
        selection_current: Callable[[str, str], bool] | None = None,
        begin_resolution: BeginResolution | None = None,
        wait_control: WaitControl | None = None,
        server_instance_id: Callable[[], str] | None = None,
        approval_repository: BrowserBridgeApprovalRepository | None = None,
        approval_record_loader: Callable[
            [str, str], Mapping[str, Any] | None
        ]
        | None = None,
        clock_ms: Callable[[], int] | None = None,
        control_id_factory: Callable[[], str] | None = None,
        grant_id_factory: Callable[[], str] | None = None,
        max_challenges: int = MAX_ACTION_CHALLENGES,
        max_decisions: int = MAX_ACTION_DECISIONS,
        max_tombstones: int = MAX_ACTION_TOMBSTONES,
        transport_profile: BrowserBridgeTransportProfile = (
            PRODUCTION_BROWSER_BRIDGE_TRANSPORT
        ),
    ) -> None:
        for value, maximum, name in (
            (max_challenges, MAX_ACTION_CHALLENGES, "challenge"),
            (max_decisions, MAX_ACTION_DECISIONS, "decision"),
            (max_tombstones, MAX_ACTION_TOMBSTONES, "tombstone"),
        ):
            if type(value) is not int or not 1 <= value <= maximum:
                raise ValueError(f"invalid action {name} bound")
        self._current_operation = current_operation or _no_operation
        self._transport_profile = require_browser_bridge_transport_profile(
            transport_profile
        )
        self._remaining_operation_ms = remaining_operation_ms or (
            lambda _operation: 0
        )
        self._lease_for = lease_for or (lambda _binding, _handle: None)
        self._document_for = document_for or (lambda _binding, _handle: None)
        self._route_verifier = route_verifier or (lambda _route: False)
        self._turn_current = turn_current or (lambda _binding: False)
        self._selection_current = selection_current or server_selection_current
        self._begin_resolution = begin_resolution or _resolution_unavailable
        self._wait_control = wait_control or _wait_unavailable
        self._server_instance_id = server_instance_id or _server_unavailable
        self._clock_ms = clock_ms or (lambda: time.time_ns() // 1_000_000)
        self._control_id_factory = control_id_factory or (
            lambda: uuid.uuid4().hex
        )
        self._grant_id_factory = grant_id_factory or (lambda: str(uuid.uuid4()))
        self._approval_repository = approval_repository or (
            BrowserBridgeApprovalRepository(
                route_authorizer=self.approval_route_current,
                active_record_loader=approval_record_loader,
                server_instance_id_loader=self._server_instance_id,
                clock_ms=self._clock_ms,
                transport_profile=self._transport_profile,
            )
        )
        if not isinstance(self._approval_repository, BrowserBridgeApprovalRepository):
            raise ValueError("invalid approval repository")
        if (
            self._approval_repository.transport_profile is not self._transport_profile
        ):
            raise ValueError("approval repository transport mismatch")
        self._max_challenges = max_challenges
        self._max_decisions = max_decisions
        self._max_tombstones = max_tombstones
        self._challenges: dict[str, ActionChallenge] = {}
        self._operation_challenges: dict[tuple[Any, ...], str] = {}
        self._decisions: dict[str, ActionDecision] = {}
        self._decision_outcomes: dict[str, str] = {}
        self._armed_decisions: set[str] = set()
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

    def ready_for(self, binding: OperationBinding) -> bool:
        """Report only whether the controller can validate a future challenge."""

        if not _operation_binding_valid(binding, self._transport_profile):
            return False
        route = BrowserBridgeContextRoute(
            binding.principal,
            binding.connector_sid,
            binding.load_generation_id,
            self._transport_profile,
        )
        try:
            with self._lock:
                return bool(
                    not self._closed
                    and self._server_id()
                    and self._route_current(route)
                    and self._turn_current(binding) is True
                    and self._selected(binding)
                )
        except Exception:
            return False

    def challenge_ready(self, binding: OperationBinding) -> bool:
        """Compatibility spelling for callers composed before runtime wiring."""

        return self.ready_for(binding)

    def approval_route_current(self, route: BrowserApprovalRoute) -> bool:
        """Exact route authorizer for the underlying once-only receipt store."""

        if not isinstance(route, BrowserApprovalRoute):
            return False
        try:
            if self._closed or route.server_instance_id != self._server_id():
                return False
            context_route = BrowserBridgeContextRoute(
                route.principal,
                route.connector_sid,
                route.load_generation_id,
                self._transport_profile,
            )
            if not self._route_current(context_route):
                return False
            operation = self._current_operation(
                principal=route.principal,
                connector_sid=route.connector_sid,
                load_generation_id=route.load_generation_id,
                op_id=route.op_id,
            )
            if not isinstance(operation, OperationTicket):
                return False
            document = self._current_document(operation)
            lease = self._lease_for(operation.binding, route.tab_handle)
            classification = _operation_classification(operation)
            return bool(
                self._turn_current(operation.binding) is True
                and self._selected(operation.binding)
                and
                operation.binding.context_id == route.context_id
                and operation.binding.browser_session_id
                == route.browser_session_id
                and operation.binding.turn_id == route.turn_id
                and operation.binding.action_id == route.action_id
                and operation.action in {"click", "type", "upload_file"}
                and operation.target_tab_handle == route.tab_handle
                and operation.target_ref in document.refs
                and operation.expected_action_class in ACTION_CLASSES
                and classification is not None
                and document.document_id == route.document_id
                and document.document_epoch == route.document_epoch
                and lease is not None
                and getattr(lease, "tab_handle", None) == route.tab_handle
                and self._remaining(operation) > 0
            )
        except Exception:
            return False

    def register_event(self, notice: ActionChallengeNotice) -> None:
        self.register_challenge(notice)

    def register_challenge(self, notice: ActionChallengeNotice) -> ActionChallenge:
        _validate_notice(notice, self._transport_profile)
        now = self._now()
        event_hash = _notice_hash(notice)
        with self._lock:
            self._ensure_open_locked()
            self._expire_locked(now)
            existing = self._challenges.get(notice.challenge_id)
            if existing is not None:
                if existing.event_hash == event_hash and self._challenge_current(existing):
                    return existing
                self._invalidate_challenge_locked(existing, "mismatch")
                raise BrowserBridgeActionAuthorityUnavailable(
                    "action challenge mismatch"
                )
            decision = self._decisions.get(notice.challenge_id)
            if decision is not None:
                if (
                    decision.challenge.event_hash == event_hash
                    and self._challenge_current(decision.challenge)
                ):
                    return decision.challenge
                raise BrowserBridgeActionAuthorityUnavailable(
                    "action challenge is terminal"
                )
            if notice.challenge_id in self._tombstones:
                raise BrowserBridgeActionAuthorityUnavailable(
                    "action challenge is terminal"
                )
            if len(self._challenges) >= self._max_challenges:
                raise BrowserBridgeActionAuthorityUnavailable(
                    "action challenge limit reached"
                )
            operation, lease, document, remaining = self._resolve_notice(notice)
            if (
                notice.expires_at_ms <= now
                or notice.expires_at_ms - now > MAX_APPROVAL_TTL_MS
            ):
                raise BrowserBridgeActionAuthorityUnavailable(
                    "action challenge expired"
                )
            operation_key = _operation_key(operation)
            if operation_key in self._operation_challenges:
                raise BrowserBridgeActionAuthorityUnavailable(
                    "operation already has an action challenge"
                )
            expires_at_ms = min(
                notice.expires_at_ms,
                now + remaining,
                now + MAX_APPROVAL_TTL_MS,
            )
            server_id = self._server_id()
            approval_route = BrowserApprovalRoute(
                server_instance_id=server_id,
                principal=notice.principal,
                connector_sid=notice.connector_sid,
                load_generation_id=notice.load_generation_id,
                context_id=notice.context_id,
                browser_session_id=notice.browser_session_id,
                turn_id=notice.turn_id,
                action_id=notice.action_id,
                op_id=notice.op_id,
                tab_handle=operation.target_tab_handle,
                document_id=document.document_id,
                document_epoch=document.document_epoch,
                transport_profile=self._transport_profile,
            )
            approval_binding = BrowserApprovalBinding(
                route=approval_route,
                canonical_parameter_hash=notice.canonical_parameter_hash,
                target_fingerprint=notice.target_fingerprint,
                origin=notice.origin,
                action_class=notice.action_class,
                data_classification=notice.data_classification,
            )
            self._approval_repository.register_challenge(
                notice.challenge_id,
                approval_binding,
                timeout_ms=expires_at_ms - now,
            )
            challenge = ActionChallenge(
                challenge_id=notice.challenge_id,
                server_instance_id=server_id,
                route=BrowserBridgeContextRoute(
                    notice.principal,
                    notice.connector_sid,
                    notice.load_generation_id,
                    self._transport_profile,
                ),
                operation=operation,
                approval_binding=approval_binding,
                origin=normalize_site_origin(getattr(lease, "origin", None)),
                action_class=notice.action_class,
                data_classification=notice.data_classification,
                canonical_parameter_hash=notice.canonical_parameter_hash,
                target_fingerprint=notice.target_fingerprint,
                lease_id_digest=notice.lease_id_digest,
                browser_id_digest=notice.browser_id_digest,
                document_id=document.document_id,
                document_epoch=document.document_epoch,
                created_at_ms=now,
                expires_at_ms=expires_at_ms,
                event_hash=event_hash,
            )
            self._challenges[challenge.challenge_id] = challenge
            self._operation_challenges[operation_key] = challenge.challenge_id
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
        choice: Any,
        expected_route: BrowserBridgeContextRoute | None = None,
    ) -> ActionDecision:
        subject = _identifier(subject_id, "subject_id")
        challenge_key = _identifier(challenge_id, "challenge_id")
        if choice not in ACTION_CHOICES:
            raise BrowserBridgeActionAuthorityError("invalid action choice")
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
                raise BrowserBridgeActionAuthorityUnavailable("action challenge unavailable")
            if existing is not None:
                if (
                    existing.challenge.route.principal.subject_id == subject
                    and existing.choice == choice
                    and self._selected(existing.challenge.operation.binding)
                ):
                    return existing
                raise BrowserBridgeActionAuthorityUnavailable(
                    "action challenge already decided"
                )
            challenge = self._challenges.get(challenge_key)
            if (
                challenge is None
                or challenge.route.principal.subject_id != subject
                or not self._challenge_current(challenge)
            ):
                if challenge is not None:
                    self._invalidate_challenge_locked(challenge, "invalidated")
                raise BrowserBridgeActionAuthorityUnavailable(
                    "action challenge unavailable"
                )
            return self._start_decision_locked(challenge, choice, now=now)

    def cancel_operation(
        self, operation: OperationTicket
    ) -> ActionAuthorityInvalidationSummary:
        if not isinstance(operation, OperationTicket):
            raise BrowserBridgeActionAuthorityError("invalid browser operation")
        return self._invalidate_matching(
            lambda challenge: challenge.operation is operation
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
    ) -> ActionAuthorityInvalidationSummary:
        values = _lifecycle_values(
            principal,
            connector_sid,
            load_generation_id,
            context_id,
            browser_session_id,
            turn_id,
        )
        return self._invalidate_matching(
            lambda challenge: _challenge_turn(challenge) == values
        )

    def disconnect(
        self,
        *,
        principal: WsPrincipal,
        connector_sid: Any,
        load_generation_id: Any,
    ) -> ActionAuthorityInvalidationSummary:
        if not isinstance(principal, WsPrincipal):
            raise BrowserBridgeActionAuthorityError("invalid bridge principal")
        sid = _identifier(connector_sid, "connector_sid")
        generation = _identifier(load_generation_id, "load_generation_id")
        return self._invalidate_matching(
            lambda challenge: (
                challenge.route.principal is principal
                and challenge.route.connector_sid == sid
                and challenge.route.load_generation_id == generation
            )
        )

    def revoke_bridge(
        self,
        *,
        server_instance_id: Any,
        bridge_id: Any,
        subject_id: Any,
    ) -> ActionAuthorityInvalidationSummary:
        server = _identifier(server_instance_id, "server_instance_id")
        bridge = _identifier(bridge_id, "bridge_id")
        subject = _identifier(subject_id, "subject_id")
        return self._invalidate_matching(
            lambda challenge: (
                challenge.server_instance_id == server
                and challenge.route.principal.principal_id == bridge
                and challenge.route.principal.subject_id == subject
            )
        )

    def expire(
        self, now_ms: int | None = None
    ) -> ActionAuthorityInvalidationSummary:
        now = self._now() if now_ms is None else _timestamp(now_ms)
        with self._lock:
            return self._expire_locked(now)

    async def close(self) -> ActionAuthorityInvalidationSummary:
        with self._lock:
            if self._closed:
                return ActionAuthorityInvalidationSummary(0, 0)
            self._closed = True
            summary = self._invalidate_all_locked("closed")
            tasks = tuple(self._tasks.values())
            self._tasks.clear()
            for task in tasks:
                task.cancel()
        if tasks:
            await asyncio.gather(*tasks, return_exceptions=True)
        return summary

    async def _resolve_decision(self, decision: ActionDecision) -> None:
        try:
            with self._lock:
                if not self._decision_current_locked(decision, require_armed=False):
                    raise BrowserBridgeActionAuthorityUnavailable(
                        "action decision is stale"
                    )
                if decision.choice == "approve_once":
                    if decision.receipt_id is None:
                        raise BrowserBridgeActionAuthorityUnavailable(
                            "action receipt unavailable"
                        )
                    consumed = self._approval_repository.consume(
                        decision.receipt_id,
                        binding=decision.challenge.approval_binding,
                    )
                    if consumed != ApprovalConsumeStatus.CONSUMED:
                        raise BrowserBridgeActionAuthorityUnavailable(
                            "action receipt unavailable"
                        )
                if not self._decision_current_locked(decision, require_armed=False):
                    raise BrowserBridgeActionAuthorityUnavailable(
                        "action decision is stale"
                    )
                self._armed_decisions.add(decision.challenge_id)
            timeout_ms = min(
                DEFAULT_ACTION_RESOLUTION_TIMEOUT_MS,
                self._remaining(decision.challenge.operation),
                max(0, decision.control_expires_at_ms - self._now()),
            )
            if timeout_ms <= 0:
                raise BrowserBridgeActionAuthorityUnavailable(
                    "action resolution expired"
                )
            ticket = await self._begin_resolution(
                decision.challenge.operation,
                control_id=decision.control_id,
                resolution=decision.resolution(),
                authorization_current=lambda: self._decision_current(decision),
                timeout_ms=timeout_ms,
            )
            if not isinstance(ticket, ControlTicket):
                raise BrowserBridgeActionAuthorityUnavailable(
                    "action resolution unavailable"
                )
            completion = await self._wait_control(ticket)
            if not _matching_completion(decision, completion):
                raise BrowserBridgeActionAuthorityUnavailable(
                    "action resolution failed"
                )
            with self._lock:
                if self._decisions.get(decision.challenge_id) is decision:
                    self._decision_outcomes[decision.challenge_id] = "resolved"
                    self._armed_decisions.discard(decision.challenge_id)
        except asyncio.CancelledError:
            raise
        except Exception:
            with self._lock:
                if self._decisions.get(decision.challenge_id) is decision:
                    self._decision_outcomes[decision.challenge_id] = "failed"
                    self._armed_decisions.discard(decision.challenge_id)

    def _start_decision_locked(
        self,
        challenge: ActionChallenge,
        choice: str,
        *,
        now: int,
    ) -> ActionDecision:
        if len(self._decisions) >= self._max_decisions:
            raise BrowserBridgeActionAuthorityUnavailable(
                "action decision limit reached"
            )
        remaining = self._remaining(challenge.operation)
        control_expires_at_ms = min(
            challenge.expires_at_ms,
            now + remaining,
            now + MAX_APPROVAL_TTL_MS,
        )
        if control_expires_at_ms <= now:
            self._invalidate_challenge_locked(challenge, "expired")
            raise BrowserBridgeActionAuthorityUnavailable(
                "action challenge expired"
            )
        control_id = self._fresh_id(
            self._control_id_factory, "control_id", core=True
        )
        grant_id = (
            self._fresh_id(self._grant_id_factory, "action_grant_id", core=False)
            if choice == "approve_once"
            else None
        )
        approval = self._approval_repository.decide(
            challenge.challenge_id,
            choice=choice,
            current_route=challenge.approval_binding.route,
            surface="webui",
        )
        expected_status = (
            ApprovalDecisionStatus.APPROVED
            if choice == "approve_once"
            else ApprovalDecisionStatus.DECLINED
        )
        if approval.status != expected_status or (
            choice == "approve_once" and approval.receipt is None
        ):
            raise BrowserBridgeActionAuthorityUnavailable(
                "action approval unavailable"
            )
        decision = ActionDecision(
            challenge=challenge,
            choice=choice,
            control_id=control_id,
            action_grant_id=grant_id,
            receipt_id=(
                approval.receipt.receipt_id if approval.receipt is not None else None
            ),
            decided_at_ms=now,
            control_expires_at_ms=control_expires_at_ms,
        )
        self._challenges.pop(challenge.challenge_id, None)
        self._decisions[challenge.challenge_id] = decision
        self._decision_outcomes[challenge.challenge_id] = "resolving"
        task = asyncio.create_task(
            self._resolve_decision(decision),
            name=f"browser-bridge-action:{challenge.challenge_id}",
        )
        self._tasks[challenge.challenge_id] = task
        task.add_done_callback(self._resolution_finished)
        return decision

    def _resolve_notice(
        self, notice: ActionChallengeNotice
    ) -> tuple[OperationTicket, Any, ActionDocumentBinding, int]:
        route = BrowserBridgeContextRoute(
            notice.principal,
            notice.connector_sid,
            notice.load_generation_id,
            self._transport_profile,
        )
        if not self._route_current(route):
            raise BrowserBridgeActionAuthorityUnavailable(
                "action route unavailable"
            )
        operation = self._lookup_operation(notice)
        if not isinstance(operation, OperationTicket):
            raise BrowserBridgeActionAuthorityUnavailable(
                "action operation unavailable"
            )
        binding = operation.binding
        classification = _operation_classification(operation)
        if (
            binding.principal is not notice.principal
            or binding.connector_sid != notice.connector_sid
            or binding.load_generation_id != notice.load_generation_id
            or binding.context_id != notice.context_id
            or binding.browser_session_id != notice.browser_session_id
            or binding.turn_id != notice.turn_id
            or binding.action_id != notice.action_id
            or binding.op_id != notice.op_id
            or operation.action not in {"click", "type", "upload_file"}
            or not operation.target_tab_handle
            or not operation.target_ref
            or operation.expected_action_class != notice.action_class
            or classification is None
            or classification != notice.data_classification
            or (
                operation.action == "type"
                and notice.summary != TYPE_CHALLENGE_SUMMARY
            )
            or (operation.action == "upload_file" and notice.summary != UPLOAD_CHALLENGE_SUMMARY)
            or operation.canonical_parameter_hash
            != notice.canonical_parameter_hash
            or self._turn_current(binding) is not True
            or not self._selected(binding)
        ):
            raise BrowserBridgeActionAuthorityUnavailable(
                "action operation mismatch"
            )
        remaining = self._remaining(operation)
        if remaining <= 0:
            raise BrowserBridgeActionAuthorityUnavailable(
                "action operation expired"
            )
        lease = self._lease_for(binding, operation.target_tab_handle)
        try:
            lease_origin = normalize_site_origin(getattr(lease, "origin", None))
        except Exception:
            raise BrowserBridgeActionAuthorityUnavailable(
                "action lease mismatch"
            ) from None
        if (
            lease is None
            or getattr(lease, "tab_handle", None) != operation.target_tab_handle
            or lease_origin != notice.origin
            or _hash_identifier(getattr(lease, "lease_id", None))
            != notice.lease_id_digest
            or _hash_identifier(getattr(lease, "tab_handle", None))
            != notice.browser_id_digest
        ):
            raise BrowserBridgeActionAuthorityUnavailable(
                "action lease mismatch"
            )
        document = self._current_document(operation)
        if (
            document.document_id != notice.document_id
            or document.document_epoch != notice.document_epoch
            or operation.target_ref not in document.refs
        ):
            raise BrowserBridgeActionAuthorityUnavailable(
                "action document mismatch"
            )
        return operation, lease, document, remaining

    def _challenge_current(self, challenge: ActionChallenge) -> bool:
        try:
            if (
                self._server_id() != challenge.server_instance_id
                or not self._route_current(challenge.route)
                or not self._selected(challenge.operation.binding)
            ):
                return False
            operation = self._current_ticket(challenge.operation)
            classification = _operation_classification(challenge.operation)
            if (
                operation is not challenge.operation
                or self._remaining(operation) <= 0
                or self._turn_current(operation.binding) is not True
            ):
                return False
            lease = self._lease_for(operation.binding, operation.target_tab_handle)
            document = self._current_document(operation)
            return bool(
                lease is not None
                and getattr(lease, "tab_handle", None)
                == operation.target_tab_handle
                and normalize_site_origin(getattr(lease, "origin", None))
                == challenge.origin
                and _hash_identifier(getattr(lease, "lease_id", None))
                == challenge.lease_id_digest
                and _hash_identifier(getattr(lease, "tab_handle", None))
                == challenge.browser_id_digest
                and document.document_id == challenge.document_id
                and document.document_epoch == challenge.document_epoch
                and operation.target_ref in document.refs
                and operation.expected_action_class == challenge.action_class
                and classification == challenge.data_classification
                and operation.canonical_parameter_hash
                == challenge.canonical_parameter_hash
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

    def _decision_current(self, decision: ActionDecision) -> bool:
        with self._lock:
            return self._decision_current_locked(decision, require_armed=True)

    def _decision_current_locked(
        self, decision: ActionDecision, *, require_armed: bool
    ) -> bool:
        return bool(
            not self._closed
            and self._decisions.get(decision.challenge_id) is decision
            and self._decision_outcomes.get(decision.challenge_id) == "resolving"
            and self._now() < decision.control_expires_at_ms
            and (
                not require_armed
                or decision.challenge_id in self._armed_decisions
            )
            and self._challenge_current(decision.challenge)
        )

    def _current_document(self, operation: OperationTicket) -> ActionDocumentBinding:
        value = self._document_for(
            operation.binding, operation.target_tab_handle
        )
        if isinstance(value, ActionDocumentBinding):
            return value
        try:
            return ActionDocumentBinding(
                document_id=getattr(value, "document_id"),
                document_epoch=getattr(value, "document_epoch"),
                refs=frozenset(getattr(value, "refs")),
            )
        except Exception:
            raise BrowserBridgeActionAuthorityUnavailable(
                "action document unavailable"
            ) from None

    def _lookup_operation(
        self, notice: ActionChallengeNotice
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
        if type(value) is not int or not 0 <= value <= MAX_APPROVAL_TTL_MS:
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
            raise BrowserBridgeActionAuthorityUnavailable(
                "action server unavailable"
            ) from None

    def _fresh_id(
        self,
        factory: Callable[[], str],
        field_name: str,
        *,
        core: bool,
    ) -> str:
        try:
            value = (
                _core_identifier(factory(), field_name)
                if core
                else _identifier(factory(), field_name)
            )
        except Exception:
            raise BrowserBridgeActionAuthorityUnavailable(
                "action identity unavailable"
            ) from None
        used = {
            decision.control_id for decision in self._decisions.values()
        } | {
            decision.action_grant_id
            for decision in self._decisions.values()
            if decision.action_grant_id is not None
        }
        if value in used:
            raise BrowserBridgeActionAuthorityUnavailable(
                "action identity collision"
            )
        return value

    def _invalidate_matching(
        self, predicate: Callable[[ActionChallenge], bool]
    ) -> ActionAuthorityInvalidationSummary:
        with self._lock:
            challenges = [
                challenge
                for challenge in self._challenges.values()
                if predicate(challenge)
            ]
            decisions = [
                decision
                for decision in self._decisions.values()
                if predicate(decision.challenge)
            ]
            for challenge in challenges:
                self._invalidate_challenge_locked(challenge, "invalidated")
            for decision in decisions:
                self._invalidate_decision_locked(decision, "invalidated")
            return ActionAuthorityInvalidationSummary(
                len(challenges), len(decisions)
            )

    def _expire_locked(self, now: int) -> ActionAuthorityInvalidationSummary:
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
        self._approval_repository.expire(now)
        return ActionAuthorityInvalidationSummary(
            len(challenges), len(decisions)
        )

    def _invalidate_challenge_locked(
        self, challenge: ActionChallenge, reason: str
    ) -> None:
        if self._challenges.get(challenge.challenge_id) is not challenge:
            return
        self._challenges.pop(challenge.challenge_id, None)
        self._operation_challenges.pop(_operation_key(challenge.operation), None)
        self._approval_repository.cancel_operation(challenge.approval_binding.route)
        self._remember_locked(challenge.challenge_id, reason)

    def _invalidate_decision_locked(
        self, decision: ActionDecision, reason: str
    ) -> None:
        if self._decisions.get(decision.challenge_id) is not decision:
            return
        self._decisions.pop(decision.challenge_id, None)
        self._decision_outcomes.pop(decision.challenge_id, None)
        self._armed_decisions.discard(decision.challenge_id)
        self._operation_challenges.pop(
            _operation_key(decision.challenge.operation), None
        )
        self._approval_repository.cancel_operation(
            decision.challenge.approval_binding.route
        )
        self._remember_locked(decision.challenge_id, reason)

    def _invalidate_all_locked(
        self, reason: str
    ) -> ActionAuthorityInvalidationSummary:
        challenges = tuple(self._challenges.values())
        decisions = tuple(self._decisions.values())
        for challenge in challenges:
            self._invalidate_challenge_locked(challenge, reason)
        for decision in decisions:
            self._invalidate_decision_locked(decision, reason)
        return ActionAuthorityInvalidationSummary(
            len(challenges), len(decisions)
        )

    def _remember_locked(self, challenge_id: str, reason: str) -> None:
        if challenge_id in self._tombstones:
            return
        self._tombstones[challenge_id] = reason
        self._tombstone_order.append(challenge_id)
        while len(self._tombstone_order) > self._max_tombstones:
            self._tombstones.pop(self._tombstone_order.popleft(), None)

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

    def _ensure_open_locked(self) -> None:
        if self._closed:
            raise BrowserBridgeActionAuthorityUnavailable(
                "action authority closed"
            )

    def _now(self) -> int:
        return _timestamp(self._clock_ms())


def _matching_completion(
    decision: ActionDecision, completion: BrokerCompletion
) -> bool:
    return bool(
        isinstance(completion, BrokerCompletion)
        and completion.ok is True
        and completion.result
        == {
            "contract_version": ACTION_AUTHORITY_VERSION,
            "control_id": decision.control_id,
            "challenge_id": decision.challenge_id,
            "status": "resolved",
            "decision": decision.choice,
        }
    )


def _validate_notice(
    notice: Any,
    transport_profile: BrowserBridgeTransportProfile,
) -> ActionChallengeNotice:
    if not isinstance(notice, ActionChallengeNotice):
        raise BrowserBridgeActionAuthorityError("invalid action challenge")
    principal = notice.principal
    try:
        require_transport_principal_identity(principal, transport_profile)
    except ValueError:
        raise BrowserBridgeActionAuthorityError("invalid bridge principal") from None
    if (
        not {"browser.operate", "browser.control", "browser.approval"}
        <= principal.scopes
    ):
        raise BrowserBridgeActionAuthorityError("invalid bridge principal")
    for field_name in (
        "connector_sid",
        "load_generation_id",
        "context_id",
        "browser_session_id",
        "turn_id",
        "action_id",
        "op_id",
        "challenge_id",
        "document_id",
    ):
        _identifier(getattr(notice, field_name), field_name)
    for field_name in (
        "canonical_parameter_hash",
        "target_fingerprint",
        "lease_id_digest",
        "browser_id_digest",
    ):
        value = getattr(notice, field_name, None)
        if not isinstance(value, str) or _DIGEST.fullmatch(value) is None:
            raise BrowserBridgeActionAuthorityError(f"invalid {field_name}")
    try:
        origin = normalize_site_origin(notice.origin)
    except BrowserBridgePolicyError as error:
        raise BrowserBridgeActionAuthorityError("invalid action origin") from error
    if (
        origin != notice.origin
        or not isinstance(notice.action_class, str)
        or notice.action_class not in ACTION_CLASSES
        or not isinstance(
            notice.data_classification, BrowserActionDataClassification
        )
        or (
            notice.data_classification.kind == "text"
            and notice.action_class != "sensitive_input"
        )
        or not _safe_integer(notice.document_epoch)
        or not _safe_integer(notice.expires_at_ms, positive=True)
        or not isinstance(notice.summary, str)
        or not notice.summary
        or not notice.summary.isprintable()
        or len(_utf8(notice.summary)) > 512
    ):
        raise BrowserBridgeActionAuthorityError("invalid action challenge")
    return notice


def _notice_hash(notice: ActionChallengeNotice) -> str:
    summary_hash = hashlib.sha256(_utf8(notice.summary)).hexdigest()
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
        notice.action_class,
        notice.canonical_parameter_hash,
        notice.target_fingerprint,
        notice.lease_id_digest,
        notice.browser_id_digest,
        notice.document_id,
        notice.document_epoch,
        summary_hash,
        notice.data_classification,
        notice.expires_at_ms,
    )
    return hashlib.sha256(repr(values).encode("utf-8")).hexdigest()


def _operation_classification(
    operation: OperationTicket,
) -> BrowserActionDataClassification | None:
    if operation.action == "click" and operation.text_sha256 is None:
        return NO_ACTION_DATA_CLASSIFICATION
    if operation.action == "upload_file" and operation.expected_action_class == "external_side_effect" and operation.text_sha256 is None:
        return NO_ACTION_DATA_CLASSIFICATION
    if (
        operation.action == "type"
        and operation.expected_action_class == "sensitive_input"
        and isinstance(operation.text_sha256, str)
        and _DIGEST.fullmatch(operation.text_sha256) is not None
    ):
        try:
            return BrowserActionDataClassification(
                "text", "sensitive", operation.text_sha256
            )
        except Exception:
            return None
    return None


def _operation_binding_valid(
    binding: OperationBinding,
    transport_profile: BrowserBridgeTransportProfile,
) -> bool:
    principal = getattr(binding, "principal", None)
    try:
        require_transport_principal_identity(principal, transport_profile)
    except ValueError:
        return False
    if (
        not isinstance(binding, OperationBinding)
        or not {"browser.operate", "browser.control", "browser.approval"}
        <= principal.scopes
    ):
        return False
    try:
        for field_name in (
            "connector_sid",
            "load_generation_id",
            "context_id",
            "browser_session_id",
            "turn_id",
            "action_id",
            "op_id",
        ):
            _identifier(getattr(binding, field_name), field_name)
    except BrowserBridgeActionAuthorityError:
        return False
    return True


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


def _challenge_turn(challenge: ActionChallenge) -> tuple[Any, ...]:
    binding = challenge.operation.binding
    return (
        id(binding.principal),
        binding.connector_sid,
        binding.load_generation_id,
        binding.context_id,
        binding.browser_session_id,
        binding.turn_id,
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
        raise BrowserBridgeActionAuthorityError("invalid bridge principal")
    return (
        id(principal),
        _identifier(connector_sid, "connector_sid"),
        _identifier(load_generation_id, "load_generation_id"),
        _identifier(context_id, "context_id"),
        _identifier(browser_session_id, "browser_session_id"),
        _identifier(turn_id, "turn_id"),
    )


def _hash_identifier(value: Any) -> str | None:
    if not isinstance(value, str) or _NATIVE_ID.fullmatch(value) is None:
        return None
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def _safe_integer(value: Any, *, positive: bool = False) -> bool:
    return bool(
        not isinstance(value, bool)
        and isinstance(value, int)
        and (1 if positive else 0) <= value <= 2**53 - 1
    )


def _identifier(value: Any, field_name: str) -> str:
    if not isinstance(value, str) or _NATIVE_ID.fullmatch(value) is None:
        raise BrowserBridgeActionAuthorityError(f"invalid {field_name}")
    return value


def _list_scope(
    context_id: Any | None, bridge_id: Any | None
) -> tuple[str | None, str | None]:
    if context_id is None and bridge_id is None:
        return None, None
    if context_id is None or bridge_id is None:
        raise BrowserBridgeActionAuthorityError("incomplete action list scope")
    return (
        _identifier(context_id, "context_id"),
        _identifier(bridge_id, "bridge_id"),
    )


def _core_identifier(value: Any, field_name: str) -> str:
    if not isinstance(value, str) or _CORE_ID.fullmatch(value) is None:
        raise BrowserBridgeActionAuthorityError(f"invalid {field_name}")
    return value


def _timestamp(value: Any) -> int:
    if not _safe_integer(value):
        raise BrowserBridgeActionAuthorityUnavailable(
            "action authority clock unavailable"
        )
    return value


def _utf8(value: Any) -> bytes:
    if not isinstance(value, str):
        raise BrowserBridgeActionAuthorityError("invalid action summary")
    try:
        return value.encode("utf-8")
    except UnicodeError:
        raise BrowserBridgeActionAuthorityError("invalid action summary") from None


def _no_operation(**_kwargs: Any) -> None:
    return None


async def _resolution_unavailable(
    *_args: Any, **_kwargs: Any
) -> ControlTicket:
    raise BrowserBridgeActionAuthorityUnavailable(
        "action resolution unavailable"
    )


async def _wait_unavailable(_ticket: ControlTicket) -> BrokerCompletion:
    raise BrowserBridgeActionAuthorityUnavailable(
        "action resolution unavailable"
    )


def _server_unavailable() -> str:
    raise BrowserBridgeActionAuthorityUnavailable("action server unavailable")


_authority: BrowserBridgeActionAuthority | None = None
_authority_lock = threading.Lock()


def bind_browser_bridge_action_authority(
    authority: BrowserBridgeActionAuthority | None,
) -> None:
    """Install or clear the server-owned controller for the protected API."""

    if authority is not None and not isinstance(
        authority, BrowserBridgeActionAuthority
    ):
        raise BrowserBridgeActionAuthorityError("invalid action authority")
    global _authority
    with _authority_lock:
        _authority = authority


def get_browser_bridge_action_authority() -> BrowserBridgeActionAuthority:
    with _authority_lock:
        authority = _authority
    if authority is None:
        raise BrowserBridgeActionAuthorityUnavailable(
            "action authority unavailable"
        )
    return authority
