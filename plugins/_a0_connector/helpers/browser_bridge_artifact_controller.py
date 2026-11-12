"""Exact-route transport controller for Browser bridge output artifacts.

The controller validates the connector wire shape, resolves authority through
an injected pending-operation binding, and delegates private spooling to
``BrowserBridgeArtifactReceiver``.  It does not materialize artifacts, support
input uploads, wire a WebSocket handler, or advertise Browser runtime readiness.
"""

from __future__ import annotations

import asyncio
import base64
import binascii
from dataclasses import dataclass
import json
import re
from typing import Any, Callable

from helpers.ws_principal import WsPrincipal, restricted_correlation_id
from plugins._a0_connector.helpers.browser_bridge_artifacts import (
    MAX_ARTIFACT_BYTES,
    MAX_CHUNK_BYTES,
    ArtifactBinding,
    ArtifactCleanupSummary,
    ArtifactDescriptor,
    ArtifactProgress,
    BrowserBridgeArtifactError,
    BrowserBridgeArtifactReceiver,
)
from plugins._a0_connector.helpers.browser_bridge_context import (
    BrowserBridgeContextRoute,
)
from plugins._a0_connector.helpers.browser_bridge_transport import (
    PRODUCTION_BROWSER_BRIDGE_TRANSPORT,
    BrowserBridgeTransportProfile,
    require_browser_bridge_transport_profile,
)


CONTRACT_VERSION = 1
WS_NAMESPACE = PRODUCTION_BROWSER_BRIDGE_TRANSPORT.namespace
RESTRICTED_HANDLER_ID = PRODUCTION_BROWSER_BRIDGE_TRANSPORT.handler_id
ARTIFACT_CHUNK_EVENT = "connector_browser_artifact_chunk"
ARTIFACT_ACK_EVENT = "connector_browser_artifact_ack"

MAX_NATIVE_FRAME_BYTES = 768 * 1024
MAX_BASE64_CHUNK_BYTES = 256 * 1024
MAX_SAFE_INTEGER = 2**53 - 1
MAX_EMIT_TIMEOUT_SECONDS = 10.0
DEFAULT_EMIT_TIMEOUT_SECONDS = 5.0
MIN_EXPIRY_INTERVAL_SECONDS = 0.01
MAX_EXPIRY_INTERVAL_SECONDS = 60.0
DEFAULT_EXPIRY_INTERVAL_SECONDS = 1.0

_IDENTIFIER = re.compile(r"[A-Za-z0-9][A-Za-z0-9._:-]{0,255}")
_SHA256 = re.compile(r"sha256:[a-f0-9]{64}")
_MIME_TYPE = re.compile(
    r"[A-Za-z0-9][A-Za-z0-9!#$&^_.+-]{0,126}/"
    r"[A-Za-z0-9][A-Za-z0-9!#$&^_.+-]{0,126}"
)

_COMMON_KEYS = frozenset(
    {
        "contract_version",
        "phase",
        "bridge_id",
        "load_generation_id",
        "context_id",
        "browser_session_id",
        "turn_id",
        "action_id",
        "op_id",
        "artifact_id",
        "direction",
        "purpose",
    }
)
_PHASE_KEYS = {
    "begin": frozenset({"mime_type", "byte_count", "sha256"}),
    "chunk": frozenset({"chunk_index", "data_base64"}),
    "end": frozenset(),
    "abort": frozenset({"reason_code"}),
}
_OUTPUT_PURPOSES = frozenset({"screenshot", "download"})
_SENDER_ABORT_REASONS = frozenset(
    {
        "ARTIFACT_TOO_LARGE",
        "CANCELED",
        "CONNECTION_LOST",
        "DEADLINE_EXCEEDED",
        "INTERNAL_ERROR",
        "OUTCOME_UNKNOWN",
    }
)
_RECEIVER_ABORT_REASONS = frozenset(
    {
        "ARTIFACT_ALREADY_COMPLETE",
        "ARTIFACT_DIGEST_INVALID",
        "ARTIFACT_ID_REUSED",
        "ARTIFACT_INTEGRITY_MISMATCH",
        "ARTIFACT_MIME_INVALID",
        "ARTIFACT_NOT_COMPLETE",
        "ARTIFACT_NOT_FOUND",
        "ARTIFACT_REGISTRY_FULL",
        "ARTIFACT_SIZE_INVALID",
        "ARTIFACT_SIZE_MISMATCH",
        "ARTIFACT_SPOOL_FULL",
        "ARTIFACT_TERMINAL",
        "CHUNK_OUT_OF_ORDER",
        "CHUNK_SIZE_INVALID",
        "CLOCK_UNAVAILABLE",
        "IDEMPOTENCY_CONFLICT",
        "SPOOL_UNAVAILABLE",
    }
)


