"""Inactive, principal-bound composition for the Browser bridge runtime.

Hello metadata is parsed as an untrusted capability claim.  A route exists only
while an injected verifier confirms the current server-owned principal and an
independent evaluator supplies a complete typed runtime admission.  This module
does not register WebSocket events, alter the hello-only authentication surface,
or consult the legacy connector runtime registry.
"""

from __future__ import annotations

from dataclasses import dataclass
import re
import threading
import time
from typing import Any, Awaitable, Callable, Mapping

from helpers.ws_principal import WsPrincipal
from plugins._a0_connector.helpers.browser_bridge_approval import (
    BrowserApprovalRoute,
)
from plugins._a0_connector.helpers.browser_bridge_artifacts import ArtifactBinding
from plugins._a0_connector.helpers.browser_bridge_context import (
    BrowserBridgeContextAccess,
    BrowserBridgeContextRoute,
)
from plugins._a0_connector.helpers.browser_bridge_operations import (
    BridgeAuthorization,
    BrowserBridgeOperationBroker,
    ControlBinding,
    OperationBinding,
    ReconciliationBinding,
    SettlementStatus,
    TurnBinding,
)
from plugins._a0_connector.helpers.browser_bridge_transport import (
    PRODUCTION_BROWSER_BRIDGE_TRANSPORT,
    RUNTIME_REQUIRED_INBOUND_EVENTS,
    RUNTIME_REQUIRED_OUTBOUND_EVENTS,
    RUNTIME_REQUIRED_SCOPES,
    BrowserBridgeTransportProfile,
    require_browser_bridge_transport_profile,
    require_runtime_transport_principal,
    runtime_transport_profile_for_principal,
)
from plugins._browser.helpers.extension_sessions import ValidatedExtensionRoute


CONNECTOR_PROTOCOL = "a0-connector.v1"
CONTRACT_VERSION = 1
RESTRICTED_HANDLER_ID = PRODUCTION_BROWSER_BRIDGE_TRANSPORT.handler_id
RESTRICTED_HANDLER_PATH = PRODUCTION_BROWSER_BRIDGE_TRANSPORT.handler_path
WS_NAMESPACE = PRODUCTION_BROWSER_BRIDGE_TRANSPORT.namespace

OPERATION_EVENT = "connector_browser_op"
CONTROL_EVENT = "connector_browser_control"
_BROKER_OUTBOUND_EVENTS = frozenset({OPERATION_EVENT, CONTROL_EVENT})

REQUIRED_OUTER_FEATURES = frozenset(
    {
        "browser_extension_bridge_v1",
        "connector_browser_control",
        "connector_browser_event",
        "connector_browser_artifact_chunks",
    }
)
REQUIRED_SCOPES = RUNTIME_REQUIRED_SCOPES
REQUIRED_INBOUND_EVENTS = RUNTIME_REQUIRED_INBOUND_EVENTS
REQUIRED_OUTBOUND_EVENTS = RUNTIME_REQUIRED_OUTBOUND_EVENTS

PROVEN_ACTIONS = frozenset(
    {"open", "list", "state", "navigate", "content", "scroll", "hover", "click", "type", "upload_file", "status", "ensure", "screenshot"}
)
PROVEN_FEATURES = frozenset(
    {"tab_leases_v1", "tab_groups_v1", "semantic_dom_v1", "cursor_v1", "trusted_input_v1", "screenshots_v1", "artifacts_v1"}
)
MINIMUM_SECURE_COMPANION = (2, 12, 0)
EXPECTED_LIMITS = (
    ("artifact_chunk_bytes", 192 * 1024),
    ("max_artifact_bytes", 25 * 1024 * 1024),
    ("max_json_frame_bytes", 768 * 1024),
)

MAX_RUNTIME_SESSIONS = 32
MAX_CAPABILITIES = 64
MAX_IDENTIFIER_BYTES = 256
MAX_LABEL_BYTES = 192

_NATIVE_IDENTIFIER = re.compile(r"[A-Za-z0-9][A-Za-z0-9._:-]{0,255}")
_EXTENSION_ID = re.compile(r"[a-p]{32}")
_VERSION = re.compile(r"[0-9A-Za-z][0-9A-Za-z.+_-]{0,63}")
_PLATFORMS = frozenset({"darwin", "linux", "windows"})
_ARCHITECTURES = frozenset({"aarch64", "arm64", "universal2", "x86_64"})


class BrowserBridgeRuntimeError(ValueError):
    """A runtime route or hello claim is malformed."""


class BrowserBridgeRuntimeDenied(PermissionError):
    """Current server authority or complete runtime admission is unavailable."""

    def __init__(self, code: str) -> None:
        super().__init__(code)
        self.code = code


@dataclass(frozen=True, slots=True)
class VerifiedActivePrincipal:
    """Server-owned identity returned by the injected active-record verifier."""

    principal: WsPrincipal
    server_instance_id: str
    extension_id: str
    companion_instance_id: str

    def __post_init__(self) -> None:
        _validate_known_runtime_principal(self.principal)
        _identifier(self.server_instance_id, "server_instance_id")
        _extension_id(self.extension_id)
        _native_identifier(self.companion_instance_id, "companion_instance_id")


@dataclass(frozen=True, slots=True)
class NormalizedBridgeHello:
    """Bounded non-authoritative projection of protocol section 4.3."""

    bridge_id: str
    browser_id: str
    browser_label: str
    load_generation_id: str
    install_instance_id: str
    extension_id: str
    extension_version: str
    companion_instance_id: str
    companion_version: str
    companion_platform: str
    companion_arch: str
    contract_version: int
    outer_features: frozenset[str]
    actions: frozenset[str]
    features: frozenset[str]
    limits: tuple[tuple[str, int], ...]

    def __post_init__(self) -> None:
        for name in ("outer_features", "actions", "features"):
            object.__setattr__(self, name, frozenset(getattr(self, name)))
        object.__setattr__(self, "limits", tuple(self.limits))


