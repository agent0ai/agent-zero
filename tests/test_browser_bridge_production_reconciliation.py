"""Real production registry/controller/dispatcher, synthetic transport and state."""
import asyncio
import threading
from types import SimpleNamespace

import pytest

from plugins._a0_connector.helpers.browser_bridge_application import BrowserBridgeApplication
from plugins._a0_connector.helpers.browser_bridge_bootstrap import admitted_hello_projection
from plugins._a0_connector.helpers.browser_bridge_reconciliation import BrowserBridgeReconciliationController
from plugins._a0_connector.helpers.browser_bridge_operations import SettlementStatus
from plugins._a0_connector.helpers.browser_bridge_transport import PRODUCTION_BROWSER_BRIDGE_TRANSPORT
from plugins._browser.helpers.extension_sessions import ExtensionSessionRegistry
from test_browser_bridge_application import Memory
from test_browser_bridge_runtime_foundation import _registry, _principal, _hello


def application(timeout_ms=1_000):
    emitted, replayed = [], []
    sent = asyncio.Event()
    async def sender(*args):
        emitted.append(args)
        sent.set()
    app = object.__new__(BrowserBridgeApplication)
    app.transport_profile = PRODUCTION_BROWSER_BRIDGE_TRANSPORT
    app._state_lock = threading.RLock()
    app._closed = False
    app._reconciliation_tasks = {}
    app.registry = _registry(sender=sender)
    app.browser = SimpleNamespace(installed=True, lifecycle=SimpleNamespace(
        registry=ExtensionSessionRegistry(persistence=Memory()),
        replay_pending=lambda: replayed.append(True)))
    app.reconciliation = BrowserBridgeReconciliationController(
        broker=app.registry.broker, snapshot_source=app._reconciliation_snapshot,
        route_current=app.registry.route_current_for_reconciliation,
        promote=app.registry.promote_reconciled, timeout_ms=timeout_ms)
    return app, emitted, replayed, sent


def result_for(control, hello):
    # Exact native-wrapped extension result, not a prevalidated summary.
    result = {"contract_version": 1, "control_id": control["control_id"],
              "install_instance_id": hello["host_browser"]["extension"]["install_instance_id"],
              "load_generation_id": control["load_generation_id"],
              "leases": [], "inflight_operations": [], "terminal_action_receipts": [],
              "pending_critical_events": [], "prior_generation_orphans": []}
    return {key: control[key] for key in ("contract_version", "method", "bridge_id", "load_generation_id", "control_id")} | {"ok": True, "result": result}


def test_first_hello_has_no_work_second_reconciles_once_then_exact_response_promotes():
    async def scenario():
        app, emitted, replayed, sent = application()
        principal = _principal()
        hello = _hello(principal)
        session, turn = app.browser.lifecycle.registry.begin_turn(
            context_id="context-A", browser_id="extension:bridge-A", bridge_id="bridge-A")
        first = app.register_hello(principal=principal, connector_sid="sid-A", data=hello)
        assert emitted == [] and replayed == [] and app._reconciliation_tasks == {}
        assert not app.registry.current_bridge_ready("bridge-A")
        assert app.registry.resolve_extension_route("context-A", "bridge-A") is None
        second = app.register_hello(principal=principal, connector_sid="sid-A", data=hello)
        assert admitted_hello_projection(first) == admitted_hello_projection(second)
        tasks = tuple(app._reconciliation_tasks.values())
        app.register_hello(principal=principal, connector_sid="sid-A", data=hello)
        assert tuple(app._reconciliation_tasks.values()) == tasks
        await asyncio.wait_for(sent.wait(), 1)
        control = emitted[0][2]
        assert control["method"] == "browser.reconcile" and len(emitted) == 1
        assert control["expected_contexts"] == [{"context_id": "context-A",
            "browser_session_id": session.browser_session_id, "active_turn_ids": [turn.turn_id]}]
        response = await app.dispatch(principal, "sid-A", "connector_browser_control_result", result_for(control, hello))
        assert response["status"] == SettlementStatus.SETTLED
        assert app.registry.current_bridge_ready("bridge-A")
        assert app.registry.resolve_extension_route("context-A", "bridge-A") is not None
        await tasks[0]
        assert replayed == [True]
        app.register_hello(principal=principal, connector_sid="sid-A", data=hello)
        assert len(emitted) == 1 and app.registry.current_bridge_ready("bridge-A")
        app.registry.retire_all()
    asyncio.run(scenario())


@pytest.mark.parametrize("mode", ["replacement", "timeout"])
def test_replacement_and_timeout_cannot_promote_or_replay(mode):
    async def scenario():
        app, emitted, replayed, sent = application(timeout_ms=20 if mode == "timeout" else 1_000)
        principal = _principal()
        hello = _hello(principal)
        app.register_hello(principal=principal, connector_sid="sid-A", data=hello)
        app.register_hello(principal=principal, connector_sid="sid-A", data=hello)
        tasks = tuple(app._reconciliation_tasks.values())
        await asyncio.wait_for(sent.wait(), 1)
        if mode == "replacement":
            newer = _hello(principal)
            newer["host_browser"]["extension"]["load_generation_id"] = "generation-B"
            app.register_hello(principal=principal, connector_sid="sid-A", data=newer)
            response = await app.dispatch(principal, "sid-A", "connector_browser_control_result", result_for(emitted[0][2], hello))
            assert response["status"] != SettlementStatus.SETTLED
        outcomes = await asyncio.gather(*tasks, return_exceptions=True)
        if mode == "replacement":
            assert len(outcomes) == 1 and getattr(outcomes[0], "code", None) == "CONNECTION_LOST"
        assert not app.registry.current_bridge_ready("bridge-A") and replayed == []
        current = app.registry.current_sid_route(principal, "sid-A")
        assert (current is not None and current.load_generation_id == "generation-B") if mode == "replacement" else current is None
        app.registry.retire_all()
    asyncio.run(scenario())


def test_private_stage_diagnostics_are_allowlisted_bounded_and_redacted(monkeypatch, caplog):
    from plugins._a0_connector.helpers import browser_bridge_application as module
    monkeypatch.setattr(module, "_stage_counts", {})
    for _ in range(10):
        module.record_production_browser_stage("RECONCILIATION_STARTED")
    module.record_production_browser_stage("PRIVATE_BRIDGE_CANARY")
    module._record_reconciliation_failure(SimpleNamespace(code="PRIVATE_EXCEPTION_CANARY"))
    module._record_reconciliation_failure(SimpleNamespace(code="DEADLINE_EXCEEDED"))
    for code in ("ADMISSION_HEARTBEAT_REJECTED", "ADMISSION_RELEASE_UNVERIFIED", "RECONCILIATION_BROKER_SCOPE_LOST"):
        for _ in range(10):
            module.record_production_browser_stage(code)
    assert len(caplog.records) == 22
    assert "PRIVATE_" not in caplog.text
    assert "RECONCILIATION_OTHER_FAILURE" in caplog.text
    assert "RECONCILIATION_TIMEOUT" in caplog.text
