"""Tests for python/api/scheduler_task_update.py — SchedulerTaskUpdate API handler."""

import sys
import threading
from pathlib import Path
from unittest.mock import MagicMock, AsyncMock, patch

import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from python.api.scheduler_task_update import SchedulerTaskUpdate
from python.helpers.task_scheduler import TaskState


def _make_handler():
    return SchedulerTaskUpdate(app=MagicMock(), thread_lock=threading.Lock())


class TestSchedulerTaskUpdate:
    @pytest.mark.asyncio
    async def test_returns_error_when_task_id_missing(self):
        handler = _make_handler()
        mock_scheduler = MagicMock()
        mock_scheduler.reload = AsyncMock()

        with patch("python.api.scheduler_task_update.TaskScheduler.get", return_value=mock_scheduler), \
             patch("python.api.scheduler_task_update.Localization"):
            result = await handler.process({}, MagicMock())

        assert "error" in result
        assert "task_id" in result["error"]

    @pytest.mark.asyncio
    async def test_returns_error_when_task_not_found(self):
        handler = _make_handler()
        mock_scheduler = MagicMock()
        mock_scheduler.reload = AsyncMock()
        mock_scheduler.get_task_by_uuid = MagicMock(return_value=None)

        with patch("python.api.scheduler_task_update.TaskScheduler.get", return_value=mock_scheduler), \
             patch("python.api.scheduler_task_update.Localization"):
            result = await handler.process({"task_id": "nonexistent"}, MagicMock())

        assert "error" in result
        assert "not found" in result["error"]

    @pytest.mark.asyncio
    async def test_updates_task_successfully(self):
        handler = _make_handler()
        mock_task = MagicMock()
        mock_task.uuid = "task-123"
        mock_updated = MagicMock()
        mock_updated.uuid = "task-123"
        task_dict = {"uuid": "task-123", "name": "Updated name"}

        mock_scheduler = MagicMock()
        mock_scheduler.reload = AsyncMock()
        mock_scheduler.get_task_by_uuid = MagicMock(return_value=mock_task)
        mock_scheduler.update_task = AsyncMock(return_value=mock_updated)

        with patch("python.api.scheduler_task_update.TaskScheduler.get", return_value=mock_scheduler), \
             patch("python.api.scheduler_task_update.serialize_task", return_value=task_dict), \
             patch("python.api.scheduler_task_update.Localization"):
            result = await handler.process({
                "task_id": "task-123",
                "name": "Updated name",
            }, MagicMock())

        assert result["ok"] is True
        assert result["task"]["name"] == "Updated name"
        mock_scheduler.update_task.assert_called_once()

    @pytest.mark.asyncio
    async def test_rejects_project_changes(self):
        handler = _make_handler()
        mock_task = MagicMock()
        mock_task.uuid = "task-123"

        mock_scheduler = MagicMock()
        mock_scheduler.reload = AsyncMock()
        mock_scheduler.get_task_by_uuid = MagicMock(return_value=mock_task)

        with patch("python.api.scheduler_task_update.TaskScheduler.get", return_value=mock_scheduler), \
             patch("python.api.scheduler_task_update.Localization"):
            result = await handler.process({
                "task_id": "task-123",
                "project_name": "new-project",
            }, MagicMock())

        assert "error" in result
        assert "Project changes" in result["error"]

    @pytest.mark.asyncio
    async def test_updates_state_when_provided(self):
        handler = _make_handler()
        mock_task = MagicMock()
        mock_task.uuid = "task-123"
        mock_updated = MagicMock()
        task_dict = {"uuid": "task-123", "state": "disabled"}

        mock_scheduler = MagicMock()
        mock_scheduler.reload = AsyncMock()
        mock_scheduler.get_task_by_uuid = MagicMock(return_value=mock_task)
        mock_scheduler.update_task = AsyncMock(return_value=mock_updated)

        with patch("python.api.scheduler_task_update.TaskScheduler.get", return_value=mock_scheduler), \
             patch("python.api.scheduler_task_update.serialize_task", return_value=task_dict), \
             patch("python.api.scheduler_task_update.Localization"):
            result = await handler.process({
                "task_id": "task-123",
                "state": "disabled",
            }, MagicMock())

        assert result["ok"] is True
        call_kwargs = mock_scheduler.update_task.call_args[1]
        assert call_kwargs["state"] == TaskState.DISABLED
