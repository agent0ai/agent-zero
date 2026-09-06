"""Bounded, process-only browser operation and control dispatch foundation.

This module deliberately has no dependency on the connector's legacy runtime
registry.  Callers must inject both current authorization and a restricted
sender.  It is an internal seam; importing it does not activate or advertise
the browser bridge.
"""

from __future__ import annotations

import asyncio
from collections import deque
from dataclasses import dataclass, field
import json
import hashlib
import math
import re
import threading
import time
from typing import Any, Awaitable, Callable, Mapping

from helpers.ws_principal import WsPrincipal
from plugins._a0_connector.helpers.browser_bridge_transport import (
    PRODUCTION_BROWSER_BRIDGE_TRANSPORT,
    BrowserBridgeTransportProfile,
    require_browser_bridge_transport_profile,
    require_runtime_transport_principal,
    require_transport_principal_identity,
    transport_profile_for_principal_identity,
)


CONTRACT_VERSION = 1
OPERATION_EVENT = "connector_browser_op"
CONTROL_EVENT = "connector_browser_control"
MAX_TIMEOUT_MS = 120_000
MAX_NON_ARTIFACT_BYTES = 512 * 1024
MAX_IDENTIFIER_BYTES = 256
MAX_REASON_BYTES = 2_048
MAX_CAPABILITIES = 64
MAX_CAPABILITY_BYTES = 128
MAX_DISPOSITIONS = 256
MAX_JSON_DEPTH = 32
MAX_JSON_NODES = 20_000

_ACTIONS = frozenset(
    {
        "open", "list", "state", "set_active", "navigate", "back",
        "forward", "reload", "content", "detail", "evaluate", "click",
        "type", "submit", "type_submit", "scroll", "hover",
        "double_click", "right_click", "drag", "wheel", "mouse",
        "keyboard", "key_chord", "clipboard", "set_viewport",
        "select_option", "set_checked", "upload_file", "screenshot",
        "close", "close_all", "multi", "ensure", "status", "claim",
    }
)
_READ_ONLY_ACTIONS = frozenset(
    {"list", "state", "content", "detail", "screenshot", "status"}
)
_CONTROL_METHODS = frozenset(
    {
        "browser.cancel",
        "browser.finalize_turn",
        "browser.resolve_challenge",
        "browser.reconcile",
    }
)
_OUTCOMES = frozenset({"not_applied", "applied", "unknown"})
_DISPOSITIONS = frozenset({"ephemeral", "deliverable", "handoff"})
_ACTION_CHALLENGE_CLASSES = frozenset(
    {"sensitive_input", "external_side_effect", "unknown"}
)
_ERROR_CODE = re.compile(r"[A-Z][A-Z0-9_]{0,63}")
_CORE_CORRELATION_ID = re.compile(r"[A-Za-z0-9_-]{1,128}")
_NATIVE_IDENTIFIER = re.compile(r"[A-Za-z0-9][A-Za-z0-9._:-]*")


class BrowserBridgeBrokerError(RuntimeError):
    """A local operation was rejected before it crossed the bridge."""

    def __init__(
        self,
        code: str,
        message: str,
        *,
        outcome: str = "not_applied",
        retryable: bool = False,
    ) -> None:
        super().__init__(message)
        self.code = code
        self.outcome = outcome
        self.retryable = retryable


@dataclass(frozen=True, slots=True)
class BridgeAuthorization:
    """Current server-derived authority and negotiated capability snapshot."""

    principal: WsPrincipal
    connector_sid: str
    load_generation_id: str
    contract_version: int
    outer_features: frozenset[str]
    actions: frozenset[str]
    features: frozenset[str]

    def __post_init__(self) -> None:
        for name in ("outer_features", "actions", "features"):
            object.__setattr__(self, name, frozenset(getattr(self, name)))


@dataclass(frozen=True, slots=True)
class OperationBinding:
    principal: WsPrincipal
    connector_sid: str
    load_generation_id: str
    context_id: str
    browser_session_id: str
    turn_id: str
    action_id: str
    op_id: str

    @property
    def bridge_id(self) -> str:
        return self.principal.principal_id


@dataclass(frozen=True, slots=True)
class TurnBinding:
    principal: WsPrincipal
    connector_sid: str
    load_generation_id: str
    context_id: str
    browser_session_id: str
    turn_id: str

    @property
    def bridge_id(self) -> str:
        return self.principal.principal_id


@dataclass(frozen=True, slots=True)
class ControlBinding:
    principal: WsPrincipal
    connector_sid: str
    load_generation_id: str
    context_id: str
    browser_session_id: str
    turn_id: str
    control_id: str
    method: str
    op_id: str | None = None
    action_id: str | None = None

    @property
    def bridge_id(self) -> str:
        return self.principal.principal_id


@dataclass(frozen=True, slots=True)
class ReconciliationBinding:
    """Process-owned provisional route identity for one reconcile control."""

    principal: WsPrincipal
    connector_sid: str
    load_generation_id: str
    control_id: str
    transport_profile: BrowserBridgeTransportProfile

    @property
    def bridge_id(self) -> str:
        return self.principal.principal_id

    @property
    def method(self) -> str:
        return "browser.reconcile"


@dataclass(frozen=True, slots=True)
class BrokerCompletion:
    ok: bool
    code: str | None = None
    error: str | None = None
    outcome: str | None = None
    retryable: bool = False
    result: dict[str, Any] | None = field(default=None, repr=False)
    receipts: tuple[Any, ...] = field(default=(), repr=False)
    artifacts: tuple[Any, ...] = field(default=(), repr=False)
    details: dict[str, Any] | None = field(default=None, repr=False)


@dataclass(frozen=True, slots=True)
class OperationTicket:
    binding: OperationBinding
    deadline_ms: int
    effect: str
    _future: asyncio.Future[BrokerCompletion] = field(
        repr=False, compare=False, hash=False
    )
    action: str = ""
    target_tab_handle: str | None = None
    target_ref: str | None = field(default=None, repr=False)
    expected_action_class: str | None = field(default=None, repr=False)
    text_sha256: str | None = field(default=None, repr=False)
    canonical_parameter_hash: str | None = field(default=None, repr=False)
    destination_origin: str | None = field(default=None, repr=False)
    _dispatch_future: asyncio.Future[BrokerCompletion] | None = field(default=None, repr=False, compare=False, hash=False)


@dataclass(frozen=True, slots=True)
class ControlTicket:
    binding: ControlBinding | ReconciliationBinding
    deadline_ms: int
    _future: asyncio.Future[BrokerCompletion] = field(
        repr=False, compare=False, hash=False
    )
    _settlement_acceptor: Callable[
        [BrokerCompletion], BrokerCompletion | None
    ] | None = field(default=None, repr=False, compare=False, hash=False)


@dataclass(frozen=True, slots=True)
class DisconnectSummary:
    operations: int
    controls: int


class SettlementStatus:
    SETTLED = "settled"
    NOT_FOUND = "not_found"
    MISMATCH = "mismatch"
    DUPLICATE = "duplicate"


Authorizer = Callable[
    [OperationBinding | TurnBinding | ControlBinding | ReconciliationBinding],
    BridgeAuthorization | None,
]
Sender = Callable[
    [str, str, dict[str, Any], str, WsPrincipal], Awaitable[None]
]


