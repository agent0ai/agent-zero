import asyncio
import pytest
from concurrent.futures import Future
from types import SimpleNamespace
from helpers.ws_principal import WsPrincipal
from plugins._a0_connector.helpers.browser_bridge_operations import (
    BridgeAuthorization,
    BrowserBridgeOperationBroker,
)
from plugins._a0_connector.helpers.browser_bridge_policy import BrowserBridgePolicyRepository
from plugins._browser.helpers.extension_runtime import configure_extension_runtime_factory
from plugins._browser.helpers.extension_services import ExtensionBrowserServices, valid_finalization_result
from plugins._browser.helpers.extension_sessions import (
    ExtensionSessionLifecycle,
    ExtensionSessionRegistry,
    ExtensionSessionStateError,
    ValidatedExtensionRoute,
    TURN_FINALIZED,
    TURN_OUTCOME_UNKNOWN,
)
from browser_bridge_test_support import MemoryPersistence
from plugins._a0_connector.helpers import browser_bridge_application, browser_bridge_runtime_owner
from plugins._browser.helpers import extension_sessions as sessions
from test_browser_extension_runtime import _fixture, _authorize, _allow


def test_finalization_rejects_malformed_duplicate_and_unbounded_lease_outcomes():
    result = {"contract_version": 1, "control_id": "control", "closed": ["lease"],
              "released": [], "retained": [], "already_finalized": [], "errors": []}
    assert valid_finalization_result(result, "control")
    assert not valid_finalization_result({**result, "contract_version": True}, "control")
    assert not valid_finalization_result({**result, "released": ["lease"]}, "control")
    assert not valid_finalization_result({**result, "closed": [12]}, "control")
    assert not valid_finalization_result({**result, "closed": [f"lease-{i}" for i in range(257)]}, "control")
    assert not valid_finalization_result({**result, "retained": [{"lease_id": "other", "tab_handle": "tab", "reason": "raw payload"}]}, "control")


def test_service_install_preserves_preexisting_factory_and_lifecycle_owners():
    lifecycle = ExtensionSessionLifecycle(
        registry=ExtensionSessionRegistry(persistence=MemoryPersistence())
    )
    services = ExtensionBrowserServices(
        lifecycle=lifecycle,
        broker=object(),
        route_resolver=lambda _context, _bridge: None,
        policy_repository=BrowserBridgePolicyRepository(load=lambda: None),
        server_instance_id="server-1",
    )
    configure_extension_runtime_factory(lambda _agent, _bridge: None)
    try:
        with pytest.raises(RuntimeError):
            services.install()
        assert not lifecycle.configured
    finally:
        configure_extension_runtime_factory(None)

    lifecycle.configure(
        route_resolver=lambda _context, _bridge: None,
        sender=lambda _intent, _route: None,
    )
    with pytest.raises(ExtensionSessionStateError) as error:
        services.install()
    assert error.value.code == "ALREADY_CONFIGURED"
    assert lifecycle.configured
    # The failed service install rolled back only its own temporary factory.
    configure_extension_runtime_factory(lambda _agent, _bridge: None)
    configure_extension_runtime_factory(None)


