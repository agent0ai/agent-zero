"""Bounded once-only approval challenges for consequential Browser actions.

This module owns only process-memory challenge and receipt state. It does not
infer approval from text, persist sensitive operation data, dispatch controls,
or advertise Browser runtime readiness.
"""

from __future__ import annotations

from collections import deque
from dataclasses import dataclass, field
import re
import threading
import time
from typing import Any, Callable, Mapping
import uuid

from helpers.ws_principal import WsPrincipal
from plugins._a0_connector.helpers.browser_bridge_pairing import validate_identifier
from plugins._a0_connector.helpers.browser_bridge_policy import (
    BrowserBridgePolicyError,
    normalize_site_origin,
)
from plugins._a0_connector.helpers.browser_bridge_transport import (
    PRODUCTION_BROWSER_BRIDGE_TRANSPORT,
    BrowserBridgeTransportProfile,
    require_browser_bridge_transport_profile,
    require_transport_principal_identity,
)


BROWSER_BRIDGE_APPROVAL_CONTRACT = "a0.browser-bridge.approval.v1"
BROWSER_BRIDGE_APPROVAL_VERSION = 1
MAX_APPROVAL_REQUEST_BYTES = 8 * 1024
MAX_APPROVAL_TTL_MS = 120_000
MAX_PENDING_APPROVAL_CHALLENGES = 128
MAX_PENDING_APPROVAL_RECEIPTS = 128
MAX_APPROVAL_TERMINAL_RECORDS = 2_048
MAX_ROUTE_IDENTIFIER_BYTES = 256

APPROVAL_CHOICES = frozenset({"approve_once", "decline"})
APPROVAL_SURFACES = frozenset({"webui", "side_panel"})
CONSEQUENTIAL_ACTION_CLASSES = frozenset(
    {"sensitive_input", "external_side_effect", "unknown"}
)

_NATIVE_IDENTIFIER = re.compile(r"[A-Za-z0-9][A-Za-z0-9._:-]{0,255}")
_SHA256_HEX = re.compile(r"[0-9a-f]{64}")


class BrowserBridgeApprovalError(ValueError):
    """An approval binding or caller input is invalid."""


class BrowserBridgeApprovalUnavailable(RuntimeError):
    """Approval authority is absent, stale, ambiguous, or at capacity."""


class ApprovalDecisionStatus:
    APPROVED = "approved"
    DECLINED = "declined"
    EXPIRED = "expired"
    INVALIDATED = "invalidated"
    ALREADY_RESOLVED = "already_resolved"
    NOT_FOUND = "not_found"


class ApprovalConsumeStatus:
    CONSUMED = "consumed"
    EXPIRED = "expired"
    INVALIDATED = "invalidated"
    ALREADY_CONSUMED = "already_consumed"
    NOT_FOUND = "not_found"


@dataclass(frozen=True, slots=True)
class BrowserActionDataClassification:
    """Immutable internal form of the exact click/type wire union."""

    kind: str
    sensitivity: str | None = None
    text_sha256: str | None = None

    def __post_init__(self) -> None:
        if self.kind == "none":
            if self.sensitivity is not None or self.text_sha256 is not None:
                raise BrowserBridgeApprovalError("invalid action data classification")
            return
        if (
            self.kind != "text"
            or self.sensitivity != "sensitive"
            or not isinstance(self.text_sha256, str)
            or _SHA256_HEX.fullmatch(self.text_sha256) is None
        ):
            raise BrowserBridgeApprovalError("invalid action data classification")

    def as_wire_value(self) -> str | dict[str, str]:
        if self.kind == "none":
            return "none"
        assert self.text_sha256 is not None
        return {
            "kind": "text",
            "sensitivity": "sensitive",
            "text_sha256": self.text_sha256,
        }


NO_ACTION_DATA_CLASSIFICATION = BrowserActionDataClassification("none")