class BrowserBridgeArtifactControllerError(ValueError):
    """An artifact frame or controller dependency is invalid."""

    def __init__(self, code: str) -> None:
        super().__init__(code)
        self.code = code


class BrowserBridgeArtifactControllerDenied(PermissionError):
    """The exact route or pending operation lacks artifact authority."""

    def __init__(self, code: str) -> None:
        super().__init__(code)
        self.code = code


@dataclass(frozen=True, slots=True)
class ArtifactBindingLookup:
    """Untrusted lookup keys; the resolver must return server-owned authority."""

    route: BrowserBridgeContextRoute
    bridge_id: str
    load_generation_id: str
    context_id: str
    browser_session_id: str
    turn_id: str
    action_id: str
    op_id: str
    artifact_id: str
    direction: str
    purpose: str


ArtifactBindingResolver = Callable[[ArtifactBindingLookup], ArtifactBinding | None]


class BrowserBridgeArtifactController:
    """Receive, validate, spool, and acknowledge output artifact frames."""

    def __init__(
        self,
        *,
        receiver: BrowserBridgeArtifactReceiver[Any],
        binding_resolver: ArtifactBindingResolver,
        manager: Any,
        expiry_interval_seconds: float = DEFAULT_EXPIRY_INTERVAL_SECONDS,
        emit_timeout_seconds: float = DEFAULT_EMIT_TIMEOUT_SECONDS,
        transport_profile: BrowserBridgeTransportProfile = (
            PRODUCTION_BROWSER_BRIDGE_TRANSPORT
        ),
    ) -> None:
        if not isinstance(receiver, BrowserBridgeArtifactReceiver):
            raise BrowserBridgeArtifactControllerError("INVALID_ARTIFACT_RECEIVER")
        if not callable(binding_resolver):
            raise BrowserBridgeArtifactControllerError("INVALID_BINDING_RESOLVER")
        if not callable(getattr(manager, "emit_to", None)):
            raise BrowserBridgeArtifactControllerError("INVALID_WEBSOCKET_MANAGER")
        if (
            isinstance(expiry_interval_seconds, bool)
            or not isinstance(expiry_interval_seconds, (int, float))
            or not MIN_EXPIRY_INTERVAL_SECONDS
            <= float(expiry_interval_seconds)
            <= MAX_EXPIRY_INTERVAL_SECONDS
        ):
            raise BrowserBridgeArtifactControllerError("INVALID_EXPIRY_INTERVAL")
        if (
            isinstance(emit_timeout_seconds, bool)
            or not isinstance(emit_timeout_seconds, (int, float))
            or not 0 < float(emit_timeout_seconds) <= MAX_EMIT_TIMEOUT_SECONDS
        ):
            raise BrowserBridgeArtifactControllerError("INVALID_EMIT_TIMEOUT")
        self._receiver = receiver
        self._transport_profile = require_browser_bridge_transport_profile(
            transport_profile
        )
        if getattr(receiver, "_transport_profile", None) is not self._transport_profile:
            raise BrowserBridgeArtifactControllerError("INVALID_ARTIFACT_RECEIVER")
        self._binding_resolver = binding_resolver
        self._manager = manager
        self._expiry_interval_seconds = float(expiry_interval_seconds)
        self._emit_timeout_seconds = float(emit_timeout_seconds)
        self._lock = asyncio.Lock()
        self._expiry_task: asyncio.Task[None] | None = None
        self._closed = False

    @property
    def expiry_task_active(self) -> bool:
        task = self._expiry_task
        return task is not None and not task.done()

    async def receive(
        self,
        route: BrowserBridgeContextRoute,
        document: Any,
    ) -> dict[str, Any]:
        route = _route(route)
        _require_transport_scope(route, self._transport_profile)
        request, decoded = _frame(document, route)
        lookup = ArtifactBindingLookup(
            route=route,
            bridge_id=request["bridge_id"],
            load_generation_id=request["load_generation_id"],
            context_id=request["context_id"],
            browser_session_id=request["browser_session_id"],
            turn_id=request["turn_id"],
            action_id=request["action_id"],
            op_id=request["op_id"],
            artifact_id=request["artifact_id"],
            direction=request["direction"],
            purpose=request["purpose"],
        )
        phase = request["phase"]

        async with self._lock:
            if self._closed:
                raise BrowserBridgeArtifactControllerError("CONTROLLER_CLOSED")
            binding = self._resolve_binding(lookup)
            try:
                if phase == "begin":
                    outcome: ArtifactProgress | ArtifactDescriptor | bool = (
                        await asyncio.to_thread(
                            self._receiver.begin,
                            binding,
                            byte_count=request["byte_count"],
                            sha256=request["sha256"],
                            mime_type=request["mime_type"],
                        )
                    )
                    self._ensure_expiry_task_locked()
                elif phase == "chunk":
                    outcome = await asyncio.to_thread(
                        self._receiver.append,
                        binding,
                        chunk_index=request["chunk_index"],
                        data=decoded,
                    )
                elif phase == "end":
                    outcome = await asyncio.to_thread(
                        self._receiver.complete, binding
                    )
                    self._ensure_expiry_task_locked()
                else:
                    outcome = await asyncio.to_thread(
                        self._receiver.abort, binding
                    )
            except BrowserBridgeArtifactError as error:
                if error.code == "SCOPE_DENIED":
                    raise BrowserBridgeArtifactControllerDenied(
                        "STALE_ARTIFACT_BINDING"
                    ) from None
                if error.code == "RECEIVER_CLOSED":
                    raise BrowserBridgeArtifactControllerError(
                        "CONTROLLER_CLOSED"
                    ) from None
                if error.code not in _RECEIVER_ABORT_REASONS:
                    raise BrowserBridgeArtifactControllerError(
                        "ARTIFACT_TRANSFER_FAILED"
                    ) from None
                acknowledgement = _abort_ack(binding, phase, error.code)
            else:
                acknowledgement = _acknowledgement(
                    binding, phase, request, outcome
                )
            try:
                self._resolve_binding(lookup)
            except BrowserBridgeArtifactControllerDenied:
                try:
                    await asyncio.to_thread(self._receiver.abort, binding)
                except BrowserBridgeArtifactError:
                    pass
                raise
            if self._receiver.active_count == 0:
                self._stop_expiry_task_locked()

        await self._emit_ack(route, acknowledgement)
        return acknowledgement

    async def disconnect(
        self,
        *,
        principal: WsPrincipal,
        connector_sid: Any,
        load_generation_id: Any,
    ) -> ArtifactCleanupSummary:
        if not isinstance(principal, WsPrincipal):
            raise BrowserBridgeArtifactControllerError("INVALID_ROUTE")
        sid = _identifier(connector_sid, "connector_sid")
        generation = _identifier(load_generation_id, "load_generation_id")
        async with self._lock:
            if self._closed:
                return ArtifactCleanupSummary(0, 0)
            summary = await asyncio.to_thread(
                self._receiver.disconnect,
                principal=principal,
                connector_sid=sid,
                load_generation_id=generation,
            )
            if self._receiver.active_count == 0:
                self._stop_expiry_task_locked()
            return summary

    async def close(self) -> ArtifactCleanupSummary:
        async with self._lock:
            if self._closed:
                return ArtifactCleanupSummary(0, 0)
            self._closed = True
            task = self._stop_expiry_task_locked()
            summary = await asyncio.to_thread(self._receiver.close)
        if task is not None:
            try:
                await task
            except asyncio.CancelledError:
                pass
        return summary

    def _resolve_binding(self, lookup: ArtifactBindingLookup) -> ArtifactBinding:
        try:
            binding = self._binding_resolver(lookup)
        except Exception:
            binding = None
        if (
            not isinstance(binding, ArtifactBinding)
            or binding.transport_profile is not self._transport_profile
            or not _binding_matches(binding, lookup)
        ):
            raise BrowserBridgeArtifactControllerDenied(
                "ARTIFACT_BINDING_UNAVAILABLE"
            )
        return binding

    async def _emit_ack(
        self,
        route: BrowserBridgeContextRoute,
        acknowledgement: dict[str, Any],
    ) -> None:
        try:
            await asyncio.wait_for(
                self._manager.emit_to(
                    self._transport_profile.namespace,
                    route.connector_sid,
                    ARTIFACT_ACK_EVENT,
                    acknowledgement,
                    handler_id=self._transport_profile.handler_id,
                    correlation_id=restricted_correlation_id(
                        acknowledgement["op_id"]
                    ),
                    expected_principal=route.principal,
                ),
                timeout=self._emit_timeout_seconds,
            )
        except asyncio.CancelledError:
            raise
        except Exception:
            raise BrowserBridgeArtifactControllerError(
                "ARTIFACT_ACK_FAILED"
            ) from None

    def _ensure_expiry_task_locked(self) -> None:
        task = self._expiry_task
        if task is None or task.done():
            self._expiry_task = asyncio.create_task(
                self._expiry_loop(), name="browser-bridge-artifact-expiry"
            )

    def _stop_expiry_task_locked(self) -> asyncio.Task[None] | None:
        task = self._expiry_task
        self._expiry_task = None
        if task is not None and task is not asyncio.current_task():
            task.cancel()
            return task
        return None

    async def _expiry_loop(self) -> None:
        current = asyncio.current_task()
        try:
            while True:
                await asyncio.sleep(self._expiry_interval_seconds)
                async with self._lock:
                    if self._closed or self._expiry_task is not current:
                        return
                    try:
                        await asyncio.to_thread(self._receiver.expire)
                    except BrowserBridgeArtifactError as error:
                        if error.code == "RECEIVER_CLOSED":
                            return
                        # Clock failures do not widen authority or delete an
                        # unexpired transfer.  Retry only on the bounded sweep.
                    except Exception:
                        # A cleanup dependency cannot terminate the only expiry
                        # owner while private transfers remain registered.
                        pass
                    if self._receiver.active_count == 0:
                        self._expiry_task = None
                        return
        except asyncio.CancelledError:
            return
        finally:
            if self._expiry_task is current:
                self._expiry_task = None


