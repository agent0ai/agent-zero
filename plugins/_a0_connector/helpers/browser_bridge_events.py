"""Durable, fail-closed receipt of critical Browser bridge events.

Only the critical event forms whose Core effects are defined here are
accepted.  Durable receipts contain hashes and cursor metadata, never browser
event data.  A separate generation-qualified acknowledgement is the only
authority for the extension to prune its write-ahead log.
"""

from __future__ import annotations

import asyncio
from copy import deepcopy
from dataclasses import dataclass, field
import hashlib
import json
import re
import threading
from typing import Any, Callable

from helpers.ws_principal import WsPrincipal, restricted_correlation_id
from plugins._a0_connector.helpers.browser_bridge_approval import (
    BrowserActionDataClassification,
    BrowserBridgeApprovalError,
    parse_action_data_classification,
)
from plugins._a0_connector.helpers.browser_bridge_context import (
    BrowserBridgeContextRoute,
)
from plugins._a0_connector.helpers.browser_bridge_policy import (
    BrowserBridgePolicyError,
    normalize_site_origin,
)
from plugins._a0_connector.helpers.browser_bridge_transport import (
    PRODUCTION_BROWSER_BRIDGE_TRANSPORT,
    BrowserBridgeTransportProfile,
    require_browser_bridge_transport_profile,
)


CONTRACT_VERSION = 1
WS_NAMESPACE = PRODUCTION_BROWSER_BRIDGE_TRANSPORT.namespace
RESTRICTED_HANDLER_ID = PRODUCTION_BROWSER_BRIDGE_TRANSPORT.handler_id
BROWSER_EVENT = "connector_browser_event"
BROWSER_EVENT_ACK = "connector_browser_event_ack"

MAX_SAFE_INTEGER = 2**53 - 1
MAX_IDENTIFIER_BYTES = 256
MAX_ROUTES = 64
MAX_RECEIPTS_PER_ROUTE = 2048
MAX_TOTAL_RECEIPTS = 8192
RETAIN_APPLIED_RECEIPTS = 256
MAX_ACK_EMIT_SECONDS = 10.0
DEFAULT_ACK_EMIT_SECONDS = 5.0
MAX_SITE_SUMMARY_BYTES = 512
MAX_ACTION_SUMMARY_BYTES = 512
TYPE_CHALLENGE_SUMMARY = "Allow Agent Zero to type into the highlighted field?"
UPLOAD_CHALLENGE_SUMMARY = "Allow Agent Zero to share the selected attachment with this site? File selection can immediately upload it."
_ACTION_CLASSES = frozenset(
    {"sensitive_input", "external_side_effect", "unknown"}
)

_STORE_KEY = "a0_browser_bridge_critical_events_v1"
_OPAQUE_ID = re.compile(r"[A-Za-z0-9][A-Za-z0-9._:-]{0,255}")
_DIGEST = re.compile(r"[a-f0-9]{64}")

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
_LEASE_OWNERSHIP = frozenset({"created", "claimed"})
_LEASE_DISPOSITIONS = frozenset({"ephemeral", "deliverable", "handoff"})
_LEASE_CHANGES = frozenset(
    {
        "created",
        "finalizing",
        "tab_closed",
        "user_takeover",
        "finalized",
        "orphaned",
    }
)
_LEASE_REASON_CODES = frozenset(
    {
        "FINALIZATION_STARTED",
        "TAB_CLOSED",
        "USER_TAKEOVER",
        "LEASE_ORPHANED",
        "FINALIZED_CLOSED",
        "FINALIZED_RELEASED",
        "FINALIZED_RETAINED",
        "FINALIZATION_OUTCOME_UNKNOWN",
    }
)

_persistent_lock = threading.RLock()


class BrowserBridgeEventError(RuntimeError):
    """A critical event cannot be accepted or durably acknowledged."""

    def __init__(self, code: str) -> None:
        super().__init__(code)
        self.code = code


class BrowserBridgeEventDenied(PermissionError):
    """The exact current Browser bridge route lacks event authority."""

    def __init__(self, code: str) -> None:
        super().__init__(code)
        self.code = code


@dataclass(frozen=True, slots=True)
class LeaseInvalidation:
    """Negative-only lease cache invalidation; it conveys no grant or state."""

    principal: WsPrincipal
    connector_sid: str
    load_generation_id: str
    context_id: str
    browser_session_id: str
    turn_id: str
    lease_id_digest: str
    browser_id_digest: str
    state: str
    ownership: str
    disposition: str
    change: str
    reason_code: str


