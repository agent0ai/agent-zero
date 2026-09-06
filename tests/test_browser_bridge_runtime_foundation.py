from __future__ import annotations

import asyncio
import time
import uuid
from copy import deepcopy
from dataclasses import replace
from typing import Any

import pytest

from helpers.ws_principal import WsPrincipal
from plugins._a0_connector.helpers.browser_bridge_approval import BrowserApprovalRoute
from plugins._a0_connector.helpers.browser_bridge_artifacts import ArtifactBinding
from plugins._a0_connector.helpers.browser_bridge_context import (
    BrowserBridgeContextAccess,
    BrowserBridgeContextRoute,
)
from plugins._a0_connector.helpers.browser_bridge_operations import (
    OperationBinding,
    SettlementStatus,
    TurnBinding,
)
from plugins._a0_connector.helpers.browser_bridge_runtime import (
    CONTROL_EVENT,
    EXPECTED_LIMITS,
    OPERATION_EVENT,
    REQUIRED_INBOUND_EVENTS,
    REQUIRED_OUTBOUND_EVENTS,
    REQUIRED_OUTER_FEATURES,
    REQUIRED_SCOPES,
    CompleteRuntimeAdmission,
    RuntimeActivationAttestation,
    BrowserBridgeRuntimeDenied,
    BrowserBridgeRuntimeError,
    BrowserBridgeRuntimeRegistry,
    VerifiedActivePrincipal,
    context_access_authorizer,
    exact_route_cleanup,
    normalize_bridge_hello,
    restricted_browser_sender,
)


EXTENSION_ID = "a" * 32
SERVER_ID = "server-A"


def _principal(bridge_id: str = "bridge-A") -> WsPrincipal:
    return WsPrincipal(
        principal_type="browser_bridge",
        principal_id=bridge_id,
        subject_id="single_user",
        scopes=REQUIRED_SCOPES,
        handler_path="plugins/_a0_connector/ws_connector",
        handler_id="ws_connector.WsConnector",
        inbound_events=REQUIRED_INBOUND_EVENTS,
        outbound_events=REQUIRED_OUTBOUND_EVENTS,
        key_generation=1,
    )


def _active(
    principal: WsPrincipal,
    *,
    server_id: str = SERVER_ID,
) -> VerifiedActivePrincipal:
    return VerifiedActivePrincipal(
        principal=principal,
        server_instance_id=server_id,
        extension_id=EXTENSION_ID,
        companion_instance_id=f"companion-{principal.principal_id}",
    )


def _hello(
    principal: WsPrincipal,
    *,
    generation: str = "generation-A",
) -> dict[str, Any]:
    return {
        "protocol": "a0-connector.v1",
        "features": sorted(REQUIRED_OUTER_FEATURES),
        "host_browser": {
            "supported": True,
            "enabled": True,
            "status": "ready",
            "backend_id": "chrome_extension",
            "browser_id": f"extension:{principal.principal_id}",
            "browser_label": "Chrome - Agent Zero Extension",
            "contract_version": 1,
            "features": ["browser_extension_bridge_v1"],
            "capabilities": {
                "actions": ["open", "list", "state", "navigate"],
                "features": ["tab_leases_v1", "cursor_v1"],
                "limits": dict(EXPECTED_LIMITS),
            },
            "extension": {
                "id": EXTENSION_ID,
                "version": "0.2.0",
                "manifest_version": 3,
                "install_instance_id": "install-A",
                "load_generation_id": generation,
            },
            "companion": {
                "instance_id": f"companion-{principal.principal_id}",
                "version": "2.12.0",
                "platform": "darwin",
                "arch": "arm64",
            },
        },
    }