def test_services_compose_real_broker_synthetic_turn_and_acknowledged_cleanup(monkeypatch):
    from plugins._browser.helpers import config as browser_config
    watched_agents = []
    follow = [True]
    def settings(*, agent):
        watched_agents.append(agent)
        return {"autofocus_active_page": follow[0]}
    monkeypatch.setattr(browser_config, "get_browser_config", settings)
    async def scenario():
        principal = WsPrincipal(
            principal_type="browser_bridge", principal_id="bridge-1", subject_id="single-user",
            scopes=frozenset({"browser.operate", "browser.control"}),
            handler_path="plugins/_a0_connector/ws_connector", handler_id="ws_connector.WsConnector",
            inbound_events=frozenset({"connector_browser_op_result", "connector_browser_control_result"}),
            outbound_events=frozenset({"connector_browser_op", "connector_browser_control"}), key_generation=1,
        )
        route = ValidatedExtensionRoute("bridge-1", "extension:bridge-1", principal, "sid-1", "load-1")
        registry = ExtensionSessionRegistry(persistence=MemoryPersistence())
        lifecycle = ExtensionSessionLifecycle(
            registry=registry, config_loader=lambda _agent: {"runtime_backend": "host_required", "host_browser_selection": "extension:bridge-1"},
        )
        sent = []
        unknown = [False]

        async def sender(sid, event, payload, _correlation, expected):
            sent.append((event, payload))
            keys = ["contract_version", "bridge_id", "load_generation_id", "context_id", "browser_session_id", "turn_id"]
            if event == "connector_browser_op":
                keys += ["op_id", "action_id"]
                broker.settle_operation(
                    principal=expected, connector_sid=sid, load_generation_id="load-1",
                    payload={**{key: payload[key] for key in keys}, "ok": True, "result": {"tabs": []}, "receipts": [], "artifacts": []},
                )
            else:
                keys += ["method", "control_id"]
                broker.settle_control(
                    principal=expected, connector_sid=sid, load_generation_id="load-1",
                    payload={**{key: payload[key] for key in keys}, "ok": True, "result": {
                        "contract_version": 1, "control_id": payload["control_id"],
                        "closed": [], "released": [], "retained": [], "already_finalized": [],
                        "errors": [{"code": "OUTCOME_UNKNOWN"}] if unknown[0] else [],
                    }},
                )

        broker = BrowserBridgeOperationBroker(sender=sender, authorizer=lambda binding: BridgeAuthorization(
            principal, "sid-1", "load-1", 1,
            frozenset({"browser_extension_bridge_v1", "connector_browser_control"}), frozenset({"list"}), frozenset(),
        ))
        services = ExtensionBrowserServices(
            lifecycle=lifecycle, broker=broker, route_resolver=lambda _context, _bridge: route,
            target_origin_resolver=lambda _binding, _handle: None,
            policy_repository=BrowserBridgePolicyRepository(load=lambda: None), server_instance_id="server-1",
        )
        tasks = []

        def submit(coroutine):
            task = asyncio.create_task(coroutine)
            tasks.append(task)
            # The production dispatcher uses a process-loop concurrent Future.
            future = Future()
            task.add_done_callback(lambda _task: future.set_result(None))
            return future

        services.install(submitter=submit)
        try:
            assert services.installed
            # The legacy/test seam cannot withdraw this exact service owner.
            configure_extension_runtime_factory(None)
            assert services.installed
            agent = SimpleNamespace(context=SimpleNamespace(id="context-1"))
            runtime = services.runtime_for_agent(agent, "bridge-1")
            assert runtime is not None
            assert runtime._operation_display("open")["foreground"] is True
            assert watched_agents == [agent]
            follow[0] = False
            assert runtime._operation_display("open")["foreground"] is False
            assert await runtime.call("list", include_content=False) == {"tabs": []}
            await asyncio.gather(*tasks)
            assert [event for event, _ in sent] == ["connector_browser_op", "connector_browser_control"]
            assert sent[0][1]["display"] == {"cursor": False, "foreground": False}
            assert sent[1][1]["method"] == "browser.finalize_turn"
            assert sent[0][1]["turn_id"] == sent[1][1]["turn_id"]
            assert registry.session("context-1").turns[-1].state == TURN_FINALIZED
            assert lifecycle.active_agent_turn(agent) is None
            # A transport-level success with per-lease errors is still unknown.
            unknown[0] = True
            assert await runtime.call("list", include_content=False) == {"tabs": []}
            await asyncio.gather(*tasks)
            assert registry.session("context-1").turns[-1].state == TURN_OUTCOME_UNKNOWN
            assert sent[0][1]["browser_session_id"] == sent[2][1]["browser_session_id"]
            assert sent[0][1]["turn_id"] != sent[2][1]["turn_id"]
        finally:
            services.uninstall()
            assert not services.installed
            assert not lifecycle.configured

    asyncio.run(scenario())


