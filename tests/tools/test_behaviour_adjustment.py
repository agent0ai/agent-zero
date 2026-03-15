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

    @pytest.mark.asyncio
    async def test_stringifies_dict_adjustments(self, tool):
        with patch("python.tools.behaviour_adjustment.update_behaviour", new_callable=AsyncMock):
            resp = await tool.execute(adjustments={"key": "value"})
        assert resp.break_loop is False
        tool.agent.read_prompt.assert_called()


class TestUpdateBehaviourHelpers:
    def test_get_custom_rules_file(self, mock_agent):
        from python.tools.behaviour_adjustment import get_custom_rules_file
        with patch("python.tools.behaviour_adjustment.files.get_abs_path", return_value="/abs/behaviour.md"):
            with patch("python.tools.behaviour_adjustment.memory.get_memory_subdir_abs", return_value="/mem"):
                path = get_custom_rules_file(mock_agent)
        assert "behaviour" in path or "mem" in path

    def test_read_rules_uses_default_when_no_file(self, mock_agent):
        from python.tools.behaviour_adjustment import read_rules
        with patch("python.tools.behaviour_adjustment.get_custom_rules_file", return_value="/nonexistent/behaviour.md"):
            with patch("python.tools.behaviour_adjustment.files.exists", return_value=False):
                mock_agent.read_prompt.side_effect = lambda t, **kw: "rules" if "behaviour" in t else "default"
                result = read_rules(mock_agent)
        assert result is not None
        assert "behaviour_default" in str(mock_agent.read_prompt.call_args_list) or "default" in str(mock_agent.read_prompt.call_args_list)

    def test_read_rules_uses_existing_file(self, mock_agent):
        from python.tools.behaviour_adjustment import read_rules
        with patch("python.tools.behaviour_adjustment.get_custom_rules_file", return_value="/exists/behaviour.md"):
            with patch("python.tools.behaviour_adjustment.files.exists", return_value=True):
                mock_agent.read_prompt.side_effect = lambda t, **kw: "custom rules" if "behaviour.md" in t else "merged"
                result = read_rules(mock_agent)
        assert result is not None


class TestUpdateBehaviourUpdateBehaviour:
    @pytest.mark.asyncio
    async def test_update_behaviour_calls_utility_model_and_writes_file(self, mock_agent, mock_log):
        from python.tools.behaviour_adjustment import update_behaviour
        mock_agent.call_utility_model = AsyncMock(return_value="Merged rules content")
        with patch("python.tools.behaviour_adjustment.read_rules", return_value="current rules"):
            with patch("python.tools.behaviour_adjustment.get_custom_rules_file", return_value="/tmp/behaviour.md"):
                with patch("python.tools.behaviour_adjustment.files.write_file", MagicMock()) as mock_write:
                    await update_behaviour(mock_agent, mock_log, "Be more concise")
        mock_agent.call_utility_model.assert_called_once()
        mock_write.assert_called_once_with("/tmp/behaviour.md", "Merged rules content")