def _admission(
    active: VerifiedActivePrincipal,
    sid: str,
    hello,
    **changes: Any,
) -> CompleteRuntimeAdmission:
    now = time.time_ns() // 1_000_000
    values = {
        "principal": active.principal,
        "server_instance_id": active.server_instance_id,
        "connector_sid": sid,
        "load_generation_id": hello.load_generation_id,
        "install_instance_id": hello.install_instance_id,
        "contract_version": hello.contract_version,
        "outer_features": hello.outer_features,
        "actions": hello.actions,
        "features": hello.features,
        "release_trust_ready": True,
        "activation_attested": True,
        "legacy_control_plane_inactive": True,
        "operation_transport_ready": True,
        "control_transport_ready": True,
        "context_transport_ready": True,
        "event_transport_ready": True,
        "artifact_transport_ready": True,
        "approval_transport_ready": True,
        "session_lifecycle_ready": True,
        "policy_enforcement_ready": True,
        "activation": RuntimeActivationAttestation(
            active.principal, active.server_instance_id, sid, hello.load_generation_id,
            active.extension_id, hello.install_instance_id, hello.outer_features,
            "preview_authorized", True, True, True, True, now, now + 30_000,
        ),
    }
    values.update(changes)
    return CompleteRuntimeAdmission(**values)


async def _sender(*_args) -> None:
    return None


def test_activation_requires_current_typed_server_evidence_not_ready_flags():
    principal = _principal()
    for changes in (
        {"selected_bridge": False}, {"heartbeat_fresh": False}, {"subject_profile_bound": False},
        {"connector_sid": "other"}, {"install_instance_id": "other"}, {"rollout": "preview"},
        {"issued_at_ms": 1, "expires_at_ms": 2},
    ):
        def evaluate(active, sid, hello):
            admission = _admission(active, sid, hello)
            return replace(admission, activation=replace(admission.activation, **changes))

        registry = _registry(admission_evaluator=evaluate)
        with pytest.raises(BrowserBridgeRuntimeDenied):
            registry.register_hello(principal=principal, connector_sid="sid-A", data=_hello(principal))
        assert registry.session_count == 0
    registry = _registry(admission_evaluator=lambda active, sid, hello: _admission(active, sid, hello, activation=None))
    with pytest.raises(BrowserBridgeRuntimeDenied):
        registry.register_hello(principal=principal, connector_sid="sid-A", data=_hello(principal))


def _registry(
    *,
    active_verifier=None,
    admission_evaluator=None,
    context_authorizer=None,
    cleanup_callbacks=(),
    max_sessions: int = 32,
    sender=_sender,
) -> BrowserBridgeRuntimeRegistry:
    return BrowserBridgeRuntimeRegistry(
        sender=sender,
        active_principal_verifier=(active_verifier or _active),
        admission_evaluator=(admission_evaluator or _admission),
        context_authorizer=(
            context_authorizer
            or (lambda _route, context_id: context_id == "context-A")
        ),
        cleanup_callbacks=cleanup_callbacks,
        max_sessions=max_sessions,
    )


async def _reconcile_registered(registry, route):
    """Explicit real controller/broker settlement over a synthetic transport."""
    from plugins._a0_connector.helpers.browser_bridge_operations import ReconciliationBinding
    from plugins._a0_connector.helpers.browser_bridge_reconciliation import (
        BrowserBridgeReconciliationController, ReconciliationSnapshot,
    )
    binding = ReconciliationBinding(route.principal, route.connector_sid,
                                    route.load_generation_id, uuid.uuid4().hex,
                                    route.transport_profile)
    assert registry.begin_reconciliation(binding)
    controller = BrowserBridgeReconciliationController(
        broker=registry.broker, snapshot_source=lambda _: ReconciliationSnapshot(),
        route_current=registry.route_current_for_reconciliation,
        promote=registry.promote_reconciled, transport_profile=route.transport_profile)
    sent = asyncio.Event()
    previous_sender = registry.broker._sender
    async def sender(sid, event, payload, correlation, principal):
        assert sid == route.connector_sid and principal is route.principal
        assert event == "connector_browser_control" and payload["method"] == "browser.reconcile"
        assert correlation == binding.control_id
        sent.set()
    registry.broker._sender = sender
    try:
        task = controller.start(binding, expected_install_instance_id=route.hello.install_instance_id)
        await asyncio.wait_for(sent.wait(), 1)
        response = {
            "contract_version": 1, "method": "browser.reconcile", "bridge_id": route.bridge_id,
            "load_generation_id": route.load_generation_id, "control_id": binding.control_id,
            "ok": True, "result": {"contract_version": 1, "control_id": binding.control_id,
                "install_instance_id": route.hello.install_instance_id,
                "load_generation_id": route.load_generation_id, "leases": [],
                "inflight_operations": [], "terminal_action_receipts": [],
                "pending_critical_events": [], "prior_generation_orphans": []},
        }
        assert registry.settle_control(principal=route.principal, connector_sid=route.connector_sid,
                                      load_generation_id=route.load_generation_id, payload=response) == SettlementStatus.SETTLED
        await task
        assert registry.current_bridge_ready(route.bridge_id)
    finally:
        registry.broker._sender = previous_sender


