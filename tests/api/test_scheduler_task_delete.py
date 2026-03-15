"""Tests for python/api/scheduler_task_delete.py — SchedulerTaskDelete API handler."""

import sys
import threading
from pathlib import Path
from unittest.mock import MagicMock, AsyncMock, patch

import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from python.api.scheduler_task_delete import SchedulerTaskDelete
from python.helpers.task_scheduler import TaskState


def _make_handler():
    return SchedulerTaskDelete(app=MagicMock(), thread_lock=threading.Lock())


class TestSchedulerTaskDelete:
    @pytest.mark.asyncio
    async def test_returns_error_when_task_id_missing(self):
        handler = _make_handler()
        mock_scheduler = MagicMock()
        mock_scheduler.reload = AsyncMock()

        with patch("python.api.scheduler_task_delete.TaskScheduler.get", return_value=mock_scheduler), \
             patch("python.api.scheduler_task_delete.Localization"):
            result = await handler.process({}, MagicMock())

        assert "error" in result
        assert "task_id" in result["error"]

    @pytest.mark.asyncio
    async def test_returns_error_when_task_not_found(self):
        handler = _make_handler()
        mock_scheduler = MagicMock()
        mock_scheduler.reload = AsyncMock()
        mock_scheduler.get_task_by_uuid = MagicMock(return_value=None)

        with patch("python.api.scheduler_task_delete.TaskScheduler.get", return_value=mock_scheduler), \
             patch("python.api.scheduler_task_delete.Localization"):
            result = await handler.process({"task_id": "nonexistent"}, MagicMock())

        assert "error" in result
        assert "not found" in result["error"]

    @pytest.mark.asyncio
    async def test_deletes_task_successfully(self):
        handler = _make_handler()
        mock_task = MagicMock()
        mock_task.uuid = "task-123"
        mock_task.context_id = None
        mock_task.state = TaskState.IDLE

        mock_scheduler = MagicMock()
        mock_scheduler.reload = AsyncMock()
        mock_scheduler.get_task_by_uuid = MagicMock(return_value=mock_task)
        mock_scheduler.remove_task_by_uuid = AsyncMock()

        with patch("python.api.scheduler_task_delete.TaskScheduler.get", return_value=mock_scheduler), \
             patch("python.api.scheduler_task_delete.Localization"):
            result = await handler.process({"task_id": "task-123"}, MagicMock())

        assert result["success"] is True
        assert "deleted successfully" in result["message"]
        mock_scheduler.remove_task_by_uuid.assert_called_once_with("task-123")

    @pytest.mark.asyncio
    async def test_cancels_running_task_before_delete(self):
        handler = _make_handler()
        mock_task = MagicMock()
        mock_task.uuid = "task-456"
        mock_task.context_id = None
        mock_task.state = TaskState.RUNNING

        mock_scheduler = MagicMock()
        mock_scheduler.reload = AsyncMock()
        mock_scheduler.get_task_by_uuid = MagicMock(return_value=mock_task)
        mock_scheduler.cancel_running_task = MagicMock()
        mock_scheduler.update_task = AsyncMock()
        mock_scheduler.save = AsyncMock()
        mock_scheduler.remove_task_by_uuid = AsyncMock()

        with patch("python.api.scheduler_task_delete.TaskScheduler.get", return_value=mock_scheduler), \
             patch("python.api.scheduler_task_delete.Localization"):
            result = await handler.process({"task_id": "task-456"}, MagicMock())

        assert result["success"] is True
        mock_scheduler.cancel_running_task.assert_called_once_with("task-456", terminate_thread=True)
        mock_scheduler.update_task.assert_called_once()
