"""Global selection uses synthetic configuration, never live pairings or chats."""
import asyncio
import json
from types import SimpleNamespace

import pytest

from plugins._a0_connector.helpers import browser_bridge_selection as selection


@pytest.fixture
def state(monkeypatch):
    from helpers import plugins, runtime
    from plugins._a0_connector.helpers import browser_bridge_bootstrap as bootstrap
    from plugins._a0_connector.helpers import browser_bridge_pairing as pairing
    from plugins._browser.helpers import bridge_foundation, config
    state = SimpleNamespace(global_config={"runtime_backend": "container", "host_browser_selection": "", "proxy_server": "global-proxy"},
                            projects={"internal": {"runtime_backend": "container"}}, writes=[], retired=[], active=True, ready=False)
    def load(_name, agent=None, project_name="", agent_profile="", **kwargs):
        project = getattr(agent, "project", project_name)
        return dict(state.projects.get(project, state.global_config))
    def save(name, project, profile, value, **kwargs):
        assert (name, project, profile) == ("_browser", "", "")
        assert config._production_selection_write.get() is True
        state.writes.append(dict(value))
        state.global_config = dict(value)
    state.application = SimpleNamespace(registry=SimpleNamespace(
        retire_bridge=state.retired.append, current_bridge_ready=lambda _: state.ready))
    monkeypatch.setattr(plugins, "get_plugin_config", load)
    monkeypatch.setattr(plugins, "save_plugin_config", save)
    monkeypatch.setattr(runtime, "get_persistent_id", lambda: "server-test")
    monkeypatch.setattr(bootstrap, "get_browser_bridge_application", lambda: state.application)
    monkeypatch.setattr(bridge_foundation, "get_browser_bridge_gate", lambda: SimpleNamespace(state="available"))
    monkeypatch.setattr(pairing, "configured_extension_id", lambda: "extension-test")
    monkeypatch.setattr(pairing, "get_browser_bridge_pairing_store", lambda: SimpleNamespace(
        active_bridge_record=lambda **_: {"subject_id": pairing.SUBJECT_ID, "extension_id": "extension-test"} if state.active else None))
    return state


def test_default_inherits_for_new_chats_without_changing_project_override(state, monkeypatch):
    from agent import AgentContext
    contexts = {}
    for name, project in (("new-chat", "new-project"), ("internal-chat", "internal")):
        context = SimpleNamespace(id=name)
        context.agent0 = SimpleNamespace(context=context, project=project)
        contexts[name] = context
    monkeypatch.setattr(AgentContext, "get", staticmethod(contexts.get))
    selection.select_default_bridge("browser-A", expected_bridge_id=None)
    assert selection.selected_bridge("new-chat") == "browser-A"
    assert selection.selected_bridge("internal-chat") is None
    assert state.projects == {"internal": {"runtime_backend": "container"}}
    assert state.global_config["proxy_server"] == "global-proxy"


def test_default_cas_retires_before_replace_and_stale_clear_has_no_effect(state):
    selection.select_default_bridge("browser-A", expected_bridge_id=None)
    selection.select_default_bridge("browser-B", expected_bridge_id="browser-A")
    assert state.retired == ["browser-A"]
    with pytest.raises(RuntimeError):
        selection.select_default_bridge(None, expected_bridge_id="browser-A")
    assert len(state.writes) == 2
    assert state.retired == ["browser-A"]
    selection.select_default_bridge(None, expected_bridge_id="browser-B")
    assert selection.default_selected_bridge() is None


def test_inactive_pair_cannot_set_default_but_unavailable_owner_can_clear(state):
    state.active = False
    with pytest.raises(RuntimeError):
        selection.select_default_bridge("browser-A", expected_bridge_id=None)
    assert state.writes == []
    state.active = True
    selection.select_default_bridge("browser-A", expected_bridge_id=None)
    state.application = None
    selection.select_default_bridge(None, expected_bridge_id="browser-A")


def test_no_chat_admission_selection_does_not_authorize_overridden_context(state, monkeypatch):
    from agent import AgentContext
    from plugins._a0_connector.helpers import browser_bridge_runtime_owner as owner_module
    monkeypatch.setattr(AgentContext, "all", staticmethod(lambda: []))
    owner = object.__new__(owner_module.BrowserBridgeRuntimeOwner)
    assert not owner._selected("browser-A")
    selection.select_default_bridge("browser-A", expected_bridge_id=None)
    assert owner._selected("browser-A")
    assert not owner._selected("browser-B")
    assert not selection.selection_current("nonexistent-chat", "browser-A")


def test_default_api_is_strict_read_only_and_readiness_is_not_selection(state):
    from plugins._a0_connector.api.browser_bridge_selection import BrowserBridgeSelection
    handler = object.__new__(BrowserBridgeSelection)
    def request(body):
        return asyncio.run(handler._dispatch(body))
    response = request({"action": "default_status"})
    assert response.status_code == 200
    assert state.writes == []
    response = request({"action": "use_default", "bridge_id": "browser-A", "expected_bridge_id": None})
    value = json.loads(response.get_data())
    assert value == {"contract": "a0.browser-bridge.default-selection.v1", "bridge_id": "browser-A",
                     "selected": True, "browser_control_ready": False, "reconnect_required": True}
    state.ready = True
    assert json.loads(request({"action": "default_status"}).get_data())["browser_control_ready"] is True
    assert request({"action": "default_status", "context_id": "chat"}).status_code == 400
    assert request({"action": "use_default", "bridge_id": "browser-B"}).status_code == 400
    assert request({"action": "clear_default", "expected_bridge_id": "browser-B"}).status_code == 409
    assert request({"action": "clear_default", "expected_bridge_id": None}).status_code == 400


def test_readiness_lookup_rechecks_admission_without_granting_context():
    from test_browser_bridge_runtime_foundation import _registry, _admission, _principal, _hello
    async def scenario():
        admitted = [True]
        registry = _registry(admission_evaluator=lambda *args: _admission(*args) if admitted[0] else None,
                             context_authorizer=lambda *_: False)
        principal = _principal()
        registry.register_hello(principal=principal, connector_sid="sid-A", data=_hello(principal))
        # Transport admission alone is provisional until exact reconciliation.
        assert registry.current_bridge_ready("bridge-A") is False
        assert registry.resolve_extension_route("context-A", "bridge-A") is None
        admitted[0] = False
        assert registry.current_bridge_ready("bridge-A") is False
        assert registry.session_count == 0
    asyncio.run(scenario())