@dataclass(frozen=True, slots=True)
class TurnFinalizedNotice:
    """Informational summary that deliberately omits a usable control ID."""

    principal: WsPrincipal
    connector_sid: str
    load_generation_id: str
    context_id: str
    browser_session_id: str
    turn_id: str
    control_id_digest: str
    status: str
    closed_count: int
    released_count: int
    retained_count: int
    already_finalized_count: int
    error_count: int


@dataclass(frozen=True, slots=True)
class SiteChallengeNotice:
    """Exact challenge registration input; it grants no site authority."""

    principal: WsPrincipal
    connector_sid: str
    load_generation_id: str
    context_id: str
    browser_session_id: str
    turn_id: str
    action_id: str
    op_id: str
    challenge_id: str
    origin: str
    canonical_parameter_hash: str
    target_fingerprint: str
    lease_id_digest: str
    browser_id_digest: str
    document_id: str | None
    document_epoch: int
    summary: str = field(repr=False)
    expires_at_ms: int


@dataclass(frozen=True, slots=True)
class ActionChallengeNotice:
    """Exact consequential-action challenge input; it grants no authority."""

    principal: WsPrincipal
    connector_sid: str
    load_generation_id: str
    context_id: str
    browser_session_id: str
    turn_id: str
    action_id: str
    op_id: str
    challenge_id: str
    origin: str
    action_class: str
    canonical_parameter_hash: str
    target_fingerprint: str
    lease_id_digest: str
    browser_id_digest: str
    document_id: str
    document_epoch: int
    summary: str = field(repr=False)
    data_classification: BrowserActionDataClassification
    expires_at_ms: int


@dataclass(frozen=True, slots=True)
class ReconciliationCriticalEventIdentity:
    """Redacted identity of one fully validated, but unapplied, replay event."""

    load_generation_id: str
    event_sequence: int
    event_type: str
    challenge_kind: str | None


RouteVerifier = Callable[[BrowserBridgeContextRoute], bool]
LeaseInvalidator = Callable[[LeaseInvalidation], None]
FinalizationObserver = Callable[[TurnFinalizedNotice], None]
SiteChallengeRegistrar = Callable[[SiteChallengeNotice], None]
ActionChallengeRegistrar = Callable[[ActionChallengeNotice], None]