def test_exact_hello_is_bounded_but_cannot_supply_runtime_admission() -> None:
    principal = _principal()
    active = _active(principal)
    hello = normalize_bridge_hello(principal, active, _hello(principal))
    assert hello.bridge_id == principal.principal_id
    assert hello.browser_id == "extension:bridge-A"
    assert hello.load_generation_id == "generation-A"
    assert hello.actions == frozenset({"open", "list", "state", "navigate"})
    assert hello.limits == EXPECTED_LIMITS

    registry = BrowserBridgeRuntimeRegistry(
        sender=_sender,
        active_principal_verifier=_active,
    )
    with pytest.raises(BrowserBridgeRuntimeDenied) as error:
        registry.register_hello(
            principal=principal,
            connector_sid="sid-A",
            data=_hello(principal),
        )
    assert error.value.code == "RUNTIME_NOT_ADMITTED"
    assert registry.session_count == 0


def test_hello_rejects_authority_injection_and_unproven_capabilities() -> None:
    principal = _principal()
    active = _active(principal)
    malformed = []

    for version in ("2.11.9", "2.12.0-preview", "02.12.0", "2.12", "v2.12.0"):
        old_companion = _hello(principal)
        old_companion["host_browser"]["companion"]["version"] = version
        malformed.append(old_companion)

    remote_authority = _hello(principal)
    remote_authority["remote_exec"] = {"enabled": True}
    malformed.append(remote_authority)

    wrong_route = _hello(principal)
    wrong_route["host_browser"]["browser_id"] = "extension:another-bridge"
    malformed.append(wrong_route)

    wrong_extension = _hello(principal)
    wrong_extension["host_browser"]["extension"]["id"] = "b" * 32
    malformed.append(wrong_extension)

    excessive = _hello(principal)
    excessive["host_browser"]["capabilities"]["actions"] = [
        f"unproven-{index}" for index in range(65)
    ]
    malformed.append(excessive)

    unknown_action = _hello(principal)
    unknown_action["host_browser"]["capabilities"]["actions"] = ["evaluate"]
    malformed.append(unknown_action)

    for candidate in malformed:
        with pytest.raises(BrowserBridgeRuntimeError):
            normalize_bridge_hello(principal, active, candidate)


def test_same_bridge_reconnect_replaces_generation_after_fail_isolated_cleanup() -> None:
    cleanup: list[tuple[WsPrincipal, str, str]] = []

    def broken(*_args) -> None:
        raise RuntimeError("cleanup canary")

    def record(principal, sid, generation) -> None:
        cleanup.append((principal, sid, generation))

    registry = _registry(cleanup_callbacks=(broken, record))
    first_principal = _principal()
    first = registry.register_hello(
        principal=first_principal,
        connector_sid="sid-old",
        data=_hello(first_principal, generation="generation-old"),
    )
    replacement_principal = replace(first_principal)
    replacement = registry.register_hello(
        principal=replacement_principal,
        connector_sid="sid-new",
        data=_hello(replacement_principal, generation="generation-new"),
    )
    assert not registry.current_bridge_ready("bridge-A")
    asyncio.run(_reconcile_registered(registry, replacement))

    assert registry.session_count == 1
    assert cleanup == [(first_principal, "sid-old", "generation-old")]
    assert registry.authorize_context_route(
        BrowserBridgeContextRoute(
            first.principal,
            first.connector_sid,
            first.load_generation_id,
        )
    ) is False
    resolved = registry.resolve_extension_route("context-A", "bridge-A")
    assert resolved is not None
    assert resolved.principal is replacement_principal
    assert resolved.connector_sid == "sid-new"
    assert resolved.load_generation_id == "generation-new"
    assert replacement.principal is replacement_principal