def _frame(
    value: Any,
    route: BrowserBridgeContextRoute,
) -> tuple[dict[str, Any], bytes]:
    if not isinstance(value, dict) or len(value) > 16:
        raise BrowserBridgeArtifactControllerError("INVALID_ARTIFACT_FRAME")
    request = dict(value)
    request.pop("correlationId", None)
    phase = request.get("phase")
    if (
        not isinstance(phase, str)
        or phase not in _PHASE_KEYS
        or set(request) != _COMMON_KEYS | _PHASE_KEYS[phase]
    ):
        raise BrowserBridgeArtifactControllerError("INVALID_ARTIFACT_FRAME")
    if type(request.get("contract_version")) is not int or request[
        "contract_version"
    ] != CONTRACT_VERSION:
        raise BrowserBridgeArtifactControllerError("VERSION_MISMATCH")
    for field in (
        "bridge_id",
        "load_generation_id",
        "context_id",
        "browser_session_id",
        "turn_id",
        "action_id",
        "op_id",
        "artifact_id",
    ):
        request[field] = _identifier(request[field], field)
    if (
        request["bridge_id"] != route.principal.principal_id
        or request["load_generation_id"] != route.load_generation_id
    ):
        raise BrowserBridgeArtifactControllerDenied("ARTIFACT_ROUTE_MISMATCH")
    if (
        request.get("direction") != "output"
        or not isinstance(request.get("purpose"), str)
        or request["purpose"] not in _OUTPUT_PURPOSES
    ):
        raise BrowserBridgeArtifactControllerDenied(
            "ARTIFACT_DIRECTION_UNAVAILABLE"
        )

    decoded = b""
    if phase == "begin":
        if not _safe_integer(request["byte_count"]) or request[
            "byte_count"
        ] > MAX_ARTIFACT_BYTES:
            raise BrowserBridgeArtifactControllerError("ARTIFACT_SIZE_INVALID")
        if not isinstance(request["sha256"], str) or _SHA256.fullmatch(
            request["sha256"]
        ) is None:
            raise BrowserBridgeArtifactControllerError("ARTIFACT_DIGEST_INVALID")
        if not isinstance(request["mime_type"], str) or _MIME_TYPE.fullmatch(
            request["mime_type"]
        ) is None:
            raise BrowserBridgeArtifactControllerError("ARTIFACT_MIME_INVALID")
    elif phase == "chunk":
        if not _safe_integer(request["chunk_index"]):
            raise BrowserBridgeArtifactControllerError("INVALID_CHUNK_INDEX")
        decoded = _canonical_base64(request["data_base64"])
    elif phase == "abort":
        if (
            not isinstance(request["reason_code"], str)
            or request["reason_code"] not in _SENDER_ABORT_REASONS
        ):
            raise BrowserBridgeArtifactControllerError("INVALID_ABORT_REASON")

    # Every variable-length field has already been bounded before this
    # serialization, so the frame check cannot allocate from attacker-sized
    # nested input.
    try:
        encoded = json.dumps(
            request, ensure_ascii=False, separators=(",", ":"), sort_keys=True
        ).encode("utf-8")
    except (TypeError, ValueError, UnicodeError):
        raise BrowserBridgeArtifactControllerError(
            "INVALID_ARTIFACT_FRAME"
        ) from None
    if len(encoded) > MAX_NATIVE_FRAME_BYTES:
        raise BrowserBridgeArtifactControllerError("ARTIFACT_FRAME_TOO_LARGE")
    return request, decoded


