"""Strict, nonactivating Browser bridge reconciliation prerequisite.

This controller can prove that an exact provisional transport returned one
bounded reconciliation snapshot.  It does not create a runtime principal,
admit a route, select a browser, persist peer lease claims, or apply/ACK events.
The injected promoter is the only composition seam and must atomically compare
and promote the exact current route.
"""

from __future__ import annotations

import asyncio
from dataclasses import dataclass
import re
import threading
from typing import Any, Callable, Mapping

from plugins._a0_connector.helpers.browser_bridge_context import (
    BrowserBridgeContextRoute,
)
from plugins._a0_connector.helpers.browser_bridge_events import (
    validate_reconciliation_critical_event,
)
from plugins._a0_connector.helpers.browser_bridge_operations import (
    BrokerCompletion,
    BrowserBridgeBrokerError,
    BrowserBridgeOperationBroker,
    ReconciliationBinding,
)
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


CONTRACT_VERSION = 1
NEGOTIATED_MAX_JSON_FRAME_BYTES = 786_432
ACTUAL_NON_ARTIFACT_PACKET_BYTES = 512 * 1024
DEFAULT_TIMEOUT_MS = 10_000
MAX_ACTIVE_RECONCILIATIONS = 32

_OPAQUE_ID = re.compile(r"[A-Za-z0-9][A-Za-z0-9._:-]{0,255}")
_DIGEST = re.compile(r"[a-f0-9]{64}")
_ERROR_CODE = re.compile(r"[A-Z][A-Z0-9_]{0,63}")
_LEASE_ORIGINS = frozenset({"created", "claimed"})
_LEASE_DISPOSITIONS = frozenset({"ephemeral", "deliverable", "handoff"})
_LEASE_STATES = frozenset(
    {
        "active",
        "finalizing",
        "closed",
        "released",
        "retained",
        "outcome_unknown",
        "orphan",
    }
)
_TAKEOVER_REASONS = frozenset(
    {
        "moved",
        "pinned",
        "unpinned",
        "ungrouped",
        "regrouped",
        "shared_group",
        "window_changed",
        "other",
    }
)
_RETENTION_REASONS = frozenset(
    {
        "user_takeover",
        "claimed_tab",
        "non_ephemeral",
        "generation_mismatch",
        "handle_mismatch",
        "context_mismatch",
        "browser_session_mismatch",
        "turn_mismatch",
        "control_mismatch",
        "identity_mismatch",
        "tab_missing",
        "protected",
        "ambiguous",
        "unresolved_reconciliation",
        "not_active",
        "outcome_unknown",
    }
)
_NONTERMINAL_STAGES = frozenset(
    {"prepared", "waiting_approval", "effect_started"}
)
_TERMINAL_STAGES = frozenset(
    {"succeeded", "failed", "canceled", "outcome_unknown"}
)
_MUTATION_OUTCOMES = frozenset({"not_applied", "applied", "unknown"})


class BrowserBridgeReconciliationError(RuntimeError):
    """A reconciliation attempt was rejected without exposing peer data."""

    def __init__(self, code: str) -> None:
        super().__init__(code)
        self.code = code


@dataclass(frozen=True, slots=True)
class ExpectedReconciliationContext:
    context_id: str
    browser_session_id: str
    active_turn_ids: tuple[str, ...]

    def as_wire_dict(self) -> dict[str, Any]:
        if not isinstance(self.active_turn_ids, tuple):
            raise BrowserBridgeReconciliationError("RECONCILE_REQUEST_INVALID")
        turns = tuple(_identifier(item) for item in self.active_turn_ids)
        if len(turns) > 32 or len(set(turns)) != len(turns):
            raise BrowserBridgeReconciliationError("RECONCILE_REQUEST_INVALID")
        return {
            "context_id": _identifier(self.context_id),
            "browser_session_id": _identifier(self.browser_session_id),
            "active_turn_ids": list(turns),
        }


@dataclass(frozen=True, slots=True)
class ReconciliationEventCursor:
    load_generation_id: str
    last_acked_event_sequence: int

    def as_wire_dict(self) -> dict[str, Any]:
        return {
            "load_generation_id": _identifier(self.load_generation_id),
            "last_acked_event_sequence": _safe_integer(
                self.last_acked_event_sequence
            ),
        }