def test_exact_hello_replay_refreshes_admission_without_disconnect_cleanup() -> None:
    cleanup: list[tuple[WsPrincipal, str, str]] = []
    principal = _principal()
    registry = _registry(
        cleanup_callbacks=(
            lambda candidate, sid, generation: cleanup.append(
                (candidate, sid, generation)
            ),
        ),
    )
    first = registry.register_hello(
        principal=principal,
        connector_sid="sid-A",
        data=_hello(principal),
    )
    asyncio.run(_reconcile_registered(registry, first))
    replayed = registry.register_hello(
        principal=principal,
        connector_sid="sid-A",
        data=_hello(principal),
    )

    assert cleanup == []
    assert registry.session_count == 1
    assert registry.current_sid_route(principal, "sid-A") is replayed
    assert replayed.principal is first.principal
    assert replayed.hello == first.hello
    assert registry.current_bridge_ready("bridge-A")


def test_active_different_principal_cannot_replace_same_sid_or_capacity() -> None:
    registry = _registry(max_sessions=1)
    principal_a = _principal("bridge-A")
    admitted = registry.register_hello(
        principal=principal_a,
        connector_sid="shared-sid",
        data=_hello(principal_a),
    )
    asyncio.run(_reconcile_registered(registry, admitted))
    principal_b = _principal("bridge-B")
    with pytest.raises(BrowserBridgeRuntimeDenied) as conflict:
        registry.register_hello(
            principal=principal_b,
            connector_sid="shared-sid",
            data=_hello(principal_b),
        )
    assert conflict.value.code == "ROUTE_CONFLICT"
    assert registry.resolve_extension_route("context-A", "bridge-A") is not None

    with pytest.raises(BrowserBridgeRuntimeDenied) as capacity:
        registry.register_hello(
            principal=principal_b,
            connector_sid="sid-B",
            data=_hello(principal_b),
        )
    assert capacity.value.code == "SESSION_LIMIT"
    assert registry.session_count == 1


def test_explicit_context_route_composes_context_approval_artifact_and_broker() -> None:
    principal = _principal()
    registry = _registry()
    route = registry.register_hello(
        principal=principal,
        connector_sid="sid-A",
        data=_hello(principal),
    )
    assert registry.resolve_extension_route("context-A", "bridge-A") is None
    asyncio.run(_reconcile_registered(registry, route))

    resolved = registry.resolve_extension_route("context-A", "bridge-A")
    assert resolved is not None
    assert resolved.browser_id == "extension:bridge-A"
    assert registry.resolve_extension_route("context-B", "bridge-A") is None
    assert registry.resolve_extension_route("context-A", "bridge-B") is None

    context_route = BrowserBridgeContextRoute(
        principal, "sid-A", route.load_generation_id
    )
    assert registry.authorize_context_route(context_route)
    assert not registry.authorize_context_route(
        replace(context_route, principal=replace(principal))
    )

    approval_route = BrowserApprovalRoute(
        server_instance_id=SERVER_ID,
        principal=principal,
        connector_sid="sid-A",
        load_generation_id=route.load_generation_id,
        context_id="context-A",
        browser_session_id="browser-session-A",
        turn_id="turn-A",
        action_id="action-A",
        op_id="op-A",
        tab_handle="tab-A",
        document_id="document-A",
        document_epoch=1,
    )
    assert registry.authorize_approval_route(approval_route)
    assert not registry.authorize_approval_route(
        replace(approval_route, context_id="context-B")
    )
    assert registry.authorize_artifact_route(
        principal=principal,
        connector_sid="sid-A",
        load_generation_id=route.load_generation_id,
        context_id="context-A",
    )
    assert registry.authorize_artifact_binding(
        ArtifactBinding(
            principal=principal,
            connector_sid="sid-A",
            load_generation_id=route.load_generation_id,
            bridge_id="bridge-A",
            context_id="context-A",
            browser_session_id="browser-session-A",
            turn_id="turn-A",
            action_id="action-A",
            op_id="op-A",
            artifact_id="artifact-A",
            direction="output",
            purpose="screenshot",
        )
    )

    binding = OperationBinding(
        principal=principal,
        connector_sid="sid-A",
        load_generation_id=route.load_generation_id,
        context_id="context-A",
        browser_session_id="browser-session-A",
        turn_id="turn-A",
        action_id="action-A",
        op_id="op-A",
    )
    authorization = registry.authorize_broker(binding)
    assert authorization is not None
    assert authorization.principal is principal
    assert authorization.actions == route.hello.actions
    assert registry.authorize_broker(
        replace(binding, context_id="context-B")
    ) is None