class BrowserBridgeOperationBroker:
    """Bounded pending registry and exact operation/control correlator."""

    def __init__(
        self,
        *,
        sender: Sender,
        authorizer: Authorizer,
        clock_ms: Callable[[], int] | None = None,
        max_pending_operations: int = 128,
        max_pending_controls: int = 128,
        max_completed_ids: int = 2_048,
        transport_profile: BrowserBridgeTransportProfile = (
            PRODUCTION_BROWSER_BRIDGE_TRANSPORT
        ),
    ) -> None:
        if min(max_pending_operations, max_pending_controls, max_completed_ids) < 1:
            raise ValueError("Broker bounds must be positive")
        self._sender = sender
        self._authorizer = authorizer
        self._transport_profile = require_browser_bridge_transport_profile(
            transport_profile
        )
        self._clock_ms = clock_ms or (lambda: time.monotonic_ns() // 1_000_000)
        self._max_pending_operations = max_pending_operations
        self._max_pending_controls = max_pending_controls
        self._max_completed_ids = max_completed_ids
        self._operations: dict[str, OperationTicket] = {}
        self._action_identities: set[tuple[str, str, str, str]] = set()
        self._controls: dict[str, ControlTicket] = {}
        self._completed_operations: deque[str] = deque()
        self._completed_operation_set: set[str] = set()
        self._completed_controls: deque[str] = deque()
        self._completed_control_set: set[str] = set()
        # A reply can settle before an injected sender returns. Bound and retain
        # transport tasks separately from pending replies so fast settlements
        # cannot create an unbounded backlog of still-running sends.
        self._send_tasks: set[asyncio.Task[None]] = set()
        self._max_send_tasks = max_pending_operations + max_pending_controls
        self._lock = threading.RLock()

    @property
    def pending_operation_count(self) -> int:
        with self._lock:
            return len(self._operations)

    @property
    def transport_profile(self) -> BrowserBridgeTransportProfile:
        return self._transport_profile

    @property
    def pending_control_count(self) -> int:
        with self._lock:
            return len(self._controls)

    def current_operation(self, *, principal: WsPrincipal, connector_sid: str,
                          load_generation_id: str, op_id: str) -> OperationTicket | None:
        """Return retained intent only for an exact still-authorized pending op."""
        with self._lock:
            ticket = self._operations.get(op_id)
            if ticket is None or not self._source_matches(ticket.binding, principal, connector_sid, load_generation_id):
                return None
            if self._clock_ms() >= ticket.deadline_ms:
                return None
            try:
                self._authorize(ticket.binding, scope="browser.operate", event=OPERATION_EVENT,
                                outer_feature="browser_extension_bridge_v1")
            except BrowserBridgeBrokerError:
                return None
            return ticket if self._operations.get(op_id) is ticket else None

    def remaining_operation_ms(self, ticket: OperationTicket) -> int:
        binding = ticket.binding
        current = self.current_operation(principal=binding.principal, connector_sid=binding.connector_sid,
                                         load_generation_id=binding.load_generation_id, op_id=binding.op_id)
        return max(0, ticket.deadline_ms - self._clock_ms()) if current is ticket else 0

    def pending_operations_for_turn(self, turn: TurnBinding) -> tuple[OperationTicket, ...]:
        """Snapshot only this exact live route's turn for process-owned cleanup."""
        self._validate_turn_binding(turn)
        with self._lock:
            return tuple(
                ticket for ticket in self._operations.values()
                if self._source_matches(ticket.binding, turn.principal, turn.connector_sid, turn.load_generation_id)
                and ticket.binding.context_id == turn.context_id
                and ticket.binding.browser_session_id == turn.browser_session_id
                and ticket.binding.turn_id == turn.turn_id
            )

    async def begin_operation(
        self,
        binding: OperationBinding,
        *,
        action: str,
        target: Mapping[str, Any] | None,
        args: Mapping[str, Any],
        timeout_ms: int,
        required_capabilities: tuple[str, ...] | list[str],
        policy: Mapping[str, Any] | None = None,
        display: Mapping[str, Any] | None = None,
        dispatch_preflight: Callable[[], bool] | None = None,
    ) -> OperationTicket:
        self._validate_operation_binding(binding)
        if action not in _ACTIONS:
            raise _rejected("UNSUPPORTED_CAPABILITY", "Unsupported browser action")
        timeout_ms = _timeout(timeout_ms)
        required = _capabilities(required_capabilities)
        canonical_target = _target(target)
        canonical_args = _mapping_copy(args, "args")
        canonical_policy = _policy(policy)
        canonical_display = _display(display)
        authorization = self._authorize(
            binding,
            scope="browser.operate",
            event=OPERATION_EVENT,
            outer_feature="browser_extension_bridge_v1",
        )
        available = authorization.actions | authorization.features
        if action not in authorization.actions or any(
            capability not in available for capability in required
        ):
            raise _rejected(
                "UNSUPPORTED_CAPABILITY",
                "The bridge does not support all required capabilities",
            )
        payload = {
            "contract_version": CONTRACT_VERSION,
            "bridge_id": binding.bridge_id,
            "load_generation_id": binding.load_generation_id,
            "op_id": binding.op_id,
            "action_id": binding.action_id,
            "context_id": binding.context_id,
            "browser_session_id": binding.browser_session_id,
            "turn_id": binding.turn_id,
            "action": action,
            "target": canonical_target,
            "args": canonical_args,
            "timeout_ms": timeout_ms,
            "required_capabilities": list(required),
            "policy": canonical_policy,
            "display": canonical_display,
        }
        payload = _bounded_json_copy(payload)
        loop = asyncio.get_running_loop()
        parameter_hash = _operation_parameter_hash(
            binding,
            action,
            canonical_target,
            canonical_args,
            canonical_display,
        )
        if action in {"navigate", "click", "type", "upload_file"} and parameter_hash is None:
            raise _rejected("INVALID_STATE", "Invalid challenge-bound browser action")
        text_sha256 = (
            _type_text_digest(canonical_args) if action == "type" else None
        )
        ticket = OperationTicket(
            binding=binding,
            deadline_ms=self._clock_ms() + timeout_ms,
            effect="read_only" if action in _READ_ONLY_ACTIONS else "mutating",
            _future=loop.create_future(),
            action=action,
            target_tab_handle=canonical_target.get("tab_handle") if canonical_target else None,
            target_ref=(
                canonical_args.get("ref")
                if action in {"click", "type", "upload_file"}
                else None
            ),
            expected_action_class=(
                canonical_args.get("expected_action_class")
                if action in {"click", "type", "upload_file"}
                else None
            ),
            text_sha256=text_sha256,
            canonical_parameter_hash=parameter_hash,
            destination_origin=_navigation_origin(action, canonical_args),
            _dispatch_future=loop.create_future(),
        )
        action_identity = self._action_identity(binding)
        with self._lock:
            self._check_send_capacity_locked()
            if len(self._operations) >= self._max_pending_operations:
                raise _rejected("INVALID_STATE", "Operation registry is full")
            if (
                binding.op_id in self._operations
                or binding.op_id in self._completed_operation_set
            ):
                raise _rejected("IDEMPOTENCY_CONFLICT", "Operation ID is not fresh")
            if action_identity in self._action_identities:
                raise _rejected("IDEMPOTENCY_CONFLICT", "Action is already pending")
            self._operations[binding.op_id] = ticket
            self._action_identities.add(action_identity)
            self._launch_send(ticket, OPERATION_EVENT, payload, binding.op_id, dispatch_preflight)
        return ticket

    async def perform(self, binding: OperationBinding, **kwargs: Any) -> BrokerCompletion:
        ticket = await self.begin_operation(binding, **kwargs)
        return await self.wait_operation(ticket)

    async def begin_cancel(
        self,
        operation: OperationTicket,
        *,
        control_id: str,
        reason: str,
        timeout_ms: int,
    ) -> ControlTicket:
        _core_correlation_id(control_id, "control_id")
        timeout_ms = _timeout(timeout_ms)
        reason = _reason(reason)
        with self._lock:
            if self._operations.get(operation.binding.op_id) is not operation:
                raise _rejected("INVALID_STATE", "Only the exact pending operation can be canceled")
        binding = ControlBinding(
            principal=operation.binding.principal,
            connector_sid=operation.binding.connector_sid,
            load_generation_id=operation.binding.load_generation_id,
            context_id=operation.binding.context_id,
            browser_session_id=operation.binding.browser_session_id,
            turn_id=operation.binding.turn_id,
            control_id=control_id,
            method="browser.cancel",
            op_id=operation.binding.op_id,
            action_id=operation.binding.action_id,
        )
        payload = {
            "method": binding.method,
            "contract_version": CONTRACT_VERSION,
            "bridge_id": binding.bridge_id,
            "load_generation_id": binding.load_generation_id,
            "control_id": binding.control_id,
            "op_id": binding.op_id,
            "action_id": binding.action_id,
            "context_id": binding.context_id,
            "browser_session_id": binding.browser_session_id,
            "turn_id": binding.turn_id,
            "reason": reason,
        }
        return await self._begin_control(binding, payload, timeout_ms)

    async def begin_finalize(
        self,
        turn: TurnBinding,
        *,
        control_id: str,
        dispositions: Mapping[str, str],
        reason: str,
        timeout_ms: int,
    ) -> ControlTicket:
        self._validate_turn_binding(turn)
        _core_correlation_id(control_id, "control_id")
        timeout_ms = _timeout(timeout_ms)
        reason = _reason(reason)
        canonical_dispositions = _dispositions(dispositions)
        binding = ControlBinding(
            principal=turn.principal,
            connector_sid=turn.connector_sid,
            load_generation_id=turn.load_generation_id,
            context_id=turn.context_id,
            browser_session_id=turn.browser_session_id,
            turn_id=turn.turn_id,
            control_id=control_id,
            method="browser.finalize_turn",
        )
        payload = {
            "method": binding.method,
            "contract_version": CONTRACT_VERSION,
            "bridge_id": binding.bridge_id,
            "load_generation_id": binding.load_generation_id,
            "control_id": binding.control_id,
            "context_id": binding.context_id,
            "browser_session_id": binding.browser_session_id,
            "turn_id": binding.turn_id,
            "dispositions": canonical_dispositions,
            "reason": reason,
        }
        return await self._begin_control(binding, payload, timeout_ms)

    async def begin_reconcile(
        self,
        binding: ReconciliationBinding,
        *,
        expected_contexts: list[Mapping[str, Any]]
        | tuple[Mapping[str, Any], ...],
        event_cursors: list[Mapping[str, Any]]
        | tuple[Mapping[str, Any], ...],
        known_control_ids: list[str] | tuple[str, ...],
        timeout_ms: int,
        dispatch_preflight: Callable[[], bool],
        settlement_acceptor: Callable[
            [BrokerCompletion], BrokerCompletion | None
        ],
    ) -> ControlTicket:
        """Queue one provisional-route reconciliation control.

        The synchronous settlement acceptor is the security barrier between a
        verified reconcile result and route promotion.  It runs before the
        result future is delivered, so a following critical event cannot rely
        on transport FIFO alone for authority.
        """

        self._validate_reconciliation_binding(binding)
        if binding.transport_profile is not self._transport_profile:
            raise _rejected("SCOPE_DENIED", "Reconciliation transport is unavailable")
        timeout_ms = _timeout(timeout_ms)
        if not callable(dispatch_preflight) or not callable(settlement_acceptor):
            raise _rejected("INVALID_STATE", "Reconciliation authority is unavailable")
        payload = {
            "method": "browser.reconcile",
            "contract_version": CONTRACT_VERSION,
            "bridge_id": binding.bridge_id,
            "load_generation_id": binding.load_generation_id,
            "control_id": binding.control_id,
            "expected_contexts": _reconciliation_expected_contexts(
                expected_contexts
            ),
            "event_cursors": _reconciliation_event_cursors(event_cursors),
            "known_control_ids": _reconciliation_control_ids(
                known_control_ids
            ),
        }
        return await self._begin_control(
            binding,
            payload,
            timeout_ms,
            dispatch_preflight,
            settlement_acceptor,
        )

    async def _begin_control(
        self,
        binding: ControlBinding | ReconciliationBinding,
        payload: dict[str, Any],
        timeout_ms: int,
        dispatch_preflight: Callable[[], bool] | None = None,
        settlement_acceptor: Callable[
            [BrokerCompletion], BrokerCompletion | None
        ] | None = None,
    ) -> ControlTicket:
        if binding.method not in _CONTROL_METHODS:
            raise _rejected("INVALID_STATE", "Unsupported browser control")
        if (binding.method == "browser.reconcile") is not isinstance(
            binding, ReconciliationBinding
        ):
            raise _rejected("INVALID_STATE", "Invalid browser control binding")
        self._authorize(
            binding,
            scope="browser.control",
            event=CONTROL_EVENT,
            outer_feature="connector_browser_control",
        )
        payload = _bounded_json_copy(payload)
        loop = asyncio.get_running_loop()
        ticket = ControlTicket(
            binding=binding,
            deadline_ms=self._clock_ms() + timeout_ms,
            _future=loop.create_future(),
            _settlement_acceptor=settlement_acceptor,
        )
        with self._lock:
            self._check_send_capacity_locked()
            if len(self._controls) >= self._max_pending_controls:
                raise _rejected("INVALID_STATE", "Control registry is full")
            if (
                binding.control_id in self._controls
                or binding.control_id in self._completed_control_set
            ):
                raise _rejected("IDEMPOTENCY_CONFLICT", "Control ID is not fresh")
            self._controls[binding.control_id] = ticket
            self._launch_send(ticket, CONTROL_EVENT, payload, binding.control_id, dispatch_preflight)
        return ticket

    async def begin_site_resolution(self, operation: OperationTicket, *, control_id: str,
                                    resolution: Mapping[str, Any], authorization_current: Callable[[], bool],
                                    timeout_ms: int = 10_000) -> ControlTicket:
        """Only server-owned site decisions may supply this control preflight."""
        _core_correlation_id(control_id, "control_id")
        if not callable(authorization_current) or authorization_current() is not True:
            raise _rejected("SCOPE_DENIED", "Site decision is not current")
        remaining = self.remaining_operation_ms(operation)
        if remaining <= 0 or operation.action != "navigate" or not operation.canonical_parameter_hash or not operation.destination_origin or not operation.target_tab_handle:
            raise _rejected("INVALID_STATE", "Navigation is no longer pending")
        data = _mapping_copy(resolution, "resolution")
        required = {"challenge_id", "tab_handle", "document_id", "document_epoch",
                    "canonical_parameter_hash", "target_fingerprint", "origin", "action_class", "decision", "grant"}
        if set(data) != required or data["action_class"] != "navigate":
            raise _rejected("INVALID_STATE", "Invalid site resolution")
        _identifier(data["challenge_id"], "challenge_id")
        if data["document_id"] is not None:
            _identifier(data["document_id"], "document_id")
        if (
            data["tab_handle"] != operation.target_tab_handle
            or data["canonical_parameter_hash"] != operation.canonical_parameter_hash
            or data["origin"] != operation.destination_origin
            or type(data["document_epoch"]) is not int or not 0 <= data["document_epoch"] <= 2**53 - 1
            or not isinstance(data["target_fingerprint"], str)
            or re.fullmatch(r"[a-f0-9]{64}", data["target_fingerprint"]) is None
            or not isinstance(data["decision"], str) or data["decision"] not in {"deny", "allow_once", "allow_turn"}
        ):
            raise _rejected("SCOPE_DENIED", "Site resolution binding mismatch")
        grant = data["grant"]
        if data["decision"] == "deny":
            if grant is not None:
                raise _rejected("INVALID_STATE", "A denial cannot grant access")
        elif (
            not isinstance(grant, dict) or set(grant) != {"origin_grant_id", "scope", "origin", "expires_at_ms"}
            or grant["scope"] != ("operation" if data["decision"] == "allow_once" else "turn")
            or grant["origin"] != data["origin"] or type(grant["expires_at_ms"]) is not int
            or not 0 < grant["expires_at_ms"] <= 2**53 - 1
        ):
            raise _rejected("INVALID_STATE", "Invalid site grant")
        else:
            _identifier(grant["origin_grant_id"], "origin_grant_id")
        source = operation.binding
        binding = ControlBinding(source.principal, source.connector_sid, source.load_generation_id,
                                 source.context_id, source.browser_session_id, source.turn_id,
                                 control_id, "browser.resolve_challenge", source.op_id, source.action_id)
        payload = {"method": binding.method, "contract_version": 1, "bridge_id": binding.bridge_id,
                   "load_generation_id": binding.load_generation_id, "control_id": control_id,
                   "context_id": binding.context_id, "browser_session_id": binding.browser_session_id,
                   "turn_id": binding.turn_id, "op_id": binding.op_id, "action_id": binding.action_id, **data}

        def still_current() -> bool:
            return self.remaining_operation_ms(operation) > 0 and authorization_current() is True

        return await self._begin_control(binding, payload, min(_timeout(timeout_ms), remaining), still_current)

    async def begin_action_resolution(
        self,
        operation: OperationTicket,
        *,
        control_id: str,
        resolution: Mapping[str, Any],
        authorization_current: Callable[[], bool],
        timeout_ms: int = 10_000,
    ) -> ControlTicket:
        """Queue one exact, server-owned consequential-action decision."""

        _core_correlation_id(control_id, "control_id")
        if not callable(authorization_current) or authorization_current() is not True:
            raise _rejected("SCOPE_DENIED", "Action decision is not current")
        remaining = self.remaining_operation_ms(operation)
        if (
            remaining <= 0
            or operation.action not in {"click", "type", "upload_file"}
            or not operation.canonical_parameter_hash
            or not operation.target_tab_handle
            or not operation.target_ref
            or operation.expected_action_class not in _ACTION_CHALLENGE_CLASSES
            or (
                operation.action == "type"
                and (
                    operation.expected_action_class != "sensitive_input"
                    or not isinstance(operation.text_sha256, str)
                    or re.fullmatch(r"[a-f0-9]{64}", operation.text_sha256)
                    is None
                )
            )
            or (operation.action in {"click", "upload_file"} and operation.text_sha256 is not None)
            or (operation.action == "upload_file" and operation.expected_action_class != "external_side_effect")
        ):
            raise _rejected("INVALID_STATE", "Action is no longer pending")
        data = _mapping_copy(resolution, "resolution")
        required = {
            "challenge_id",
            "tab_handle",
            "document_id",
            "document_epoch",
            "canonical_parameter_hash",
            "target_fingerprint",
            "origin",
            "action_class",
            "data_classification",
            "decision",
            "grant",
        }
        if set(data) != required:
            raise _rejected("INVALID_STATE", "Invalid action resolution")
        _identifier(data["challenge_id"], "challenge_id")
        _identifier(data["document_id"], "document_id")
        try:
            from plugins._a0_connector.helpers.browser_bridge_policy import (
                normalize_site_origin,
            )
            from plugins._a0_connector.helpers.browser_bridge_approval import (
                BrowserActionDataClassification,
                NO_ACTION_DATA_CLASSIFICATION,
                parse_action_data_classification,
            )

            canonical_origin = normalize_site_origin(data["origin"])
            classification = parse_action_data_classification(
                data["data_classification"]
            )
        except Exception:
            raise _rejected("SCOPE_DENIED", "Action resolution origin is invalid") from None
        expected_classification = (
            NO_ACTION_DATA_CLASSIFICATION
            if operation.action in {"click", "upload_file"}
            else BrowserActionDataClassification(
                "text", "sensitive", operation.text_sha256
            )
        )
        if (
            data["tab_handle"] != operation.target_tab_handle
            or data["canonical_parameter_hash"]
            != operation.canonical_parameter_hash
            or type(data["document_epoch"]) is not int
            or not 0 <= data["document_epoch"] <= 2**53 - 1
            or not isinstance(data["target_fingerprint"], str)
            or re.fullmatch(r"[a-f0-9]{64}", data["target_fingerprint"])
            is None
            or not isinstance(data["action_class"], str)
            or data["action_class"] not in _ACTION_CHALLENGE_CLASSES
            or data["action_class"] != operation.expected_action_class
            or classification != expected_classification
            or not isinstance(data["decision"], str)
            or data["decision"] not in {"decline", "approve_once"}
            or canonical_origin != data["origin"]
        ):
            raise _rejected("SCOPE_DENIED", "Action resolution binding mismatch")
        grant = data["grant"]
        if data["decision"] == "decline":
            if grant is not None:
                raise _rejected("INVALID_STATE", "A decline cannot grant access")
        elif (
            not isinstance(grant, dict)
            or set(grant)
            != {
                "action_grant_id",
                "scope",
                "origin",
                "action_class",
                "canonical_parameter_hash",
                "target_fingerprint",
                "data_classification",
                "expires_at_ms",
            }
            or grant["scope"] != "operation"
            or grant["origin"] != data["origin"]
            or grant["action_class"] != data["action_class"]
            or grant["canonical_parameter_hash"]
            != data["canonical_parameter_hash"]
            or grant["target_fingerprint"] != data["target_fingerprint"]
            or type(grant["expires_at_ms"]) is not int
            or not 0 < grant["expires_at_ms"] <= 2**53 - 1
        ):
            raise _rejected("INVALID_STATE", "Invalid action grant")
        else:
            _identifier(grant["action_grant_id"], "action_grant_id")
            try:
                grant_classification = parse_action_data_classification(
                    grant["data_classification"]
                )
            except Exception:
                raise _rejected("INVALID_STATE", "Invalid action grant") from None
            if grant_classification != classification:
                raise _rejected("INVALID_STATE", "Invalid action grant")
        data["data_classification"] = classification.as_wire_value()
        if isinstance(grant, dict):
            grant["data_classification"] = classification.as_wire_value()
        source = operation.binding
        binding = ControlBinding(
            source.principal,
            source.connector_sid,
            source.load_generation_id,
            source.context_id,
            source.browser_session_id,
            source.turn_id,
            control_id,
            "browser.resolve_challenge",
            source.op_id,
            source.action_id,
        )
        payload = {
            "method": binding.method,
            "contract_version": CONTRACT_VERSION,
            "bridge_id": binding.bridge_id,
            "load_generation_id": binding.load_generation_id,
            "control_id": control_id,
            "context_id": binding.context_id,
            "browser_session_id": binding.browser_session_id,
            "turn_id": binding.turn_id,
            "op_id": binding.op_id,
            "action_id": binding.action_id,
            **data,
        }

        def still_current() -> bool:
            return (
                self.remaining_operation_ms(operation) > 0
                and authorization_current() is True
            )

        return await self._begin_control(
            binding,
            payload,
            min(_timeout(timeout_ms), remaining),
            still_current,
        )

    async def wait_operation(self, ticket: OperationTicket) -> BrokerCompletion:
        return await self._wait(ticket, operation=True)

    async def wait_dispatched(self, ticket: OperationTicket) -> None:
        """Wait for this exact operation's transport send before input frames.

        Successful dispatch is ordering evidence, never effect completion. A
        canceled caller cannot cancel the process-owned dispatch or its receipt.
        """
        with self._lock:
            if self._operations.get(ticket.binding.op_id) is not ticket or ticket._dispatch_future is None:
                raise _rejected("INVALID_STATE", "Operation dispatch is no longer pending")
        remaining = max(0, ticket.deadline_ms - self._clock_ms()) / 1_000
        try:
            completion = await asyncio.wait_for(asyncio.shield(ticket._dispatch_future), remaining)
        except asyncio.TimeoutError:
            self._expire_ticket(ticket)
            raise _rejected("DEADLINE_EXCEEDED", "Operation dispatch deadline expired") from None
        with self._lock:
            if not completion.ok:
                raise _rejected(completion.code or "CONNECTION_LOST", "Operation transport dispatch failed")
            if self._operations.get(ticket.binding.op_id) is not ticket or self._clock_ms() >= ticket.deadline_ms:
                raise _rejected("INVALID_STATE", "Operation retired before input transfer")

    async def wait_control(self, ticket: ControlTicket) -> BrokerCompletion:
        return await self._wait(ticket, operation=False)

    async def _wait(
        self,
        ticket: OperationTicket | ControlTicket,
        *,
        operation: bool,
    ) -> BrokerCompletion:
        remaining = max(0, ticket.deadline_ms - self._clock_ms()) / 1_000
        try:
            return await asyncio.wait_for(asyncio.shield(ticket._future), remaining)
        except asyncio.TimeoutError:
            self.expire(self._clock_ms())
            # A custom clock may be fixed in tests. Ensure this exact ticket is
            # terminal even when the real asyncio timeout won the race first.
            if not ticket._future.done():
                completion = self._deadline_completion(ticket, operation=operation)
                if operation:
                    self._finish_operation(ticket, completion)
                else:
                    self._finish_control(ticket, completion)
            return await asyncio.shield(ticket._future)

    def settle_operation(
        self,
        *,
        principal: WsPrincipal,
        connector_sid: str,
        load_generation_id: str,
        payload: Mapping[str, Any],
    ) -> str:
        candidate = _incoming_mapping(payload)
        op_id = candidate.get("op_id") if candidate is not None else None
        if not isinstance(op_id, str):
            return SettlementStatus.NOT_FOUND
        with self._lock:
            ticket = self._operations.get(op_id)
            if ticket is None:
                return (
                    SettlementStatus.DUPLICATE
                    if op_id in self._completed_operation_set
                    else SettlementStatus.NOT_FOUND
                )
            if candidate is None or not self._operation_result_matches(
                ticket.binding, principal, connector_sid, load_generation_id, candidate
            ):
                return SettlementStatus.MISMATCH
            completion = _parse_operation_completion(candidate)
            if completion is None:
                return SettlementStatus.MISMATCH
            if ticket.deadline_ms <= self._clock_ms():
                completion = self._deadline_completion(ticket, operation=True)
            self._remove_operation_locked(ticket)
        self._deliver(ticket._future, completion)
        return SettlementStatus.SETTLED

    def settle_control(
        self,
        *,
        principal: WsPrincipal,
        connector_sid: str,
        load_generation_id: str,
        payload: Mapping[str, Any],
    ) -> str:
        candidate = _incoming_mapping(payload)
        control_id = candidate.get("control_id") if candidate is not None else None
        if not isinstance(control_id, str):
            return SettlementStatus.NOT_FOUND
        with self._lock:
            ticket = self._controls.get(control_id)
            if ticket is None:
                return (
                    SettlementStatus.DUPLICATE
                    if control_id in self._completed_control_set
                    else SettlementStatus.NOT_FOUND
                )
            if candidate is None or not self._control_result_matches(
                ticket.binding, principal, connector_sid, load_generation_id, candidate
            ):
                return SettlementStatus.MISMATCH
            completion = _parse_control_completion(candidate)
            if completion is None:
                return SettlementStatus.MISMATCH
            if ticket.deadline_ms <= self._clock_ms():
                completion = self._deadline_completion(ticket, operation=False)
            elif ticket._settlement_acceptor is not None:
                try:
                    completion = ticket._settlement_acceptor(completion)
                except Exception:
                    completion = None
                if completion is None:
                    return SettlementStatus.MISMATCH
            self._remove_control_locked(ticket)
        self._deliver(ticket._future, completion)
        return SettlementStatus.SETTLED

    def disconnect(
        self,
        *,
        principal: WsPrincipal,
        connector_sid: str,
        load_generation_id: str,
    ) -> DisconnectSummary:
        operations: list[OperationTicket] = []
        controls: list[ControlTicket] = []
        with self._lock:
            for ticket in tuple(self._operations.values()):
                if self._source_matches(ticket.binding, principal, connector_sid, load_generation_id):
                    self._remove_operation_locked(ticket)
                    operations.append(ticket)
            for ticket in tuple(self._controls.values()):
                if self._source_matches(ticket.binding, principal, connector_sid, load_generation_id):
                    self._remove_control_locked(ticket)
                    controls.append(ticket)
        for ticket in operations:
            if ticket.effect == "mutating":
                completion = _error("OUTCOME_UNKNOWN", "Browser operation outcome is unknown", "unknown")
            else:
                completion = _error(
                    "CONNECTION_LOST", "Browser bridge connection was lost",
                    "not_applied", retryable=True,
                )
            self._deliver(ticket._future, completion)
        for ticket in controls:
            completion = (
                _error(
                    "CONNECTION_LOST",
                    "Browser reconciliation connection was lost",
                    "not_applied",
                    retryable=True,
                )
                if isinstance(ticket.binding, ReconciliationBinding)
                else _error(
                    "OUTCOME_UNKNOWN",
                    "Browser control outcome is unknown",
                    "unknown",
                )
            )
            self._deliver(ticket._future, completion)
        return DisconnectSummary(len(operations), len(controls))

    def expire(self, now_ms: int | None = None) -> DisconnectSummary:
        now = self._clock_ms() if now_ms is None else now_ms
        operations: list[OperationTicket] = []
        controls: list[ControlTicket] = []
        with self._lock:
            for ticket in tuple(self._operations.values()):
                if ticket.deadline_ms <= now:
                    self._remove_operation_locked(ticket)
                    operations.append(ticket)
            for ticket in tuple(self._controls.values()):
                if ticket.deadline_ms <= now:
                    self._remove_control_locked(ticket)
                    controls.append(ticket)
        for ticket in operations:
            self._deliver(ticket._future, self._deadline_completion(ticket, operation=True))
        for ticket in controls:
            self._deliver(ticket._future, self._deadline_completion(ticket, operation=False))
        return DisconnectSummary(len(operations), len(controls))

    def _deadline_completion(
        self, ticket: OperationTicket | ControlTicket, *, operation: bool
    ) -> BrokerCompletion:
        if operation and isinstance(ticket, OperationTicket) and ticket.effect == "read_only":
            return _error(
                "DEADLINE_EXCEEDED", "Browser operation deadline expired",
                "not_applied", retryable=True,
            )
        if (
            isinstance(ticket, ControlTicket)
            and isinstance(ticket.binding, ReconciliationBinding)
        ):
            return _error(
                "DEADLINE_EXCEEDED",
                "Browser reconciliation deadline expired",
                "not_applied",
                retryable=True,
            )
        subject = "control" if isinstance(ticket, ControlTicket) else "operation"
        return _error("OUTCOME_UNKNOWN", f"Browser {subject} outcome is unknown", "unknown")

    def _launch_send(
        self,
        ticket: OperationTicket | ControlTicket,
        event: str,
        payload: dict[str, Any],
        correlation_id: str,
        dispatch_preflight: Callable[[], bool] | None = None,
    ) -> None:
        async def send_if_current() -> None:
            operation = isinstance(ticket, OperationTicket)
            with self._lock:
                pending = (
                    self._operations.get(correlation_id)
                    if operation else self._controls.get(correlation_id)
                )
                if pending is not ticket:
                    return
                authorization = self._authorize(
                    ticket.binding,
                    scope="browser.operate" if operation else "browser.control",
                    event=event,
                    outer_feature=(
                        "browser_extension_bridge_v1" if operation
                        else "connector_browser_control"
                    ),
                )
                if operation and (
                    payload["action"] not in authorization.actions
                    or any(capability not in authorization.actions | authorization.features
                           for capability in payload["required_capabilities"])
                ):
                    raise _rejected("UNSUPPORTED_CAPABILITY", "Browser capabilities changed before dispatch")
                if operation and not _operation_intent_matches(ticket, payload):
                    raise _rejected(
                        "INVALID_STATE",
                        "Browser operation intent changed before dispatch",
                    )
                if dispatch_preflight is not None:
                    try:
                        permitted = dispatch_preflight() is True
                    except Exception:
                        permitted = False
                    if not permitted:
                        raise _rejected("ORIGIN_BLOCKED", "Browser policy changed before dispatch")
            # The restricted sender must still revalidate the exact principal
            # at its own final transport boundary. No caller metadata can grant
            # authority across an await inside that sender.
            await self._sender(
                ticket.binding.connector_sid, event, payload, correlation_id,
                ticket.binding.principal,
            )

        async def dispatch() -> None:
            try:
                remaining = max(0, ticket.deadline_ms - self._clock_ms()) / 1_000
                if remaining <= 0:
                    self.expire()
                    return
                await asyncio.wait_for(send_if_current(), timeout=remaining)
                if isinstance(ticket, OperationTicket) and ticket._dispatch_future is not None:
                    with self._lock:
                        if self._operations.get(ticket.binding.op_id) is ticket:
                            self._deliver(ticket._dispatch_future, BrokerCompletion(ok=True))
            except BrowserBridgeBrokerError as exc:
                completion = _error(exc.code, "Browser dispatch authorization is unavailable", "not_applied")
                if isinstance(ticket, OperationTicket):
                    self._finish_operation(ticket, completion)
                else:
                    self._finish_control(ticket, completion)
            except asyncio.CancelledError:
                self._transport_failed(ticket)
                raise
            except Exception:
                self._transport_failed(ticket)

        loop = asyncio.get_running_loop()
        # Expiration survives cancellation of every caller waiting for a reply.
        # Successful send is not completion and must not leave a pending slot
        # occupied forever when the remote peer never returns a result.
        deadline = loop.call_later(
            max(0, ticket.deadline_ms - self._clock_ms()) / 1_000,
            self._expire_ticket, ticket,
        )
        ticket._future.add_done_callback(lambda _future: deadline.cancel())
        task = loop.create_task(dispatch())
        self._send_tasks.add(task)
        task.add_done_callback(self._send_finished)

    def _check_send_capacity_locked(self) -> None:
        if len(self._send_tasks) >= self._max_send_tasks:
            raise _rejected("INVALID_STATE", "Browser transport queue is full")

    def _send_finished(self, task: asyncio.Task[None]) -> None:
        with self._lock:
            self._send_tasks.discard(task)

    def _expire_ticket(self, ticket: OperationTicket | ControlTicket) -> None:
        completion = self._deadline_completion(ticket, operation=isinstance(ticket, OperationTicket))
        if isinstance(ticket, OperationTicket):
            self._finish_operation(ticket, completion)
        else:
            self._finish_control(ticket, completion)

    def _transport_failed(self, ticket: OperationTicket | ControlTicket) -> None:
        if isinstance(ticket, OperationTicket):
            completion = (
                _error(
                    "CONNECTION_LOST", "Browser bridge send failed",
                    "not_applied", retryable=True,
                )
                if ticket.effect == "read_only"
                else _error("OUTCOME_UNKNOWN", "Browser operation outcome is unknown", "unknown")
            )
            self._finish_operation(ticket, completion)
        else:
            self._finish_control(
                ticket,
                (
                    _error(
                        "CONNECTION_LOST",
                        "Browser reconciliation send failed",
                        "not_applied",
                        retryable=True,
                    )
                    if isinstance(ticket.binding, ReconciliationBinding)
                    else _error(
                        "OUTCOME_UNKNOWN",
                        "Browser control outcome is unknown",
                        "unknown",
                    )
                ),
            )

    def _finish_operation(
        self, ticket: OperationTicket, completion: BrokerCompletion
    ) -> bool:
        with self._lock:
            if self._operations.get(ticket.binding.op_id) is not ticket:
                return False
            self._remove_operation_locked(ticket)
        self._deliver(ticket._future, completion)
        return True

    def _finish_control(
        self, ticket: ControlTicket, completion: BrokerCompletion
    ) -> bool:
        with self._lock:
            if self._controls.get(ticket.binding.control_id) is not ticket:
                return False
            self._remove_control_locked(ticket)
        self._deliver(ticket._future, completion)
        return True

    def _remove_operation_locked(self, ticket: OperationTicket) -> None:
        if ticket._dispatch_future is not None:
            self._deliver(ticket._dispatch_future, _error("CONNECTION_LOST", "Operation retired before dispatch", "not_applied"))
        self._operations.pop(ticket.binding.op_id, None)
        self._action_identities.discard(self._action_identity(ticket.binding))
        self._remember(
            ticket.binding.op_id,
            self._completed_operations,
            self._completed_operation_set,
        )

    def _remove_control_locked(self, ticket: ControlTicket) -> None:
        self._controls.pop(ticket.binding.control_id, None)
        self._remember(
            ticket.binding.control_id,
            self._completed_controls,
            self._completed_control_set,
        )

    def _remember(self, value: str, queue: deque[str], values: set[str]) -> None:
        queue.append(value)
        values.add(value)
        while len(queue) > self._max_completed_ids:
            values.discard(queue.popleft())

    @staticmethod
    def _deliver(
        future: asyncio.Future[BrokerCompletion], completion: BrokerCompletion
    ) -> None:
        def set_result() -> None:
            if not future.done():
                future.set_result(completion)

        try:
            future.get_loop().call_soon_threadsafe(set_result)
        except RuntimeError:
            # Process shutdown can close the owning loop after the pending item
            # was removed. Never let that escape through an inbound handler.
            return

    def _authorize(
        self,
        binding: OperationBinding
        | TurnBinding
        | ControlBinding
        | ReconciliationBinding,
        *,
        scope: str,
        event: str,
        outer_feature: str,
    ) -> BridgeAuthorization:
        principal = binding.principal
        try:
            require_transport_principal_identity(
                principal, self._transport_profile
            )
        except ValueError:
            raise _rejected("SCOPE_DENIED", "Browser bridge scope is unavailable") from None
        if scope not in principal.scopes or not principal.permits_outbound(
            event, self._transport_profile.handler_id
        ):
            raise _rejected("SCOPE_DENIED", "Browser bridge scope is unavailable")
        try:
            authorization = self._authorizer(binding)
        except Exception:
            raise _rejected("SCOPE_DENIED", "Browser bridge authorization is unavailable") from None
        if (
            authorization is None
            or not isinstance(authorization, BridgeAuthorization)
            or authorization.principal is not principal
            or authorization.connector_sid != binding.connector_sid
            or authorization.load_generation_id != binding.load_generation_id
            or authorization.contract_version != CONTRACT_VERSION
            or outer_feature not in authorization.outer_features
        ):
            raise _rejected("SCOPE_DENIED", "Browser bridge authorization is stale")
        return authorization

    @staticmethod
    def _source_matches(
        binding: OperationBinding | ControlBinding | ReconciliationBinding,
        principal: WsPrincipal,
        connector_sid: str,
        load_generation_id: str,
    ) -> bool:
        return (
            binding.principal is principal
            and binding.connector_sid == connector_sid
            and binding.load_generation_id == load_generation_id
        )

    def _operation_result_matches(
        self,
        binding: OperationBinding,
        principal: WsPrincipal,
        connector_sid: str,
        load_generation_id: str,
        payload: dict[str, Any],
    ) -> bool:
        return self._source_matches(binding, principal, connector_sid, load_generation_id) and all(
            payload.get(key) == value
            for key, value in {
                "contract_version": CONTRACT_VERSION,
                "bridge_id": binding.bridge_id,
                "load_generation_id": binding.load_generation_id,
                "context_id": binding.context_id,
                "browser_session_id": binding.browser_session_id,
                "turn_id": binding.turn_id,
                "op_id": binding.op_id,
                "action_id": binding.action_id,
            }.items()
        )

    def _control_result_matches(
        self,
        binding: ControlBinding | ReconciliationBinding,
        principal: WsPrincipal,
        connector_sid: str,
        load_generation_id: str,
        payload: dict[str, Any],
    ) -> bool:
        if type(payload.get("contract_version")) is not int:
            return False
        expected: dict[str, Any] = {
            "contract_version": CONTRACT_VERSION,
            "method": (
                "browser.reconcile"
                if isinstance(binding, ReconciliationBinding)
                else binding.method
            ),
            "bridge_id": binding.bridge_id,
            "load_generation_id": binding.load_generation_id,
            "control_id": binding.control_id,
        }
        if isinstance(binding, ControlBinding):
            expected.update(
                context_id=binding.context_id,
                browser_session_id=binding.browser_session_id,
                turn_id=binding.turn_id,
            )
        if isinstance(binding, ControlBinding) and binding.method in {
            "browser.cancel",
            "browser.resolve_challenge",
        }:
            expected.update(op_id=binding.op_id, action_id=binding.action_id)
        return self._source_matches(binding, principal, connector_sid, load_generation_id) and all(
            payload.get(key) == value for key, value in expected.items()
        )

    @staticmethod
    def _action_identity(binding: OperationBinding) -> tuple[str, str, str, str]:
        return (
            binding.bridge_id,
            binding.context_id,
            binding.browser_session_id,
            binding.action_id,
        )

    @staticmethod
    def _validate_operation_binding(binding: OperationBinding) -> None:
        for name in (
            "connector_sid", "load_generation_id", "context_id",
            "browser_session_id", "turn_id", "action_id", "op_id",
        ):
            _identifier(getattr(binding, name), name)
        _native_identifier(binding.load_generation_id, "load_generation_id")
        _core_correlation_id(binding.op_id, "op_id")
        _validate_principal(binding.principal)

    @staticmethod
    def _validate_turn_binding(binding: TurnBinding) -> None:
        for name in (
            "connector_sid", "load_generation_id", "context_id",
            "browser_session_id", "turn_id",
        ):
            _identifier(getattr(binding, name), name)
        _native_identifier(binding.load_generation_id, "load_generation_id")
        _validate_principal(binding.principal)

    @staticmethod
    def _validate_reconciliation_binding(
        binding: ReconciliationBinding,
    ) -> None:
        for name in ("connector_sid", "load_generation_id", "control_id"):
            _identifier(getattr(binding, name), name)
        _native_identifier(binding.load_generation_id, "load_generation_id")
        _core_correlation_id(binding.control_id, "control_id")
        _validate_principal(binding.principal)


def _validate_principal(principal: WsPrincipal) -> None:
    try:
        transport_profile_for_principal_identity(principal)
    except ValueError:
        raise _rejected("SCOPE_DENIED", "A restricted bridge principal is required")
    _identifier(principal.principal_id, "bridge_id")


def _identifier(value: Any, name: str) -> str:
    if (
        not isinstance(value, str)
        or not value
        or len(value.encode("utf-8")) > MAX_IDENTIFIER_BYTES
        or any(ord(character) < 0x20 or ord(character) == 0x7F for character in value)
    ):
        raise _rejected("INVALID_STATE", f"Invalid {name}")
    return value


def _timeout(value: Any) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or not 1 <= value <= MAX_TIMEOUT_MS:
        raise _rejected("INVALID_STATE", "Invalid browser operation timeout")
    return value


def _core_correlation_id(value: Any, name: str) -> str:
    value = _identifier(value, name)
    if _CORE_CORRELATION_ID.fullmatch(value) is None:
        raise _rejected("INVALID_STATE", f"Invalid {name}")
    return value


def _native_identifier(value: Any, name: str) -> str:
    value = _identifier(value, name)
    if _NATIVE_IDENTIFIER.fullmatch(value) is None:
        raise _rejected("INVALID_STATE", f"Invalid {name}")
    return value


def _reason(value: Any) -> str:
    if (
        not isinstance(value, str)
        or not value
        or len(value.encode("utf-8")) > MAX_REASON_BYTES
        or any(ord(character) < 0x20 or ord(character) == 0x7F for character in value)
    ):
        raise _rejected("INVALID_STATE", "Invalid browser control reason")
    return value


def _capabilities(values: Any) -> tuple[str, ...]:
    if not isinstance(values, (tuple, list)) or len(values) > MAX_CAPABILITIES:
        raise _rejected("INVALID_STATE", "Invalid required capabilities")
    result: list[str] = []
    seen: set[str] = set()
    for value in values:
        if (
            not isinstance(value, str)
            or not value
            or len(value.encode("utf-8")) > MAX_CAPABILITY_BYTES
            or value in seen
        ):
            raise _rejected("INVALID_STATE", "Invalid required capabilities")
        seen.add(value)
        result.append(value)
    return tuple(result)


def _target(value: Mapping[str, Any] | None) -> dict[str, Any] | None:
    if value is None:
        return None
    if not isinstance(value, Mapping) or set(value) != {"tab_handle"}:
        raise _rejected("INVALID_STATE", "Invalid browser target")
    return {"tab_handle": _identifier(value["tab_handle"], "tab_handle")}


def _policy(value: Mapping[str, Any] | None) -> dict[str, str | None]:
    value = {} if value is None else value
    if not isinstance(value, Mapping) or not set(value) <= {"origin_grant_id", "action_grant_id"}:
        raise _rejected("INVALID_STATE", "Invalid browser policy")
    result: dict[str, str | None] = {}
    for key in ("origin_grant_id", "action_grant_id"):
        item = value.get(key)
        result[key] = None if item is None else _identifier(item, key)
    return result


def _display(value: Mapping[str, Any] | None) -> dict[str, bool]:
    value = {} if value is None else value
    if not isinstance(value, Mapping) or not set(value) <= {"cursor", "foreground"}:
        raise _rejected("INVALID_STATE", "Invalid browser display options")
    cursor = value.get("cursor", False)
    foreground = value.get("foreground", False)
    if not isinstance(cursor, bool) or not isinstance(foreground, bool):
        raise _rejected("INVALID_STATE", "Invalid browser display options")
    return {"cursor": cursor, "foreground": foreground}


def _dispositions(value: Mapping[str, str]) -> dict[str, str]:
    if not isinstance(value, Mapping) or len(value) > MAX_DISPOSITIONS:
        raise _rejected("INVALID_STATE", "Invalid browser lease dispositions")
    result: dict[str, str] = {}
    for lease_id, disposition in value.items():
        lease_id = _identifier(lease_id, "lease_id")
        if disposition not in _DISPOSITIONS:
            raise _rejected("INVALID_STATE", "Invalid browser lease disposition")
        result[lease_id] = disposition
    return result


def _reconciliation_expected_contexts(values: Any) -> list[dict[str, Any]]:
    if not isinstance(values, (tuple, list)) or len(values) > 128:
        raise _rejected("INVALID_STATE", "Invalid reconciliation contexts")
    result: list[dict[str, Any]] = []
    context_ids: set[str] = set()
    for value in values:
        if not isinstance(value, Mapping) or set(value) != {
            "context_id",
            "browser_session_id",
            "active_turn_ids",
        }:
            raise _rejected("INVALID_STATE", "Invalid reconciliation context")
        context_id = _identifier(value["context_id"], "context_id")
        browser_session_id = _identifier(
            value["browser_session_id"], "browser_session_id"
        )
        turns = value["active_turn_ids"]
        if not isinstance(turns, (tuple, list)) or len(turns) > 32:
            raise _rejected("INVALID_STATE", "Invalid reconciliation turns")
        active_turn_ids = [
            _identifier(turn, "turn_id") for turn in turns
        ]
        if (
            context_id in context_ids
            or len(set(active_turn_ids)) != len(active_turn_ids)
        ):
            raise _rejected("INVALID_STATE", "Duplicate reconciliation identity")
        context_ids.add(context_id)
        result.append(
            {
                "context_id": context_id,
                "browser_session_id": browser_session_id,
                "active_turn_ids": active_turn_ids,
            }
        )
    return result


def _reconciliation_event_cursors(values: Any) -> list[dict[str, Any]]:
    if not isinstance(values, (tuple, list)) or len(values) > 16:
        raise _rejected("INVALID_STATE", "Invalid reconciliation cursors")
    result: list[dict[str, Any]] = []
    generations: set[str] = set()
    for value in values:
        if not isinstance(value, Mapping) or set(value) != {
            "load_generation_id",
            "last_acked_event_sequence",
        }:
            raise _rejected("INVALID_STATE", "Invalid reconciliation cursor")
        generation = _native_identifier(
            value["load_generation_id"], "load_generation_id"
        )
        sequence = value["last_acked_event_sequence"]
        if (
            generation in generations
            or isinstance(sequence, bool)
            or not isinstance(sequence, int)
            or not 0 <= sequence <= 2**53 - 1
        ):
            raise _rejected("INVALID_STATE", "Invalid reconciliation cursor")
        generations.add(generation)
        result.append(
            {
                "load_generation_id": generation,
                "last_acked_event_sequence": sequence,
            }
        )
    return result


def _reconciliation_control_ids(values: Any) -> list[str]:
    if not isinstance(values, (tuple, list)) or len(values) > 2_048:
        raise _rejected("INVALID_STATE", "Invalid reconciliation controls")
    result = [_identifier(value, "control_id") for value in values]
    if len(set(result)) != len(result):
        raise _rejected("INVALID_STATE", "Duplicate reconciliation control")
    return result


def _mapping_copy(value: Mapping[str, Any], name: str) -> dict[str, Any]:
    if not isinstance(value, Mapping):
        raise _rejected("INVALID_STATE", f"Invalid browser {name}")
    return _bounded_json_copy(dict(value))


def _bounded_json_copy(value: Any) -> Any:
    try:
        _validate_json_tree(value)
        encoded = json.dumps(
            value, ensure_ascii=False, allow_nan=False, separators=(",", ":")
        ).encode("utf-8")
    except (TypeError, ValueError, OverflowError, RecursionError):
        raise _rejected("INVALID_STATE", "Browser payload is not canonical JSON") from None
    if len(encoded) > MAX_NON_ARTIFACT_BYTES:
        raise _rejected("INVALID_STATE", "Browser payload exceeds the bounded frame")
    return json.loads(encoded)


def _validate_json_tree(value: Any) -> None:
    nodes = 0

    def visit(item: Any, depth: int) -> None:
        nonlocal nodes
        nodes += 1
        if nodes > MAX_JSON_NODES or depth > MAX_JSON_DEPTH:
            raise ValueError("JSON tree exceeds broker bounds")
        if item is None or isinstance(item, (bool, str, int)):
            return
        if isinstance(item, float):
            if not math.isfinite(item):
                raise ValueError("JSON number must be finite")
            return
        if isinstance(item, dict):
            for key, child in item.items():
                if (
                    not isinstance(key, str)
                    or not key
                    or len(key.encode("utf-8")) > MAX_IDENTIFIER_BYTES
                    or any(ord(character) < 0x20 or ord(character) == 0x7F for character in key)
                ):
                    raise ValueError("JSON object key is invalid")
                visit(child, depth + 1)
            return
        if isinstance(item, list):
            for child in item:
                visit(child, depth + 1)
            return
        raise TypeError("Value is not JSON")

    visit(value, 0)


def _incoming_mapping(value: Mapping[str, Any]) -> dict[str, Any] | None:
    if not isinstance(value, Mapping):
        return None
    try:
        return _bounded_json_copy(dict(value))
    except BrowserBridgeBrokerError:
        return None


def _parse_operation_completion(payload: dict[str, Any]) -> BrokerCompletion | None:
    common = {
        "contract_version", "bridge_id", "load_generation_id", "context_id",
        "browser_session_id", "turn_id", "op_id", "action_id", "ok",
    }
    if payload.get("ok") is True:
        if set(payload) != common | {"result", "receipts", "artifacts"}:
            return None
        if not isinstance(payload.get("result"), dict):
            return None
        receipts = payload.get("receipts")
        artifacts = payload.get("artifacts")
        if not isinstance(receipts, list) or not isinstance(artifacts, list):
            return None
        return BrokerCompletion(
            ok=True,
            result=_bounded_json_copy(payload["result"]),
            receipts=tuple(_bounded_json_copy(receipts)),
            artifacts=tuple(_bounded_json_copy(artifacts)),
        )
    if payload.get("ok") is False and set(payload) == common | {"code", "error", "error_data"}:
        return _parse_error(payload)
    return None


def _parse_control_completion(payload: dict[str, Any]) -> BrokerCompletion | None:
    common = {
        "contract_version",
        "method",
        "bridge_id",
        "load_generation_id",
        "control_id",
        "ok",
    }
    if payload.get("method") != "browser.reconcile":
        common |= {"context_id", "browser_session_id", "turn_id"}
    if payload.get("method") in {"browser.cancel", "browser.resolve_challenge"}:
        common |= {"op_id", "action_id"}
    if payload.get("ok") is True and set(payload) == common | {"result"}:
        if not isinstance(payload.get("result"), dict):
            return None
        return BrokerCompletion(ok=True, result=_bounded_json_copy(payload["result"]))
    if payload.get("ok") is False and set(payload) == common | {"code", "error", "error_data"}:
        return _parse_error(payload)
    return None


def _parse_error(payload: dict[str, Any]) -> BrokerCompletion | None:
    code = payload.get("code")
    error = payload.get("error")
    data = payload.get("error_data")
    if (
        not isinstance(code, str)
        or _ERROR_CODE.fullmatch(code) is None
        or not isinstance(error, str)
        or not error
        or len(error.encode("utf-8")) > 2_048
        or not isinstance(data, dict)
        or data.get("outcome") not in _OUTCOMES
        or not isinstance(data.get("retryable"), bool)
        or not isinstance(data.get("details", {}), dict)
    ):
        return None
    return BrokerCompletion(
        ok=False,
        code=code,
        error=error,
        outcome=data["outcome"],
        retryable=data["retryable"],
        details=_bounded_json_copy(data.get("details", {})),
    )


def _error(
    code: str, message: str, outcome: str, *, retryable: bool = False
) -> BrokerCompletion:
    return BrokerCompletion(
        ok=False, code=code, error=message, outcome=outcome, retryable=retryable
    )


def _rejected(code: str, message: str) -> BrowserBridgeBrokerError:
    return BrowserBridgeBrokerError(code, message)


def _operation_parameter_hash(binding, action, target, args, display) -> str | None:
    if not target or set(target) != {"tab_handle"}:
        return None
    if action == "navigate":
        valid_args = set(args) == {"url"} and isinstance(args["url"], str)
    elif action == "click":
        valid_args = (
            set(args) == {"ref", "expected_action_class"}
            and _valid_click_ref(args["ref"])
            and isinstance(args["expected_action_class"], str)
            and args["expected_action_class"] in _ACTION_CHALLENGE_CLASSES
        )
    elif action == "type":
        valid_args = _type_text_digest(args) is not None
    elif action == "upload_file":
        valid_args = _valid_upload_args(args)
    else:
        return None
    if not valid_args:
        return None
    # Matches the extension's parsed (camelCase target) stable JSON, not the
    # transport-only bridge/load fields or policy receipt identifiers.
    value = {"action": action, "target": {"tabHandle": target["tab_handle"]},
             "context_id": binding.context_id, "browser_session_id": binding.browser_session_id,
             "turn_id": binding.turn_id, "args": args, "display": display}
    encoded = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(encoded.encode("utf-8")).hexdigest()


def _operation_intent_matches(
    ticket: OperationTicket, payload: dict[str, Any]
) -> bool:
    if ticket.action not in {"navigate", "click", "type", "upload_file"}:
        return True
    target = payload.get("target")
    if (
        payload.get("action") != ticket.action
        or not isinstance(target, dict)
        or target != {"tab_handle": ticket.target_tab_handle}
    ):
        return False
    try:
        parameter_hash = _operation_parameter_hash(
            ticket.binding,
            ticket.action,
            target,
            payload.get("args"),
            payload.get("display"),
        )
    except Exception:
        return False
    if parameter_hash != ticket.canonical_parameter_hash:
        return False
    args = payload.get("args")
    if not isinstance(args, dict):
        return False
    if ticket.action == "navigate":
        return True
    if (
        args.get("ref") != ticket.target_ref
        or args.get("expected_action_class") != ticket.expected_action_class
    ):
        return False
    if ticket.action in {"click", "upload_file"}:
        return ticket.text_sha256 is None
    return _type_text_digest(args) == ticket.text_sha256


def _valid_upload_args(args: Any) -> bool:
    return (
        isinstance(args, dict)
        and set(args) == {"ref", "expected_action_class", "artifact_id", "mime_type", "byte_count", "sha256"}
        and _valid_click_ref(args["ref"])
        and args["expected_action_class"] == "external_side_effect"
        and isinstance(args["artifact_id"], str)
        and re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9._:-]{0,255}", args["artifact_id"]) is not None
        and isinstance(args["mime_type"], str) and len(args["mime_type"]) <= 255
        and re.fullmatch(r"[a-z0-9!#$&^_.+-]+/[a-z0-9!#$&^_.+-]+", args["mime_type"]) is not None
        and type(args["byte_count"]) is int and 1 <= args["byte_count"] <= 25 * 1024 * 1024
        and isinstance(args["sha256"], str)
        and re.fullmatch(r"sha256:[a-f0-9]{64}", args["sha256"]) is not None
    )


