import asyncio
import sys
from pathlib import Path
from types import ModuleType

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import helpers.settings as settings_module


def test_apply_settings_updates_mcp_from_current_settings(monkeypatch):
    base_settings = settings_module.get_default_settings()
    previous_mcp_servers = '{"mcpServers": {}}'
    current_mcp_servers = '{"mcpServers": {"deepwiki": {"url": "https://mcp.deepwiki.com/mcp"}}}'
    previous = {
        **base_settings,
        "mcp_servers": previous_mcp_servers,
        "mcp_server_token": "unchanged-token",
    }
    current = {
        **base_settings,
        "mcp_servers": current_mcp_servers,
        "mcp_server_token": "unchanged-token",
    }
    received_mcp_servers: list[str] = []

    class FakeDeferredTask:
        def start_task(self, func, *args, **kwargs):
            asyncio.run(func(*args, **kwargs))
            return self

    class FakePrintStyle:
        def __init__(self, *args, **kwargs):
            pass

        def print(self, *args, **kwargs):
            pass

    class FakeMCPConfig:
        @classmethod
        def get_instance(cls):
            return cls()

        @classmethod
        def update(cls, mcp_servers):
            received_mcp_servers.append(mcp_servers)

        def model_dump_json(self):
            return "{}"

    agent_stub = ModuleType("agent")
    agent_stub.Agent = object

    class FakeAgentContext:
        @staticmethod
        def all():
            return []

    agent_stub.AgentContext = FakeAgentContext

    initialize_stub = ModuleType("initialize")
    initialize_stub.initialize_agent = lambda override_settings=None: None

    mcp_handler_stub = ModuleType("helpers.mcp_handler")
    mcp_handler_stub.MCPConfig = FakeMCPConfig

    monkeypatch.setitem(sys.modules, "agent", agent_stub)
    monkeypatch.setitem(sys.modules, "initialize", initialize_stub)
    monkeypatch.setitem(sys.modules, "helpers.mcp_handler", mcp_handler_stub)
    monkeypatch.setattr(settings_module, "_settings", current)
    monkeypatch.setattr(settings_module, "_apply_timezone_setting", lambda *args, **kwargs: None)
    monkeypatch.setattr(settings_module.defer, "DeferredTask", FakeDeferredTask)
    monkeypatch.setattr(settings_module, "PrintStyle", FakePrintStyle)
    monkeypatch.setattr(settings_module.NotificationManager, "send_notification", lambda **kwargs: None)
    monkeypatch.setattr(settings_module, "create_auth_token", lambda: "unchanged-token")

    settings_module._apply_settings(previous)

    assert received_mcp_servers == [current_mcp_servers]