def parse_action_data_classification(
    value: Any,
) -> BrowserActionDataClassification:
    """Parse the exact wire union without retaining a mutable request object."""

    if value == "none" and isinstance(value, str):
        return NO_ACTION_DATA_CLASSIFICATION
    if not isinstance(value, dict) or set(value) != {
        "kind",
        "sensitivity",
        "text_sha256",
    }:
        raise BrowserBridgeApprovalError("invalid action data classification")
    return BrowserActionDataClassification(
        kind=value.get("kind"),
        sensitivity=value.get("sensitivity"),
        text_sha256=value.get("text_sha256"),
    )


@dataclass(frozen=True, slots=True)
class BrowserApprovalRoute:
    """Exact server-owned route for one currently pending Browser operation."""

    server_instance_id: str
    principal: WsPrincipal
    connector_sid: str
    load_generation_id: str
    context_id: str
    browser_session_id: str
    turn_id: str
    action_id: str
    op_id: str
    tab_handle: str
    document_id: str
    document_epoch: int
    transport_profile: BrowserBridgeTransportProfile = (
        PRODUCTION_BROWSER_BRIDGE_TRANSPORT
    )

    def __post_init__(self) -> None:
        _validate_route(self)

    @property
    def bridge_id(self) -> str:
        return self.principal.principal_id

    @property
    def subject_id(self) -> str:
        return self.principal.subject_id

    @property
    def key_generation(self) -> int:
        return self.principal.key_generation


@dataclass(frozen=True, slots=True)
class BrowserApprovalBinding:
    route: BrowserApprovalRoute
    canonical_parameter_hash: str
    target_fingerprint: str
    origin: str
    action_class: str
    data_classification: BrowserActionDataClassification = (
        NO_ACTION_DATA_CLASSIFICATION
    )

    def __post_init__(self) -> None:
        if not isinstance(self.route, BrowserApprovalRoute):
            raise BrowserBridgeApprovalError("invalid approval route")
        _digest(self.canonical_parameter_hash, "canonical parameter hash")
        _digest(self.target_fingerprint, "target fingerprint")
        if self.action_class not in CONSEQUENTIAL_ACTION_CLASSES:
            raise BrowserBridgeApprovalError("invalid consequential action class")
        if not isinstance(
            self.data_classification, BrowserActionDataClassification
        ) or (
            self.data_classification.kind == "text"
            and self.action_class != "sensitive_input"
        ):
            raise BrowserBridgeApprovalError("invalid action data classification")
        try:
            canonical_origin = normalize_site_origin(self.origin)
        except BrowserBridgePolicyError as error:
            raise BrowserBridgeApprovalError("invalid approval origin") from error
        object.__setattr__(self, "origin", canonical_origin)


@dataclass(frozen=True, slots=True)
class BrowserApprovalChallenge:
    challenge_id: str
    binding: BrowserApprovalBinding = field(repr=False)
    created_at_ms: int
    expires_at_ms: int


@dataclass(frozen=True, slots=True)
class BrowserApprovalReceipt:
    receipt_id: str
    challenge_id: str
    binding: BrowserApprovalBinding = field(repr=False)
    approving_surface: str
    decided_at_ms: int
    expires_at_ms: int


@dataclass(frozen=True, slots=True)
class BrowserApprovalDecision:
    challenge_id: str
    status: str
    receipt: BrowserApprovalReceipt | None = field(default=None, repr=False)


@dataclass(frozen=True, slots=True)
class BrowserApprovalInvalidationSummary:
    challenges: int
    receipts: int


RouteAuthorizer = Callable[[BrowserApprovalRoute], bool]
ActiveRecordLoader = Callable[[str, str], Mapping[str, Any] | None]
ServerInstanceIdLoader = Callable[[], str]