@dataclass(frozen=True, slots=True)
class RuntimeActivationAttestation:
    """Short-lived server-owned selection/heartbeat/profile/cutover evidence.

    No production constructor derives this from hello claims or ready flags.
    The evaluator must repeat each underlying check on every route lookup.
    """

    principal: WsPrincipal
    server_instance_id: str
    connector_sid: str
    load_generation_id: str
    extension_id: str
    install_instance_id: str
    server_features: frozenset[str]
    rollout: str
    selected_bridge: bool
    heartbeat_fresh: bool
    subject_profile_bound: bool
    legacy_control_plane_inactive: bool
    issued_at_ms: int
    expires_at_ms: int

    def __post_init__(self) -> None:
        _validate_runtime_principal(
            self.principal, PRODUCTION_BROWSER_BRIDGE_TRANSPORT
        )
        object.__setattr__(self, "server_features", frozenset(self.server_features))

    def as_wire_dict(self) -> dict[str, Any]:
        _validate_runtime_principal(
            self.principal, PRODUCTION_BROWSER_BRIDGE_TRANSPORT
        )
        now = time.time_ns() // 1_000_000
        if not _activation_fresh(self, now):
            raise BrowserBridgeRuntimeDenied("ACTIVATION_EXPIRED")
        return {
            "principal": "browser_bridge", "bridge_id": self.principal.principal_id,
            "key_generation": self.principal.key_generation, "extension_id": self.extension_id,
            "install_instance_id": self.install_instance_id, "server_features": sorted(self.server_features),
            "rollout": self.rollout, "selected_bridge": self.selected_bridge,
            "heartbeat_fresh": self.heartbeat_fresh, "subject_profile_bound": self.subject_profile_bound,
            "legacy_control_plane_inactive": self.legacy_control_plane_inactive,
        }


@dataclass(frozen=True, slots=True)
class CompleteRuntimeAdmission:
    """Independent, exact attestation that every runtime boundary is present."""

    principal: WsPrincipal
    server_instance_id: str
    connector_sid: str
    load_generation_id: str
    install_instance_id: str
    contract_version: int
    outer_features: frozenset[str]
    actions: frozenset[str]
    features: frozenset[str]
    release_trust_ready: bool
    activation_attested: bool
    legacy_control_plane_inactive: bool
    operation_transport_ready: bool
    control_transport_ready: bool
    context_transport_ready: bool
    event_transport_ready: bool
    artifact_transport_ready: bool
    approval_transport_ready: bool
    session_lifecycle_ready: bool
    policy_enforcement_ready: bool
    activation: RuntimeActivationAttestation | None = None

    def __post_init__(self) -> None:
        _validate_runtime_principal(
            self.principal, PRODUCTION_BROWSER_BRIDGE_TRANSPORT
        )
        for name in ("outer_features", "actions", "features"):
            object.__setattr__(self, name, frozenset(getattr(self, name)))


@dataclass(frozen=True, slots=True)
class BrowserBridgeRuntimeRoute:
    """One admitted process-only route scoped to the current server instance."""

    server_instance_id: str
    principal: WsPrincipal
    connector_sid: str
    hello: NormalizedBridgeHello
    activation: RuntimeActivationAttestation
    transport_profile: BrowserBridgeTransportProfile = (
        PRODUCTION_BROWSER_BRIDGE_TRANSPORT
    )

    def __post_init__(self) -> None:
        profile = require_browser_bridge_transport_profile(self.transport_profile)
        _validate_runtime_principal(self.principal, profile)
        if profile is not PRODUCTION_BROWSER_BRIDGE_TRANSPORT:
            raise BrowserBridgeRuntimeDenied("RUNTIME_NOT_ADMITTED")
        if (
            not isinstance(self.activation, RuntimeActivationAttestation)
            or self.activation.principal is not self.principal
        ):
            raise BrowserBridgeRuntimeDenied("RUNTIME_NOT_ADMITTED")

    @property
    def bridge_id(self) -> str:
        return self.principal.principal_id

    @property
    def browser_id(self) -> str:
        return self.hello.browser_id

    @property
    def load_generation_id(self) -> str:
        return self.hello.load_generation_id

    def as_extension_route(self) -> ValidatedExtensionRoute:
        return ValidatedExtensionRoute(
            bridge_id=self.bridge_id,
            browser_id=self.browser_id,
            principal=self.principal,
            connector_sid=self.connector_sid,
            load_generation_id=self.load_generation_id,
            transport_profile=self.transport_profile,
        )


ActivePrincipalVerifier = Callable[[WsPrincipal], VerifiedActivePrincipal | None]
AdmissionEvaluator = Callable[
    [VerifiedActivePrincipal, str, NormalizedBridgeHello],
    CompleteRuntimeAdmission | None,
]
ContextAuthorizer = Callable[[BrowserBridgeRuntimeRoute, str], bool]
RouteCleanup = Callable[[WsPrincipal, str, str], None]
BrokerSender = Callable[
    [str, str, dict[str, Any], str, WsPrincipal], Awaitable[None]
]


