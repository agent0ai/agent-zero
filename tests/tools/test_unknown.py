"""Tests for python/tools/unknown.py — Unknown tool fallback."""

import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

try:
    from python.tools.unknown import Unknown
except (ImportError, AttributeError) as e:
    pytest.skip(f"Failed to import unknown tool: {e}", allow_module_level=True)


@pytest.fixture
def mock_agent():
    agent = MagicMock()
    agent.read_prompt = MagicMock(side_effect=lambda t, **kw: f"Tool not found: {kw.get('tool_name', '')}. Tools: {kw.get('tools_prompt', '')[:50]}")
    return agent


@pytest.fixture
def tool(mock_agent):
    return Unknown(
        agent=mock_agent,
        name="unknown_tool",
        method=None,
        args={},
        message="",
        loop_data=None,
    )


class TestUnknownExecute:
    @pytest.mark.asyncio
    async def test_returns_tool_not_found_message(self, tool):
        with patch("python.tools.unknown.get_tools_prompt", return_value="Available tools: ..."):
            resp = await tool.execute()
        assert "not found" in resp.message.lower() or "unknown_tool" in resp.message
        assert resp.break_loop is False

    @pytest.mark.asyncio
    async def test_includes_tools_prompt(self, tool):
        with patch("python.tools.unknown.get_tools_prompt", return_value="code_execution, browser_agent"):
            resp = await tool.execute()
        assert "code_execution" in resp.message or "Tools" in str(tool.agent.read_prompt.call_args)