class BrowserBridgeCriticalEventReceiver:
    """Validate, reserve, apply, and ACK exact critical event sequences."""

    def __init__(
        self,
        *,
        manager: Any,
        server_instance_id: Callable[[], str],
        current_route_verifier: RouteVerifier | None = None,
        invalidate_lease: LeaseInvalidator | None = None,
        observe_finalization: FinalizationObserver | None = None,
        register_site_challenge: SiteChallengeRegistrar | None = None,
        register_action_challenge: ActionChallengeRegistrar | None = None,
        load: Callable[[], Any] | None = None,
        save: Callable[[dict[str, Any]], None] | None = None,
        ack_emit_seconds: float = DEFAULT_ACK_EMIT_SECONDS,
        lock: threading.RLock | None = None,
        transport_profile: BrowserBridgeTransportProfile = (
            PRODUCTION_BROWSER_BRIDGE_TRANSPORT
        ),
    ) -> None:
        if not callable(getattr(manager, "emit_to", None)):
            raise BrowserBridgeEventError("INVALID_WEBSOCKET_MANAGER")
        if not callable(server_instance_id):
            raise BrowserBridgeEventError("INVALID_SERVER_INSTANCE")
        if (
            isinstance(ack_emit_seconds, bool)
            or not isinstance(ack_emit_seconds, (int, float))
            or not 0 < float(ack_emit_seconds) <= MAX_ACK_EMIT_SECONDS
        ):
            raise BrowserBridgeEventError("INVALID_ACK_TIMEOUT")
        self._manager = manager
        self._transport_profile = require_browser_bridge_transport_profile(
            transport_profile
        )
        self._server_instance_id = server_instance_id
        self._current_route_verifier = current_route_verifier or (
            lambda _route: False
        )
        self._invalidate_lease = invalidate_lease or _unavailable_callback
        self._observe_finalization = (
            observe_finalization or _unavailable_callback
        )
        self._register_site_challenge = (
            register_site_challenge or _unavailable_callback
        )
        self._register_action_challenge = (
            register_action_challenge or _unavailable_callback
        )
        self._load = load or _load_events
        self._save = save or _save_events
        self._ack_emit_seconds = float(ack_emit_seconds)
        self._lock = lock or _persistent_lock

    async def receive(
        self,
        route: BrowserBridgeContextRoute,
        document: Any,
    ) -> dict[str, Any]:
        route = _route(route)
        event, callback_value = _validate_event(
            route, document, self._transport_profile
        )
        server_id = self._current_server(route)
        owner_hash = _hash_json(
            {
                "server_instance_id": server_id,
                "bridge_id": route.principal.principal_id,
                "subject_id": route.principal.subject_id,
            }
        )
        binding_hash = _hash_json(
            {
                "owner_hash": owner_hash,
                "key_generation": route.principal.key_generation,
                "load_generation_id": route.load_generation_id,
            }
        )
        event_id_hash = _hash_text(event["event_id"])
        event_hash = _hash_json(event)

        with self._lock:
            self._require_current(route, server_id)
            state = self._state()
            routes = state["routes"]
            record = routes.get(binding_hash)
            if record is None:
                # A verified current route establishes replacement.  An event
                # claim by itself never deletes another generation's cursor.
                for key in tuple(routes):
                    if routes[key]["owner_hash"] == owner_hash:
                        routes.pop(key)
                if len(routes) >= MAX_ROUTES:
                    raise BrowserBridgeEventError("EVENT_REGISTRY_FULL")
                record = {
                    "owner_hash": owner_hash,
                    "binding_hash": binding_hash,
                    "cursor": 0,
                    "receipts": {},
                }
                routes[binding_hash] = record

            initial_cursor = record["cursor"]
            sequence_key = str(event["event_sequence"])
            receipt = record["receipts"].get(sequence_key)
            duplicate_sequence = next(
                (
                    sequence
                    for sequence, candidate in record["receipts"].items()
                    if candidate["event_id_hash"] == event_id_hash
                    and sequence != sequence_key
                ),
                None,
            )
            if duplicate_sequence is not None:
                raise BrowserBridgeEventError("EVENT_ID_CONFLICT")
            if receipt is not None and (
                receipt["event_id_hash"] != event_id_hash
                or receipt["event_hash"] != event_hash
            ):
                raise BrowserBridgeEventError("EVENT_SEQUENCE_CONFLICT")

            should_apply = False
            if event["event_sequence"] <= initial_cursor:
                # Old applied receipts may have compacted.  The generation's
                # durable cursor is sufficient to ACK without replaying any
                # callback or creating new authority.
                should_ack = True
            else:
                if receipt is None:
                    self._make_receipt_space(state, record)
                    receipt = {
                        "event_id_hash": event_id_hash,
                        "event_hash": event_hash,
                        "state": "accepted",
                    }
                    record["receipts"][sequence_key] = receipt
                    self._persist(state)
                    self._require_current(route, server_id)
                    should_apply = True
                elif receipt["state"] == "accepted":
                    should_apply = True

                if should_apply:
                    self._run_callback(event["event_type"], callback_value)
                    self._require_current(route, server_id)
                    # The first save is the crash-safe reservation.  This save
                    # records successful callback application and cursor motion.
                    receipt["state"] = "applied"

                cursor = record["cursor"]
                while True:
                    next_receipt = record["receipts"].get(str(cursor + 1))
                    if next_receipt is None or next_receipt["state"] != "applied":
                        break
                    cursor += 1
                if should_apply or cursor != record["cursor"]:
                    record["cursor"] = cursor
                    self._compact_applied(record)
                    self._persist(state)
                    self._require_current(route, server_id)
                should_ack = cursor > initial_cursor

        if should_ack:
            await self._emit_ack(route, server_id, record["cursor"])
        return {
            "contract_version": CONTRACT_VERSION,
            "event_id": event["event_id"],
            "status": "accepted",
        }

    def _state(self) -> dict[str, Any]:
        try:
            value = self._load()
        except Exception:
            raise BrowserBridgeEventError("EVENT_STORE_UNAVAILABLE") from None
        if value is None or value == {}:
            return {"schema_version": 1, "routes": {}}
        if (
            not isinstance(value, dict)
            or set(value) != {"schema_version", "routes"}
            or type(value["schema_version"]) is not int
            or value["schema_version"] != 1
            or not isinstance(value["routes"], dict)
            or len(value["routes"]) > MAX_ROUTES
        ):
            raise BrowserBridgeEventError("EVENT_STORE_UNAVAILABLE")
        routes: dict[str, dict[str, Any]] = {}
        total_receipts = 0
        for key, raw_record in value["routes"].items():
            if (
                not isinstance(key, str)
                or _DIGEST.fullmatch(key) is None
                or not isinstance(raw_record, dict)
                or set(raw_record)
                != {"owner_hash", "binding_hash", "cursor", "receipts"}
                or raw_record.get("binding_hash") != key
                or not isinstance(raw_record.get("owner_hash"), str)
                or _DIGEST.fullmatch(raw_record["owner_hash"]) is None
                or not _safe_integer(raw_record.get("cursor"))
                or not isinstance(raw_record.get("receipts"), dict)
                or len(raw_record["receipts"]) > MAX_RECEIPTS_PER_ROUTE
            ):
                raise BrowserBridgeEventError("EVENT_STORE_UNAVAILABLE")
            receipts: dict[str, dict[str, str]] = {}
            event_ids: set[str] = set()
            cursor = raw_record["cursor"]
            for sequence, raw_receipt in raw_record["receipts"].items():
                if (
                    not isinstance(sequence, str)
                    or not sequence.isascii()
                    or not sequence.isdigit()
                    or sequence.startswith("0")
                    or len(sequence) > 16
                ):
                    raise BrowserBridgeEventError("EVENT_STORE_UNAVAILABLE")
                number = int(sequence)
                if not 1 <= number <= MAX_SAFE_INTEGER or str(number) != sequence:
                    raise BrowserBridgeEventError("EVENT_STORE_UNAVAILABLE")
                if (
                    not isinstance(raw_receipt, dict)
                    or set(raw_receipt)
                    != {"event_id_hash", "event_hash", "state"}
                    or not isinstance(raw_receipt.get("event_id_hash"), str)
                    or _DIGEST.fullmatch(raw_receipt["event_id_hash"]) is None
                    or not isinstance(raw_receipt.get("event_hash"), str)
                    or _DIGEST.fullmatch(raw_receipt["event_hash"]) is None
                    or raw_receipt.get("state") not in {"accepted", "applied"}
                    or (number <= cursor and raw_receipt["state"] != "applied")
                    or raw_receipt["event_id_hash"] in event_ids
                ):
                    raise BrowserBridgeEventError("EVENT_STORE_UNAVAILABLE")
                event_ids.add(raw_receipt["event_id_hash"])
                receipts[sequence] = dict(raw_receipt)
            total_receipts += len(receipts)
            routes[key] = {
                "owner_hash": raw_record["owner_hash"],
                "binding_hash": key,
                "cursor": cursor,
                "receipts": receipts,
            }
        if total_receipts > MAX_TOTAL_RECEIPTS:
            raise BrowserBridgeEventError("EVENT_STORE_UNAVAILABLE")
        return {"schema_version": 1, "routes": routes}

    def _make_receipt_space(
        self,
        state: dict[str, Any],
        record: dict[str, Any],
    ) -> None:
        self._compact_applied(record)
        total = sum(
            len(candidate["receipts"])
            for candidate in state["routes"].values()
        )
        if (
            len(record["receipts"]) >= MAX_RECEIPTS_PER_ROUTE
            or total >= MAX_TOTAL_RECEIPTS
        ):
            raise BrowserBridgeEventError("EVENT_REGISTRY_FULL")

    @staticmethod
    def _compact_applied(record: dict[str, Any]) -> None:
        cutoff = max(record["cursor"] - RETAIN_APPLIED_RECEIPTS, 0)
        record["receipts"] = {
            sequence: receipt
            for sequence, receipt in record["receipts"].items()
            if int(sequence) > cutoff
        }

    def _run_callback(self, event_type: str, value: Any) -> None:
        if value is None:
            return
        if event_type == "challenge.required":
            callback = (
                self._register_action_challenge
                if isinstance(value, ActionChallengeNotice)
                else self._register_site_challenge
                if isinstance(value, SiteChallengeNotice)
                else None
            )
        else:
            callback = {
                "lease.changed": self._invalidate_lease,
                "turn.finalized": self._observe_finalization,
            }.get(event_type)
        if callback is None:
            raise BrowserBridgeEventError("EVENT_CALLBACK_FAILED")
        try:
            result = callback(value)
        except Exception:
            raise BrowserBridgeEventError("EVENT_CALLBACK_FAILED") from None
        if result is not None:
            raise BrowserBridgeEventError("EVENT_CALLBACK_FAILED")

    def _persist(self, state: dict[str, Any]) -> None:
        try:
            self._save(deepcopy(state))
        except Exception:
            raise BrowserBridgeEventError("EVENT_STORE_UNAVAILABLE") from None

    def _current_server(self, route: BrowserBridgeContextRoute) -> str:
        try:
            server_id = _identifier(self._server_instance_id(), "server_instance_id")
        except Exception:
            raise BrowserBridgeEventDenied("STALE_BRIDGE_ROUTE") from None
        self._require_current(route, server_id)
        return server_id

    def _require_current(
        self, route: BrowserBridgeContextRoute, server_id: str
    ) -> None:
        try:
            current = self._current_route_verifier(route) is True
            same_server = self._server_instance_id() == server_id
        except Exception:
            current = False
            same_server = False
        if not current or not same_server:
            raise BrowserBridgeEventDenied("STALE_BRIDGE_ROUTE")
        if route.transport_profile is not self._transport_profile:
            raise BrowserBridgeEventDenied("SCOPE_DENIED")

    async def _emit_ack(
        self,
        route: BrowserBridgeContextRoute,
        server_id: str,
        cursor: int,
    ) -> None:
        self._require_current(route, server_id)
        try:
            await asyncio.wait_for(
                self._manager.emit_to(
                    self._transport_profile.namespace,
                    route.connector_sid,
                    BROWSER_EVENT_ACK,
                    {
                        "contract_version": CONTRACT_VERSION,
                        "bridge_id": route.principal.principal_id,
                        "load_generation_id": route.load_generation_id,
                        "highest_contiguous_event_sequence": cursor,
                    },
                    handler_id=self._transport_profile.handler_id,
                    correlation_id=restricted_correlation_id(None),
                    expected_principal=route.principal,
                ),
                timeout=self._ack_emit_seconds,
            )
        except asyncio.CancelledError:
            raise
        except Exception:
            raise BrowserBridgeEventError("EVENT_ACK_FAILED") from None
        self._require_current(route, server_id)


