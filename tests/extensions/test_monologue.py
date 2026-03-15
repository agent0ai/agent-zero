"""Tests for monologue extensions: memory_init, rename_chat, memorize_fragments, memorize_solutions, waiting_for_input."""

import asyncio
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

    @pytest.mark.asyncio
    async def test_change_name_trims_long_name(self, mock_agent):
        mock_agent.history = MagicMock()
        mock_agent.history.output_text.return_value = "short history"
        mock_agent.config.utility_model = MagicMock()
        mock_agent.config.utility_model.ctx_length = 8000
        mock_agent.context.name = "Old Chat"
        mock_agent.read_prompt = MagicMock(side_effect=lambda t, **kw: "sys" if "sys" in t else ("x" * 50))
        mock_agent.call_utility_model = AsyncMock(return_value="A" * 50)
        mock_agent.context.id = "ctx-1"

        with patch("python.extensions.monologue_start._60_rename_chat.persist_chat.save_tmp_chat", MagicMock()):
            from python.extensions.monologue_start._60_rename_chat import RenameChat

            ext = RenameChat(agent=mock_agent)
            await ext.change_name()

        assert len(mock_agent.context.name) <= 43  # 40 + "..."

    @pytest.mark.asyncio
    async def test_change_name_saves_context(self, mock_agent):
        mock_agent.history = MagicMock()
        mock_agent.history.output_text.return_value = "history"
        mock_agent.config.utility_model = MagicMock()
        mock_agent.config.utility_model.ctx_length = 8000
        mock_agent.context.name = "Old"
        mock_agent.read_prompt = MagicMock(side_effect=lambda t, **kw: "sys" if "sys" in t else "New Name")
        mock_agent.call_utility_model = AsyncMock(return_value="New Name")
        mock_agent.context.id = "ctx-1"

        with patch("python.extensions.monologue_start._60_rename_chat.persist_chat.save_tmp_chat", MagicMock()) as mock_save:
            from python.extensions.monologue_start._60_rename_chat import RenameChat

            ext = RenameChat(agent=mock_agent)
            await ext.change_name()

        assert mock_agent.context.name == "New Name"
        mock_save.assert_called_once_with(mock_agent.context)

    @pytest.mark.asyncio
    async def test_change_name_handles_empty_response(self, mock_agent):
        mock_agent.history = MagicMock()
        mock_agent.history.output_text.return_value = "history"
        mock_agent.config.utility_model = MagicMock()
        mock_agent.config.utility_model.ctx_length = 8000
        mock_agent.context.name = "Original"
        mock_agent.read_prompt = MagicMock(return_value="prompt")
        mock_agent.call_utility_model = AsyncMock(return_value=None)

        with patch("python.extensions.monologue_start._60_rename_chat.persist_chat.save_tmp_chat", MagicMock()):
            from python.extensions.monologue_start._60_rename_chat import RenameChat

            ext = RenameChat(agent=mock_agent)
            await ext.change_name()

        assert mock_agent.context.name == "Original"


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

    @pytest.mark.asyncio
    async def test_returns_task_when_enabled(self, mock_agent, mock_loop_data):
        mock_agent.history = []
        mock_agent.concat_messages = MagicMock(return_value="chat history")
        mock_agent.call_utility_model = AsyncMock(return_value=None)
        mock_agent.context.log.log = MagicMock(return_value=MagicMock(update=MagicMock()))

        with patch(
            "python.extensions.monologue_end._50_memorize_fragments.settings.get_settings",
            return_value={"memory_memorize_enabled": True, "memory_memorize_replace_threshold": 0},
        ):
            with patch(
                "python.extensions.monologue_end._50_memorize_fragments.Memory.get",
                new_callable=AsyncMock,
                return_value=MagicMock(insert_text=AsyncMock(), delete_documents_by_query=AsyncMock(return_value=[])),
            ):
                from python.extensions.monologue_end._50_memorize_fragments import (
                    MemorizeMemories,
                    DeferredTask,
                )

                ext = MemorizeMemories(agent=mock_agent)
                result = await ext.execute(loop_data=mock_loop_data)

        assert result is not None
        assert hasattr(result, "start_task") or hasattr(result, "is_ready")

    @pytest.mark.asyncio
    async def test_memorize_handles_empty_utility_response(self, mock_agent, mock_loop_data):
        mock_agent.history = []
        mock_agent.concat_messages = MagicMock(return_value="chat")
        mock_agent.call_utility_model = AsyncMock(return_value="")
        mock_log = MagicMock(update=MagicMock())
        mock_agent.context.log.log = MagicMock(return_value=mock_log)

        with patch(
            "python.extensions.monologue_end._50_memorize_fragments.settings.get_settings",
            return_value={"memory_memorize_enabled": True, "memory_memorize_replace_threshold": 0},
        ):
            with patch(
                "python.extensions.monologue_end._50_memorize_fragments.Memory.get",
                new_callable=AsyncMock,
                return_value=MagicMock(),
            ):
                from python.extensions.monologue_end._50_memorize_fragments import MemorizeMemories

                ext = MemorizeMemories(agent=mock_agent)
                # Call memorize directly to test empty response handling
                await ext.memorize(mock_loop_data, mock_log)

        mock_log.update.assert_called()
        calls = [str(c) for c in mock_log.update.call_args_list]
        assert any("Empty" in c or "No response" in c for c in calls)


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

    @pytest.mark.asyncio
    async def test_returns_task_when_enabled(self, mock_agent, mock_loop_data):
        mock_agent.history = []
        mock_agent.concat_messages = MagicMock(return_value="chat history")
        mock_agent.call_utility_model = AsyncMock(return_value=None)
        mock_agent.context.log.log = MagicMock(return_value=MagicMock(update=MagicMock()))

        with patch(
            "python.extensions.monologue_end._51_memorize_solutions.settings.get_settings",
            return_value={"memory_memorize_enabled": True, "memory_memorize_replace_threshold": 0},
        ):
            with patch(
                "python.extensions.monologue_end._51_memorize_solutions.Memory.get",
                new_callable=AsyncMock,
                return_value=MagicMock(insert_text=AsyncMock(), delete_documents_by_query=AsyncMock(return_value=[])),
            ):
                from python.extensions.monologue_end._51_memorize_solutions import MemorizeSolutions

                ext = MemorizeSolutions(agent=mock_agent)
                result = await ext.execute(loop_data=mock_loop_data)

        assert result is not None

    @pytest.mark.asyncio
    async def test_memorize_handles_parse_error(self, mock_agent, mock_loop_data):
        mock_agent.history = []
        mock_agent.concat_messages = MagicMock(return_value="chat")
        mock_agent.call_utility_model = AsyncMock(return_value='["solution1"]')
        mock_log = MagicMock(update=MagicMock())
        mock_agent.context.log.log = MagicMock(return_value=mock_log)

        with patch(
            "python.extensions.monologue_end._51_memorize_solutions.settings.get_settings",
            return_value={"memory_memorize_enabled": True, "memory_memorize_replace_threshold": 0},
        ):
            with patch(
                "python.extensions.monologue_end._51_memorize_solutions.Memory.get",
                new_callable=AsyncMock,
                return_value=MagicMock(insert_text=AsyncMock(), delete_documents_by_query=AsyncMock(return_value=[])),
            ):
                with patch(
                    "python.extensions.monologue_end._51_memorize_solutions.DirtyJson.parse_string",
                    side_effect=ValueError("Parse error"),
                ):
                    from python.extensions.monologue_end._51_memorize_solutions import MemorizeSolutions

                    ext = MemorizeSolutions(agent=mock_agent)
                    await ext.memorize(mock_loop_data, mock_log)

        mock_log.update.assert_called()
        calls = [str(c) for c in mock_log.update.call_args_list]
        assert any("Failed to parse" in c or "parse" in c.lower() for c in calls)


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
