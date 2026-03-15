"""
Unit tests for python/helpers/mcp_server.py — MCP server lifecycle, tool registration,
DynamicMcpProxy, send_message, finish_chat, routing, and middleware.
"""
import sys
import asyncio
from pathlib import Path
from unittest.mock import MagicMock, AsyncMock, patch, PropertyMock

import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


# ─── Fixtures: patch heavy dependencies before importing mcp_server ────────────

@pytest.fixture(autouse=True)
def _patch_mcp_dependencies():
    """Patch external deps so mcp_server can be imported without full Agent Zero stack."""
    with (
        patch("python.helpers.mcp_server.AgentContext"),
        patch("python.helpers.mcp_server.initialize_agent"),
        patch("python.helpers.mcp_server.remove_chat"),
        patch("python.helpers.mcp_server.projects"),
        patch("python.helpers.mcp_server.settings"),
        patch("python.helpers.mcp_server.PrintStyle"),
    ):
        yield


def _import_mcp_server():
    """Import mcp_server under patches (call inside test or fixture)."""
    import python.helpers.mcp_server as mcp
    return mcp


# ─── ToolResponse / ToolError models ──────────────────────────────────────────

class TestToolModels:
    def test_tool_response_defaults(self):
        mcp = _import_mcp_server()
        r = mcp.ToolResponse(response="ok", chat_id="c1")
        assert r.status == "success"
        assert r.response == "ok"
        assert r.chat_id == "c1"

    def test_tool_error_defaults(self):
        mcp = _import_mcp_server()
        e = mcp.ToolError(error="fail", chat_id="c1")
        assert e.status == "error"
        assert e.error == "fail"
        assert e.chat_id == "c1"


# ─── send_message tool ────────────────────────────────────────────────────────

def _send_message(mcp):
    """Get the raw send_message async function (unwrap FunctionTool decorator)."""
    tool = getattr(mcp, "send_message")
    return tool.fn if hasattr(tool, "fn") else tool


def _finish_chat(mcp):
    """Get the raw finish_chat async function (unwrap FunctionTool decorator)."""
    tool = getattr(mcp, "finish_chat")
    return tool.fn if hasattr(tool, "fn") else tool