@dataclass(frozen=True, slots=True)
class ReconciliationSnapshot:
    expected_contexts: tuple[ExpectedReconciliationContext, ...] = ()
    event_cursors: tuple[ReconciliationEventCursor, ...] = ()
    known_control_ids: tuple[str, ...] = ()

    def as_wire_parts(
        self,
    ) -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[str]]:
        if (
            not isinstance(self.expected_contexts, tuple)
            or not isinstance(self.event_cursors, tuple)
            or not isinstance(self.known_control_ids, tuple)
            or
            len(self.expected_contexts) > 128
            or len(self.event_cursors) > 16
            or len(self.known_control_ids) > 2_048
            or not all(
                isinstance(value, ExpectedReconciliationContext)
                for value in self.expected_contexts
            )
            or not all(
                isinstance(value, ReconciliationEventCursor)
                for value in self.event_cursors
            )
        ):
            raise BrowserBridgeReconciliationError("RECONCILE_REQUEST_INVALID")
        contexts = [value.as_wire_dict() for value in self.expected_contexts]
        cursors = [value.as_wire_dict() for value in self.event_cursors]
        controls = [_identifier(value) for value in self.known_control_ids]
        if (
            len({value["context_id"] for value in contexts}) != len(contexts)
            or len({value["load_generation_id"] for value in cursors})
            != len(cursors)
            or len(set(controls)) != len(controls)
        ):
            raise BrowserBridgeReconciliationError("RECONCILE_REQUEST_INVALID")
        return contexts, cursors, controls


@dataclass(frozen=True, slots=True)
class BrowserBridgeReconciliationSummary:
    """Only non-authoritative counts retained from the peer snapshot."""

    lease_count: int
    inflight_operation_count: int
    terminal_receipt_count: int
    pending_critical_event_count: int
    prior_generation_orphan_count: int

    def as_wire_dict(self) -> dict[str, int]:
        return {
            "contract_version": CONTRACT_VERSION,
            "lease_count": self.lease_count,
            "inflight_operation_count": self.inflight_operation_count,
            "terminal_receipt_count": self.terminal_receipt_count,
            "pending_critical_event_count": self.pending_critical_event_count,
            "prior_generation_orphan_count": self.prior_generation_orphan_count,
        }


SnapshotSource = Callable[[ReconciliationBinding], ReconciliationSnapshot]
RouteCurrent = Callable[[ReconciliationBinding], bool]
RoutePromoter = Callable[
    [ReconciliationBinding, BrowserBridgeReconciliationSummary], bool
]