class BrowserBridgeRuntimeRegistry:
    """Bounded current-route registry and restricted broker composition."""

    def __init__(
        self,
        *,
        sender: BrokerSender | None = None,
        active_principal_verifier: ActivePrincipalVerifier | None = None,
        admission_evaluator: AdmissionEvaluator | None = None,
        context_authorizer: ContextAuthorizer | None = None,
        cleanup_callbacks: tuple[RouteCleanup, ...] = (),
        max_sessions: int = MAX_RUNTIME_SESSIONS,
        transport_profile: BrowserBridgeTransportProfile = (
            PRODUCTION_BROWSER_BRIDGE_TRANSPORT
        ),
    ) -> None:
        self._transport_profile = require_browser_bridge_transport_profile(
            transport_profile
        )
        if isinstance(max_sessions, bool) or not 1 <= max_sessions <= 1_024:
            raise ValueError("runtime session bound must be positive")
        if not isinstance(cleanup_callbacks, tuple) or any(
            not callable(callback) for callback in cleanup_callbacks
        ):
            raise ValueError("invalid runtime cleanup callbacks")
        self._active_principal_verifier = (
            active_principal_verifier or (lambda _principal: None)
        )
        self._admission_evaluator = (
            admission_evaluator or (lambda _active, _sid, _hello: None)
        )
        self._context_authorizer = (
            context_authorizer or (lambda _route, _context_id: False)
        )
        self._cleanup_callbacks = cleanup_callbacks
        self._max_sessions = max_sessions
        self._by_sid: dict[str, BrowserBridgeRuntimeRoute] = {}
        self._sid_by_bridge: dict[str, str] = {}
        self._reconciling: dict[str, ReconciliationBinding] = {}
        self._reconciled: set[str] = set()
        self._lock = threading.RLock()
        self._broker = BrowserBridgeOperationBroker(
            sender=sender or _unavailable_sender,
            authorizer=self.authorize_broker,
            transport_profile=self._transport_profile,
        )

    @property
    def broker(self) -> BrowserBridgeOperationBroker:
        return self._broker

    @property
    def session_count(self) -> int:
        with self._lock:
            return len(self._by_sid)

    def current_sid_route(self, principal: WsPrincipal, connector_sid: str) -> BrowserBridgeRuntimeRoute | None:
        """Resolve only server-retained generation; callers cannot pick one."""
        with self._lock:
            route = self._by_sid.get(connector_sid)
        if route is None or route.principal is not principal:
            return None
        return self._current_exact_route(principal, connector_sid, route.load_generation_id)

    def retire_bridge(self, bridge_id: str) -> BrowserBridgeRuntimeRoute | None:
        """Withdraw one exact bridge before a server selection/config changes."""
        with self._lock:
            sid = self._sid_by_bridge.get(bridge_id)
            route = self._by_sid.get(sid) if sid is not None else None
            if route is None:
                return None
            self._remove_locked(route)
        self._cleanup(route)
        return route

    def retire_all(self) -> tuple[BrowserBridgeRuntimeRoute, ...]:
        """Withdraw only this owner's routes before shutdown cleanup."""
        with self._lock:
            routes = tuple(self._by_sid.values())
            for route in routes:
                self._remove_locked(route)
        for route in routes:
            self._cleanup(route)
        return routes

    def retire_sid(self, principal: WsPrincipal, connector_sid: str) -> BrowserBridgeRuntimeRoute | None:
        """Cleanup remains possible after revocation makes current checks fail."""
        with self._lock:
            route = self._by_sid.get(connector_sid)
            if route is None or route.principal is not principal:
                return None
            self._remove_locked(route)
        self._cleanup(route)
        return route

    def register_hello(
        self,
        *,
        principal: WsPrincipal,
        connector_sid: Any,
        data: Any,
    ) -> BrowserBridgeRuntimeRoute:
        sid = _identifier(connector_sid, "connector_sid")
        active = self._verify_active(principal)
        hello = normalize_bridge_hello(
            principal, active, data, transport_profile=self._transport_profile
        )
        self._require_admission(active, sid, hello)
        self._prune_stale_routes()

        for _attempt in range(4):
            with self._lock:
                conflicts = self._conflicts_locked(sid, principal.principal_id)
            stale_or_equivalent: list[BrowserBridgeRuntimeRoute] = []
            active_conflict = False
            for route in conflicts:
                if _equivalent_principal(route.principal, principal):
                    stale_or_equivalent.append(route)
                elif self._route_is_current(route):
                    active_conflict = True
                else:
                    stale_or_equivalent.append(route)
            if active_conflict:
                raise BrowserBridgeRuntimeDenied("ROUTE_CONFLICT")

            active = self._verify_active(principal)
            hello = normalize_bridge_hello(
                principal,
                active,
                data,
                transport_profile=self._transport_profile,
            )
            admission = self._require_admission(active, sid, hello)
            route = BrowserBridgeRuntimeRoute(
                server_instance_id=active.server_instance_id,
                principal=principal,
                connector_sid=sid,
                hello=hello,
                activation=admission.activation,
                transport_profile=self._transport_profile,
            )
            with self._lock:
                if not _same_route_objects(
                    self._conflicts_locked(sid, principal.principal_id), conflicts
                ):
                    continue
                exact_replay = bool(
                    len(conflicts) == 1
                    and conflicts[0].principal is principal
                    and conflicts[0].connector_sid == sid
                    and conflicts[0].server_instance_id == active.server_instance_id
                    and conflicts[0].hello == hello
                )
                if exact_replay:
                    # Refresh the short-lived server attestation without
                    # treating the same authenticated hello as a disconnect.
                    self._by_sid[sid] = route
                    self._sid_by_bridge[route.bridge_id] = sid
                    replacing = ()
                else:
                    replacing = tuple(stale_or_equivalent)
                    if len(self._by_sid) - len(replacing) >= self._max_sessions:
                        raise BrowserBridgeRuntimeDenied("SESSION_LIMIT")
                    for previous in replacing:
                        self._remove_locked(previous)
                    self._by_sid[sid] = route
                    self._sid_by_bridge[route.bridge_id] = sid
            for previous in replacing:
                self._cleanup(previous)
            if not self._route_is_current(route):
                self._retire(route)
                raise BrowserBridgeRuntimeDenied("RUNTIME_NOT_ADMITTED")
            return route
        raise BrowserBridgeRuntimeDenied("ROUTE_BUSY")

    def resolve_extension_route(
        self,
        context_id: Any,
        bridge_id: Any,
    ) -> ValidatedExtensionRoute | None:
        try:
            context = _identifier(context_id, "context_id")
            bridge = _identifier(bridge_id, "bridge_id")
            route = self._current_bridge_route(bridge)
            if route is None or route.browser_id != f"extension:{bridge}":
                return None
            if not self._context_is_authorized(route, context):
                return None
            return route.as_extension_route()
        except Exception:
            return None

    def authorize_broker(
        self,
        binding: OperationBinding | TurnBinding | ControlBinding,
    ) -> BridgeAuthorization | None:
        if not isinstance(binding, (OperationBinding, TurnBinding, ControlBinding, ReconciliationBinding)):
            return None
        route = self._current_exact_route(
            binding.principal,
            binding.connector_sid,
            binding.load_generation_id,
        )
        if route is None:
            return None
        if isinstance(binding, ReconciliationBinding):
            if not self.route_current_for_reconciliation(binding):
                return None
        elif not self._context_is_authorized(route, binding.context_id):
            return None
        return BridgeAuthorization(
            principal=route.principal,
            connector_sid=route.connector_sid,
            load_generation_id=route.load_generation_id,
            contract_version=route.hello.contract_version,
            outer_features=route.hello.outer_features,
            actions=route.hello.actions,
            features=route.hello.features,
        )

    def authorize_context_route(self, route: BrowserBridgeContextRoute) -> bool:
        if (
            not isinstance(route, BrowserBridgeContextRoute)
            or route.transport_profile is not self._transport_profile
        ):
            return False
        current = self._current_exact_route(
            route.principal,
            route.connector_sid,
            route.load_generation_id,
        )
        return current is not None and self._is_reconciled(current)

    def authorize_approval_route(self, route: BrowserApprovalRoute) -> bool:
        if (
            not isinstance(route, BrowserApprovalRoute)
            or route.transport_profile is not self._transport_profile
        ):
            return False
        current = self._current_exact_route(
            route.principal,
            route.connector_sid,
            route.load_generation_id,
        )
        return bool(
            current is not None
            and current.server_instance_id == route.server_instance_id
            and self._context_is_authorized(current, route.context_id)
        )

    def authorize_artifact_route(
        self,
        *,
        principal: WsPrincipal,
        connector_sid: Any,
        load_generation_id: Any,
        context_id: Any,
    ) -> bool:
        try:
            sid = _identifier(connector_sid, "connector_sid")
            generation = _native_identifier(
                load_generation_id, "load_generation_id"
            )
            context = _identifier(context_id, "context_id")
        except BrowserBridgeRuntimeError:
            return False
        route = self._current_exact_route(principal, sid, generation)
        return bool(route is not None and self._context_is_authorized(route, context))

    def authorize_artifact_binding(self, binding: ArtifactBinding) -> bool:
        if (
            not isinstance(binding, ArtifactBinding)
            or binding.transport_profile is not self._transport_profile
        ):
            return False
        if binding.bridge_id != binding.principal.principal_id:
            return False
        return self.authorize_artifact_route(
            principal=binding.principal,
            connector_sid=binding.connector_sid,
            load_generation_id=binding.load_generation_id,
            context_id=binding.context_id,
        )

    def settle_operation(
        self,
        *,
        principal: WsPrincipal,
        connector_sid: Any,
        load_generation_id: Any,
        payload: Mapping[str, Any],
    ) -> str:
        if self._settlement_route(principal, connector_sid, load_generation_id) is None:
            return SettlementStatus.MISMATCH
        return self._broker.settle_operation(
            principal=principal,
            connector_sid=connector_sid,
            load_generation_id=load_generation_id,
            payload=payload,
        )

    def settle_control(
        self,
        *,
        principal: WsPrincipal,
        connector_sid: Any,
        load_generation_id: Any,
        payload: Mapping[str, Any],
    ) -> str:
        if self._settlement_route(principal, connector_sid, load_generation_id) is None:
            return SettlementStatus.MISMATCH
        return self._broker.settle_control(
            principal=principal,
            connector_sid=connector_sid,
            load_generation_id=load_generation_id,
            payload=payload,
        )

    def disconnect(
        self,
        *,
        principal: WsPrincipal,
        connector_sid: Any,
        load_generation_id: Any,
    ) -> bool:
        try:
            sid = _identifier(connector_sid, "connector_sid")
            generation = _native_identifier(
                load_generation_id, "load_generation_id"
            )
        except BrowserBridgeRuntimeError:
            return False
        with self._lock:
            route = self._by_sid.get(sid)
            if (
                route is None
                or route.principal is not principal
                or route.load_generation_id != generation
            ):
                return False
            self._remove_locked(route)
        self._cleanup(route)
        return True

    def _settlement_route(
        self,
        principal: WsPrincipal,
        connector_sid: Any,
        load_generation_id: Any,
    ) -> BrowserBridgeRuntimeRoute | None:
        try:
            sid = _identifier(connector_sid, "connector_sid")
            generation = _native_identifier(
                load_generation_id, "load_generation_id"
            )
        except BrowserBridgeRuntimeError:
            return None
        return self._current_exact_route(principal, sid, generation)

    def current_bridge_ready(self, bridge_id: str) -> bool:
        """Redacted readiness only; never authorizes a context or operation."""
        route = self._current_bridge_route(bridge_id)
        return route is not None and self._is_reconciled(route)

    def begin_reconciliation(self, binding: ReconciliationBinding) -> bool:
        if not isinstance(binding, ReconciliationBinding) or binding.transport_profile is not self._transport_profile:
            return False
        route = self._current_exact_route(binding.principal, binding.connector_sid, binding.load_generation_id)
        with self._lock:
            if route is None or self._by_sid.get(binding.connector_sid) is not route or binding.connector_sid in self._reconciling:
                return False
            self._reconciling[binding.connector_sid] = binding
            return True

    def route_current_for_reconciliation(self, binding: ReconciliationBinding) -> bool:
        if not isinstance(binding, ReconciliationBinding) or binding.transport_profile is not self._transport_profile:
            return False
        route = self._current_exact_route(binding.principal, binding.connector_sid, binding.load_generation_id)
        with self._lock:
            return route is not None and self._by_sid.get(binding.connector_sid) is route and self._reconciling.get(binding.connector_sid) is binding

    def promote_reconciled(self, binding, summary) -> bool:
        from plugins._a0_connector.helpers.browser_bridge_reconciliation import BrowserBridgeReconciliationSummary
        if not isinstance(summary, BrowserBridgeReconciliationSummary) or not self.route_current_for_reconciliation(binding):
            return False
        with self._lock:
            route = self._by_sid.get(binding.connector_sid)
            if (route is None or route.principal is not binding.principal
                    or route.load_generation_id != binding.load_generation_id
                    or self._reconciling.get(binding.connector_sid) is not binding):
                return False
            self._reconciled.add(binding.connector_sid)
            return True

    def _is_reconciled(self, route) -> bool:
        with self._lock:
            return self._by_sid.get(route.connector_sid) is route and route.connector_sid in self._reconciled

    def _current_bridge_route(
        self, bridge_id: str
    ) -> BrowserBridgeRuntimeRoute | None:
        with self._lock:
            sid = self._sid_by_bridge.get(bridge_id)
            route = self._by_sid.get(sid) if sid is not None else None
        if route is None or route.bridge_id != bridge_id:
            return None
        if not self._route_is_current(route):
            self._retire(route)
            return None
        return route

    def _current_exact_route(
        self,
        principal: WsPrincipal,
        connector_sid: str,
        load_generation_id: str,
    ) -> BrowserBridgeRuntimeRoute | None:
        with self._lock:
            route = self._by_sid.get(connector_sid)
        if (
            route is None
            or route.principal is not principal
            or route.load_generation_id != load_generation_id
        ):
            return None
        if not self._route_is_current(route):
            self._retire(route)
            return None
        return route

    def _context_is_authorized(
        self,
        route: BrowserBridgeRuntimeRoute,
        context_id: str,
    ) -> bool:
        if not self._is_reconciled(route):
            return False
        try:
            authorized = self._context_authorizer(route, context_id) is True
        except Exception:
            authorized = False
        if not authorized:
            return False
        if not self._route_is_current(route):
            self._retire(route)
            return False
        return True

    def _route_is_current(self, route: BrowserBridgeRuntimeRoute) -> bool:
        try:
            active = self._verify_active(route.principal)
            if active.server_instance_id != route.server_instance_id:
                return False
            normalize_bridge_hello(
                route.principal,
                active,
                _hello_mapping(route.hello),
                transport_profile=self._transport_profile,
            )
            self._require_admission(active, route.connector_sid, route.hello)
            return True
        except Exception:
            return False

    def _verify_active(self, principal: WsPrincipal) -> VerifiedActivePrincipal:
        _validate_runtime_principal(principal, self._transport_profile)
        try:
            active = self._active_principal_verifier(principal)
        except Exception:
            active = None
        if not isinstance(active, VerifiedActivePrincipal) or active.principal is not principal:
            raise BrowserBridgeRuntimeDenied("PRINCIPAL_NOT_ACTIVE")
        return active

    def _require_admission(
        self,
        active: VerifiedActivePrincipal,
        connector_sid: str,
        hello: NormalizedBridgeHello,
    ) -> CompleteRuntimeAdmission:
        if self._transport_profile is not PRODUCTION_BROWSER_BRIDGE_TRANSPORT:
            raise BrowserBridgeRuntimeDenied("RUNTIME_NOT_ADMITTED")
        try:
            admission = self._admission_evaluator(active, connector_sid, hello)
        except Exception:
            admission = None
        if not _admission_matches(admission, active, connector_sid, hello):
            raise BrowserBridgeRuntimeDenied("RUNTIME_NOT_ADMITTED")
        return admission

    def _conflicts_locked(
        self,
        connector_sid: str,
        bridge_id: str,
    ) -> tuple[BrowserBridgeRuntimeRoute, ...]:
        values: list[BrowserBridgeRuntimeRoute] = []
        by_sid = self._by_sid.get(connector_sid)
        if by_sid is not None:
            values.append(by_sid)
        prior_sid = self._sid_by_bridge.get(bridge_id)
        by_bridge = self._by_sid.get(prior_sid) if prior_sid is not None else None
        if by_bridge is not None and all(by_bridge is not item for item in values):
            values.append(by_bridge)
        return tuple(values)

    def _prune_stale_routes(self) -> None:
        with self._lock:
            routes = tuple(self._by_sid.values())
        for route in routes:
            if not self._route_is_current(route):
                self._retire(route)

    def _remove_locked(self, route: BrowserBridgeRuntimeRoute) -> bool:
        if self._by_sid.get(route.connector_sid) is not route:
            return False
        self._by_sid.pop(route.connector_sid, None)
        self._reconciling.pop(route.connector_sid, None)
        self._reconciled.discard(route.connector_sid)
        if self._sid_by_bridge.get(route.bridge_id) == route.connector_sid:
            self._sid_by_bridge.pop(route.bridge_id, None)
        return True

    def _retire(self, route: BrowserBridgeRuntimeRoute) -> None:
        with self._lock:
            removed = self._remove_locked(route)
        if removed:
            self._cleanup(route)

    def _cleanup(self, route: BrowserBridgeRuntimeRoute) -> None:
        callbacks: tuple[RouteCleanup, ...] = (
            lambda principal, sid, generation: self._broker.disconnect(
                principal=principal,
                connector_sid=sid,
                load_generation_id=generation,
            ),
            *self._cleanup_callbacks,
        )
        for callback in callbacks:
            try:
                callback(
                    route.principal,
                    route.connector_sid,
                    route.load_generation_id,
                )
            except Exception:
                continue


