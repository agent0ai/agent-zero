"""Tests for python/tools/response.py — ResponseTool."""

import sys
from pathlib import Path
from unittest.mock import MagicMock

import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


@pytest.fixture
def mock_agent():
    return MagicMock()


@pytest.fixture
def tool(mock_agent):
    from python.tools.response import ResponseTool
    return ResponseTool(
        agent=mock_agent,
        name="response",
        method=None,
        args={"text": "Final answer"},
        message="",
        loop_data=None,
    )


class TestResponseToolExecute:
    @pytest.mark.asyncio
    async def test_returns_text_and_breaks_loop(self, tool):
        resp = await tool.execute()
        assert resp.message == "Final answer"
        assert resp.break_loop is True

    @pytest.mark.asyncio
    async def test_uses_message_if_no_text(self, mock_agent):
        from python.tools.response import ResponseTool
        t = ResponseTool(mock_agent, "r", None, {"message": "Alternative"}, "", None)
        resp = await t.execute()
        assert resp.message == "Alternative"
        assert resp.break_loop is True