class BrowserBridgeApprovalRepository:
    """Atomic bounded registry for one-operation approval authority."""

    def __init__(
        self,
        *,
        route_authorizer: RouteAuthorizer | None = None,
        active_record_loader: ActiveRecordLoader | None = None,
        server_instance_id_loader: ServerInstanceIdLoader | None = None,
        clock_ms: Callable[[], int] | None = None,
        receipt_id_factory: Callable[[], str] | None = None,
        max_pending_challenges: int = MAX_PENDING_APPROVAL_CHALLENGES,
        max_pending_receipts: int = MAX_PENDING_APPROVAL_RECEIPTS,
        max_terminal_records: int = MAX_APPROVAL_TERMINAL_RECORDS,
        transport_profile: BrowserBridgeTransportProfile = (
            PRODUCTION_BROWSER_BRIDGE_TRANSPORT
        ),
    ) -> None:
        if min(max_pending_challenges, max_pending_receipts, max_terminal_records) < 1:
            raise ValueError("approval repository bounds must be positive")
        self._route_authorizer = route_authorizer or (lambda _route: False)
        self._transport_profile = require_browser_bridge_transport_profile(
            transport_profile
        )
        self._active_record_loader = active_record_loader or _load_active_record
        self._server_instance_id_loader = (
            server_instance_id_loader or _load_server_instance_id
        )
        self._clock_ms = clock_ms or (lambda: time.time_ns() // 1_000_000)
        self._receipt_id_factory = receipt_id_factory or (lambda: str(uuid.uuid4()))
        self._max_pending_challenges = max_pending_challenges
        self._max_pending_receipts = max_pending_receipts
        self._max_terminal_records = max_terminal_records
        self._challenges: dict[str, BrowserApprovalChallenge] = {}
        self._operation_challenges: dict[tuple[Any, ...], str] = {}
        self._receipts: dict[str, BrowserApprovalReceipt] = {}
        self._challenge_terminal: dict[str, str] = {}
        self._challenge_terminal_order: deque[str] = deque()
        self._receipt_terminal: dict[str, str] = {}
        self._receipt_terminal_order: deque[str] = deque()
        self._lock = threading.RLock()

    @property
    def pending_challenge_count(self) -> int:
        with self._lock:
            return len(self._challenges)

    @property
    def transport_profile(self) -> BrowserBridgeTransportProfile:
        return self._transport_profile

    @property
    def pending_receipt_count(self) -> int:
        with self._lock:
            return len(self._receipts)

    def register_challenge(
        self,
        challenge_id: Any,
        binding: BrowserApprovalBinding,
        *,
        timeout_ms: int,
    ) -> BrowserApprovalChallenge:
        safe_challenge_id = _native_identifier(challenge_id, "challenge_id")
        binding = _binding(binding)
        self._require_profile(binding.route)
        timeout_ms = _timeout(timeout_ms)
        now = self._now()
        with self._lock:
            self._expire_locked(now)
            existing = self._challenges.get(safe_challenge_id)
            if existing is not None:
                if (
                    _same_binding(existing.binding, binding)
                    and self._route_is_current(binding.route)
                ):
                    return existing
                self._invalidate_challenge_locked(existing)
                raise BrowserBridgeApprovalUnavailable("approval challenge mismatch")
            if safe_challenge_id in self._challenge_terminal:
                raise BrowserBridgeApprovalUnavailable("approval challenge is terminal")
            operation_key = _operation_key(binding.route)
            prior_id = self._operation_challenges.get(operation_key)
            if prior_id is not None:
                prior = self._challenges.get(prior_id)
                if prior is not None:
                    self._invalidate_challenge_locked(prior)
                raise BrowserBridgeApprovalUnavailable("operation challenge conflict")
            if len(self._challenges) >= self._max_pending_challenges:
                raise BrowserBridgeApprovalUnavailable("approval challenge limit reached")
            if not self._route_is_current(binding.route):
                raise BrowserBridgeApprovalUnavailable("approval route is unavailable")
            challenge = BrowserApprovalChallenge(
                challenge_id=safe_challenge_id,
                binding=binding,
                created_at_ms=now,
                expires_at_ms=now + timeout_ms,
            )
            self._challenges[safe_challenge_id] = challenge
            self._operation_challenges[operation_key] = safe_challenge_id
            return challenge

    def decide(
        self,
        challenge_id: Any,
        *,
        choice: Any,
        current_route: BrowserApprovalRoute,
        surface: str,
    ) -> BrowserApprovalDecision:
        safe_challenge_id = _native_identifier(challenge_id, "challenge_id")
        if choice not in APPROVAL_CHOICES:
            raise BrowserBridgeApprovalError("invalid approval choice")
        if surface not in APPROVAL_SURFACES:
            raise BrowserBridgeApprovalError("invalid approving surface")
        if not isinstance(current_route, BrowserApprovalRoute):
            raise BrowserBridgeApprovalError("invalid approval route")
        self._require_profile(current_route)
        now = self._now()
        with self._lock:
            self._expire_locked(now)
            terminal = self._challenge_terminal.get(safe_challenge_id)
            if terminal is not None:
                status = (
                    ApprovalDecisionStatus.EXPIRED
                    if terminal == ApprovalDecisionStatus.EXPIRED
                    else ApprovalDecisionStatus.ALREADY_RESOLVED
                )
                return BrowserApprovalDecision(safe_challenge_id, status)
            challenge = self._challenges.get(safe_challenge_id)
            if challenge is None:
                return BrowserApprovalDecision(
                    safe_challenge_id,
                    ApprovalDecisionStatus.NOT_FOUND,
                )
            if (
                not _same_route(challenge.binding.route, current_route)
                or not self._route_is_current(current_route)
            ):
                self._invalidate_challenge_locked(challenge)
                return BrowserApprovalDecision(
                    safe_challenge_id,
                    ApprovalDecisionStatus.INVALIDATED,
                )
            if choice == "decline":
                self._remove_challenge_locked(
                    challenge,
                    terminal=ApprovalDecisionStatus.DECLINED,
                )
                return BrowserApprovalDecision(
                    safe_challenge_id,
                    ApprovalDecisionStatus.DECLINED,
                )
            if len(self._receipts) >= self._max_pending_receipts:
                self._invalidate_challenge_locked(challenge)
                raise BrowserBridgeApprovalUnavailable("approval receipt limit reached")
            receipt_id = self._fresh_receipt_id_locked()
            receipt = BrowserApprovalReceipt(
                receipt_id=receipt_id,
                challenge_id=safe_challenge_id,
                binding=challenge.binding,
                approving_surface=surface,
                decided_at_ms=now,
                expires_at_ms=now + MAX_APPROVAL_TTL_MS,
            )
            self._receipts[receipt_id] = receipt
            self._remove_challenge_locked(
                challenge,
                terminal=ApprovalDecisionStatus.APPROVED,
            )
            return BrowserApprovalDecision(
                safe_challenge_id,
                ApprovalDecisionStatus.APPROVED,
                receipt,
            )

    def consume(
        self,
        receipt_id: Any,
        *,
        binding: BrowserApprovalBinding,
    ) -> str:
        safe_receipt_id = _native_identifier(receipt_id, "receipt_id")
        binding = _binding(binding)
        self._require_profile(binding.route)
        now = self._now()
        with self._lock:
            self._expire_locked(now)
            terminal = self._receipt_terminal.get(safe_receipt_id)
            if terminal is not None:
                return (
                    ApprovalConsumeStatus.ALREADY_CONSUMED
                    if terminal == ApprovalConsumeStatus.CONSUMED
                    else terminal
                )
            receipt = self._receipts.get(safe_receipt_id)
            if receipt is None:
                return ApprovalConsumeStatus.NOT_FOUND
            if (
                not _same_binding(receipt.binding, binding)
                or not self._route_is_current(binding.route)
            ):
                self._remove_receipt_locked(
                    receipt,
                    terminal=ApprovalConsumeStatus.INVALIDATED,
                )
                return ApprovalConsumeStatus.INVALIDATED
            self._remove_receipt_locked(
                receipt,
                terminal=ApprovalConsumeStatus.CONSUMED,
            )
            return ApprovalConsumeStatus.CONSUMED

    def cancel_operation(
        self,
        route: BrowserApprovalRoute,
    ) -> BrowserApprovalInvalidationSummary:
        route = _route(route)
        self._require_profile(route)
        return self._invalidate_matching(
            lambda candidate: _same_route(candidate, route)
        )

    def finalize_turn(
        self,
        route: BrowserApprovalRoute,
    ) -> BrowserApprovalInvalidationSummary:
        route = _route(route)
        self._require_profile(route)
        return self._invalidate_matching(
            lambda candidate: _same_turn(candidate, route)
        )

    def disconnect(
        self,
        *,
        principal: WsPrincipal,
        connector_sid: Any,
        load_generation_id: Any,
    ) -> BrowserApprovalInvalidationSummary:
        safe_sid = _route_identifier(connector_sid, "connector_sid")
        safe_generation = _native_identifier(
            load_generation_id,
            "load_generation_id",
        )
        if not isinstance(principal, WsPrincipal):
            raise BrowserBridgeApprovalError("invalid bridge principal")
        return self._invalidate_matching(
            lambda candidate: (
                candidate.principal is principal
                and candidate.connector_sid == safe_sid
                and candidate.load_generation_id == safe_generation
            )
        )

    def revoke_bridge(
        self,
        *,
        server_instance_id: Any,
        bridge_id: Any,
        subject_id: Any,
    ) -> BrowserApprovalInvalidationSummary:
        safe_server = _pairing_identifier(server_instance_id, "server_instance_id")
        safe_bridge = _pairing_identifier(bridge_id, "bridge_id")
        safe_subject = _pairing_identifier(subject_id, "subject_id")
        return self._invalidate_matching(
            lambda candidate: (
                candidate.server_instance_id == safe_server
                and candidate.bridge_id == safe_bridge
                and candidate.subject_id == safe_subject
            )
        )

    def expire(self, now_ms: int | None = None) -> BrowserApprovalInvalidationSummary:
        now = self._now() if now_ms is None else _timestamp(now_ms)
        with self._lock:
            return self._expire_locked(now)

    def _invalidate_matching(
        self,
        predicate: Callable[[BrowserApprovalRoute], bool],
    ) -> BrowserApprovalInvalidationSummary:
        challenges: list[BrowserApprovalChallenge] = []
        receipts: list[BrowserApprovalReceipt] = []
        with self._lock:
            challenges.extend(
                challenge
                for challenge in self._challenges.values()
                if predicate(challenge.binding.route)
            )
            receipts.extend(
                receipt
                for receipt in self._receipts.values()
                if predicate(receipt.binding.route)
            )
            for challenge in challenges:
                self._invalidate_challenge_locked(challenge)
            for receipt in receipts:
                self._remove_receipt_locked(
                    receipt,
                    terminal=ApprovalConsumeStatus.INVALIDATED,
                )
        return BrowserApprovalInvalidationSummary(len(challenges), len(receipts))

    def _route_is_current(self, route: BrowserApprovalRoute) -> bool:
        try:
            if (
                self._server_instance_id_loader() != route.server_instance_id
                or self._route_authorizer(route) is not True
            ):
                return False
            record = self._active_record_loader(
                route.server_instance_id,
                route.bridge_id,
            )
        except Exception:
            return False
        if not isinstance(record, Mapping):
            return False
        scopes = record.get("scopes")
        return (
            record.get("state") == "active"
            and record.get("server_instance_id") == route.server_instance_id
            and record.get("bridge_id") == route.bridge_id
            and record.get("subject_id") == route.subject_id
            and record.get("key_generation") == route.key_generation
            and isinstance(scopes, list)
            and frozenset(scopes) == route.principal.scopes
            and "browser.approval" in scopes
        )

    def _expire_locked(self, now: int) -> BrowserApprovalInvalidationSummary:
        challenges = [
            challenge
            for challenge in self._challenges.values()
            if challenge.expires_at_ms <= now
        ]
        receipts = [
            receipt
            for receipt in self._receipts.values()
            if receipt.expires_at_ms <= now
        ]
        for challenge in challenges:
            self._remove_challenge_locked(
                challenge,
                terminal=ApprovalDecisionStatus.EXPIRED,
            )
        for receipt in receipts:
            self._remove_receipt_locked(
                receipt,
                terminal=ApprovalConsumeStatus.EXPIRED,
            )
        return BrowserApprovalInvalidationSummary(len(challenges), len(receipts))

    def _invalidate_challenge_locked(self, challenge: BrowserApprovalChallenge) -> None:
        self._remove_challenge_locked(
            challenge,
            terminal=ApprovalDecisionStatus.INVALIDATED,
        )

    def _remove_challenge_locked(
        self,
        challenge: BrowserApprovalChallenge,
        *,
        terminal: str,
    ) -> None:
        if self._challenges.get(challenge.challenge_id) is not challenge:
            return
        self._challenges.pop(challenge.challenge_id, None)
        self._operation_challenges.pop(_operation_key(challenge.binding.route), None)
        self._remember_terminal_locked(
            challenge.challenge_id,
            terminal,
            self._challenge_terminal,
            self._challenge_terminal_order,
        )

    def _remove_receipt_locked(
        self,
        receipt: BrowserApprovalReceipt,
        *,
        terminal: str,
    ) -> None:
        if self._receipts.get(receipt.receipt_id) is not receipt:
            return
        self._receipts.pop(receipt.receipt_id, None)
        self._remember_terminal_locked(
            receipt.receipt_id,
            terminal,
            self._receipt_terminal,
            self._receipt_terminal_order,
        )

    def _fresh_receipt_id_locked(self) -> str:
        try:
            receipt_id = _native_identifier(
                self._receipt_id_factory(),
                "receipt_id",
            )
        except Exception as error:
            raise BrowserBridgeApprovalUnavailable(
                "approval receipt identity unavailable"
            ) from error
        if receipt_id in self._receipts or receipt_id in self._receipt_terminal:
            raise BrowserBridgeApprovalUnavailable("approval receipt identity collision")
        return receipt_id

    def _remember_terminal_locked(
        self,
        item_id: str,
        status: str,
        statuses: dict[str, str],
        order: deque[str],
    ) -> None:
        if item_id in statuses:
            return
        statuses[item_id] = status
        order.append(item_id)
        while len(order) > self._max_terminal_records:
            statuses.pop(order.popleft(), None)

    def _now(self) -> int:
        return _timestamp(self._clock_ms())

    def _require_profile(self, route: BrowserApprovalRoute) -> None:
        if route.transport_profile is not self._transport_profile:
            raise BrowserBridgeApprovalUnavailable("approval route is unavailable")


def _binding(value: Any) -> BrowserApprovalBinding:
    if not isinstance(value, BrowserApprovalBinding):
        raise BrowserBridgeApprovalError("invalid approval binding")
    return value


def _route(value: Any) -> BrowserApprovalRoute:
    if not isinstance(value, BrowserApprovalRoute):
        raise BrowserBridgeApprovalError("invalid approval route")
    return value


def _validate_route(route: BrowserApprovalRoute) -> None:
    _pairing_identifier(route.server_instance_id, "server_instance_id")
    principal = route.principal
    try:
        profile = require_browser_bridge_transport_profile(route.transport_profile)
        require_transport_principal_identity(principal, profile)
    except ValueError:
        raise BrowserBridgeApprovalError("invalid bridge principal") from None
    if (
        "browser.approval" not in principal.scopes
        or type(principal.key_generation) is not int
        or principal.key_generation < 1
    ):
        raise BrowserBridgeApprovalError("invalid bridge principal")
    _pairing_identifier(principal.principal_id, "bridge_id")
    _pairing_identifier(principal.subject_id, "subject_id")
    _route_identifier(route.connector_sid, "connector_sid")
    _native_identifier(route.load_generation_id, "load_generation_id")
    for name in (
        "context_id",
        "browser_session_id",
        "turn_id",
        "action_id",
        "op_id",
        "tab_handle",
        "document_id",
    ):
        _route_identifier(getattr(route, name), name)
    if (
        isinstance(route.document_epoch, bool)
        or not isinstance(route.document_epoch, int)
        or route.document_epoch < 0
    ):
        raise BrowserBridgeApprovalError("invalid document_epoch")


def _same_binding(
    expected: BrowserApprovalBinding,
    candidate: BrowserApprovalBinding,
) -> bool:
    return (
        _same_route(expected.route, candidate.route)
        and expected.canonical_parameter_hash == candidate.canonical_parameter_hash
        and expected.target_fingerprint == candidate.target_fingerprint
        and expected.origin == candidate.origin
        and expected.action_class == candidate.action_class
        and expected.data_classification == candidate.data_classification
    )


def _same_route(expected: BrowserApprovalRoute, candidate: BrowserApprovalRoute) -> bool:
    return (
        expected.principal is candidate.principal
        and expected.transport_profile is candidate.transport_profile
        and expected.server_instance_id == candidate.server_instance_id
        and expected.connector_sid == candidate.connector_sid
        and expected.load_generation_id == candidate.load_generation_id
        and expected.context_id == candidate.context_id
        and expected.browser_session_id == candidate.browser_session_id
        and expected.turn_id == candidate.turn_id
        and expected.action_id == candidate.action_id
        and expected.op_id == candidate.op_id
        and expected.tab_handle == candidate.tab_handle
        and expected.document_id == candidate.document_id
        and expected.document_epoch == candidate.document_epoch
    )


def _same_turn(expected: BrowserApprovalRoute, candidate: BrowserApprovalRoute) -> bool:
    return (
        expected.principal is candidate.principal
        and expected.server_instance_id == candidate.server_instance_id
        and expected.connector_sid == candidate.connector_sid
        and expected.load_generation_id == candidate.load_generation_id
        and expected.context_id == candidate.context_id
        and expected.browser_session_id == candidate.browser_session_id
        and expected.turn_id == candidate.turn_id
    )


def _operation_key(route: BrowserApprovalRoute) -> tuple[Any, ...]:
    return (
        id(route.principal),
        route.server_instance_id,
        route.connector_sid,
        route.load_generation_id,
        route.context_id,
        route.browser_session_id,
        route.turn_id,
        route.action_id,
        route.op_id,
        route.tab_handle,
        route.document_id,
        route.document_epoch,
    )


def _pairing_identifier(value: Any, field_name: str) -> str:
    try:
        return validate_identifier(value, field_name=field_name)
    except Exception as error:
        raise BrowserBridgeApprovalError(f"invalid {field_name}") from error


def _route_identifier(value: Any, field_name: str) -> str:
    if (
        not isinstance(value, str)
        or not value
        or value != value.strip()
        or not value.isprintable()
    ):
        raise BrowserBridgeApprovalError(f"invalid {field_name}")
    try:
        size = len(value.encode("utf-8"))
    except UnicodeError:
        raise BrowserBridgeApprovalError(f"invalid {field_name}") from None
    if size > MAX_ROUTE_IDENTIFIER_BYTES:
        raise BrowserBridgeApprovalError(f"invalid {field_name}")
    return value


def _native_identifier(value: Any, field_name: str) -> str:
    value = _route_identifier(value, field_name)
    if _NATIVE_IDENTIFIER.fullmatch(value) is None:
        raise BrowserBridgeApprovalError(f"invalid {field_name}")
    return value


def validate_approval_identifier(value: Any, *, field_name: str) -> str:
    """Validate one native-protocol approval identifier."""

    return _native_identifier(value, field_name)


def _digest(value: Any, field_name: str) -> str:
    if not isinstance(value, str) or _SHA256_HEX.fullmatch(value) is None:
        raise BrowserBridgeApprovalError(f"invalid {field_name}")
    return value


def _timeout(value: Any) -> int:
    if (
        isinstance(value, bool)
        or not isinstance(value, int)
        or not 1 <= value <= MAX_APPROVAL_TTL_MS
    ):
        raise BrowserBridgeApprovalError("invalid approval timeout")
    return value


def _timestamp(value: Any) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value < 0:
        raise BrowserBridgeApprovalUnavailable("approval clock unavailable")
    return value


def _load_active_record(
    server_instance_id: str,
    bridge_id: str,
) -> Mapping[str, Any] | None:
    from plugins._a0_connector.helpers.browser_bridge_pairing import (
        get_browser_bridge_pairing_store,
    )

    return get_browser_bridge_pairing_store().active_bridge_record(
        bridge_id=bridge_id,
        server_instance_id=server_instance_id,
    )


def _load_server_instance_id() -> str:
    from helpers import runtime

    return runtime.get_persistent_id()


_repository: BrowserBridgeApprovalRepository | None = None
_repository_lock = threading.Lock()


def get_browser_bridge_approval_repository() -> BrowserBridgeApprovalRepository:
    global _repository
    if _repository is None:
        with _repository_lock:
            if _repository is None:
                _repository = BrowserBridgeApprovalRepository()
    return _repository