def normalize_bridge_hello(
    principal: WsPrincipal,
    active: VerifiedActivePrincipal,
    data: Any,
    *,
    transport_profile: BrowserBridgeTransportProfile = (
        PRODUCTION_BROWSER_BRIDGE_TRANSPORT
    ),
) -> NormalizedBridgeHello:
    """Strictly project one section-4.3 hello without granting authority."""
    profile = require_browser_bridge_transport_profile(transport_profile)
    _validate_runtime_principal(principal, profile)
    if not isinstance(active, VerifiedActivePrincipal) or active.principal is not principal:
        raise BrowserBridgeRuntimeError("active principal mismatch")
    root = _exact_mapping(data, {"protocol", "features", "host_browser"}, "hello")
    if root["protocol"] != CONNECTOR_PROTOCOL:
        raise BrowserBridgeRuntimeError("invalid connector protocol")
    outer_features = _capability_set(
        root["features"], REQUIRED_OUTER_FEATURES, "outer features"
    )
    if outer_features != REQUIRED_OUTER_FEATURES:
        raise BrowserBridgeRuntimeError("incomplete outer features")

    host = _exact_mapping(
        root["host_browser"],
        {
            "supported",
            "enabled",
            "status",
            "backend_id",
            "browser_id",
            "browser_label",
            "contract_version",
            "features",
            "capabilities",
            "extension",
            "companion",
        },
        "host browser",
    )
    bridge_id = principal.principal_id
    browser_id = f"extension:{bridge_id}"
    if (
        host["supported"] is not True
        or host["enabled"] is not True
        or host["status"] != "ready"
        or host["backend_id"] != "chrome_extension"
        or host["browser_id"] != browser_id
        or type(host["contract_version"]) is not int
        or host["contract_version"] != CONTRACT_VERSION
    ):
        raise BrowserBridgeRuntimeError("invalid extension backend")
    browser_label = _bounded_text(host["browser_label"], MAX_LABEL_BYTES, "browser label")
    host_features = _capability_set(
        host["features"], {"browser_extension_bridge_v1"}, "host features"
    )
    if host_features != frozenset({"browser_extension_bridge_v1"}):
        raise BrowserBridgeRuntimeError("invalid host features")

    capabilities = _exact_mapping(
        host["capabilities"], {"actions", "features", "limits"}, "capabilities"
    )
    actions = _capability_set(capabilities["actions"], PROVEN_ACTIONS, "actions")
    features = _capability_set(
        capabilities["features"], PROVEN_FEATURES, "features"
    )
    if len(actions) + len(features) > MAX_CAPABILITIES:
        raise BrowserBridgeRuntimeError("capability limit exceeded")
    limits = _limits(capabilities["limits"])

    extension = _exact_mapping(
        host["extension"],
        {
            "id",
            "version",
            "manifest_version",
            "install_instance_id",
            "load_generation_id",
        },
        "extension",
    )
    extension_id = _extension_id(extension["id"])
    if extension_id != active.extension_id or extension["manifest_version"] != 3:
        raise BrowserBridgeRuntimeError("extension identity mismatch")
    extension_version = _version(extension["version"], "extension version")
    install_instance_id = _native_identifier(
        extension["install_instance_id"], "install_instance_id"
    )
    load_generation_id = _native_identifier(
        extension["load_generation_id"], "load_generation_id"
    )

    companion = _exact_mapping(
        host["companion"],
        {"instance_id", "version", "platform", "arch"},
        "companion",
    )
    companion_instance_id = _native_identifier(
        companion["instance_id"], "companion_instance_id"
    )
    if companion_instance_id != active.companion_instance_id:
        raise BrowserBridgeRuntimeError("companion identity mismatch")
    companion_version = _version(companion["version"], "companion version")
    if (re.fullmatch(r"(?:0|[1-9][0-9]*)\.(?:0|[1-9][0-9]*)\.(?:0|[1-9][0-9]*)", companion_version) is None
            or tuple(map(int, companion_version.split("."))) < MINIMUM_SECURE_COMPANION):
        raise BrowserBridgeRuntimeError("incompatible companion version")
    if companion["platform"] not in _PLATFORMS or companion["arch"] not in _ARCHITECTURES:
        raise BrowserBridgeRuntimeError("invalid companion target")

    return NormalizedBridgeHello(
        bridge_id=bridge_id,
        browser_id=browser_id,
        browser_label=browser_label,
        load_generation_id=load_generation_id,
        install_instance_id=install_instance_id,
        extension_id=extension_id,
        extension_version=extension_version,
        companion_instance_id=companion_instance_id,
        companion_version=companion_version,
        companion_platform=companion["platform"],
        companion_arch=companion["arch"],
        contract_version=CONTRACT_VERSION,
        outer_features=outer_features,
        actions=actions,
        features=features,
        limits=limits,
    )


