"""Tests for python/helpers/mcp_handler.py — MCP tool discovery, invocation, response parsing."""

import sys
import json
import asyncio
from pathlib import Path
from unittest.mock import MagicMock, AsyncMock, patch, PropertyMock

import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


@pytest.fixture(autouse=True)
def _reset_mcp_config():
    """Reset MCPConfig singleton state before each test."""
    import python.helpers.mcp_handler as mcp_module
    mcp_module.MCPConfig._MCPConfig__instance = None
    mcp_module.MCPConfig._MCPConfig__initialized = False
    yield
    mcp_module.MCPConfig._MCPConfig__instance = None
    mcp_module.MCPConfig._MCPConfig__initialized = False


# --- normalize_name ---

class TestNormalizeName:
    def test_lowercase_and_strip(self):
        from python.helpers.mcp_handler import normalize_name
        assert normalize_name("  MyServer  ") == "myserver"

    def test_replaces_non_alphanumeric_with_underscore(self):
        from python.helpers.mcp_handler import normalize_name
        assert normalize_name("my-server!") == "my_server_"

    def test_unicode_chars_replaced(self):
        from python.helpers.mcp_handler import normalize_name
        assert normalize_name("café") == "caf_"

    def test_spaces_replaced(self):
        from python.helpers.mcp_handler import normalize_name
        assert normalize_name("my server") == "my_server"


# --- _determine_server_type ---

class TestDetermineServerType:
    def test_explicit_sse_returns_remote(self):
        from python.helpers.mcp_handler import _determine_server_type
        assert _determine_server_type({"type": "sse"}) == "MCPServerRemote"

    def test_explicit_streamable_http_returns_remote(self):
        from python.helpers.mcp_handler import _determine_server_type
        assert _determine_server_type({"type": "streamable-http"}) == "MCPServerRemote"

    def test_explicit_stdio_returns_local(self):
        from python.helpers.mcp_handler import _determine_server_type
        assert _determine_server_type({"type": "stdio"}) == "MCPServerLocal"

    def test_url_present_returns_remote(self):
        from python.helpers.mcp_handler import _determine_server_type
        assert _determine_server_type({"url": "https://example.com"}) == "MCPServerRemote"

    def test_server_url_present_returns_remote(self):
        from python.helpers.mcp_handler import _determine_server_type
        assert _determine_server_type({"serverUrl": "https://example.com"}) == "MCPServerRemote"

    def test_no_url_no_type_returns_local(self):
        from python.helpers.mcp_handler import _determine_server_type
        assert _determine_server_type({"command": "npx", "args": ["mcp-server"]}) == "MCPServerLocal"


# --- _is_streaming_http_type ---

class TestIsStreamingHttpType:
    def test_streamable_http_true(self):
        from python.helpers.mcp_handler import _is_streaming_http_type
        assert _is_streaming_http_type("streamable-http") is True

    def test_sse_false(self):
        from python.helpers.mcp_handler import _is_streaming_http_type
        assert _is_streaming_http_type("sse") is False

    def test_stdio_false(self):
        from python.helpers.mcp_handler import _is_streaming_http_type
        assert _is_streaming_http_type("stdio") is False


# --- MCPConfig.normalize_config ---

class TestMCPConfigNormalizeConfig:
    def test_list_passthrough(self):
        from python.helpers.mcp_handler import MCPConfig
        config = [{"name": "s1", "url": "https://x.com"}, {"name": "s2", "command": "npx"}]
        result = MCPConfig.normalize_config(config)
        assert len(result) == 2
        assert result[0]["name"] == "s1"
        assert result[1]["name"] == "s2"

    def test_mcp_servers_dict_normalized(self):
        from python.helpers.mcp_handler import MCPConfig
        config = {"mcpServers": {"my-server": {"url": "https://x.com"}, "other": {"command": "npx"}}}
        result = MCPConfig.normalize_config(config)
        assert len(result) == 2
        names = [r["name"] for r in result]
        assert "my-server" in names
        assert "other" in names

    def test_mcp_servers_list_normalized(self):
        from python.helpers.mcp_handler import MCPConfig
        config = {"mcpServers": [{"name": "s1", "url": "https://x.com"}]}
        result = MCPConfig.normalize_config(config)
        assert len(result) == 1
        assert result[0]["name"] == "s1"

    def test_single_dict_wrapped(self):
        from python.helpers.mcp_handler import MCPConfig
        config = {"name": "single", "url": "https://x.com"}
        result = MCPConfig.normalize_config(config)
        assert len(result) == 1
        assert result[0]["name"] == "single"

    def test_non_dict_items_skipped(self):
        from python.helpers.mcp_handler import MCPConfig
        config = [{"name": "s1"}, "invalid", {"name": "s2"}]
        result = MCPConfig.normalize_config(config)
        assert len(result) == 2


# --- MCPConfig singleton and update ---