def _canonical_base64(value: Any) -> bytes:
    if (
        not isinstance(value, str)
        or not value
        or len(value) > MAX_BASE64_CHUNK_BYTES
        or not value.isascii()
    ):
        raise BrowserBridgeArtifactControllerError("CHUNK_SIZE_INVALID")
    try:
        decoded = base64.b64decode(value, validate=True)
    except (binascii.Error, ValueError):
        raise BrowserBridgeArtifactControllerError("INVALID_CHUNK_BASE64") from None
    if (
        not decoded
        or len(decoded) > MAX_CHUNK_BYTES
        or base64.b64encode(decoded).decode("ascii") != value
    ):
        raise BrowserBridgeArtifactControllerError("INVALID_CHUNK_BASE64")
    return decoded


def _acknowledgement(
    binding: ArtifactBinding,
    phase: str,
    request: dict[str, Any],
    outcome: ArtifactProgress | ArtifactDescriptor | bool,
) -> dict[str, Any]:
    result = _ack_binding(binding, phase)
    if phase in {"begin", "chunk"}:
        if not isinstance(outcome, ArtifactProgress):
            raise BrowserBridgeArtifactControllerError("INVALID_RECEIVER_RESULT")
        result.update(
            {
                "status": outcome.status,
                "next_chunk_index": outcome.next_chunk_index,
                "received_bytes": outcome.received_bytes,
            }
        )
    elif phase == "end":
        if not isinstance(outcome, ArtifactDescriptor):
            raise BrowserBridgeArtifactControllerError("INVALID_RECEIVER_RESULT")
        result.update({"status": "complete", "descriptor": outcome.as_dict()})
    else:
        if not isinstance(outcome, bool):
            raise BrowserBridgeArtifactControllerError("INVALID_RECEIVER_RESULT")
        result.update(
            {"status": "aborted", "reason_code": request["reason_code"]}
        )
    return result