def _validate_event(
    route: BrowserBridgeContextRoute,
    value: Any,
    transport_profile: BrowserBridgeTransportProfile,
) -> tuple[
    dict[str, Any],
    LeaseInvalidation
    | TurnFinalizedNotice
    | SiteChallengeNotice
    | ActionChallengeNotice
    | None,
]:
    profile = require_browser_bridge_transport_profile(transport_profile)
    if (
        route.transport_profile is not profile
        or
        "browser.operate" not in route.principal.scopes
        or not route.principal.permits_inbound(BROWSER_EVENT, profile.handler_id)
    ):
        raise BrowserBridgeEventDenied("SCOPE_DENIED")
    if not isinstance(value, dict):
        raise BrowserBridgeEventError("INVALID_EVENT")
    event = dict(value)
    # Shared WsManager supplies this sanitized envelope-only value to handlers.
    event.pop("correlationId", None)
    if set(event) != {
        "contract_version",
        "event_id",
        "load_generation_id",
        "event_sequence",
        "delivery",
        "event_type",
        "observed_at_ms",
        "context_id",
        "browser_session_id",
        "turn_id",
        "op_id",
        "action_id",
        "data",
    }:
        raise BrowserBridgeEventError("INVALID_EVENT")
    if (
        type(event["contract_version"]) is not int
        or event["contract_version"] != CONTRACT_VERSION
        or event["load_generation_id"] != route.load_generation_id
        or event["delivery"] != "critical"
        or not isinstance(event["event_type"], str)
        or event["event_type"]
        not in {"lease.changed", "turn.finalized", "challenge.required"}
        or not _safe_integer(event["event_sequence"], positive=True)
        or not _safe_integer(event["observed_at_ms"])
    ):
        raise BrowserBridgeEventError("INVALID_EVENT")
    for name in (
        "event_id",
        "load_generation_id",
        "context_id",
        "browser_session_id",
        "turn_id",
    ):
        event[name] = _identifier(event[name], name)
    for name in ("op_id", "action_id"):
        if event[name] is not None:
            event[name] = _identifier(event[name], name)
    if event["event_type"] == "challenge.required":
        if event["op_id"] is None or event["action_id"] is None:
            raise BrowserBridgeEventError("INVALID_EVENT")
        kind = event["data"].get("kind") if isinstance(event["data"], dict) else None
        if kind == "site":
            data = _site_challenge_data(event["data"])
            callback = SiteChallengeNotice(
                principal=route.principal,
                connector_sid=route.connector_sid,
                load_generation_id=route.load_generation_id,
                context_id=event["context_id"],
                browser_session_id=event["browser_session_id"],
                turn_id=event["turn_id"],
                action_id=event["action_id"],
                op_id=event["op_id"],
                challenge_id=data["challenge_id"],
                origin=data["origin"],
                canonical_parameter_hash=data["canonical_parameter_hash"],
                target_fingerprint=data["target_fingerprint"],
                lease_id_digest=data["lease_id_digest"],
                browser_id_digest=data["browser_id_digest"],
                document_id=data["document_id"],
                document_epoch=data["document_epoch"],
                summary=data["summary"],
                expires_at_ms=data["expires_at_ms"],
            )
        elif kind == "action":
            data = _action_challenge_data(event["data"])
            callback = ActionChallengeNotice(
                principal=route.principal,
                connector_sid=route.connector_sid,
                load_generation_id=route.load_generation_id,
                context_id=event["context_id"],
                browser_session_id=event["browser_session_id"],
                turn_id=event["turn_id"],
                action_id=event["action_id"],
                op_id=event["op_id"],
                challenge_id=data["challenge_id"],
                origin=data["origin"],
                action_class=data["action_class"],
                canonical_parameter_hash=data["canonical_parameter_hash"],
                target_fingerprint=data["target_fingerprint"],
                lease_id_digest=data["lease_id_digest"],
                browser_id_digest=data["browser_id_digest"],
                document_id=data["document_id"],
                document_epoch=data["document_epoch"],
                summary=data["summary"],
                data_classification=parse_action_data_classification(
                    data["data_classification"]
                ),
                expires_at_ms=data["expires_at_ms"],
            )
        else:
            raise BrowserBridgeEventError("INVALID_EVENT")
    elif event["event_type"] == "lease.changed":
        data = _lease_data(event["data"])
        # Creation is passive evidence and cannot grant Core authority.  It
        # also must not withdraw a lease recorded from the successful operation
        # result if the at-least-once event arrives later.
        callback: LeaseInvalidation | TurnFinalizedNotice | None = None
        if data["change"] != "created":
            callback = LeaseInvalidation(
                principal=route.principal,
                connector_sid=route.connector_sid,
                load_generation_id=route.load_generation_id,
                context_id=event["context_id"],
                browser_session_id=event["browser_session_id"],
                turn_id=event["turn_id"],
                lease_id_digest=data["lease_id_digest"],
                browser_id_digest=data["browser_id_digest"],
                state=data["state"],
                ownership=data["ownership"],
                disposition=data["disposition"],
                change=data["change"],
                reason_code=data["reason_code"],
            )
    else:
        data = _finalization_data(event["data"])
        callback = TurnFinalizedNotice(
            principal=route.principal,
            connector_sid=route.connector_sid,
            load_generation_id=route.load_generation_id,
            context_id=event["context_id"],
            browser_session_id=event["browser_session_id"],
            turn_id=event["turn_id"],
            control_id_digest=_hash_text(data["control_id"]),
            status=data["status"],
            closed_count=data["closed_count"],
            released_count=data["released_count"],
            retained_count=data["retained_count"],
            already_finalized_count=data["already_finalized_count"],
            error_count=data["error_count"],
        )
    event["data"] = data
    return event, callback


