"""Production composition with independently rechecked server authority.

The release verifier is supplied by the server's verified-release owner, never
by a request, hello, environment readiness switch, or presentation catalog.
An absent verifier cannot install this owner.
"""

from __future__ import annotations

from dataclasses import dataclass
import time
import threading
from typing import Callable

from plugins._a0_connector.helpers.browser_bridge_bootstrap import (
    bind_browser_bridge_application, retire_browser_bridge_application,
)
from plugins._a0_connector.helpers.browser_bridge_cutover import (
    LegacyDetectionState, detect_installed_legacy_browser_bridge,
)
from plugins._a0_connector.helpers.browser_bridge_pairing import (
    SUBJECT_ID, configured_extension_id, get_browser_bridge_pairing_store,
)
from plugins._a0_connector.helpers.browser_bridge_runtime import (
    CompleteRuntimeAdmission, NormalizedBridgeHello, RuntimeActivationAttestation,
    VerifiedActivePrincipal,
)
from plugins._a0_connector.helpers.browser_bridge_selection import default_selected_bridge, selection_current
from plugins._a0_connector.helpers.browser_bridge_session import is_active
from plugins._a0_connector.helpers.browser_bridge_transport import (
    PRODUCTION_BROWSER_BRIDGE_TRANSPORT as PROFILE,
)
from plugins._browser.helpers.bridge_foundation import get_browser_bridge_gate


HEARTBEAT_MAX_AGE_MS = 30_000
REQUIRED_BOUNDARIES = frozenset({
    "operation", "control", "context", "event", "artifact", "approval",
    "lifecycle", "policy",
})


@dataclass(frozen=True, slots=True)
class VerifiedBrowserRelease:
    """Exact release-verifier result; construction alone grants no admission.

    Only the independently configured verifier is consulted. The server owner
    compares every field against the authenticated route on every lookup.
    Public release metadata is intentionally not accepted by this interface.
    """

    principal: object
    server_instance_id: str
    connector_sid: str
    load_generation_id: str
    install_instance_id: str
    extension_id: str
    extension_version: str
    companion_version: str
    companion_platform: str
    companion_arch: str


ReleaseVerifier = Callable[
    [VerifiedActivePrincipal, str, NormalizedBridgeHello], VerifiedBrowserRelease | None
]


def _admission_denied(code):
    from plugins._a0_connector.helpers.browser_bridge_application import record_production_browser_stage
    record_production_browser_stage(code)
    return None


def _server_instance_id() -> str:
    from helpers import runtime

    return runtime.get_persistent_id()