class BrowserBridgeReconciliationController:
    """Own bounded reconcile tasks for exact provisional transport routes.

    ``route_current`` means the exact binding is live in either provisional or
    promoted state.  ``promote`` must synchronously compare-and-promote that
    route without blocking or awaiting.  Composition must use a consistent lock
    order because promotion runs while the broker holds its settlement lock.
    Route retirement remains an owner responsibility and must also disconnect
    the broker ticket; this helper never invents lifecycle authority.
    """

    def __init__(
        self,
        *,
        broker: BrowserBridgeOperationBroker,
        snapshot_source: SnapshotSource,
        route_current: RouteCurrent,
        promote: RoutePromoter,
        transport_profile: BrowserBridgeTransportProfile = (
            PRODUCTION_BROWSER_BRIDGE_TRANSPORT
        ),
        timeout_ms: int = DEFAULT_TIMEOUT_MS,
        max_active: int = MAX_ACTIVE_RECONCILIATIONS,
    ) -> None:
        self._transport_profile = require_browser_bridge_transport_profile(
            transport_profile
        )
        if broker.transport_profile is not self._transport_profile:
            raise BrowserBridgeReconciliationError("TRANSPORT_PROFILE_MISMATCH")
        if not callable(snapshot_source) or not callable(route_current) or not callable(promote):
            raise BrowserBridgeReconciliationError("RECONCILIATION_UNAVAILABLE")
        if (
            isinstance(timeout_ms, bool)
            or not isinstance(timeout_ms, int)
            or not 1 <= timeout_ms <= 120_000
            or isinstance(max_active, bool)
            or not isinstance(max_active, int)
            or not 1 <= max_active <= MAX_ACTIVE_RECONCILIATIONS
        ):
            raise BrowserBridgeReconciliationError("RECONCILIATION_INVALID")
        self._broker = broker
        self._snapshot_source = snapshot_source
        self._route_current = route_current
        self._promote = promote
        self._timeout_ms = timeout_ms
        self._max_active = max_active
        self._active: dict[
            tuple[int, str, str], asyncio.Task[BrowserBridgeReconciliationSummary]
        ] = {}
        self._lock = threading.RLock()

    def start(
        self,
        binding: ReconciliationBinding,
        *,
        expected_install_instance_id: str,
    ) -> asyncio.Task[BrowserBridgeReconciliationSummary]:
        """Start a controller-owned task that survives caller cancellation."""

        self._validate_binding(binding)
        expected_install_instance_id = _identifier(expected_install_instance_id)
        self._require_current(binding)
        key = self._route_key(binding)
        with self._lock:
            if key in self._active:
                raise BrowserBridgeReconciliationError(
                    "RECONCILIATION_IN_PROGRESS"
                )
            if len(self._active) >= self._max_active:
                raise BrowserBridgeReconciliationError(
                    "RECONCILIATION_CAPACITY"
                )
            task = asyncio.get_running_loop().create_task(
                self._run(binding, expected_install_instance_id)
            )
            self._active[key] = task
            task.add_done_callback(
                lambda completed, route_key=key: self._finished(
                    route_key, completed
                )
            )
            return task

    async def reconcile(
        self,
        binding: ReconciliationBinding,
        *,
        expected_install_instance_id: str,
    ) -> BrowserBridgeReconciliationSummary:
        return await asyncio.shield(
            self.start(
                binding,
                expected_install_instance_id=expected_install_instance_id,
            )
        )

    async def _run(
        self,
        binding: ReconciliationBinding,
        expected_install_instance_id: str,
    ) -> BrowserBridgeReconciliationSummary:
        self._require_current(binding, "RECONCILIATION_START_SCOPE_LOST")
        try:
            snapshot = self._snapshot_source(binding)
        except BrowserBridgeReconciliationError:
            raise
        except Exception:
            raise BrowserBridgeReconciliationError(
                "RECONCILIATION_UNAVAILABLE"
            ) from None
        if not isinstance(snapshot, ReconciliationSnapshot):
            raise BrowserBridgeReconciliationError("RECONCILE_REQUEST_INVALID")
        contexts, cursors, controls = snapshot.as_wire_parts()
        self._require_current(binding, "RECONCILIATION_SNAPSHOT_SCOPE_LOST")

        def accept(
            completion: BrokerCompletion,
        ) -> BrokerCompletion | None:
            if not completion.ok:
                return completion
            if not self._is_current(binding):
                return _denied_completion()
            try:
                summary = parse_browser_reconcile_result(
                    completion.result,
                    binding=binding,
                    expected_install_instance_id=expected_install_instance_id,
                    transport_profile=self._transport_profile,
                )
            except BrowserBridgeReconciliationError:
                return None
            if not self._is_current(binding):
                return _denied_completion()
            # This callback must atomically compare and promote the exact route.
            # It is intentionally synchronous and runs in broker settlement
            # before the future is resolved or the next FIFO event can rely on
            # the route.
            try:
                promoted = self._promote(binding, summary) is True
            except Exception:
                promoted = False
            if not promoted or not self._is_current(binding):
                return _denied_completion()
            return BrokerCompletion(ok=True, result=summary.as_wire_dict())

        try:
            ticket = await self._broker.begin_reconcile(
                binding,
                expected_contexts=contexts,
                event_cursors=cursors,
                known_control_ids=controls,
                timeout_ms=self._timeout_ms,
                dispatch_preflight=lambda: self._is_current(binding),
                settlement_acceptor=accept,
            )
        except BrowserBridgeBrokerError as exc:
            if exc.code == "SCOPE_DENIED":
                from plugins._a0_connector.helpers.browser_bridge_application import record_production_browser_stage
                record_production_browser_stage("RECONCILIATION_BROKER_SCOPE_LOST")
            raise BrowserBridgeReconciliationError(exc.code) from None
        self._require_current(binding, "RECONCILIATION_PENDING_SCOPE_LOST")
        completion = await self._broker.wait_control(ticket)
        if not completion.ok:
            # Disconnect removes route authority before resolving this future.
            # Preserve its typed failure instead of masking it as scope loss;
            # a negative completion cannot promote or replay anything.
            raise BrowserBridgeReconciliationError(
                completion.code or "RECONCILIATION_FAILED"
            )
        self._require_current(binding, "RECONCILIATION_SETTLEMENT_SCOPE_LOST")
        return _summary_from_wire(completion.result)

    def _validate_binding(self, binding: ReconciliationBinding) -> None:
        if not isinstance(binding, ReconciliationBinding):
            raise BrowserBridgeReconciliationError("RECONCILIATION_INVALID")
        try:
            if binding.transport_profile is not self._transport_profile:
                raise ValueError("transport profile mismatch")
            require_transport_principal_identity(
                binding.principal, self._transport_profile
            )
            _identifier(binding.principal.principal_id)
            _identifier(binding.principal.subject_id)
            if (
                type(binding.principal.key_generation) is not int
                or binding.principal.key_generation < 1
            ):
                raise ValueError("invalid key generation")
            _identifier(binding.connector_sid)
            _identifier(binding.load_generation_id)
            _identifier(binding.control_id)
        except (ValueError, BrowserBridgeReconciliationError):
            raise BrowserBridgeReconciliationError("SCOPE_DENIED") from None

    def _is_current(self, binding: ReconciliationBinding) -> bool:
        try:
            return self._route_current(binding) is True
        except Exception:
            return False

    def _require_current(self, binding: ReconciliationBinding, stage=None) -> None:
        if not self._is_current(binding):
            if stage is not None:
                from plugins._a0_connector.helpers.browser_bridge_application import record_production_browser_stage
                record_production_browser_stage(stage)
            raise BrowserBridgeReconciliationError("SCOPE_DENIED")

    @staticmethod
    def _route_key(binding: ReconciliationBinding) -> tuple[int, str, str]:
        return (
            id(binding.principal),
            binding.connector_sid,
            binding.load_generation_id,
        )

    def _finished(
        self,
        key: tuple[int, str, str],
        task: asyncio.Task[BrowserBridgeReconciliationSummary],
    ) -> None:
        with self._lock:
            if self._active.get(key) is task:
                self._active.pop(key, None)
        # A shielded caller may be canceled while this process-owned task keeps
        # running.  Retrieve its terminal exception so asyncio never reports an
        # unobserved background failure; later awaits still receive it.
        try:
            task.exception()
        except asyncio.CancelledError:
            pass