def validate_reconciliation_critical_event(
    route: BrowserBridgeContextRoute,
    value: Any,
    *,
    transport_profile: BrowserBridgeTransportProfile = (
        PRODUCTION_BROWSER_BRIDGE_TRANSPORT
    ),
) -> ReconciliationCriticalEventIdentity:
    """Validate a replay snapshot without applying or acknowledging it.

    This deliberately returns only routing/cursor metadata.  The full event
    stays owned by the extension WAL until it is replayed through the normal
    durable receiver after route promotion.
    """

    # Embedded reconcile events are native event objects, not WsManager
    # envelopes.  The live receiver tolerates and strips its sanitized
    # correlationId wrapper, but accepting that extra key here would diverge
    # from the extension's exact parseBrowserEventParams schema.
    if not isinstance(value, dict) or set(value) != {
        "contract_version",
        "event_id",
        "load_generation_id",
        "event_sequence",
        "delivery",
        "event_type",
        "observed_at_ms",
        "context_id",
        "browser_session_id",
        "turn_id",
        "op_id",
        "action_id",
        "data",
    }:
        raise BrowserBridgeEventError("INVALID_EVENT")
    event, callback = _validate_event(route, value, transport_profile)
    return ReconciliationCriticalEventIdentity(
        load_generation_id=event["load_generation_id"],
        event_sequence=event["event_sequence"],
        event_type=event["event_type"],
        challenge_kind=(
            "site"
            if isinstance(callback, SiteChallengeNotice)
            else "action"
            if isinstance(callback, ActionChallengeNotice)
            else None
        ),
    )


