from __future__ import annotations

import asyncio
from types import SimpleNamespace

import pytest

from agent import AgentContext
from helpers import extension
from helpers.api import Response
from plugins._a0_connector.api.v1.capabilities import _feature_list
from plugins._a0_connector.api.v1.composer_controls import ComposerControls


@pytest.fixture
def context(monkeypatch):
    agent = SimpleNamespace(enabled={"sample.mode", "sample.format"})
    context = SimpleNamespace(id="composer-test", agent0=agent)
    monkeypatch.setattr(AgentContext, "get", lambda key: context if key == context.id else None)
    return context


def call(context, **payload):
    return asyncio.run(ComposerControls(None, None).process({"context_id": context.id, **payload}, None))


def test_generic_controls_are_authenticated_csrf_protected_and_capability_gated():
    assert "composer_controls" in _feature_list()
    assert ComposerControls.requires_auth() is True
    assert ComposerControls.requires_csrf() is True


def test_two_scoped_extensions_can_supply_and_handle_unrelated_controls(context, monkeypatch):
    class Mode(extension.Extension):
        async def execute(self, action, input, controls, result):
            if action == "list":
                controls.append({"id": "sample.mode", "type": "choice", "label": "Mode", "value": "fast", "options": []})
            elif input["control_id"] == "sample.mode":
                result["response"] = {"ok": True, "accepted": input["value"]}

    class Format(extension.Extension):
        async def execute(self, action, input, controls, result):
            if action == "list":
                controls.append({"id": "sample.format", "type": "choice", "label": "Format", "value": "json", "options": []})
            elif input["control_id"] == "sample.format":
                result["response"] = Response(status=409, response="Stale format revision")

    def scoped(point, agent, **kwargs):
        assert point == "connector_controls"
        assert agent is context.agent0
        return [cls for name, cls in (("sample.mode", Mode), ("sample.format", Format)) if name in agent.enabled]

    monkeypatch.setattr(extension, "_get_extension_classes", scoped)
    assert [control["id"] for control in call(context, action="list")["controls"]] == ["sample.mode", "sample.format"]
    assert call(context, action="set", control_id="sample.mode", value="careful") == {"ok": True, "accepted": "careful"}
    response = call(context, action="set", control_id="sample.format", value="text", revision="old")
    assert response.status_code == 409
    context.agent0.enabled.clear()
    assert call(context, action="list") == {"ok": True, "controls": []}
    assert call(context, action="set", control_id="sample.mode", value="fast").status_code == 404


@pytest.mark.parametrize("payload,status", [
    ({"context_id": ""}, 400), ({"context_id": "missing"}, 404),
    ({"action": "run_code"}, 400), ({"action": "set", "control_id": ""}, 400),
    ({"action": "set", "control_id": "mode", "value": []}, 400),
    ({"action": "set", "control_id": "mode", "value": "fast", "custom": "false"}, 400),
])
def test_invalid_requests_never_reach_extensions(context, monkeypatch, payload, status):
    async def unexpected(*args, **kwargs):
        pytest.fail("Invalid requests must not dispatch extensions")

    monkeypatch.setattr(extension, "call_extensions_async", unexpected)
    assert call(context, **payload).status_code == status