def parse_browser_reconcile_result(
    value: Any,
    *,
    binding: ReconciliationBinding,
    expected_install_instance_id: str,
    transport_profile: BrowserBridgeTransportProfile = (
        PRODUCTION_BROWSER_BRIDGE_TRANSPORT
    ),
) -> BrowserBridgeReconciliationSummary:
    """Strictly validate the full extension result, retaining counts only."""

    profile = require_browser_bridge_transport_profile(transport_profile)
    try:
        if binding.transport_profile is not profile:
            raise ValueError("transport profile mismatch")
        require_transport_principal_identity(binding.principal, profile)
        _identifier(binding.principal.principal_id)
        _identifier(binding.principal.subject_id)
        _identifier(binding.connector_sid)
        _identifier(binding.load_generation_id)
        _identifier(binding.control_id)
        if (
            type(binding.principal.key_generation) is not int
            or binding.principal.key_generation < 1
        ):
            raise ValueError("invalid key generation")
    except (ValueError, BrowserBridgeReconciliationError):
        raise BrowserBridgeReconciliationError("SCOPE_DENIED") from None
    result = _record(
        value,
        {
            "contract_version",
            "control_id",
            "install_instance_id",
            "load_generation_id",
            "leases",
            "inflight_operations",
            "terminal_action_receipts",
            "pending_critical_events",
            "prior_generation_orphans",
        },
    )
    if (
        type(result["contract_version"]) is not int
        or result["contract_version"] != CONTRACT_VERSION
        or _identifier(result["control_id"]) != binding.control_id
        or _identifier(result["install_instance_id"])
        != _identifier(expected_install_instance_id)
        or _identifier(result["load_generation_id"])
        != binding.load_generation_id
    ):
        raise BrowserBridgeReconciliationError("RECONCILE_RESULT_INVALID")

    leases = _array(result["leases"], 512)
    inflight = _array(result["inflight_operations"], 256)
    receipts = _array(result["terminal_action_receipts"], 2_048)
    pending_events = _array(result["pending_critical_events"], 1_024)
    orphans = _array(result["prior_generation_orphans"], 512)

    lease_ids: set[str] = set()
    tab_handles: set[str] = set()
    for item in leases:
        lease_id, tab_handle, generation = _validate_lease(item)
        if (
            generation != binding.load_generation_id
            or lease_id in lease_ids
            or tab_handle in tab_handles
        ):
            raise BrowserBridgeReconciliationError("RECONCILE_RESULT_INVALID")
        lease_ids.add(lease_id)
        tab_handles.add(tab_handle)

    inflight_ids: set[str] = set()
    for item in inflight:
        action_id = _validate_inflight(item)
        if action_id in inflight_ids:
            raise BrowserBridgeReconciliationError("RECONCILE_RESULT_INVALID")
        inflight_ids.add(action_id)

    receipt_ids: set[str] = set()
    for item in receipts:
        action_id = _validate_receipt(item)
        if action_id in receipt_ids:
            raise BrowserBridgeReconciliationError("RECONCILE_RESULT_INVALID")
        receipt_ids.add(action_id)

    event_identities: set[tuple[str, int]] = set()
    for item in pending_events:
        try:
            event_generation = _identifier(
                item.get("load_generation_id")
                if isinstance(item, Mapping)
                else None
            )
            route = BrowserBridgeContextRoute(
                binding.principal,
                binding.connector_sid,
                event_generation,
                transport_profile=profile,
            )
            identity = validate_reconciliation_critical_event(
                route, item, transport_profile=profile
            )
        except Exception:
            raise BrowserBridgeReconciliationError(
                "RECONCILE_RESULT_INVALID"
            ) from None
        key = (identity.load_generation_id, identity.event_sequence)
        if key in event_identities:
            raise BrowserBridgeReconciliationError("RECONCILE_RESULT_INVALID")
        event_identities.add(key)

    orphan_digests: set[str] = set()
    for item in orphans:
        generation, digest = _validate_orphan(item)
        if generation == binding.load_generation_id or digest in orphan_digests:
            raise BrowserBridgeReconciliationError("RECONCILE_RESULT_INVALID")
        orphan_digests.add(digest)

    return BrowserBridgeReconciliationSummary(
        lease_count=len(leases),
        inflight_operation_count=len(inflight),
        terminal_receipt_count=len(receipts),
        pending_critical_event_count=len(pending_events),
        prior_generation_orphan_count=len(orphans),
    )