def _type_text_digest(args: Any) -> str | None:
    if not isinstance(args, dict) or set(args) != {
        "ref",
        "text",
        "text_sha256",
        "expected_action_class",
    }:
        return None
    if (
        not _valid_click_ref(args["ref"])
        or args["expected_action_class"] != "sensitive_input"
        or not isinstance(args["text_sha256"], str)
        or re.fullmatch(r"[a-f0-9]{64}", args["text_sha256"]) is None
        or not isinstance(args["text"], str)
        or "\x00" in args["text"]
        or "\r" in args["text"]
    ):
        return None
    try:
        encoded = args["text"].encode("utf-8")
    except UnicodeError:
        return None
    if not 1 <= len(encoded) <= 32_768:
        return None
    digest = hashlib.sha256(encoded).hexdigest()
    return digest if digest == args["text_sha256"] else None


def _valid_click_ref(value: Any) -> bool:
    try:
        return bool(
            isinstance(value, str)
            and value
            and len(value.encode("utf-8")) <= 128
            and _NATIVE_IDENTIFIER.fullmatch(value) is not None
        )
    except UnicodeError:
        return False


def _navigation_origin(action, args) -> str | None:
    if action != "navigate" or not isinstance(args.get("url"), str):
        return None
    from urllib.parse import urlsplit, urlunsplit
    from plugins._a0_connector.helpers.browser_bridge_policy import normalize_site_origin
    try:
        url = urlsplit(args["url"])
        return normalize_site_origin(urlunsplit((url.scheme, url.netloc, "", "", "")))
    except Exception:
        return None
