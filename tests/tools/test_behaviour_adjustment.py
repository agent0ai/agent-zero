"""Tests for python/tools/behaviour_adjustment.py — UpdateBehaviour tool."""

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
    agent.read_prompt = MagicMock(side_effect=lambda t, **kw: "Merged rules content")
    agent.call_utility_model = AsyncMock(return_value="Updated behaviour rules")
    return agent


@pytest.fixture
def mock_log():
    log = MagicMock()
    log.stream = MagicMock()
    log.update = MagicMock()
    return log


@pytest.fixture
def tool(mock_agent):
    from python.tools.behaviour_adjustment import UpdateBehaviour
    t = UpdateBehaviour(
        agent=mock_agent,
        name="update_behaviour",
        method=None,
        args={"adjustments": "Be more concise"},
        message="",
        loop_data=None,
    )
    t.log = MagicMock(stream=MagicMock(), update=MagicMock())
    return t


class TestUpdateBehaviourExecute:
    @pytest.mark.asyncio
    async def test_execute_returns_updated_message(self, tool):
        with patch("python.tools.behaviour_adjustment.update_behaviour", new_callable=AsyncMock):
            resp = await tool.execute(adjustments="Be more concise")
        assert "behaviour.updated" in str(tool.agent.read_prompt.call_args) or "updated" in resp.message.lower()
        assert resp.break_loop is False

    @pytest.mark.asyncio
    async def test_stringifies_non_string_adjustments(self, tool):
        with patch("python.tools.behaviour_adjustment.update_behaviour", new_callable=AsyncMock):
            resp = await tool.execute(adjustments=123)
        assert resp.break_loop is False