class TestMCPConfigSingleton:
    def test_get_instance_returns_singleton(self):
        from python.helpers.mcp_handler import MCPConfig
        a = MCPConfig.get_instance()
        b = MCPConfig.get_instance()
        assert a is b

    def test_update_with_empty_string_initializes_empty(self):
        from python.helpers.mcp_handler import MCPConfig
        with patch("python.helpers.mcp_handler.dirty_json") as mock_dj:
            mock_dj.try_parse.return_value = []
            MCPConfig.update("")
            inst = MCPConfig.get_instance()
            assert inst.servers == []
            assert MCPConfig._MCPConfig__initialized is True

    def test_update_with_valid_json_creates_servers(self):
        from python.helpers.mcp_handler import MCPConfig
        config_str = '[{"name": "remote1", "url": "https://example.com"}]'
        mock_client_instance = MagicMock()
        mock_client_instance.update_tools = AsyncMock(return_value=mock_client_instance)
        mock_client_instance.tools = []
        mock_client_instance.error = ""
        mock_client_instance.has_tool = lambda n: False
        with (
            patch("python.helpers.mcp_handler.dirty_json") as mock_dj,
            patch("python.helpers.mcp_handler.MCPClientRemote", return_value=mock_client_instance),
        ):
            mock_dj.try_parse.return_value = [{"name": "remote1", "url": "https://example.com"}]
            MCPConfig.update(config_str)
            inst = MCPConfig.get_instance()
            assert len(inst.servers) == 1
            assert inst.servers[0].name == "remote1"


# --- MCPConfig.has_tool, get_tool, call_tool ---

class TestMCPConfigToolOperations:
    def test_has_tool_requires_dot(self):
        from python.helpers.mcp_handler import MCPConfig
        MCPConfig._MCPConfig__instance = MCPConfig(servers_list=[])
        assert MCPConfig.get_instance().has_tool("bare_tool") is False

    def test_has_tool_false_when_no_servers(self):
        from python.helpers.mcp_handler import MCPConfig
        MCPConfig._MCPConfig__instance = MCPConfig(servers_list=[])
        assert MCPConfig.get_instance().has_tool("server.tool") is False

    def test_get_tool_returns_none_when_not_found(self, mock_agent):
        from python.helpers.mcp_handler import MCPConfig
        MCPConfig._MCPConfig__instance = MCPConfig(servers_list=[])
        result = MCPConfig.get_instance().get_tool(mock_agent, "server.tool")
        assert result is None

    def test_get_tool_returns_mcp_tool_when_found(self, mock_agent):
        from python.helpers.mcp_handler import MCPConfig, MCPTool
        inst = MCPConfig(servers_list=[])
        mock_server = MagicMock()
        mock_server.name = "myserver"
        mock_server.has_tool.return_value = True
        inst.servers = [mock_server]
        MCPConfig._MCPConfig__instance = inst
        result = MCPConfig.get_instance().get_tool(mock_agent, "myserver.mytool")
        assert result is not None
        assert isinstance(result, MCPTool)
        assert result.name == "myserver.mytool"


# --- MCPConfig.get_servers_status, get_server_detail ---

class TestMCPConfigStatus:
    def test_get_servers_status_empty(self):
        from python.helpers.mcp_handler import MCPConfig
        MCPConfig._MCPConfig__instance = MCPConfig(servers_list=[])
        status = MCPConfig.get_instance().get_servers_status()
        assert status == []

    def test_get_servers_status_includes_disconnected(self):
        from python.helpers.mcp_handler import MCPConfig
        inst = MCPConfig(servers_list=[])
        inst.disconnected_servers = [{"name": "failed", "error": "Disabled", "config": {}}]
        status = inst.get_servers_status()
        assert any(s["name"] == "failed" and not s["connected"] for s in status)

    def test_get_server_detail_empty_when_not_found(self):
        from python.helpers.mcp_handler import MCPConfig
        MCPConfig._MCPConfig__instance = MCPConfig(servers_list=[])
        detail = MCPConfig.get_instance().get_server_detail("nonexistent")
        assert detail == {}


# --- MCPConfig.get_tools_prompt ---

class TestMCPConfigGetToolsPrompt:
    def test_get_tools_prompt_raises_for_unknown_server(self):
        from python.helpers.mcp_handler import MCPConfig
        MCPConfig._MCPConfig__instance = MCPConfig(servers_list=[])
        with pytest.raises(ValueError, match="Server .* not found"):
            MCPConfig.get_instance().get_tools_prompt(server_name="unknown")

    def test_get_tools_prompt_returns_header_without_servers(self):
        from python.helpers.mcp_handler import MCPConfig
        MCPConfig._MCPConfig__instance = MCPConfig(servers_list=[])
        prompt = MCPConfig.get_instance().get_tools_prompt()
        assert "Remote (MCP Server) Agent Tools" in prompt


# --- MCPTool execute ---