class TestSendMessage:
    @pytest.mark.asyncio
    async def test_empty_message_returns_error(self):
        mcp = _import_mcp_server()
        mcp._mcp_project_name.set(None)
        with patch.object(mcp, "_run_chat", new_callable=AsyncMock):
            result = await _send_message(mcp)(message="", chat_id=None, persistent_chat=False)
        assert isinstance(result, mcp.ToolError)
        assert "Message is required" in result.error

    @pytest.mark.asyncio
    async def test_chat_not_found_returns_error(self):
        mcp = _import_mcp_server()
        mcp._mcp_project_name.set(None)
        mcp.AgentContext.get.return_value = None
        result = await _send_message(mcp)(message="hi", chat_id="nonexistent")
        assert isinstance(result, mcp.ToolError)
        assert "Chat not found" in result.error

    @pytest.mark.asyncio
    async def test_project_mismatch_returns_error(self):
        mcp = _import_mcp_server()
        mcp._mcp_project_name.set("project_a")
        ctx = MagicMock()
        ctx.id = "chat-1"
        ctx.get_data.return_value = "project_b"
        mcp.AgentContext.get.return_value = ctx
        result = await _send_message(mcp)(message="hi", chat_id="chat-1")
        assert isinstance(result, mcp.ToolError)
        assert "Chat belongs to project" in result.error

    @pytest.mark.asyncio
    async def test_success_non_persistent_removes_context(self):
        mcp = _import_mcp_server()
        mcp._mcp_project_name.set(None)
        mcp.initialize_agent.return_value = MagicMock()
        ctx = MagicMock()
        ctx.id = "ctx-1"
        mcp.AgentContext.return_value = ctx
        with patch.object(mcp, "_run_chat", new_callable=AsyncMock, return_value="Done"):
            result = await _send_message(mcp)(
                message="hello", chat_id=None, persistent_chat=False
            )
        assert isinstance(result, mcp.ToolResponse)
        assert result.response == "Done"
        assert result.chat_id == ""
        mcp.remove_chat.assert_called_once_with("ctx-1")
        mcp.AgentContext.remove.assert_called_once_with("ctx-1")

    @pytest.mark.asyncio
    async def test_success_persistent_keeps_chat_id(self):
        mcp = _import_mcp_server()
        mcp._mcp_project_name.set(None)
        mcp.initialize_agent.return_value = MagicMock()
        ctx = MagicMock()
        ctx.id = "ctx-1"
        mcp.AgentContext.return_value = ctx
        with patch.object(mcp, "_run_chat", new_callable=AsyncMock, return_value="Done"):
            result = await _send_message(mcp)(
                message="hello", chat_id=None, persistent_chat=True
            )
        assert result.chat_id == "ctx-1"
        mcp.remove_chat.assert_not_called()

    @pytest.mark.asyncio
    async def test_exception_returns_tool_error(self):
        mcp = _import_mcp_server()
        mcp._mcp_project_name.set(None)
        mcp.initialize_agent.return_value = MagicMock()
        ctx = MagicMock()
        ctx.id = "ctx-1"
        mcp.AgentContext.return_value = ctx
        with patch.object(
            mcp, "_run_chat", new_callable=AsyncMock, side_effect=ValueError("boom")
        ):
            result = await _send_message(mcp)(
                message="hello", chat_id=None, persistent_chat=False
            )
        assert isinstance(result, mcp.ToolError)
        assert "boom" in result.error

    @pytest.mark.asyncio
    async def test_activate_project_failure_returns_error(self):
        mcp = _import_mcp_server()
        mcp._mcp_project_name.set("myproj")
        mcp.initialize_agent.return_value = MagicMock()
        ctx = MagicMock()
        ctx.id = "ctx-1"
        mcp.AgentContext.return_value = ctx
        mcp.projects.activate_project.side_effect = Exception("Project not found")
        result = await _send_message(mcp)(message="hi", chat_id=None)
        assert isinstance(result, mcp.ToolError)
        assert "Failed to activate project" in result.error


# ─── finish_chat tool ────────────────────────────────────────────────────────

class TestFinishChat:
    @pytest.mark.asyncio
    async def test_empty_chat_id_returns_error(self):
        mcp = _import_mcp_server()
        result = await _finish_chat(mcp)(chat_id="")
        assert isinstance(result, mcp.ToolError)
        assert "Chat ID is required" in result.error

    @pytest.mark.asyncio
    async def test_chat_not_found_returns_error(self):
        mcp = _import_mcp_server()
        mcp.AgentContext.get.return_value = None
        result = await _finish_chat(mcp)(chat_id="missing")
        assert isinstance(result, mcp.ToolError)
        assert "Chat not found" in result.error

    @pytest.mark.asyncio
    async def test_success_removes_chat(self):
        mcp = _import_mcp_server()
        ctx = MagicMock()
        ctx.id = "chat-1"
        mcp.AgentContext.get.return_value = ctx
        result = await _finish_chat(mcp)(chat_id="chat-1")
        assert isinstance(result, mcp.ToolResponse)
        assert result.response == "Chat finished"
        assert result.chat_id == "chat-1"
        ctx.reset.assert_called_once()
        mcp.AgentContext.remove.assert_called_once_with("chat-1")
        mcp.remove_chat.assert_called_once_with("chat-1")


# ─── _run_chat helper ─────────────────────────────────────────────────────────