def restricted_browser_sender(
    manager: Any,
    *,
    transport_profile: BrowserBridgeTransportProfile = (
        PRODUCTION_BROWSER_BRIDGE_TRANSPORT
    ),
) -> BrokerSender:
    """Build the only allowed broker transport over the shared WS manager."""
    profile = require_browser_bridge_transport_profile(transport_profile)
    if not callable(getattr(manager, "emit_to", None)):
        raise BrowserBridgeRuntimeError("invalid WebSocket manager")

    async def send(
        connector_sid: str,
        event: str,
        payload: dict[str, Any],
        correlation_id: str,
        principal: WsPrincipal,
    ) -> None:
        if event not in _BROKER_OUTBOUND_EVENTS:
            raise BrowserBridgeRuntimeDenied("EVENT_NOT_ALLOWED")
        _validate_runtime_principal(principal, profile)
        await manager.emit_to(
            profile.namespace,
            connector_sid,
            event,
            payload,
            handler_id=profile.handler_id,
            correlation_id=correlation_id,
            expected_principal=principal,
        )

    return send


def context_access_authorizer(
    access: BrowserBridgeContextAccess,
) -> ContextAuthorizer:
    """Adapt the purpose-built advertised-context boundary for route selection."""
    if not isinstance(access, BrowserBridgeContextAccess):
        raise BrowserBridgeRuntimeError("invalid context access")

    def authorize(route: BrowserBridgeRuntimeRoute, context_id: str) -> bool:
        try:
            access.authorize_message_target(
                BrowserBridgeContextRoute(
                    principal=route.principal,
                    connector_sid=route.connector_sid,
                    load_generation_id=route.load_generation_id,
                    transport_profile=route.transport_profile,
                ),
                context_id=context_id,
            )
            return True
        except Exception:
            return False

    return authorize