def _validate_lease(value: Any) -> tuple[str, str, str]:
    item = _record(
        value,
        {
            "lease_id",
            "tab_handle",
            "load_generation_id",
            "context_id",
            "browser_session_id",
            "turn_id",
            "origin",
            "disposition",
            "state",
            "site_origin",
            "identity",
            "group_intent_id",
            "provider_group_id",
            "finalization_control_id",
            "user_intervened",
            "user_takeover_reason",
            "is_protected",
            "is_ambiguous",
            "unresolved_reconciliation",
            "overlay_attached",
            "debugger_attached",
            "retention_reason",
            "revision",
        },
    )
    lease_id = _identifier(item["lease_id"])
    tab_handle = _identifier(item["tab_handle"])
    generation = _identifier(item["load_generation_id"])
    for name in ("context_id", "browser_session_id", "turn_id"):
        _identifier(item[name])
    _enum(item["origin"], _LEASE_ORIGINS)
    _enum(item["disposition"], _LEASE_DISPOSITIONS)
    _enum(item["state"], _LEASE_STATES)
    _origin(item["site_origin"])
    identity = _record(
        item["identity"],
        {
            "browser_instance_id",
            "provider_tab_id",
            "provider_window_id",
            "document_id",
            "document_epoch",
        },
    )
    _identifier(identity["browser_instance_id"])
    _safe_integer(identity["provider_tab_id"])
    _safe_integer(identity["provider_window_id"])
    _nullable_identifier(identity["document_id"])
    _safe_integer(identity["document_epoch"])
    _nullable_identifier(item["group_intent_id"])
    _nullable_safe_integer(item["provider_group_id"])
    _nullable_identifier(item["finalization_control_id"])
    _boolean(item["user_intervened"])
    _nullable_enum(item["user_takeover_reason"], _TAKEOVER_REASONS)
    for name in (
        "is_protected",
        "is_ambiguous",
        "unresolved_reconciliation",
        "overlay_attached",
        "debugger_attached",
    ):
        _boolean(item[name])
    _nullable_enum(item["retention_reason"], _RETENTION_REASONS)
    _safe_integer(item["revision"])
    return lease_id, tab_handle, generation