def _lease_data(value: Any) -> dict[str, Any]:
    if not isinstance(value, dict) or set(value) != {
        "lease_id_digest",
        "browser_id_digest",
        "state",
        "ownership",
        "disposition",
        "change",
        "reason_code",
    }:
        raise BrowserBridgeEventError("INVALID_EVENT")
    data = dict(value)
    for name in ("lease_id_digest", "browser_id_digest"):
        if not isinstance(data[name], str) or _DIGEST.fullmatch(data[name]) is None:
            raise BrowserBridgeEventError("INVALID_EVENT")
    if (
        not isinstance(data["state"], str)
        or data["state"] not in _LEASE_STATES
        or not isinstance(data["ownership"], str)
        or data["ownership"] not in _LEASE_OWNERSHIP
        or not isinstance(data["disposition"], str)
        or data["disposition"] not in _LEASE_DISPOSITIONS
        or not isinstance(data["change"], str)
        or data["change"] not in _LEASE_CHANGES
        or (
            data["reason_code"] is not None
            and (
                not isinstance(data["reason_code"], str)
                or data["reason_code"] not in _LEASE_REASON_CODES
            )
        )
    ):
        raise BrowserBridgeEventError("INVALID_EVENT")
    expected = {
        "created": {("active", None)},
        "finalizing": {("finalizing", "FINALIZATION_STARTED")},
        "tab_closed": {("closed", "TAB_CLOSED")},
        "user_takeover": {("released", "USER_TAKEOVER")},
        "orphaned": {("orphan", "LEASE_ORPHANED")},
        "finalized": {
            ("closed", "FINALIZED_CLOSED"),
            ("released", "FINALIZED_RELEASED"),
            ("retained", "FINALIZED_RETAINED"),
            ("outcome_unknown", "FINALIZATION_OUTCOME_UNKNOWN"),
        },
    }
    if (data["state"], data["reason_code"]) not in expected[data["change"]]:
        raise BrowserBridgeEventError("INVALID_EVENT")
    return data