def test_route_is_rechecked_after_context_authorizer_and_server_change() -> None:
    principal = _principal()
    current_server = [SERVER_ID]

    def verifier(candidate: WsPrincipal) -> VerifiedActivePrincipal:
        return _active(candidate, server_id=current_server[0])

    def context_authorizer(_route, _context_id) -> bool:
        current_server[0] = "server-B"
        return True

    registry = _registry(
        active_verifier=verifier,
        context_authorizer=context_authorizer,
    )
    route = registry.register_hello(
        principal=principal,
        connector_sid="sid-A",
        data=_hello(principal),
    )
    asyncio.run(_reconcile_registered(registry, route))
    assert registry.resolve_extension_route("context-A", "bridge-A") is None
    assert registry.session_count == 0


def test_context_access_adapter_uses_the_exact_registered_route() -> None:
    class _Access(BrowserBridgeContextAccess):
        def __init__(self) -> None:
            self.calls = []

        def authorize_message_target(self, route, *, context_id) -> None:
            self.calls.append((route, context_id))
            if context_id != "context-A":
                raise PermissionError("not advertised")

    principal = _principal()
    access = _Access()
    registry = _registry(context_authorizer=context_access_authorizer(access))
    registered = registry.register_hello(
        principal=principal,
        connector_sid="sid-A",
        data=_hello(principal),
    )
    asyncio.run(_reconcile_registered(registry, registered))
    assert registry.resolve_extension_route("context-A", "bridge-A") is not None
    projected_route, context_id = access.calls[-1]
    assert context_id == "context-A"
    assert projected_route.principal is principal
    assert projected_route.connector_sid == "sid-A"
    assert projected_route.load_generation_id == registered.load_generation_id
    assert registry.resolve_extension_route("context-B", "bridge-A") is None


def test_result_settlement_requires_the_exact_current_registered_route() -> None:
    async def scenario() -> None:
        sent: list[dict[str, Any]] = []

        async def sender(_sid, _event, payload, _correlation, _principal) -> None:
            sent.append(payload)

        principal = _principal()
        registry = _registry(sender=sender)
        route = registry.register_hello(
            principal=principal,
            connector_sid="sid-A",
            data=_hello(principal),
        )
        await _reconcile_registered(registry, route)
        binding = OperationBinding(
            principal,
            "sid-A",
            route.load_generation_id,
            "context-A",
            "browser-session-A",
            "turn-A",
            "action-A",
            "op-A",
        )
        ticket = await registry.broker.begin_operation(
            binding,
            action="state",
            target=None,
            args={},
            timeout_ms=5_000,
            required_capabilities=["state"],
        )
        await asyncio.sleep(0)
        wire = sent[0]
        result = {
            key: wire[key]
            for key in (
                "contract_version",
                "bridge_id",
                "load_generation_id",
                "context_id",
                "browser_session_id",
                "turn_id",
                "op_id",
                "action_id",
            )
        }
        result.update(ok=True, result={"status": "ready"}, receipts=[], artifacts=[])
        assert registry.settle_operation(
            principal=replace(principal),
            connector_sid="sid-A",
            load_generation_id=route.load_generation_id,
            payload=result,
        ) == SettlementStatus.MISMATCH
        assert registry.settle_operation(
            principal=principal,
            connector_sid="sid-A",
            load_generation_id=route.load_generation_id,
            payload=result,
        ) == SettlementStatus.SETTLED
        assert (await registry.broker.wait_operation(ticket)).ok

        control = await registry.broker.begin_finalize(
            TurnBinding(
                principal,
                "sid-A",
                route.load_generation_id,
                "context-A",
                "browser-session-A",
                "turn-A",
            ),
            control_id="control-A",
            dispositions={},
            reason="turn complete",
            timeout_ms=5_000,
        )
        await asyncio.sleep(0)
        control_wire = sent[1]
        control_result = {
            key: control_wire[key]
            for key in (
                "contract_version",
                "method",
                "bridge_id",
                "load_generation_id",
                "context_id",
                "browser_session_id",
                "turn_id",
                "control_id",
            )
        }
        control_result.update(
            ok=True,
            result={"contract_version": 1, "control_id": "control-A"},
        )
        assert registry.settle_control(
            principal=principal,
            connector_sid="sid-A",
            load_generation_id="stale-generation",
            payload=control_result,
        ) == SettlementStatus.MISMATCH
        assert registry.settle_control(
            principal=principal,
            connector_sid="sid-A",
            load_generation_id=route.load_generation_id,
            payload=control_result,
        ) == SettlementStatus.SETTLED
        assert (await registry.broker.wait_control(control)).ok

    asyncio.run(scenario())


