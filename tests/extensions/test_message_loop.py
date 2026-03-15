"""Tests for message_loop extensions: iteration_no, organize_history, save_chat, organize_history_wait."""

import sys
from pathlib import Path
from unittest.mock import MagicMock, AsyncMock, patch

import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


class TestIterationNo:
    """Tests for message_loop_start/_10_iteration_no.py."""

    @pytest.mark.asyncio
    async def test_increments_iteration_no(self, mock_agent, mock_loop_data):
        mock_agent.get_data.return_value = 5

        from python.extensions.message_loop_start._10_iteration_no import (
            IterationNo,
            get_iter_no,
        )

        ext = IterationNo(agent=mock_agent)
        await ext.execute(loop_data=mock_loop_data)

        mock_agent.set_data.assert_called_with("iteration_no", 6)

    @pytest.mark.asyncio
    async def test_starts_at_one_when_none(self, mock_agent, mock_loop_data):
        mock_agent.get_data.return_value = None

        from python.extensions.message_loop_start._10_iteration_no import IterationNo

        ext = IterationNo(agent=mock_agent)
        await ext.execute(loop_data=mock_loop_data)

        mock_agent.set_data.assert_called_with("iteration_no", 1)


class TestOrganizeHistory:
    """Tests for message_loop_end/_10_organize_history.py."""

    @pytest.mark.asyncio
    async def test_starts_compress_task(self, mock_agent, mock_loop_data):
        mock_agent.get_data.return_value = None
        mock_agent.history = MagicMock()
        mock_agent.history.compress = MagicMock()

        with patch(
            "python.extensions.message_loop_end._10_organize_history.DeferredTask"
        ) as mock_task_cls:
            mock_task = MagicMock()
            mock_task_cls.return_value = mock_task

            from python.extensions.message_loop_end._10_organize_history import (
                OrganizeHistory,
            )

            ext = OrganizeHistory(agent=mock_agent)
            await ext.execute(loop_data=mock_loop_data)

        mock_agent.set_data.assert_called()
        mock_task.start_task.assert_called()


class TestSaveChat:
    """Tests for message_loop_end/_90_save_chat.py."""

    @pytest.mark.asyncio
    async def test_skips_background_context(self, mock_agent, mock_loop_data):
        from agent import AgentContextType

        mock_agent.context.type = AgentContextType.BACKGROUND

        with patch(
            "python.extensions.message_loop_end._90_save_chat.persist_chat.save_tmp_chat"
        ) as mock_save:
            from python.extensions.message_loop_end._90_save_chat import SaveChat

            ext = SaveChat(agent=mock_agent)
            await ext.execute(loop_data=mock_loop_data)

        mock_save.assert_not_called()

    @pytest.mark.asyncio
    async def test_saves_chat_for_normal_context(self, mock_agent, mock_loop_data):
        from agent import AgentContextType

        mock_agent.context.type = AgentContextType.USER

        with patch(
            "python.extensions.message_loop_end._90_save_chat.persist_chat.save_tmp_chat"
        ) as mock_save:
            from python.extensions.message_loop_end._90_save_chat import SaveChat

            ext = SaveChat(agent=mock_agent)
            await ext.execute(loop_data=mock_loop_data)

        mock_save.assert_called_once_with(mock_agent.context)


class TestOrganizeHistoryWait:
    """Tests for message_loop_prompts_before/_90_organize_history_wait.py."""

    @pytest.mark.asyncio
    async def test_returns_early_when_not_over_limit(self, mock_agent, mock_loop_data):
        mock_agent.history = MagicMock()
        mock_agent.history.is_over_limit.return_value = False

        from python.extensions.message_loop_prompts_before._90_organize_history_wait import (
            OrganizeHistoryWait,
        )

        ext = OrganizeHistoryWait(agent=mock_agent)
        await ext.execute(loop_data=mock_loop_data)

        mock_agent.history.is_over_limit.assert_called()
