"""Tests for system_prompt and before_main_llm_call extensions."""

import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


class TestSystemPrompt:
    """Tests for system_prompt/_10_system_prompt.py."""

    @pytest.mark.asyncio
    async def test_appends_main_and_tools(self, mock_agent, mock_loop_data):
        system_prompt = []

        def read_prompt(p, **kw):
            return f"prompt:{p}"

        mock_agent.read_prompt.side_effect = read_prompt
        mock_agent.config.chat_model = MagicMock()
        mock_agent.config.chat_model.vision = False
        mock_agent.context.get_data = MagicMock(return_value=None)

        with patch(
            "python.extensions.system_prompt._10_system_prompt.MCPConfig.get_instance",
            return_value=MagicMock(servers=[]),
        ), patch(
            "python.extensions.system_prompt._10_system_prompt.skills.list_skills",
            return_value=[],
        ), patch(
            "python.extensions.system_prompt._10_system_prompt.get_settings",
            return_value={"variables": {}},
        ):
            from python.extensions.system_prompt._10_system_prompt import SystemPrompt

            ext = SystemPrompt(agent=mock_agent)
            await ext.execute(system_prompt=system_prompt, loop_data=mock_loop_data)

        assert len(system_prompt) >= 2
        assert any("main" in p for p in system_prompt)
        assert any("tools" in p for p in system_prompt)


class TestBehaviourPrompt:
    """Tests for system_prompt/_20_behaviour_prompt.py."""

    @pytest.mark.asyncio
    async def test_inserts_behaviour_at_front(self, mock_agent, mock_loop_data):
        system_prompt = ["existing"]
        mock_agent.read_prompt.return_value = "behaviour rules"

        with patch(
            "python.extensions.system_prompt._20_behaviour_prompt.files.get_abs_path",
            return_value="/mem/behaviour.md",
        ), patch(
            "python.extensions.system_prompt._20_behaviour_prompt.files.exists",
            return_value=True,
        ), patch(
            "python.extensions.system_prompt._20_behaviour_prompt.files.read_file",
            return_value="custom rules",
        ):
            from python.extensions.system_prompt._20_behaviour_prompt import (
                BehaviourPrompt,
            )

            ext = BehaviourPrompt(agent=mock_agent)
            await ext.execute(system_prompt=system_prompt, loop_data=mock_loop_data)

        assert system_prompt[0] == "behaviour rules"
        assert "existing" in system_prompt


class TestLogForStream:
    """Tests for before_main_llm_call/_10_log_for_stream.py."""

    @pytest.mark.asyncio
    async def test_creates_log_item(self, mock_agent, mock_loop_data):
        mock_loop_data.params_temporary = {}
        mock_log_item = MagicMock()
        mock_agent.context.log.log.return_value = mock_log_item

        from python.extensions.before_main_llm_call._10_log_for_stream import (
            LogForStream,
            build_heading,
            build_default_heading,
        )

        ext = LogForStream(agent=mock_agent)
        await ext.execute(loop_data=mock_loop_data)

        assert "log_item_generating" in mock_loop_data.params_temporary

    def test_build_heading_includes_agent_prefix(self, mock_agent):
        from python.extensions.before_main_llm_call._10_log_for_stream import (
            build_heading,
        )

        mock_agent.agent_name = "A0"
        result = build_heading(mock_agent, "Thinking")
        assert "A0" in result
        assert "Thinking" in result