class BrowserBridgeRuntimeOwner:
    """Own production factory acquisition, admission, readback and withdrawal."""

    def __init__(self, *, manager, release_verifier: ReleaseVerifier) -> None:
        if not callable(release_verifier):
            raise TypeError("a verified Browser release owner is required")
        if not callable(getattr(manager, "principal_for_sid", None)):
            raise TypeError("the server WebSocket manager is required")
        from plugins._a0_connector.helpers.browser_bridge_application import BrowserBridgeApplication
        from plugins._browser.helpers.extension_sessions import (
            get_extension_session_lifecycle,
        )

        self.manager = manager
        self._release_verifier = release_verifier
        self._closed = False
        self.application = BrowserBridgeApplication(
            manager=manager,
            server_instance_id=_server_instance_id,
            lifecycle=get_extension_session_lifecycle(),
            active_principal_verifier=self.verify_principal,
            admission_evaluator=self.evaluate_admission,
            context_authorizer=self.authorize_context,
            selection_current=selection_current,
        )

    def install(self) -> bool:
        if self._closed:
            raise RuntimeError("Browser runtime owner is closed")
        if self.application.installed:
            return False
        self.application.install()
        try:
            bind_browser_bridge_application(self.application)
        except Exception:
            # Construction has acquired factory ownership, so a failed bind
            # must not leave that factory reachable by normal Browser calls.
            self.application.browser.uninstall()
            raise
        return True

    async def close(self) -> bool:
        if self._closed:
            return False
        self._closed = True
        retired = await retire_browser_bridge_application(self.application)
        if not retired:
            await self.application.close()
        return True

    def verify_principal(self, principal) -> VerifiedActivePrincipal | None:
        try:
            if self._closed or not is_active(principal):
                return None
            record = get_browser_bridge_pairing_store().active_bridge_record(
                bridge_id=principal.principal_id,
                server_instance_id=_server_instance_id(),
            )
            if record is None or principal.subject_id != SUBJECT_ID:
                return None
            return VerifiedActivePrincipal(
                principal=principal,
                server_instance_id=_server_instance_id(),
                extension_id=record["extension_id"],
                companion_instance_id=record["companion_instance_id"],
            )
        except Exception:
            return None


    def authorize_context(self, route, context_id: str) -> bool:
        return bool(
            route.principal.subject_id == SUBJECT_ID
            and selection_current(context_id, route.bridge_id)
        )

    def _selected(self, bridge_id: str) -> bool:
        from agent import AgentContext

        return default_selected_bridge() == bridge_id or any(
            selection_current(context.id, bridge_id) for context in AgentContext.all()
        )

    def _heartbeat_fresh(self, principal, sid: str) -> bool:
        # A connected socket is insufficient. Require recent server-observed
        # authenticated traffic. Native sends same-generation hello refreshes
        # during idle; callers cannot supply a heartbeat timestamp.
        with self.manager.lock:
            connection = self.manager.connections.get((PROFILE.namespace, sid))
            if connection is None or connection.principal is not principal:
                return False
            observed = int(connection.last_activity.timestamp() * 1000)
            # A concurrent authenticated receive may have advanced activity
            # since admission began. Sample now after the activity snapshot,
            # under its owning lock, rather than rejecting that fresh traffic
            # as a future timestamp and retiring an otherwise current route.
            now = time.time_ns() // 1_000_000
        return 0 <= now - observed < HEARTBEAT_MAX_AGE_MS

    def evaluate_admission(self, active, sid, hello) -> CompleteRuntimeAdmission | None:
        try:
            now = time.time_ns() // 1_000_000
            checks = (
                ("ADMISSION_OWNER_UNAVAILABLE", lambda: not self._closed and self.application.installed),
                ("ADMISSION_SOCKET_MISMATCH", lambda: self.manager.principal_for_sid(PROFILE.namespace, sid) is active.principal),
                ("ADMISSION_PRINCIPAL_REJECTED", lambda: self.verify_principal(active.principal) == active),
                ("ADMISSION_EXTENSION_MISMATCH", lambda: active.extension_id == configured_extension_id()),
                ("ADMISSION_ROLLOUT_DISABLED", lambda: get_browser_bridge_gate().state == "available"),
                ("ADMISSION_SELECTION_MISSING", lambda: self._selected(active.principal.principal_id)),
                ("ADMISSION_HEARTBEAT_REJECTED", lambda: self._heartbeat_fresh(active.principal, sid)),
                ("ADMISSION_LEGACY_PRESENT", lambda: detect_installed_legacy_browser_bridge().state is LegacyDetectionState.ABSENT),
            )
            for code, permitted in checks:
                if not permitted():
                    return _admission_denied(code)
            boundaries = getattr(self.application, "runtime_boundaries", lambda: frozenset())()
            if type(boundaries) is not frozenset or not REQUIRED_BOUNDARIES <= boundaries:
                return _admission_denied("ADMISSION_BOUNDARY_MISSING")
            evidence = self._release_verifier(active, sid, hello)
            if type(evidence) is not VerifiedBrowserRelease or evidence.principal is not active.principal:
                return _admission_denied("ADMISSION_RELEASE_UNVERIFIED")
            if (
                evidence.server_instance_id != active.server_instance_id
                or evidence.connector_sid != sid
                or any(getattr(evidence, field) != getattr(hello, field) for field in (
                    "load_generation_id", "install_instance_id", "extension_id",
                    "extension_version", "companion_version", "companion_platform", "companion_arch",
                ))
            ):
                return _admission_denied("ADMISSION_RELEASE_MISMATCH")
            activation = RuntimeActivationAttestation(
                principal=active.principal, server_instance_id=active.server_instance_id,
                connector_sid=sid, load_generation_id=hello.load_generation_id,
                extension_id=active.extension_id, install_instance_id=hello.install_instance_id,
                server_features=hello.outer_features, rollout="available", selected_bridge=True,
                heartbeat_fresh=True, subject_profile_bound=True, legacy_control_plane_inactive=True,
                issued_at_ms=now, expires_at_ms=now + HEARTBEAT_MAX_AGE_MS,
            )
            return CompleteRuntimeAdmission(
                principal=active.principal, server_instance_id=active.server_instance_id,
                connector_sid=sid, load_generation_id=hello.load_generation_id,
                install_instance_id=hello.install_instance_id, contract_version=hello.contract_version,
                outer_features=hello.outer_features, actions=hello.actions, features=hello.features,
                release_trust_ready=True, activation_attested=True, legacy_control_plane_inactive=True,
                operation_transport_ready="operation" in boundaries,
                control_transport_ready="control" in boundaries,
                context_transport_ready="context" in boundaries,
                event_transport_ready="event" in boundaries,
                artifact_transport_ready="artifact" in boundaries,
                approval_transport_ready="approval" in boundaries,
                session_lifecycle_ready="lifecycle" in boundaries,
                policy_enforcement_ready="policy" in boundaries,
                activation=activation,
            )
        except Exception:
            return _admission_denied("ADMISSION_CHECK_EXCEPTION")


_owner: BrowserBridgeRuntimeOwner | None = None
_owner_lock = threading.RLock()
_release_verifier: ReleaseVerifier | None = None
_retiring = False


def configure_verified_browser_releases(verifier: ReleaseVerifier) -> None:
    """Configure server-owned release verification before startup, never via HTTP."""
    if not callable(verifier):
        raise TypeError("invalid Browser release verifier")
    global _release_verifier
    with _owner_lock:
        if _owner is not None or _retiring:
            raise RuntimeError("retire the Browser runtime before changing release trust")
        _release_verifier = verifier


def install_configured_browser_runtime(manager) -> bool:
    """Normal startup; admission stays closed without independently verified trust."""
    global _owner
    if get_browser_bridge_gate().state != "available" or configured_extension_id() is None:
        return False
    with _owner_lock:
        if _retiring:
            raise RuntimeError("Browser runtime is retiring")
        if _owner is not None:
            if _owner.manager is not manager or not _owner.application.installed:
                raise RuntimeError("Browser runtime owner conflict")
            return False
        from plugins._a0_connector.helpers.browser_bridge_release_policy import verify_configured_browser_release

        candidate = BrowserBridgeRuntimeOwner(
            manager=manager,
            release_verifier=_release_verifier or verify_configured_browser_release,
        )
        candidate.install()
        _owner = candidate
        return True


async def retire_configured_browser_runtime(*, manager=None) -> bool:
    global _owner, _retiring
    with _owner_lock:
        if _owner is None or _retiring:
            return False
        if manager is not None and _owner.manager is not manager:
            return False
        owner = _owner
        _owner = None
        _retiring = True
    try:
        return await owner.close()
    finally:
        with _owner_lock:
            _retiring = False


async def reload_configured_browser_runtime(manager) -> bool:
    """Explicit reload withdraws and awaits the former owner before installation."""
    await retire_configured_browser_runtime()
    return install_configured_browser_runtime(manager)