def exact_route_cleanup(target: Any) -> RouteCleanup:
    """Adapt a context, approval, or artifact disconnect boundary exactly."""
    disconnect = getattr(target, "disconnect", None)
    if not callable(disconnect):
        raise BrowserBridgeRuntimeError("invalid route cleanup target")

    def cleanup(
        principal: WsPrincipal,
        connector_sid: str,
        load_generation_id: str,
    ) -> None:
        disconnect(
            principal=principal,
            connector_sid=connector_sid,
            load_generation_id=load_generation_id,
        )

    return cleanup


async def _unavailable_sender(
    _connector_sid: str,
    _event: str,
    _payload: dict[str, Any],
    _correlation_id: str,
    _principal: WsPrincipal,
) -> None:
    raise BrowserBridgeRuntimeDenied("TRANSPORT_NOT_CONFIGURED")


def _admission_matches(
    value: CompleteRuntimeAdmission | None,
    active: VerifiedActivePrincipal,
    connector_sid: str,
    hello: NormalizedBridgeHello,
) -> bool:
    if not isinstance(value, CompleteRuntimeAdmission):
        return False
    try:
        _validate_runtime_principal(
            active.principal, PRODUCTION_BROWSER_BRIDGE_TRANSPORT
        )
        _validate_runtime_principal(
            value.principal, PRODUCTION_BROWSER_BRIDGE_TRANSPORT
        )
    except BrowserBridgeRuntimeDenied:
        return False
    readiness = (
        value.release_trust_ready,
        value.activation_attested,
        value.legacy_control_plane_inactive,
        value.operation_transport_ready,
        value.control_transport_ready,
        value.context_transport_ready,
        value.event_transport_ready,
        value.artifact_transport_ready,
        value.approval_transport_ready,
        value.session_lifecycle_ready,
        value.policy_enforcement_ready,
    )
    return bool(
        value.principal is active.principal
        and value.server_instance_id == active.server_instance_id
        and value.connector_sid == connector_sid
        and value.load_generation_id == hello.load_generation_id
        and value.install_instance_id == hello.install_instance_id
        and value.contract_version == hello.contract_version
        and value.outer_features == hello.outer_features
        and value.actions == hello.actions
        and value.features == hello.features
        and all(type(item) is bool and item is True for item in readiness)
        and _activation_matches(value.activation, active, connector_sid, hello)
    )