def _validate_inflight(value: Any) -> str:
    item = _record(
        value,
        {
            "load_generation_id",
            "action_id",
            "kind",
            "canonical_parameter_hash",
            "stage",
            "created_at_ms",
            "updated_at_ms",
        },
    )
    _identifier(item["load_generation_id"])
    action_id = _identifier(item["action_id"])
    _bounded_text(item["kind"], 128)
    _digest(item["canonical_parameter_hash"])
    _enum(item["stage"], _NONTERMINAL_STAGES)
    _safe_integer(item["created_at_ms"])
    _safe_integer(item["updated_at_ms"])
    return action_id


def _validate_receipt(value: Any) -> str:
    item = _record(
        value,
        {
            "load_generation_id",
            "action_id",
            "kind",
            "canonical_parameter_hash",
            "stage",
            "safe_receipt",
            "created_at_ms",
            "updated_at_ms",
            "acknowledged_at_ms",
        },
    )
    _identifier(item["load_generation_id"])
    action_id = _identifier(item["action_id"])
    _bounded_text(item["kind"], 128)
    _digest(item["canonical_parameter_hash"])
    _enum(item["stage"], _TERMINAL_STAGES)
    receipt = _record(
        item["safe_receipt"],
        {"outcome", "code", "lease_handle_digest"},
    )
    _enum(receipt["outcome"], _MUTATION_OUTCOMES)
    if receipt["code"] is not None and (
        not isinstance(receipt["code"], str)
        or _ERROR_CODE.fullmatch(receipt["code"]) is None
    ):
        raise BrowserBridgeReconciliationError("RECONCILE_RESULT_INVALID")
    if receipt["lease_handle_digest"] is not None:
        _digest(receipt["lease_handle_digest"])
    _safe_integer(item["created_at_ms"])
    _safe_integer(item["updated_at_ms"])
    _nullable_safe_integer(item["acknowledged_at_ms"])
    return action_id


def _validate_orphan(value: Any) -> tuple[str, str]:
    item = _record(
        value,
        {
            "load_generation_id",
            "lease_handle_digest",
            "exact_identity_digest",
            "browser_instance_id",
            "provider_tab_id",
            "provider_window_id",
            "provider_group_id",
            "context_id",
            "browser_session_id",
            "turn_id",
            "origin",
            "disposition",
            "state",
            "url_identity",
            "user_intervened",
            "finalization_control_id",
            "retention_reason",
            "updated_at_ms",
        },
    )
    generation = _identifier(item["load_generation_id"])
    digest = _digest(item["lease_handle_digest"])
    _digest(item["exact_identity_digest"])
    _identifier(item["browser_instance_id"])
    _safe_integer(item["provider_tab_id"])
    _safe_integer(item["provider_window_id"])
    _nullable_safe_integer(item["provider_group_id"])
    for name in ("context_id", "browser_session_id", "turn_id"):
        _identifier(item[name])
    _enum(item["origin"], _LEASE_ORIGINS)
    _enum(item["disposition"], _LEASE_DISPOSITIONS)
    if item["state"] != "orphan":
        raise BrowserBridgeReconciliationError("RECONCILE_RESULT_INVALID")
    url_identity = _record(item["url_identity"], {"origin", "path_digest"})
    _origin(url_identity["origin"])
    _digest(url_identity["path_digest"])
    _boolean(item["user_intervened"])
    _nullable_identifier(item["finalization_control_id"])
    _nullable_enum(item["retention_reason"], _RETENTION_REASONS)
    _safe_integer(item["updated_at_ms"])
    return generation, digest