class TestRunChat:
    @pytest.mark.asyncio
    async def test_run_chat_success(self):
        mcp = _import_mcp_server()
        ctx = MagicMock()
        task = AsyncMock()
        task.result = AsyncMock(return_value="Result text")
        ctx.communicate.return_value = task
        result = await mcp._run_chat(ctx, "hello", None)
        assert result == "Result text"
        ctx.communicate.assert_called_once()

    @pytest.mark.asyncio
    async def test_run_chat_raises_runtime_error_on_failure(self):
        mcp = _import_mcp_server()
        ctx = MagicMock()
        task = AsyncMock()
        task.result = AsyncMock(side_effect=Exception("LLM failed"))
        ctx.communicate.return_value = task
        with pytest.raises(RuntimeError, match="MCP Chat message failed"):
            await mcp._run_chat(ctx, "hello", None)


# ─── DynamicMcpProxy singleton and lifecycle ─────────────────────────────────

class TestDynamicMcpProxy:
    def test_get_instance_returns_singleton(self):
        mcp = _import_mcp_server()
        mcp.DynamicMcpProxy._instance = None
        with (
            patch("python.helpers.mcp_server.settings.get_settings") as gs,
            patch("python.helpers.mcp_server.create_sse_app"),
            patch.object(mcp.DynamicMcpProxy, "_create_custom_http_app", return_value=MagicMock()),
        ):
            gs.return_value = {"mcp_server_token": "tok1"}
            p1 = mcp.DynamicMcpProxy.get_instance()
            p2 = mcp.DynamicMcpProxy.get_instance()
        assert p1 is p2

    def test_reconfigure_updates_token_and_paths(self):
        mcp = _import_mcp_server()
        mcp.DynamicMcpProxy._instance = None
        with (
            patch("python.helpers.mcp_server.settings.get_settings") as gs,
            patch("python.helpers.mcp_server.create_sse_app") as sse,
            patch.object(mcp.DynamicMcpProxy, "_create_custom_http_app", return_value=MagicMock()),
        ):
            gs.return_value = {"mcp_server_token": "tok1"}
            proxy = mcp.DynamicMcpProxy()
            proxy.reconfigure("tok2")
        assert proxy.token == "tok2"
        assert mcp.fastmcp.settings.sse_path == "/t-tok2/sse"

    def test_reconfigure_same_token_no_op(self):
        mcp = _import_mcp_server()
        mcp.DynamicMcpProxy._instance = None
        with (
            patch("python.helpers.mcp_server.create_sse_app") as sse,
            patch("python.helpers.mcp_server.settings.get_settings") as gs,
            patch.object(mcp.DynamicMcpProxy, "_create_custom_http_app", return_value=MagicMock()),
        ):
            gs.return_value = {"mcp_server_token": "tok1"}
            proxy = mcp.DynamicMcpProxy()
            init_calls = sse.call_count
            proxy.reconfigure("tok1")  # same token, should not recreate apps
            assert sse.call_count == init_calls


# ─── DynamicMcpProxy __call__ routing ────────────────────────────────────────

