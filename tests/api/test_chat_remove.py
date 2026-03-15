"""Tests for python/api/chat_remove.py — RemoveChat API handler."""

import sys
import threading
from pathlib import Path
from unittest.mock import MagicMock, AsyncMock, patch

import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from python.api.chat_remove import RemoveChat


def _make_handler(app=None, lock=None):
    return RemoveChat(app=app or MagicMock(), thread_lock=lock or threading.Lock())


class TestRemoveChat:
    @pytest.mark.asyncio
    async def test_removes_context_and_returns_message(self, mock_app):
        app, lock = mock_app
        handler = _make_handler(app, lock)
        mock_ctx = MagicMock()
        mock_scheduler = MagicMock()
        mock_scheduler.cancel_tasks_by_context = MagicMock()
        mock_scheduler.reload = AsyncMock()
        mock_scheduler.get_tasks_by_context_id = MagicMock(return_value=[])
        mock_scheduler.remove_task_by_uuid = AsyncMock()

        with patch("python.api.chat_remove.TaskScheduler") as MockScheduler, \
             patch("python.api.chat_remove.AgentContext") as MockCtx, \
             patch("python.api.chat_remove.persist_chat"), \
             patch("python.helpers.state_monitor_integration.mark_dirty_all"):
            MockScheduler.get.return_value = mock_scheduler
            MockCtx.use.return_value = mock_ctx
            MockCtx.remove = MagicMock()

            result = await handler.process({"context": "ctx-123"}, MagicMock())

        assert result["message"] == "Context removed."
        MockCtx.remove.assert_called_once_with("ctx-123")

    @pytest.mark.asyncio
    async def test_cancels_tasks_and_removes_msg_files(self, mock_app):
        app, lock = mock_app
        handler = _make_handler(app, lock)
        mock_scheduler = MagicMock()
        mock_scheduler.cancel_tasks_by_context = MagicMock()
        mock_scheduler.reload = AsyncMock()
        mock_scheduler.get_tasks_by_context_id = MagicMock(return_value=[])

        with patch("python.api.chat_remove.TaskScheduler") as MockScheduler, \
             patch("python.api.chat_remove.AgentContext") as MockCtx, \
             patch("python.api.chat_remove.persist_chat") as mock_persist, \
             patch("python.helpers.state_monitor_integration.mark_dirty_all"):
            MockScheduler.get.return_value = mock_scheduler
            MockCtx.use.return_value = MagicMock()

            await handler.process({"context": "ctx-456"}, MagicMock())

        mock_scheduler.cancel_tasks_by_context.assert_called_once_with("ctx-456", terminate_thread=True)
        mock_persist.remove_chat.assert_called_once_with("ctx-456")

    @pytest.mark.asyncio
    async def test_empty_context_still_processes(self, mock_app):
        app, lock = mock_app
        handler = _make_handler(app, lock)
        mock_scheduler = MagicMock()
        mock_scheduler.cancel_tasks_by_context = MagicMock()
        mock_scheduler.reload = AsyncMock()
        mock_scheduler.get_tasks_by_context_id = MagicMock(return_value=[])

        with patch("python.api.chat_remove.TaskScheduler") as MockScheduler, \
             patch("python.api.chat_remove.AgentContext") as MockCtx, \
             patch("python.api.chat_remove.persist_chat"), \
             patch("python.helpers.state_monitor_integration.mark_dirty_all"):
            MockScheduler.get.return_value = mock_scheduler
            MockCtx.use.return_value = MagicMock()

            result = await handler.process({"context": ""}, MagicMock())

        assert result["message"] == "Context removed."
