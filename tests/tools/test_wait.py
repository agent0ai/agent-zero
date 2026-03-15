"""Tests for python/tools/wait.py — WaitTool."""

import sys
from pathlib import Path
from datetime import datetime, timedelta, timezone
from unittest.mock import MagicMock, AsyncMock, patch

import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


@pytest.fixture
def mock_agent():
    agent = MagicMock()
    agent.handle_intervention = AsyncMock()
    agent.read_prompt = MagicMock(side_effect=lambda t, **kw: f"Wait complete: {kw.get('target_time', '')}")
    agent.context = MagicMock()
    agent.context.log = MagicMock()
    agent.context.log.log = MagicMock(return_value=MagicMock(update=MagicMock()))
    return agent


@pytest.fixture
def tool(mock_agent):
    from python.tools.wait import WaitTool
    return WaitTool(
        agent=mock_agent,
        name="wait",
        method=None,
        args={"seconds": 1, "minutes": 0, "hours": 0, "days": 0},
        message="",
        loop_data=None,
    )


class TestWaitToolExecute:
    @pytest.mark.asyncio
    async def test_zero_duration_returns_error(self, tool):
        tool.args = {"seconds": 0, "minutes": 0, "hours": 0, "days": 0}
        resp = await tool.execute()
        assert "positive" in resp.message or "duration" in resp.message.lower()
        assert resp.break_loop is False

    @pytest.mark.asyncio
    async def test_invalid_until_timestamp_returns_error(self, tool):
        tool.args = {"until": "not-a-valid-date"}
        with patch("python.tools.wait.Localization.get") as mock_loc:
            mock_loc.return_value.localtime_str_to_utc_dt = MagicMock(return_value=None)
            resp = await tool.execute()
        assert "Invalid" in resp.message or "invalid" in resp.message.lower()

    @pytest.mark.asyncio
    async def test_past_target_time_returns_error(self, tool):
        tool.args = {"until": "2020-01-01T00:00:00Z"}
        with patch("python.tools.wait.Localization.get") as mock_loc:
            past = datetime(2020, 1, 1, tzinfo=timezone.utc)
            mock_loc.return_value.localtime_str_to_utc_dt = MagicMock(return_value=past)
            resp = await tool.execute()
        assert "past" in resp.message.lower()

    @pytest.mark.asyncio
    async def test_duration_wait_completes(self, tool):
        tool.args = {"seconds": 1, "minutes": 0, "hours": 0, "days": 0}
        with patch("python.tools.wait.managed_wait", new_callable=AsyncMock) as mock_wait:
            mock_wait.return_value = datetime.now(timezone.utc) + timedelta(seconds=1)
            resp = await tool.execute()
        assert "Wait complete" in resp.message or "complete" in resp.message.lower()
        assert resp.break_loop is False


class TestWaitToolGetHeading:
    def test_get_heading_includes_done_icon(self, tool):
        h = tool.get_heading("Done", done=True)
        assert "done" in h.lower() or "icon" in h