def _summary_from_wire(value: Any) -> BrowserBridgeReconciliationSummary:
    item = _record(
        value,
        {
            "contract_version",
            "lease_count",
            "inflight_operation_count",
            "terminal_receipt_count",
            "pending_critical_event_count",
            "prior_generation_orphan_count",
        },
    )
    if (
        type(item["contract_version"]) is not int
        or item["contract_version"] != CONTRACT_VERSION
    ):
        raise BrowserBridgeReconciliationError("RECONCILIATION_FAILED")
    return BrowserBridgeReconciliationSummary(
        lease_count=_safe_integer(item["lease_count"], maximum=512),
        inflight_operation_count=_safe_integer(
            item["inflight_operation_count"], maximum=256
        ),
        terminal_receipt_count=_safe_integer(
            item["terminal_receipt_count"], maximum=2_048
        ),
        pending_critical_event_count=_safe_integer(
            item["pending_critical_event_count"], maximum=1_024
        ),
        prior_generation_orphan_count=_safe_integer(
            item["prior_generation_orphan_count"], maximum=512
        ),
    )


def _record(value: Any, keys: set[str]) -> dict[str, Any]:
    if not isinstance(value, Mapping) or set(value) != keys:
        raise BrowserBridgeReconciliationError("RECONCILE_RESULT_INVALID")
    return dict(value)


def _array(value: Any, maximum: int) -> list[Any]:
    if not isinstance(value, list) or len(value) > maximum:
        raise BrowserBridgeReconciliationError("RECONCILE_RESULT_INVALID")
    return value


def _identifier(value: Any) -> str:
    if not isinstance(value, str) or _OPAQUE_ID.fullmatch(value) is None:
        raise BrowserBridgeReconciliationError("RECONCILE_RESULT_INVALID")
    return value


def _safe_integer(value: Any, *, maximum: int = 2**53 - 1) -> int:
    if (
        isinstance(value, bool)
        or not isinstance(value, int)
        or not 0 <= value <= maximum
    ):
        raise BrowserBridgeReconciliationError("RECONCILE_RESULT_INVALID")
    return value


def _nullable_safe_integer(value: Any) -> int | None:
    return None if value is None else _safe_integer(value)


def _boolean(value: Any) -> bool:
    if not isinstance(value, bool):
        raise BrowserBridgeReconciliationError("RECONCILE_RESULT_INVALID")
    return value


def _enum(value: Any, allowed: frozenset[str]) -> str:
    if not isinstance(value, str) or value not in allowed:
        raise BrowserBridgeReconciliationError("RECONCILE_RESULT_INVALID")
    return value


def _nullable_enum(value: Any, allowed: frozenset[str]) -> str | None:
    return None if value is None else _enum(value, allowed)


def _nullable_identifier(value: Any) -> str | None:
    return None if value is None else _identifier(value)


def _digest(value: Any) -> str:
    if not isinstance(value, str) or _DIGEST.fullmatch(value) is None:
        raise BrowserBridgeReconciliationError("RECONCILE_RESULT_INVALID")
    return value


def _bounded_text(value: Any, maximum: int) -> str:
    if (
        not isinstance(value, str)
        or not value
        or len(value) > maximum
        or any(ord(character) < 0x20 or ord(character) == 0x7F for character in value)
    ):
        raise BrowserBridgeReconciliationError("RECONCILE_RESULT_INVALID")
    return value


def _origin(value: Any) -> str:
    try:
        normalized = normalize_site_origin(value)
    except (BrowserBridgePolicyError, TypeError):
        raise BrowserBridgeReconciliationError(
            "RECONCILE_RESULT_INVALID"
        ) from None
    if normalized != value:
        raise BrowserBridgeReconciliationError("RECONCILE_RESULT_INVALID")
    return normalized


def _denied_completion() -> BrokerCompletion:
    return BrokerCompletion(
        ok=False,
        code="SCOPE_DENIED",
        error="Browser reconciliation authority is unavailable",
        outcome="not_applied",
        retryable=False,
    )
