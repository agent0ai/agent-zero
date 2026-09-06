from __future__ import annotations

import asyncio
from copy import deepcopy
import json
from pathlib import Path

import pytest

from helpers.ws_principal import WsPrincipal
from plugins._a0_connector.helpers.browser_bridge_operations import (
    BridgeAuthorization,
    BrowserBridgeOperationBroker,
    ReconciliationBinding,
    SettlementStatus,
)
from plugins._a0_connector.helpers.browser_bridge_reconciliation import (
    BrowserBridgeReconciliationController,
    BrowserBridgeReconciliationError,
    BrowserBridgeReconciliationSummary,
    ExpectedReconciliationContext,
    ReconciliationEventCursor,
    ReconciliationSnapshot,
    parse_browser_reconcile_result,
)
from plugins._a0_connector.helpers.browser_bridge_transport import (
    PRODUCTION_BROWSER_BRIDGE_TRANSPORT,
)


FIXTURE = json.loads(
    (Path(__file__).parent / "fixtures" / "browser-reconcile-v1.json").read_text()
)


def _principal() -> WsPrincipal:
    profile = PRODUCTION_BROWSER_BRIDGE_TRANSPORT
    return WsPrincipal(
        principal_type=profile.principal_type,
        principal_id="bridge-dev-1",
        subject_id="single-user",
        scopes=frozenset({"browser.control", "browser.operate"}),
        handler_path=profile.handler_path,
        handler_id=profile.handler_id,
        inbound_events=frozenset(
            {"connector_browser_control_result", "connector_browser_event"}
        ),
        outbound_events=frozenset({"connector_browser_control"}),
        key_generation=1,
    )


def _binding(principal: WsPrincipal | None = None) -> ReconciliationBinding:
    return ReconciliationBinding(
        principal=principal or _principal(),
        connector_sid="sid-dev-1",
        load_generation_id="load-dev-1",
        control_id="reconcile-1",
        transport_profile=PRODUCTION_BROWSER_BRIDGE_TRANSPORT,
    )


def _snapshot() -> ReconciliationSnapshot:
    return ReconciliationSnapshot(
        expected_contexts=(
            ExpectedReconciliationContext(
                "context-1", "browser-session-1", ("turn-1",)
            ),
        ),
        event_cursors=(ReconciliationEventCursor("load-dev-1", 7),),
        known_control_ids=("finalize-older-1",),
    )


def _authorization(binding: ReconciliationBinding) -> BridgeAuthorization:
    return BridgeAuthorization(
        principal=binding.principal,
        connector_sid=binding.connector_sid,
        load_generation_id=binding.load_generation_id,
        contract_version=1,
        outer_features=frozenset({"connector_browser_control"}),
        actions=frozenset(),
        features=frozenset(),
    )


def _controller(*, timeout_ms: int = 1_000):
    sent: list[tuple] = []
    state = {"current": True, "phase": "provisional"}
    promoted: list[BrowserBridgeReconciliationSummary] = []

    async def sender(*args):
        sent.append(args)

    broker = BrowserBridgeOperationBroker(
        sender=sender,
        authorizer=_authorization,
        transport_profile=PRODUCTION_BROWSER_BRIDGE_TRANSPORT,
    )

    def current(_binding):
        return state["current"] and state["phase"] in {
            "provisional",
            "ready",
        }

    def promote(_binding, summary):
        if not current(_binding) or state["phase"] != "provisional":
            return False
        promoted.append(summary)
        state["phase"] = "ready"
        return True

    controller = BrowserBridgeReconciliationController(
        broker=broker,
        snapshot_source=lambda _binding: _snapshot(),
        route_current=current,
        promote=promote,
        transport_profile=PRODUCTION_BROWSER_BRIDGE_TRANSPORT,
        timeout_ms=timeout_ms,
    )
    return controller, broker, sent, state, promoted