def _activation_fresh(value: RuntimeActivationAttestation, now: int) -> bool:
    return bool(
        type(value.issued_at_ms) is int and type(value.expires_at_ms) is int
        and 0 < value.issued_at_ms <= now < value.expires_at_ms <= 2**53 - 1
        and value.expires_at_ms - value.issued_at_ms <= 30_000
        and isinstance(value.rollout, str) and value.rollout in {"available", "preview_authorized"}
        and all(type(flag) is bool and flag is True for flag in (
            value.selected_bridge, value.heartbeat_fresh, value.subject_profile_bound,
            value.legacy_control_plane_inactive,
        ))
    )


def _activation_matches(value, active, sid, hello) -> bool:
    try:
        _validate_runtime_principal(
            active.principal, PRODUCTION_BROWSER_BRIDGE_TRANSPORT
        )
        if isinstance(value, RuntimeActivationAttestation):
            _validate_runtime_principal(
                value.principal, PRODUCTION_BROWSER_BRIDGE_TRANSPORT
            )
    except BrowserBridgeRuntimeDenied:
        return False
    return bool(
        isinstance(value, RuntimeActivationAttestation)
        and value.principal is active.principal and value.server_instance_id == active.server_instance_id
        and value.connector_sid == sid and value.load_generation_id == hello.load_generation_id
        and value.extension_id == active.extension_id == hello.extension_id
        and value.install_instance_id == hello.install_instance_id
        and value.server_features == hello.outer_features
        and _activation_fresh(value, time.time_ns() // 1_000_000)
    )


def _hello_mapping(hello: NormalizedBridgeHello) -> dict[str, Any]:
    return {
        "protocol": CONNECTOR_PROTOCOL,
        "features": sorted(hello.outer_features),
        "host_browser": {
            "supported": True,
            "enabled": True,
            "status": "ready",
            "backend_id": "chrome_extension",
            "browser_id": hello.browser_id,
            "browser_label": hello.browser_label,
            "contract_version": hello.contract_version,
            "features": ["browser_extension_bridge_v1"],
            "capabilities": {
                "actions": sorted(hello.actions),
                "features": sorted(hello.features),
                "limits": dict(hello.limits),
            },
            "extension": {
                "id": hello.extension_id,
                "version": hello.extension_version,
                "manifest_version": 3,
                "install_instance_id": hello.install_instance_id,
                "load_generation_id": hello.load_generation_id,
            },
            "companion": {
                "instance_id": hello.companion_instance_id,
                "version": hello.companion_version,
                "platform": hello.companion_platform,
                "arch": hello.companion_arch,
            },
        },
    }


def _equivalent_principal(expected: WsPrincipal, candidate: WsPrincipal) -> bool:
    return expected == candidate


def _same_route_objects(
    left: tuple[BrowserBridgeRuntimeRoute, ...],
    right: tuple[BrowserBridgeRuntimeRoute, ...],
) -> bool:
    return len(left) == len(right) and all(
        candidate is expected for candidate, expected in zip(left, right)
    )


def _validate_known_runtime_principal(principal: Any) -> WsPrincipal:
    try:
        runtime_transport_profile_for_principal(principal)
    except ValueError:
        raise BrowserBridgeRuntimeDenied("INVALID_PRINCIPAL") from None
    _identifier(principal.principal_id, "bridge_id")
    _identifier(principal.subject_id, "subject_id")
    return principal


def _validate_runtime_principal(
    principal: Any,
    transport_profile: BrowserBridgeTransportProfile = (
        PRODUCTION_BROWSER_BRIDGE_TRANSPORT
    ),
) -> WsPrincipal:
    try:
        profile = require_browser_bridge_transport_profile(transport_profile)
        require_runtime_transport_principal(principal, profile)
    except ValueError:
        raise BrowserBridgeRuntimeDenied("INVALID_PRINCIPAL") from None
    if (
        not isinstance(principal, WsPrincipal)
        or principal.principal_type != profile.principal_type
        or principal.handler_id != profile.handler_id
        or principal.handler_path != profile.handler_path
    ):
        raise BrowserBridgeRuntimeDenied("INVALID_PRINCIPAL")
    _identifier(principal.principal_id, "bridge_id")
    _identifier(principal.subject_id, "subject_id")
    return principal


def _exact_mapping(value: Any, fields: set[str], subject: str) -> Mapping[str, Any]:
    if not isinstance(value, Mapping) or set(value) != fields:
        raise BrowserBridgeRuntimeError(f"invalid {subject}")
    return value


def _capability_set(value: Any, allowed: set[str] | frozenset[str], subject: str) -> frozenset[str]:
    if not isinstance(value, list) or len(value) > MAX_CAPABILITIES:
        raise BrowserBridgeRuntimeError(f"invalid {subject}")
    result: list[str] = []
    for item in value:
        if (
            not isinstance(item, str)
            or item not in allowed
            or len(item.encode("utf-8")) > MAX_IDENTIFIER_BYTES
        ):
            raise BrowserBridgeRuntimeError(f"invalid {subject}")
        result.append(item)
    if len(set(result)) != len(result):
        raise BrowserBridgeRuntimeError(f"duplicate {subject}")
    return frozenset(result)


def _limits(value: Any) -> tuple[tuple[str, int], ...]:
    mapping = _exact_mapping(value, set(dict(EXPECTED_LIMITS)), "limits")
    if any(
        type(mapping[key]) is not int or mapping[key] != expected
        for key, expected in EXPECTED_LIMITS
    ):
        raise BrowserBridgeRuntimeError("invalid limits")
    return EXPECTED_LIMITS


def _bounded_text(value: Any, maximum: int, subject: str) -> str:
    try:
        encoded_size = len(value.encode("utf-8")) if isinstance(value, str) else -1
    except UnicodeError:
        encoded_size = -1
    if (
        not isinstance(value, str)
        or not value
        or not 0 <= encoded_size <= maximum
        or not value.isprintable()
    ):
        raise BrowserBridgeRuntimeError(f"invalid {subject}")
    return value


def _identifier(value: Any, subject: str) -> str:
    return _bounded_text(value, MAX_IDENTIFIER_BYTES, subject)


def _native_identifier(value: Any, subject: str) -> str:
    value = _identifier(value, subject)
    if _NATIVE_IDENTIFIER.fullmatch(value) is None:
        raise BrowserBridgeRuntimeError(f"invalid {subject}")
    return value


def _extension_id(value: Any) -> str:
    if not isinstance(value, str) or _EXTENSION_ID.fullmatch(value) is None:
        raise BrowserBridgeRuntimeError("invalid extension_id")
    return value


def _version(value: Any, subject: str) -> str:
    if not isinstance(value, str) or _VERSION.fullmatch(value) is None:
        raise BrowserBridgeRuntimeError(f"invalid {subject}")
    return value
