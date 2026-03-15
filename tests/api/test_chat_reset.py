"""Tests for python/api/chat_reset.py — Reset API handler."""

import sys
import threading
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from python.api.chat_reset import Reset


def _make_handler(app=None, lock=None):
    return Reset(app=app or MagicMock(), thread_lock=lock or threading.Lock())


class TestReset:
    @pytest.mark.asyncio
    async def test_resets_context_and_returns_message(self, mock_app):
        app, lock = mock_app
        handler = _make_handler(app, lock)
        mock_ctx = MagicMock()
        mock_scheduler = MagicMock()
        mock_scheduler.cancel_tasks_by_context = MagicMock()

        with patch.object(handler, "use_context", return_value=mock_ctx), \
             patch("python.api.chat_reset.TaskScheduler") as MockScheduler, \
             patch("python.api.chat_reset.persist_chat") as mock_persist, \
             patch("python.helpers.state_monitor_integration.mark_dirty_all"):
            MockScheduler.get.return_value = mock_scheduler

            result = await handler.process({"context": "ctx-123"}, MagicMock())

        assert result["message"] == "Agent restarted."
        mock_ctx.reset.assert_called_once()
        mock_persist.save_tmp_chat.assert_called_once_with(mock_ctx)
        mock_persist.remove_msg_files.assert_called_once_with("ctx-123")

    @pytest.mark.asyncio
    async def test_cancels_tasks_before_reset(self, mock_app):
        app, lock = mock_app
        handler = _make_handler(app, lock)
        mock_ctx = MagicMock()
        mock_scheduler = MagicMock()
        mock_scheduler.cancel_tasks_by_context = MagicMock()

        with patch.object(handler, "use_context", return_value=mock_ctx), \
             patch("python.api.chat_reset.TaskScheduler") as MockScheduler, \
             patch("python.api.chat_reset.persist_chat"), \
             patch("python.helpers.state_monitor_integration.mark_dirty_all"):
            MockScheduler.get.return_value = mock_scheduler

            await handler.process({"context": "ctx-456"}, MagicMock())

        mock_scheduler.cancel_tasks_by_context.assert_called_once_with("ctx-456", terminate_thread=True)

    @pytest.mark.asyncio
    async def test_calls_mark_dirty_all(self, mock_app):
        app, lock = mock_app
        handler = _make_handler(app, lock)

        with patch.object(handler, "use_context", return_value=MagicMock()), \
             patch("python.api.chat_reset.TaskScheduler"), \
             patch("python.api.chat_reset.persist_chat"), \
             patch("python.helpers.state_monitor_integration.mark_dirty_all") as mark_dirty:
            await handler.process({"context": "ctx-1"}, MagicMock())
            mark_dirty.assert_called_once_with(reason="api.chat_reset.Reset")
