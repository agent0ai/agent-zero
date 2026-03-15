"""Tests for monologue extensions: memory_init, rename_chat, memorize_fragments, memorize_solutions, waiting_for_input."""

import sys
from pathlib import Path
from unittest.mock import MagicMock, AsyncMock, patch

import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


class TestMemoryInit:
    """Tests for monologue_start/_10_memory_init.py."""

    @pytest.mark.asyncio
    async def test_initializes_memory(self, mock_agent, mock_loop_data):
        with patch(
            "python.extensions.monologue_start._10_memory_init.memory.Memory.get",
            new_callable=AsyncMock,
            return_value=MagicMock(),
        ):
            from python.extensions.monologue_start._10_memory_init import MemoryInit

            ext = MemoryInit(agent=mock_agent)
            await ext.execute(loop_data=mock_loop_data)


class TestRenameChat:
    """Tests for monologue_start/_60_rename_chat.py."""

    @pytest.mark.asyncio
    async def test_schedules_rename_task(self, mock_agent, mock_loop_data):
        mock_agent.history = MagicMock()
        mock_agent.history.output_text.return_value = "chat history"
        mock_agent.config.utility_model = MagicMock()
        mock_agent.config.utility_model.ctx_length = 8000
        mock_agent.context.name = "Chat 1"

        with patch(
            "python.extensions.monologue_start._60_rename_chat.asyncio.create_task",
        ) as mock_create:
            from python.extensions.monologue_start._60_rename_chat import RenameChat

            ext = RenameChat(agent=mock_agent)
            await ext.execute(loop_data=mock_loop_data)

        mock_create.assert_called_once()


class TestMemorizeMemories:
    """Tests for monologue_end/_50_memorize_fragments.py."""

    @pytest.mark.asyncio
    async def test_returns_early_when_disabled(self, mock_agent, mock_loop_data):
        with patch(
            "python.extensions.monologue_end._50_memorize_fragments.settings.get_settings",
            return_value={"memory_memorize_enabled": False},
        ):
            from python.extensions.monologue_end._50_memorize_fragments import (
                MemorizeMemories,
            )

            ext = MemorizeMemories(agent=mock_agent)
            result = await ext.execute(loop_data=mock_loop_data)

        assert result is None


class TestMemorizeSolutions:
    """Tests for monologue_end/_51_memorize_solutions.py."""

    @pytest.mark.asyncio
    async def test_returns_early_when_disabled(self, mock_agent, mock_loop_data):
        with patch(
            "python.extensions.monologue_end._51_memorize_solutions.settings.get_settings",
            return_value={"memory_memorize_enabled": False},
        ):
            from python.extensions.monologue_end._51_memorize_solutions import (
                MemorizeSolutions,
            )

            ext = MemorizeSolutions(agent=mock_agent)
            result = await ext.execute(loop_data=mock_loop_data)

        assert result is None


class TestWaitingForInputMsg:
    """Tests for monologue_end/_90_waiting_for_input_msg.py."""

    @pytest.mark.asyncio
    async def test_sets_initial_progress_for_main_agent(self, mock_agent, mock_loop_data):
        mock_agent.number = 0

        from python.extensions.monologue_end._90_waiting_for_input_msg import (
            WaitingForInputMsg,
        )

        ext = WaitingForInputMsg(agent=mock_agent)
        await ext.execute(loop_data=mock_loop_data)

        mock_agent.context.log.set_initial_progress.assert_called_once()

    @pytest.mark.asyncio
    async def test_skips_for_subordinate_agent(self, mock_agent, mock_loop_data):
        mock_agent.number = 1

        from python.extensions.monologue_end._90_waiting_for_input_msg import (
            WaitingForInputMsg,
        )

        ext = WaitingForInputMsg(agent=mock_agent)
        await ext.execute(loop_data=mock_loop_data)

        mock_agent.context.log.set_initial_progress.assert_not_called()