def test_fixture_reconcile_promotes_synchronously_and_retains_counts_only():
    async def scenario():
        controller, broker, sent, state, promoted = _controller()
        binding = _binding()
        task = controller.start(
            binding, expected_install_instance_id="install-dev-1"
        )
        await asyncio.sleep(0)
        await asyncio.sleep(0)
        assert sent[0][2] == FIXTURE["core_control"]
        assert sent[0][3] == "reconcile-1"
        native_request = deepcopy(sent[0][2])
        for name in ("method", "bridge_id", "load_generation_id"):
            native_request.pop(name)
        assert native_request == FIXTURE["extension_request"]
        assert (
            FIXTURE["core_control_result"]["result"]
            == FIXTURE["extension_result"]
        )
        assert state["phase"] == "provisional"

        status = broker.settle_control(
            principal=binding.principal,
            connector_sid=binding.connector_sid,
            load_generation_id=binding.load_generation_id,
            payload=FIXTURE["core_control_result"],
        )
        assert status == SettlementStatus.SETTLED
        # Promotion is part of synchronous acceptance, before a following
        # critical-event handler can run.
        assert state["phase"] == "ready"
        summary = await task
        assert summary == BrowserBridgeReconciliationSummary(1, 1, 1, 1, 1)
        assert promoted == [summary]
        assert set(summary.as_wire_dict()) == {
            "contract_version",
            "lease_count",
            "inflight_operation_count",
            "terminal_receipt_count",
            "pending_critical_event_count",
            "prior_generation_orphan_count",
        }

    asyncio.run(scenario())


def test_forged_full_result_does_not_settle_or_promote():
    async def scenario():
        controller, broker, _sent, _state, promoted = _controller()
        binding = _binding()
        task = controller.start(
            binding, expected_install_instance_id="install-dev-1"
        )
        await asyncio.sleep(0)
        forged = deepcopy(FIXTURE["core_control_result"])
        forged["result"]["leases"][0]["identity"]["provider_tab_id"] = True
        assert (
            broker.settle_control(
                principal=binding.principal,
                connector_sid=binding.connector_sid,
                load_generation_id=binding.load_generation_id,
                payload=forged,
            )
            == SettlementStatus.MISMATCH
        )
        forged_outer_version = deepcopy(FIXTURE["core_control_result"])
        forged_outer_version["contract_version"] = True
        assert (
            broker.settle_control(
                principal=binding.principal,
                connector_sid=binding.connector_sid,
                load_generation_id=binding.load_generation_id,
                payload=forged_outer_version,
            )
            == SettlementStatus.MISMATCH
        )
        assert promoted == []
        broker.disconnect(
            principal=binding.principal,
            connector_sid=binding.connector_sid,
            load_generation_id=binding.load_generation_id,
        )
        with pytest.raises(BrowserBridgeReconciliationError) as error:
            await task
        assert error.value.code == "CONNECTION_LOST"

    asyncio.run(scenario())


def test_stale_route_is_rejected_inside_result_acceptance():
    async def scenario():
        controller, broker, _sent, state, promoted = _controller()
        binding = _binding()
        task = controller.start(
            binding, expected_install_instance_id="install-dev-1"
        )
        await asyncio.sleep(0)
        state["current"] = False
        assert (
            broker.settle_control(
                principal=binding.principal,
                connector_sid=binding.connector_sid,
                load_generation_id=binding.load_generation_id,
                payload=FIXTURE["core_control_result"],
            )
            == SettlementStatus.SETTLED
        )
        assert promoted == []
        with pytest.raises(BrowserBridgeReconciliationError) as error:
            await task
        assert error.value.code == "SCOPE_DENIED"

    asyncio.run(scenario())


def test_timeout_never_promotes():
    async def scenario():
        controller, _broker, _sent, _state, promoted = _controller(timeout_ms=10)
        task = controller.start(
            _binding(), expected_install_instance_id="install-dev-1"
        )
        with pytest.raises(BrowserBridgeReconciliationError) as error:
            await task
        assert error.value.code == "DEADLINE_EXCEEDED"
        assert promoted == []

    asyncio.run(scenario())


def test_result_parser_rejects_duplicate_peer_authority_without_adopting_it():
    result = deepcopy(FIXTURE["extension_result"])
    result["leases"].append(deepcopy(result["leases"][0]))
    with pytest.raises(BrowserBridgeReconciliationError) as error:
        parse_browser_reconcile_result(
            result,
            binding=_binding(),
            expected_install_instance_id="install-dev-1",
            transport_profile=PRODUCTION_BROWSER_BRIDGE_TRANSPORT,
        )
    assert error.value.code == "RECONCILE_RESULT_INVALID"

    envelope_alias = deepcopy(FIXTURE["extension_result"])
    envelope_alias["pending_critical_events"][0]["correlationId"] = "rpc-1"
    with pytest.raises(BrowserBridgeReconciliationError) as error:
        parse_browser_reconcile_result(
            envelope_alias,
            binding=_binding(),
            expected_install_instance_id="install-dev-1",
            transport_profile=PRODUCTION_BROWSER_BRIDGE_TRANSPORT,
        )
    assert error.value.code == "RECONCILE_RESULT_INVALID"