class TestMCPToolExecute:
    @pytest.mark.asyncio
    async def test_execute_success_returns_response(self, mock_agent):
        from python.helpers.mcp_handler import MCPTool
        from python.helpers.tool import Response
        from mcp.types import TextContent, CallToolResult
        tool = MCPTool(agent=mock_agent, name="server.mytool", method=None, args={}, message="", loop_data=None)
        with patch("python.helpers.mcp_handler.MCPConfig.get_instance") as mock_get:
            mock_config = MagicMock()
            mock_config.call_tool = AsyncMock(
                return_value=CallToolResult(content=[TextContent(type="text", text="ok")], isError=False)
            )
            mock_get.return_value = mock_config
            resp = await tool.execute()
            assert isinstance(resp, Response)
            assert resp.message == "ok"
            assert resp.break_loop is False

    @pytest.mark.asyncio
    async def test_execute_error_sets_message(self, mock_agent):
        from python.helpers.mcp_handler import MCPTool
        from mcp.types import TextContent, CallToolResult
        tool = MCPTool(agent=mock_agent, name="server.mytool", method=None, args={}, message="", loop_data=None)
        with patch("python.helpers.mcp_handler.MCPConfig.get_instance") as mock_get:
            mock_config = MagicMock()
            mock_config.call_tool = AsyncMock(
                return_value=CallToolResult(content=[TextContent(type="text", text="Tool failed")], isError=True)
            )
            mock_get.return_value = mock_config
            resp = await tool.execute()
            assert "Tool failed" in resp.message

    @pytest.mark.asyncio
    async def test_execute_exception_returns_error_message(self, mock_agent):
        from python.helpers.mcp_handler import MCPTool
        tool = MCPTool(agent=mock_agent, name="server.mytool", method=None, args={}, message="", loop_data=None)
        with patch("python.helpers.mcp_handler.MCPConfig.get_instance") as mock_get:
            mock_config = MagicMock()
            mock_config.call_tool = AsyncMock(side_effect=ConnectionError("Connection refused"))
            mock_get.return_value = mock_config
            resp = await tool.execute()
            assert "Connection refused" in resp.message

    @pytest.mark.asyncio
    async def test_execute_joins_multiple_text_content_items(self, mock_agent):
        from python.helpers.mcp_handler import MCPTool
        from mcp.types import TextContent, CallToolResult
        tool = MCPTool(agent=mock_agent, name="server.mytool", method=None, args={}, message="", loop_data=None)
        with patch("python.helpers.mcp_handler.MCPConfig.get_instance") as mock_get:
            mock_config = MagicMock()
            mock_config.call_tool = AsyncMock(
                return_value=CallToolResult(
                    content=[
                        TextContent(type="text", text="part1"),
                        TextContent(type="text", text="part2"),
                    ],
                    isError=False,
                )
            )
            mock_get.return_value = mock_config
            resp = await tool.execute()
            assert "part1" in resp.message and "part2" in resp.message


# --- MCPServerRemote / MCPServerLocal update ---

class TestMCPServerUpdate:
    def test_mcpserver_remote_update_remaps_server_url(self):
        from python.helpers.mcp_handler import MCPServerRemote
        with patch("python.helpers.mcp_handler.MCPClientRemote"):
            server = MCPServerRemote({"name": "Test", "serverUrl": "https://x.com"})
            assert server.url == "https://x.com"

    def test_mcpserver_local_update_sets_command(self):
        from python.helpers.mcp_handler import MCPServerLocal
        with patch("python.helpers.mcp_handler.MCPClientLocal"):
            server = MCPServerLocal({"name": "local", "command": "npx", "args": ["mcp-server"]})
            assert server.command == "npx"
            assert server.args == ["mcp-server"]


# --- call_tool error handling ---

class TestMCPConfigCallTool:
    @pytest.mark.asyncio
    async def test_call_tool_raises_for_missing_dot(self):
        from python.helpers.mcp_handler import MCPConfig
        MCPConfig._MCPConfig__instance = MCPConfig(servers_list=[])
        with pytest.raises(ValueError, match="Tool .* not found"):
            await MCPConfig.get_instance().call_tool("bare_tool", {})

    @pytest.mark.asyncio
    async def test_call_tool_raises_when_server_not_found(self):
        from python.helpers.mcp_handler import MCPConfig
        MCPConfig._MCPConfig__instance = MCPConfig(servers_list=[])
        with pytest.raises(ValueError, match="Tool .* not found"):
            await MCPConfig.get_instance().call_tool("unknown.tool", {})


# --- initialize_mcp ---

class TestInitializeMCP:
    def test_initialize_mcp_skips_when_already_initialized(self):
        from python.helpers.mcp_handler import initialize_mcp, MCPConfig
        MCPConfig._MCPConfig__initialized = True
        with patch("python.helpers.mcp_handler.MCPConfig.update") as mock_update:
            initialize_mcp('[{"name":"x","url":"https://x.com"}]')
            mock_update.assert_not_called()
