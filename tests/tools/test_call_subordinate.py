"""Tests for python/tools/call_subordinate.py — Delegation (call_subordinate) tool."""

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
    agent.number = 0
    agent.get_data = MagicMock(return_value=None)
    agent.set_data = MagicMock()
    agent.context = MagicMock()
    agent.read_prompt = MagicMock(return_value="Hint for long response")
    return agent


@pytest.fixture
def tool(mock_agent):
    from python.tools.call_subordinate import Delegation
    t = Delegation(
        agent=mock_agent,
        name="call_subordinate",
        method=None,
        args={"message": "Analyze this"},
        message="",
        loop_data=None,
    )
    t.log = MagicMock()
    return t


class TestDelegationExecute:
    @pytest.mark.asyncio
    async def test_creates_subordinate_when_none(self, tool):
        mock_sub = MagicMock()
        mock_sub.hist_add_user_message = MagicMock()
        mock_sub.monologue = AsyncMock(return_value="Subordinate result")
        mock_sub.history = MagicMock()
        mock_sub.history.new_topic = MagicMock()

        stored = {}
        tool.agent.get_data = MagicMock(side_effect=lambda k: stored.get(k))
        tool.agent.set_data = MagicMock(side_effect=lambda k, v: stored.__setitem__(k, v))

        with patch("python.tools.call_subordinate.initialize_agent", return_value=MagicMock()):
            with patch("python.tools.call_subordinate.Agent", return_value=mock_sub):
                resp = await tool.execute(message="Do something", reset="false")
        assert resp.message == "Subordinate result"
        assert resp.break_loop is False

    @pytest.mark.asyncio
    async def test_reset_creates_new_subordinate(self, tool):
        stored = {}
        tool.agent.get_data = MagicMock(side_effect=lambda k: stored.get(k))
        tool.agent.set_data = MagicMock(side_effect=lambda k, v: stored.__setitem__(k, v))
        stored["_subordinate_"] = MagicMock()

        with patch("python.tools.call_subordinate.initialize_agent", return_value=MagicMock()):
            with patch("python.tools.call_subordinate.Agent") as MockAgent:
                new_sub = MagicMock()
                new_sub.monologue = AsyncMock(return_value="New result")
                new_sub.history = MagicMock(new_topic=MagicMock())
                new_sub.hist_add_user_message = MagicMock()
                MockAgent.return_value = new_sub
                resp = await tool.execute(message="Task", reset="true")
        assert resp.message == "New result"