def test_restricted_sender_uses_exact_shared_manager_boundary() -> None:
    class _Manager:
        def __init__(self) -> None:
            self.calls = []

        async def emit_to(self, *args, **kwargs) -> None:
            self.calls.append((args, kwargs))

    async def scenario() -> None:
        manager = _Manager()
        sender = restricted_browser_sender(manager)
        principal = _principal()
        payload = {"contract_version": 1}
        await sender("sid-A", OPERATION_EVENT, payload, "op-A", principal)
        assert manager.calls == [
            (
                ("/ws", "sid-A", OPERATION_EVENT, payload),
                {
                    "handler_id": "ws_connector.WsConnector",
                    "correlation_id": "op-A",
                    "expected_principal": principal,
                },
            )
        ]
        with pytest.raises(BrowserBridgeRuntimeDenied) as error:
            await sender(
                "sid-A",
                "connector_context_snapshot",
                {},
                "snapshot-A",
                principal,
            )
        assert error.value.code == "EVENT_NOT_ALLOWED"
        assert len(manager.calls) == 1

    asyncio.run(scenario())


def test_admission_revocation_retires_route_before_rejecting_late_result() -> None:
    async def scenario() -> None:
        admitted = [True]

        def evaluator(active, sid, hello):
            return _admission(active, sid, hello) if admitted[0] else None

        principal = _principal()
        registry = _registry(admission_evaluator=evaluator)
        route = registry.register_hello(
            principal=principal,
            connector_sid="sid-A",
            data=_hello(principal),
        )
        await _reconcile_registered(registry, route)
        binding = OperationBinding(
            principal,
            "sid-A",
            route.load_generation_id,
            "context-A",
            "browser-session-A",
            "turn-A",
            "action-A",
            "op-A",
        )
        ticket = await registry.broker.begin_operation(
            binding,
            action="state",
            target=None,
            args={},
            timeout_ms=5_000,
            required_capabilities=["state"],
        )
        admitted[0] = False
        assert registry.settle_operation(
            principal=principal,
            connector_sid="sid-A",
            load_generation_id=route.load_generation_id,
            payload={"op_id": "op-A"},
        ) == SettlementStatus.MISMATCH
        completion = await registry.broker.wait_operation(ticket)
        assert completion.ok is False
        assert completion.code == "CONNECTION_LOST"
        assert registry.session_count == 0

    asyncio.run(scenario())


def test_disconnect_is_exact_and_callbacks_receive_principal_object_identity() -> None:
    class _CleanupTarget:
        def __init__(self) -> None:
            self.calls = []

        def disconnect(self, **identity) -> None:
            self.calls.append(identity)

    target = _CleanupTarget()
    principal = _principal()
    registry = _registry(
        cleanup_callbacks=(exact_route_cleanup(target),)
    )
    route = registry.register_hello(
        principal=principal,
        connector_sid="sid-A",
        data=_hello(principal),
    )
    assert not registry.disconnect(
        principal=principal,
        connector_sid="sid-A",
        load_generation_id="stale-generation",
    )
    assert not registry.disconnect(
        principal=replace(principal),
        connector_sid="sid-A",
        load_generation_id=route.load_generation_id,
    )
    assert registry.disconnect(
        principal=principal,
        connector_sid="sid-A",
        load_generation_id=route.load_generation_id,
    )
    assert target.calls == [
        {
            "principal": principal,
            "connector_sid": "sid-A",
            "load_generation_id": route.load_generation_id,
        }
    ]
    assert registry.session_count == 0