def _finalization_data(value: Any) -> dict[str, Any]:
    if not isinstance(value, dict) or set(value) != {
        "control_id",
        "status",
        "closed_count",
        "released_count",
        "retained_count",
        "already_finalized_count",
        "error_count",
    }:
        raise BrowserBridgeEventError("INVALID_EVENT")
    data = dict(value)
    data["control_id"] = _identifier(data["control_id"], "control_id")
    if data["status"] != "completed" or any(
        not _safe_integer(data[name]) or data[name] > 256
        for name in (
            "closed_count",
            "released_count",
            "retained_count",
            "already_finalized_count",
            "error_count",
        )
    ):
        raise BrowserBridgeEventError("INVALID_EVENT")
    return data


def _site_challenge_data(value: Any) -> dict[str, Any]:
    if not isinstance(value, dict) or set(value) != {
        "challenge_id",
        "kind",
        "origin",
        "action_class",
        "canonical_parameter_hash",
        "target_fingerprint",
        "lease_id_digest",
        "browser_id_digest",
        "document_id",
        "document_epoch",
        "summary",
        "options",
        "expires_at_ms",
    }:
        raise BrowserBridgeEventError("INVALID_EVENT")
    data = dict(value)
    data["challenge_id"] = _identifier(data["challenge_id"], "challenge_id")
    if data["document_id"] is not None:
        data["document_id"] = _identifier(data["document_id"], "document_id")
    for name in (
        "canonical_parameter_hash",
        "target_fingerprint",
        "lease_id_digest",
        "browser_id_digest",
    ):
        if not isinstance(data[name], str) or _DIGEST.fullmatch(data[name]) is None:
            raise BrowserBridgeEventError("INVALID_EVENT")
    try:
        canonical_origin = normalize_site_origin(data["origin"])
    except BrowserBridgePolicyError:
        raise BrowserBridgeEventError("INVALID_EVENT") from None
    summary = data["summary"]
    try:
        summary_bytes = summary.encode("utf-8") if isinstance(summary, str) else b""
    except UnicodeError:
        raise BrowserBridgeEventError("INVALID_EVENT") from None
    if (
        canonical_origin != data["origin"]
        or data["kind"] != "site"
        or data["action_class"] != "navigate"
        or not _safe_integer(data["document_epoch"])
        or not _safe_integer(data["expires_at_ms"], positive=True)
        or data["options"] != ["deny", "allow_once", "allow_turn"]
        or not isinstance(summary, str)
        or not summary
        or not summary.isprintable()
        or len(summary_bytes) > MAX_SITE_SUMMARY_BYTES
    ):
        raise BrowserBridgeEventError("INVALID_EVENT")
    data["origin"] = canonical_origin
    return data


