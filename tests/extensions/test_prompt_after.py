"""Tests for message_loop_prompts_after extensions: datetime, skills, agent_info, workdir, recall_wait."""

import sys
from pathlib import Path
from unittest.mock import MagicMock, AsyncMock, patch

import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


class TestIncludeCurrentDatetime:
    """Tests for _60_include_current_datetime.py."""

    @pytest.mark.asyncio
    async def test_adds_datetime_to_extras(self, mock_agent, mock_loop_data):
        mock_loop_data.extras_temporary = {}
        mock_agent.read_prompt.return_value = "Current time: 2025-03-15 12:00:00"

        with patch(
            "python.extensions.message_loop_prompts_after._60_include_current_datetime.Localization.get"
        ) as mock_loc:
            mock_loc.return_value.utc_dt_to_localtime_str.return_value = "2025-03-15 12:00:00"

            from python.extensions.message_loop_prompts_after._60_include_current_datetime import (
                IncludeCurrentDatetime,
            )

            ext = IncludeCurrentDatetime(agent=mock_agent)
            await ext.execute(loop_data=mock_loop_data)

        assert "current_datetime" in mock_loop_data.extras_temporary
        mock_agent.read_prompt.assert_called()


class TestIncludeLoadedSkills:
    """Tests for _65_include_loaded_skills.py."""

    @pytest.mark.asyncio
    async def test_returns_early_without_skills(self, mock_agent, mock_loop_data):
        mock_loop_data.extras_persistent = {}
        mock_agent.data = MagicMock()
        mock_agent.data.get.return_value = None

        from python.extensions.message_loop_prompts_after._65_include_loaded_skills import (
            IncludeLoadedSkills,
        )

        ext = IncludeLoadedSkills(agent=mock_agent)
        await ext.execute(loop_data=mock_loop_data)

        assert "loaded_skills" not in mock_loop_data.extras_persistent

    @pytest.mark.asyncio
    async def test_adds_loaded_skills_to_extras(self, mock_agent, mock_loop_data):
        mock_loop_data.extras_persistent = {}
        mock_agent.data = MagicMock()
        mock_agent.data.get.side_effect = lambda k, d=None: (
            ["skill_a", "skill_b"] if "loaded" in str(k) else d
        )

        with patch(
            "python.extensions.message_loop_prompts_after._65_include_loaded_skills.skills.load_skill_for_agent",
            side_effect=lambda **kw: "skill content",
        ):
            from python.extensions.message_loop_prompts_after._65_include_loaded_skills import (
                IncludeLoadedSkills,
            )

            ext = IncludeLoadedSkills(agent=mock_agent)
            await ext.execute(loop_data=mock_loop_data)

        assert "loaded_skills" in mock_loop_data.extras_persistent


class TestIncludeAgentInfo:
    """Tests for _70_include_agent_info.py."""

    @pytest.mark.asyncio
    async def test_adds_agent_info_to_extras(self, mock_agent, mock_loop_data):
        mock_loop_data.extras_temporary = {}
        mock_agent.config.profile = "Default"
        mock_agent.config.chat_model = MagicMock()
        mock_agent.config.chat_model.provider = "openai"
        mock_agent.config.chat_model.name = "gpt-4"
        mock_agent.read_prompt.return_value = "Agent 0 info"

        from python.extensions.message_loop_prompts_after._70_include_agent_info import (
            IncludeAgentInfo,
        )

        ext = IncludeAgentInfo(agent=mock_agent)
        await ext.execute(loop_data=mock_loop_data)

        assert "agent_info" in mock_loop_data.extras_temporary
        mock_agent.read_prompt.assert_called_with(
            "agent.extras.agent_info.md",
            number=mock_agent.number,
            profile="Default",
            llm="openai/gpt-4",
        )


class TestIncludeWorkdirExtras:
    """Tests for _75_include_workdir_extras.py."""

    @pytest.mark.asyncio
    async def test_returns_early_when_disabled(self, mock_agent, mock_loop_data):
        mock_loop_data.extras_temporary = {}

        with patch(
            "python.extensions.message_loop_prompts_after._75_include_workdir_extras.projects.get_context_project_name",
            return_value=None,
        ), patch(
            "python.extensions.message_loop_prompts_after._75_include_workdir_extras.settings.get_settings",
            return_value={"workdir_show": False},
        ):
            from python.extensions.message_loop_prompts_after._75_include_workdir_extras import (
                IncludeWorkdirExtras,
            )

            ext = IncludeWorkdirExtras(agent=mock_agent)
            await ext.execute(loop_data=mock_loop_data)

        assert "project_file_structure" not in mock_loop_data.extras_temporary

    @pytest.mark.asyncio
    async def test_cleanup_gitignore_strips_comments(self):
        from python.extensions.message_loop_prompts_after._75_include_workdir_extras import (
            cleanup_gitignore,
        )

        result = cleanup_gitignore("*.pyc  # compiled\nnode_modules")
        assert "*.pyc" in result
        assert "#" not in result or "compiled" not in result


class TestRecallWait:
    """Tests for _91_recall_wait.py."""

    @pytest.mark.asyncio
    async def test_returns_early_when_no_task(self, mock_agent, mock_loop_data):
        mock_agent.get_data.return_value = None

        with patch(
            "python.extensions.message_loop_prompts_after._91_recall_wait.settings.get_settings",
            return_value={"memory_recall_delayed": False},
        ):
            from python.extensions.message_loop_prompts_after._91_recall_wait import (
                RecallWait,
            )

            ext = RecallWait(agent=mock_agent)
            await ext.execute(loop_data=mock_loop_data)

    @pytest.mark.asyncio
    async def test_adds_delayed_msg_when_delayed_mode(self, mock_agent, mock_loop_data):
        task = MagicMock()
        task.done.return_value = False
        mock_agent.get_data.side_effect = lambda k: (
            task if "recall_memories_task" in str(k) else 1
        )

        with patch(
            "python.extensions.message_loop_prompts_after._91_recall_wait.settings.get_settings",
            return_value={"memory_recall_delayed": True},
        ):
            from python.extensions.message_loop_prompts_after._91_recall_wait import (
                RecallWait,
            )

            ext = RecallWait(agent=mock_agent)
            await ext.execute(loop_data=mock_loop_data)

        assert "memory_recall_delayed" in mock_loop_data.extras_temporary