def _abort_ack(
    binding: ArtifactBinding, phase: str, reason_code: str
) -> dict[str, Any]:
    result = _ack_binding(binding, phase)
    result.update({"status": "aborted", "reason_code": reason_code})
    return result


def _ack_binding(binding: ArtifactBinding, phase: str) -> dict[str, Any]:
    return {
        "contract_version": CONTRACT_VERSION,
        "phase": phase,
        "bridge_id": binding.bridge_id,
        "load_generation_id": binding.load_generation_id,
        "context_id": binding.context_id,
        "browser_session_id": binding.browser_session_id,
        "turn_id": binding.turn_id,
        "action_id": binding.action_id,
        "op_id": binding.op_id,
        "artifact_id": binding.artifact_id,
        "direction": binding.direction,
        "purpose": binding.purpose,
    }


def _binding_matches(
    binding: ArtifactBinding, lookup: ArtifactBindingLookup
) -> bool:
    return (
        binding.principal is lookup.route.principal
        and binding.connector_sid == lookup.route.connector_sid
        and binding.load_generation_id == lookup.route.load_generation_id
        and all(
            getattr(binding, field) == getattr(lookup, field)
            for field in (
                "bridge_id",
                "load_generation_id",
                "context_id",
                "browser_session_id",
                "turn_id",
                "action_id",
                "op_id",
                "artifact_id",
                "direction",
                "purpose",
            )
        )
        and binding.contract_version == CONTRACT_VERSION
    )


def _require_transport_scope(
    route: BrowserBridgeContextRoute,
    transport_profile: BrowserBridgeTransportProfile,
) -> None:
    profile = require_browser_bridge_transport_profile(transport_profile)
    principal = route.principal
    if (
        route.transport_profile is not profile
        or "browser.artifact" not in principal.scopes
        or not principal.permits_inbound(
            ARTIFACT_CHUNK_EVENT, profile.handler_id
        )
        or not principal.permits_outbound(
            ARTIFACT_ACK_EVENT, profile.handler_id
        )
    ):
        raise BrowserBridgeArtifactControllerDenied("SCOPE_DENIED")


def _route(value: Any) -> BrowserBridgeContextRoute:
    if not isinstance(value, BrowserBridgeContextRoute):
        raise BrowserBridgeArtifactControllerError("INVALID_ROUTE")
    return value


def _identifier(value: Any, field: str) -> str:
    if not isinstance(value, str) or _IDENTIFIER.fullmatch(value) is None:
        raise BrowserBridgeArtifactControllerError(f"INVALID_{field.upper()}")
    return value


def _safe_integer(value: Any) -> bool:
    return (
        not isinstance(value, bool)
        and isinstance(value, int)
        and 0 <= value <= MAX_SAFE_INTEGER
    )
