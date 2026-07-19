from __future__ import annotations

import importlib
import json
import sys
import types
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


def _load_fasta2a_server(monkeypatch):
    settings_stub = types.ModuleType("helpers.settings")
    settings_stub.get_settings = lambda: {
        "a2a_server_enabled": True,
        "mcp_server_token": "test-token",
    }
    monkeypatch.setitem(sys.modules, "helpers.settings", settings_stub)

    projects_stub = types.ModuleType("helpers.projects")
    projects_stub.activate_project = lambda *args, **kwargs: None
    monkeypatch.setitem(sys.modules, "helpers.projects", projects_stub)

    print_style_stub = types.ModuleType("helpers.print_style")

    class _PrintStyle:
        def __init__(self, *args, **kwargs):
            pass

        def print(self, *args, **kwargs):
            pass

    print_style_stub.PrintStyle = _PrintStyle
    monkeypatch.setitem(sys.modules, "helpers.print_style", print_style_stub)

    starlette_stub = types.ModuleType("starlette")
    starlette_responses_stub = types.ModuleType("starlette.responses")

    class _Response:
        def __init__(self, content=b"", media_type=None, *args, **kwargs):
            self.body = content if isinstance(content, bytes) else str(content).encode()
            self.media_type = media_type

    starlette_responses_stub.Response = _Response
    starlette_requests_stub = types.ModuleType("starlette.requests")
    starlette_requests_stub.Request = object
    monkeypatch.setitem(sys.modules, "starlette", starlette_stub)
    monkeypatch.setitem(sys.modules, "starlette.responses", starlette_responses_stub)
    monkeypatch.setitem(sys.modules, "starlette.requests", starlette_requests_stub)

    agent_stub = types.ModuleType("agent")
    agent_stub.AgentContext = type(
        "AgentContext",
        (),
        {"remove": staticmethod(lambda *args, **kwargs: None)},
    )
    agent_stub.UserMessage = lambda **kwargs: types.SimpleNamespace(**kwargs)
    agent_stub.AgentContextType = types.SimpleNamespace(BACKGROUND="background")
    monkeypatch.setitem(sys.modules, "agent", agent_stub)

    initialize_stub = types.ModuleType("initialize")
    initialize_stub.initialize_agent = lambda: {}
    monkeypatch.setitem(sys.modules, "initialize", initialize_stub)

    persist_chat_stub = types.ModuleType("helpers.persist_chat")
    persist_chat_stub.remove_chat = lambda *args, **kwargs: None
    monkeypatch.setitem(sys.modules, "helpers.persist_chat", persist_chat_stub)

    sys.modules.pop("helpers.fasta2a_server", None)
    return importlib.import_module("helpers.fasta2a_server")


def test_a2a_agent_card_streaming_capability_is_enabled_by_default(monkeypatch):
    module = _load_fasta2a_server(monkeypatch)

    updated = module._enable_streaming_capability(
        b'{"name":"Agent Zero","capabilities":{"streaming":false,"pushNotifications":false}}'
    )

    agent_card = json.loads(updated)
    assert agent_card["capabilities"]["streaming"] is True
    assert agent_card["capabilities"]["pushNotifications"] is False


def test_a2a_agent_card_streaming_capability_creates_missing_block(monkeypatch):
    module = _load_fasta2a_server(monkeypatch)

    updated = module._enable_streaming_capability(b'{"name":"Agent Zero"}')

    assert json.loads(updated)["capabilities"] == {"streaming": True}


def test_a2a_proxy_uses_streaming_enabled_fast_a2a_wrapper(monkeypatch):
    module = _load_fasta2a_server(monkeypatch)
    proxy = object.__new__(module.DynamicA2AProxy)

    proxy._configure()

    assert isinstance(proxy.app, module.AgentZeroFastA2A)
