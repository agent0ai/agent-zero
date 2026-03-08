import asyncio
import threading

from python.api.mcp_servers_status import McpServersStatuss
from python.api.mcp_tools_reload import McpToolsReload
from python.helpers.mcp_handler import MCPConfig


class _FakeMCPConfig:
    def __init__(self, should_fail: bool = False):
        self.should_fail = should_fail
        self.status = [{"name": "demo", "connected": True, "tool_count": 3, "error": "", "has_log": False}]

    async def reload_tools(self, force_reconnect: bool = False):
        if self.should_fail:
            raise RuntimeError("reload failed")
        return {
            "rebuilt": True,
            "cache_key": "abc123",
            "tool_count": 3,
            "duration_ms": 12,
            "error": None,
        }

    def get_servers_status_lightweight(self):
        return self.status


def test_mcp_tools_reload_api_success(monkeypatch):
    fake = _FakeMCPConfig()
    monkeypatch.setattr(MCPConfig, "get_instance", classmethod(lambda cls: fake))

    handler = McpToolsReload(app=None, thread_lock=threading.Lock())
    result = asyncio.run(handler.process({"force_reconnect": True}, request=None))

    assert result["success"] is True
    assert result["status"] == fake.status
    assert result["cache"]["rebuilt"] is True
    assert result["cache"]["tool_count"] == 3


def test_mcp_tools_reload_api_failure(monkeypatch):
    fake = _FakeMCPConfig(should_fail=True)
    monkeypatch.setattr(MCPConfig, "get_instance", classmethod(lambda cls: fake))

    handler = McpToolsReload(app=None, thread_lock=threading.Lock())
    result = asyncio.run(handler.process({"force_reconnect": True}, request=None))

    assert result["success"] is False
    assert result["status"] == fake.status
    assert "reload failed" in (result["cache"]["error"] or "")


def test_mcp_servers_status_uses_lightweight_status(monkeypatch):
    fake = _FakeMCPConfig()
    monkeypatch.setattr(MCPConfig, "get_instance", classmethod(lambda cls: fake))

    handler = McpServersStatuss(app=None, thread_lock=threading.Lock())
    result = asyncio.run(handler.process({}, request=None))

    assert result["success"] is True
    assert result["status"] == fake.status
