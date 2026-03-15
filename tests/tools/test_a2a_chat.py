"""Tests for python/tools/a2a_chat.py — A2AChatTool."""

import sys
from pathlib import Path
from unittest.mock import MagicMock, AsyncMock, patch

import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


@pytest.fixture
def mock_agent():
    agent = MagicMock()
    agent.get_data = MagicMock(return_value={})
    agent.set_data = MagicMock()
    return agent


@pytest.fixture
def tool(mock_agent):
    from python.tools.a2a_chat import A2AChatTool
    return A2AChatTool(
        agent=mock_agent,
        name="a2a_chat",
        method=None,
        args={},
        message="",
        loop_data=None,
    )


class TestA2AChatToolExecute:
    @pytest.mark.asyncio
    async def test_client_not_available_returns_message(self, tool):
        with patch("python.tools.a2a_chat.is_client_available", return_value=False):
            resp = await tool.execute(agent_url="http://agent", message="hi")
        assert "not available" in resp.message
        assert resp.break_loop is False

    @pytest.mark.asyncio
    async def test_missing_agent_url_returns_error(self, tool):
        with patch("python.tools.a2a_chat.is_client_available", return_value=True):
            resp = await tool.execute(agent_url="", message="hi")
        assert "agent_url" in resp.message

    @pytest.mark.asyncio
    async def test_missing_message_returns_error(self, tool):
        with patch("python.tools.a2a_chat.is_client_available", return_value=True):
            resp = await tool.execute(agent_url="http://agent", message="")
        assert "message" in resp.message

    @pytest.mark.asyncio
    async def test_success_returns_assistant_text(self, tool):
        mock_conn = MagicMock()
        mock_conn.__aenter__ = AsyncMock(return_value=mock_conn)
        mock_conn.__aexit__ = AsyncMock(return_value=None)
        mock_conn.send_message = AsyncMock(return_value={"result": {"id": "task-1"}})
        mock_conn.wait_for_completion = AsyncMock(return_value={
            "result": {
                "context_id": "ctx-1",
                "history": [{"parts": [{"kind": "text", "text": "Hello from agent"}]}],
            }
        })
        with patch("python.tools.a2a_chat.is_client_available", return_value=True):
            with patch("python.tools.a2a_chat.connect_to_agent", new_callable=AsyncMock) as mock_connect:
                mock_connect.return_value = mock_conn
                resp = await tool.execute(agent_url="http://agent", message="hi")
        assert "Hello from agent" in resp.message
        assert resp.break_loop is False

    @pytest.mark.asyncio
    async def test_exception_returns_error_message(self, tool):
        with patch("python.tools.a2a_chat.is_client_available", return_value=True):
            with patch("python.tools.a2a_chat.connect_to_agent", new_callable=AsyncMock, side_effect=Exception("Connection failed")):
                resp = await tool.execute(agent_url="http://agent", message="hi")
        assert "A2A chat error" in resp.message or "Connection failed" in resp.message
