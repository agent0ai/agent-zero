"""Tests for hist_add, error_format, process_chain, user_message_ui, util_model_call extensions."""

import sys
from pathlib import Path
from unittest.mock import MagicMock, AsyncMock, patch

import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


class TestMaskHistoryContent:
    """Tests for hist_add_before/_10_mask_content.py."""

    @pytest.mark.asyncio
    async def test_returns_early_without_content_data(self, mock_agent):
        from python.extensions.hist_add_before._10_mask_content import MaskHistoryContent

        ext = MaskHistoryContent(agent=mock_agent)
        await ext.execute(content_data=None)

    @pytest.mark.asyncio
    async def test_masks_content(self, mock_agent):
        content_data = {"content": "secret123"}

        with patch(
            "python.extensions.hist_add_before._10_mask_content.get_secrets_manager"
        ) as mock_mgr:
            mock_mgr.return_value.mask_values.return_value = "***"

            from python.extensions.hist_add_before._10_mask_content import (
                MaskHistoryContent,
            )

            ext = MaskHistoryContent(agent=mock_agent)
            await ext.execute(content_data=content_data)

        assert content_data["content"] == "***"


class TestSaveToolCallFile:
    """Tests for hist_add_tool_result/_90_save_tool_call_file.py."""

    @pytest.mark.asyncio
    async def test_returns_early_without_data(self, mock_agent):
        from python.extensions.hist_add_tool_result._90_save_tool_call_file import (
            SaveToolCallFile,
        )

        ext = SaveToolCallFile(agent=mock_agent)
        await ext.execute(data=None)

    @pytest.mark.asyncio
    async def test_skips_short_results(self, mock_agent):
        data = {"tool_result": "short"}

        with patch(
            "python.extensions.hist_add_tool_result._90_save_tool_call_file.persist_chat.get_chat_msg_files_folder",
            return_value="/tmp/msgs",
        ):
            from python.extensions.hist_add_tool_result._90_save_tool_call_file import (
                SaveToolCallFile,
            )

            ext = SaveToolCallFile(agent=mock_agent)
            await ext.execute(data=data)

        assert "file" not in data

    @pytest.mark.asyncio
    async def test_saves_long_result_to_file(self, mock_agent, tmp_path):
        data = {"tool_result": "x" * 600}
        mock_agent.context.id = "ctx-1"
        msgs_dir = tmp_path / "msgs"
        msgs_dir.mkdir(exist_ok=True)

        with patch(
            "python.extensions.hist_add_tool_result._90_save_tool_call_file.persist_chat.get_chat_msg_files_folder",
            return_value=str(msgs_dir),
        ), patch(
            "python.extensions.hist_add_tool_result._90_save_tool_call_file.files.get_abs_path",
            side_effect=lambda *a: str(msgs_dir / "1.txt"),
        ), patch(
            "python.extensions.hist_add_tool_result._90_save_tool_call_file.files.write_file",
        ) as mock_write:
            from python.extensions.hist_add_tool_result._90_save_tool_call_file import (
                SaveToolCallFile,
            )

            ext = SaveToolCallFile(agent=mock_agent)
            await ext.execute(data=data)

        assert "file" in data
        mock_write.assert_called_once()


class TestMaskErrorSecrets:
    """Tests for error_format/_10_mask_errors.py."""

    @pytest.mark.asyncio
    async def test_returns_early_without_msg(self, mock_agent):
        from python.extensions.error_format._10_mask_errors import MaskErrorSecrets

        ext = MaskErrorSecrets(agent=mock_agent)
        await ext.execute(msg=None)

    @pytest.mark.asyncio
    async def test_masks_error_message(self, mock_agent):
        msg = {"message": "error: secret_key leaked"}

        with patch(
            "python.extensions.error_format._10_mask_errors.get_secrets_manager"
        ) as mock_mgr:
            mock_mgr.return_value.mask_values.return_value = "error: ***"

            from python.extensions.error_format._10_mask_errors import MaskErrorSecrets

            ext = MaskErrorSecrets(agent=mock_agent)
            await ext.execute(msg=msg)

        assert msg["message"] == "error: ***"


class TestProcessQueue:
    """Tests for process_chain_end/_50_process_queue.py."""

    @pytest.mark.asyncio
    async def test_skips_for_subordinate_agent(self, mock_agent, mock_loop_data):
        mock_agent.number = 1

        with patch(
            "python.extensions.process_chain_end._50_process_queue.asyncio.create_task",
        ) as mock_create:
            from python.extensions.process_chain_end._50_process_queue import (
                ProcessQueue,
            )

            ext = ProcessQueue(agent=mock_agent)
            await ext.execute(loop_data=mock_loop_data)

        # Subordinate agent skips, so create_task not called
        mock_create.assert_not_called()


class TestTaskStatusSync:
    """Tests for process_chain_end/_60_task_status_sync.py."""

    @pytest.mark.asyncio
    async def test_skips_for_subordinate_agent(self, mock_agent, mock_loop_data):
        mock_agent.number = 1

        from python.extensions.process_chain_end._60_task_status_sync import (
            TaskStatusSync,
        )

        ext = TaskStatusSync(agent=mock_agent)
        await ext.execute(loop_data=mock_loop_data)


class TestUpdateCheck:
    """Tests for user_message_ui/_10_update_check.py."""

    @pytest.mark.asyncio
    async def test_returns_early_when_disabled(self, mock_agent, mock_loop_data):
        with patch(
            "python.extensions.user_message_ui._10_update_check.settings.get_settings",
            return_value={"update_check_enabled": False},
        ):
            from python.extensions.user_message_ui._10_update_check import UpdateCheck

            ext = UpdateCheck(agent=mock_agent)
            await ext.execute(loop_data=mock_loop_data)


class TestUtilModelCallMaskSecrets:
    """Tests for util_model_call_before/_10_mask_secrets.py."""

    @pytest.mark.asyncio
    async def test_masks_system_and_message(self, mock_agent):
        call_data = {"system": "sys with secret", "message": "msg with secret"}

        with patch(
            "python.extensions.util_model_call_before._10_mask_secrets.get_secrets_manager"
        ) as mock_mgr:
            mock_mgr.return_value.mask_values.side_effect = lambda x: "***"

            from python.extensions.util_model_call_before._10_mask_secrets import (
                MaskToolSecrets,
            )

            ext = MaskToolSecrets(agent=mock_agent)
            await ext.execute(call_data=call_data)

        assert call_data["system"] == "***"
        assert call_data["message"] == "***"