def test_production_owner_hook_open_and_content_share_turn_until_monologue_end(monkeypatch):
    async def scenario():
        original_binding, policy = _fixture()
        principal = original_binding.principal
        _allow(policy)
        lifecycle = sessions.ExtensionSessionLifecycle(
            registry=sessions.ExtensionSessionRegistry(persistence=MemoryPersistence()),
            config_loader=lambda _agent: {"runtime_backend": "host_required", "host_browser_selection": "extension:bridge-1"})
        monkeypatch.setattr(sessions, "_lifecycle", lifecycle)
        # Capture the real production constructor's dependency choice without
        # installing a live socket/application or touching the default KVP.
        monkeypatch.setattr(browser_bridge_application, "BrowserBridgeApplication",
            lambda **kwargs: SimpleNamespace(browser=SimpleNamespace(lifecycle=kwargs["lifecycle"])))
        owner = browser_bridge_runtime_owner.BrowserBridgeRuntimeOwner(
            manager=SimpleNamespace(principal_for_sid=lambda *args: None), release_verifier=lambda *args: None)
        assert owner.application.browser.lifecycle is sessions.get_extension_session_lifecycle()
        route = sessions.ValidatedExtensionRoute("bridge-1", "extension:bridge-1", principal, "sid-1", "load-1")
        sent, bindings, tasks = [], [], []
        async def sender(sid, event, payload, correlation, expected):
            sent.append((event, payload))
            keys = ["contract_version", "bridge_id", "load_generation_id", "context_id", "browser_session_id", "turn_id"]
            if event == "connector_browser_op":
                keys += ["op_id", "action_id"]
                if payload["action"] == "open":
                    result = {"browser_id": "tab-1", "tab_handle": "tab-1", "lease_id": "lease-1",
                              "origin": "https://example.com", "disposition": "ephemeral", "grouped": True}
                else:
                    result = {"browser_id": "tab-1", "tab_handle": "tab-1", "lease_id": "lease-1",
                              "document_id": "doc-1", "document_epoch": "1", "title": "Synthetic",
                              "text": "Synthetic page", "nodes": [], "truncated": False}
                broker.settle_operation(principal=expected, connector_sid=sid, load_generation_id="load-1",
                    payload={**{key: payload[key] for key in keys}, "ok": True, "result": result, "receipts": [], "artifacts": []})
            else:
                keys += ["method", "control_id"]
                broker.settle_control(principal=expected, connector_sid=sid, load_generation_id="load-1",
                    payload={**{key: payload[key] for key in keys}, "ok": True, "result": {
                        "contract_version": 1, "control_id": payload["control_id"], "closed": ["lease-1"],
                        "released": [], "retained": [], "already_finalized": [], "errors": []}})
        def authorize(binding):
            if hasattr(binding, "op_id"):
                bindings.append(binding)
            return _authorize(binding)
        broker = BrowserBridgeOperationBroker(sender=sender, authorizer=authorize)
        services = ExtensionBrowserServices(lifecycle=owner.application.browser.lifecycle, broker=broker,
            route_resolver=lambda *args: route, policy_repository=policy, server_instance_id="server-1")
        def submit(coroutine):
            tasks.append(asyncio.create_task(coroutine))
            return Future()
        services.install(submitter=submit)
        agent = SimpleNamespace(context=SimpleNamespace(id="context-1"))
        try:
            assert sessions.begin_extension_monologue(agent) is not None
            first = services.runtime_for_agent(agent, "bridge-1")
            result = await first.call("open", "https://example.com/")
            second = services.runtime_for_agent(agent, "bridge-1")
            assert (await second.call("content", result["browser_id"], None))["text"] == "Synthetic page"
            operations = [payload for event, payload in sent if event == "connector_browser_op"]
            assert len(operations) == 2 and operations[0]["turn_id"] == operations[1]["turn_id"]
            assert operations[0]["browser_session_id"] == operations[1]["browser_session_id"]
            assert not tasks and all(event == "connector_browser_op" for event, payload in sent)
            assert services.leases.origin_for(bindings[-1], "tab-1") == "https://example.com"
            sessions.finalize_extension_monologue(agent, reason="completed")
            await asyncio.gather(*tasks)
            assert services.leases.origin_for(bindings[-1], "tab-1") is None
            assert len([event for event, payload in sent if event == "connector_browser_control"]) == 1
        finally:
            services.uninstall()
            await asyncio.gather(*tasks)
    asyncio.run(scenario())