class TestDynamicMcpProxyRouting:
    @pytest.fixture
    def _proxy_with_mocked_apps(self):
        mcp = _import_mcp_server()
        mcp.DynamicMcpProxy._instance = None
        with (
            patch("python.helpers.mcp_server.settings.get_settings") as gs,
            patch("python.helpers.mcp_server.create_sse_app", return_value=MagicMock()),
            patch.object(mcp.DynamicMcpProxy, "_create_custom_http_app", return_value=MagicMock()),
        ):
            gs.return_value = {"mcp_server_token": "t123"}
            proxy = mcp.DynamicMcpProxy()
        return mcp, proxy

    @pytest.mark.asyncio
    async def test_uninitialized_apps_raises_runtime_error(self):
        mcp = _import_mcp_server()
        mcp.DynamicMcpProxy._instance = None
        with (
            patch("python.helpers.mcp_server.settings.get_settings") as gs,
            patch("python.helpers.mcp_server.create_sse_app"),
            patch.object(mcp.DynamicMcpProxy, "_create_custom_http_app", return_value=MagicMock()),
        ):
            gs.return_value = {"mcp_server_token": "t"}
            proxy = mcp.DynamicMcpProxy()
        proxy.sse_app = None
        proxy.http_app = None
        scope = {"path": "/t-t/sse", "type": "http"}
        receive = AsyncMock()
        send = AsyncMock()
        with pytest.raises(RuntimeError, match="MCP apps not initialized"):
            await proxy(scope, receive, send)

    @pytest.mark.asyncio
    async def test_path_without_token_raises_403(self, _proxy_with_mocked_apps):
        mcp, proxy = _proxy_with_mocked_apps
        proxy.sse_app = AsyncMock()
        proxy.http_app = AsyncMock()
        scope = {"path": "/wrong/sse", "type": "http"}
        receive = AsyncMock()
        send = AsyncMock()
        with pytest.raises(mcp.StarletteHTTPException) as exc_info:
            await proxy(scope, receive, send)
        assert exc_info.value.status_code == 403

    @pytest.mark.asyncio
    async def test_sse_path_routes_to_sse_app(self, _proxy_with_mocked_apps):
        mcp, proxy = _proxy_with_mocked_apps
        sse_app = AsyncMock()
        proxy.sse_app = sse_app
        proxy.http_app = AsyncMock()
        scope = {"path": "/t-t123/sse", "type": "http"}
        receive = AsyncMock()
        send = AsyncMock()
        await proxy(scope, receive, send)
        sse_app.assert_called_once()
        call_scope = sse_app.call_args[0][0]
        assert call_scope["path"] == "/t-t123/sse"

    @pytest.mark.asyncio
    async def test_http_path_routes_to_http_app(self, _proxy_with_mocked_apps):
        mcp, proxy = _proxy_with_mocked_apps
        proxy.sse_app = AsyncMock()
        http_app = AsyncMock()
        proxy.http_app = http_app
        scope = {"path": "/t-t123/http", "type": "http"}
        receive = AsyncMock()
        send = AsyncMock()
        await proxy(scope, receive, send)
        http_app.assert_called_once()

    @pytest.mark.asyncio
    async def test_project_extracted_from_path_and_stripped(self, _proxy_with_mocked_apps):
        mcp, proxy = _proxy_with_mocked_apps
        proxy.sse_app = AsyncMock()
        proxy.http_app = AsyncMock()
        scope = {"path": "/t-t123/p-myproject/sse", "type": "http"}
        receive = AsyncMock()
        send = AsyncMock()
        await proxy(scope, receive, send)
        call_scope = proxy.sse_app.call_args[0][0]
        assert call_scope["path"] == "/t-t123/sse"
        assert mcp._mcp_project_name.get() == "myproject"


# ─── mcp_middleware ───────────────────────────────────────────────────────────

class TestMcpMiddleware:
    @pytest.mark.asyncio
    async def test_middleware_disabled_raises_403(self):
        mcp = _import_mcp_server()
        mcp.settings.get_settings.return_value = {"mcp_server_enabled": False}
        request = MagicMock()
        call_next = AsyncMock()
        with pytest.raises(mcp.StarletteHTTPException) as exc_info:
            await mcp.mcp_middleware(request, call_next)
        assert exc_info.value.status_code == 403
        assert "disabled" in str(exc_info.value.detail).lower()

    @pytest.mark.asyncio
    async def test_middleware_enabled_calls_next(self):
        mcp = _import_mcp_server()
        mcp.settings.get_settings.return_value = {"mcp_server_enabled": True}
        request = MagicMock()
        call_next = AsyncMock(return_value="response")
        result = await mcp.mcp_middleware(request, call_next)
        assert result == "response"
        call_next.assert_called_once_with(request)


# ─── mcp_server tool registration ────────────────────────────────────────────

class TestMcpServerTools:
    def test_send_message_registered(self):
        mcp = _import_mcp_server()
        tool = getattr(mcp, "send_message", None)
        assert tool is not None
        assert hasattr(tool, "fn") and callable(tool.fn)

    def test_finish_chat_registered(self):
        mcp = _import_mcp_server()
        tool = getattr(mcp, "finish_chat", None)
        assert tool is not None
        assert hasattr(tool, "fn") and callable(tool.fn)