def _action_challenge_data(value: Any) -> dict[str, Any]:
    if not isinstance(value, dict) or set(value) != {
        "challenge_id",
        "kind",
        "origin",
        "action_class",
        "canonical_parameter_hash",
        "target_fingerprint",
        "lease_id_digest",
        "browser_id_digest",
        "document_id",
        "document_epoch",
        "summary",
        "options",
        "data_classification",
        "expires_at_ms",
    }:
        raise BrowserBridgeEventError("INVALID_EVENT")
    data = dict(value)
    data["challenge_id"] = _identifier(data["challenge_id"], "challenge_id")
    data["document_id"] = _identifier(data["document_id"], "document_id")
    for name in (
        "canonical_parameter_hash",
        "target_fingerprint",
        "lease_id_digest",
        "browser_id_digest",
    ):
        if not isinstance(data[name], str) or _DIGEST.fullmatch(data[name]) is None:
            raise BrowserBridgeEventError("INVALID_EVENT")
    try:
        canonical_origin = normalize_site_origin(data["origin"])
    except BrowserBridgePolicyError:
        raise BrowserBridgeEventError("INVALID_EVENT") from None
    try:
        classification = parse_action_data_classification(
            data["data_classification"]
        )
    except BrowserBridgeApprovalError:
        raise BrowserBridgeEventError("INVALID_EVENT") from None
    summary = data["summary"]
    try:
        summary_bytes = summary.encode("utf-8") if isinstance(summary, str) else b""
    except UnicodeError:
        raise BrowserBridgeEventError("INVALID_EVENT") from None
    if (
        canonical_origin != data["origin"]
        or data["kind"] != "action"
        or not isinstance(data["action_class"], str)
        or data["action_class"] not in _ACTION_CLASSES
        or (
            classification.kind == "text"
            and (
                data["action_class"] != "sensitive_input"
                or summary != TYPE_CHALLENGE_SUMMARY
            )
        )
        or not _safe_integer(data["document_epoch"])
        or not _safe_integer(data["expires_at_ms"], positive=True)
        or data["options"] != ["decline", "approve_once"]
        or not isinstance(summary, str)
        or not summary
        or not summary.isprintable()
        or len(summary_bytes) > MAX_ACTION_SUMMARY_BYTES
    ):
        raise BrowserBridgeEventError("INVALID_EVENT")
    data["origin"] = canonical_origin
    data["data_classification"] = classification.as_wire_value()
    return data


def _safe_integer(value: Any, *, positive: bool = False) -> bool:
    return (
        not isinstance(value, bool)
        and isinstance(value, int)
        and (1 if positive else 0) <= value <= MAX_SAFE_INTEGER
    )


def _identifier(value: Any, name: str) -> str:
    if not isinstance(value, str) or _OPAQUE_ID.fullmatch(value) is None:
        raise BrowserBridgeEventError(f"INVALID_{name.upper()}")
    try:
        if len(value.encode("utf-8")) > MAX_IDENTIFIER_BYTES:
            raise BrowserBridgeEventError(f"INVALID_{name.upper()}")
    except UnicodeError:
        raise BrowserBridgeEventError(f"INVALID_{name.upper()}") from None
    return value


def _route(value: Any) -> BrowserBridgeContextRoute:
    if not isinstance(value, BrowserBridgeContextRoute):
        raise BrowserBridgeEventError("INVALID_ROUTE")
    return value


def _hash_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def _hash_json(value: Any) -> str:
    encoded = json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def _unavailable_callback(_value: Any) -> None:
    raise BrowserBridgeEventError("EVENT_CALLBACK_UNAVAILABLE")


def _load_events() -> Any:
    from helpers import kvp

    return kvp.get_persistent(_STORE_KEY, None)


def _save_events(value: dict[str, Any]) -> None:
    from helpers import kvp

    kvp.set_persistent(_STORE_KEY, value)
