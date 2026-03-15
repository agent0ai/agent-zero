"""Tests for python/api/scheduler_task_run.py — SchedulerTaskRun API handler."""

import sys
import threading
from pathlib import Path
from unittest.mock import MagicMock, AsyncMock, patch

import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from python.api.scheduler_task_run import SchedulerTaskRun
from python.helpers.task_scheduler import TaskState


def _make_handler():
    return SchedulerTaskRun(app=MagicMock(), thread_lock=threading.Lock())


class TestSchedulerTaskRun:
    @pytest.mark.asyncio
    async def test_returns_error_when_task_id_missing(self):
        handler = _make_handler()
        with patch("python.api.scheduler_task_run.Localization"):
            result = await handler.process({}, MagicMock())

        assert "error" in result
        assert "task_id" in result["error"]

    @pytest.mark.asyncio
    async def test_returns_error_when_task_not_found(self):
        handler = _make_handler()
        mock_scheduler = MagicMock()
        mock_scheduler.reload = AsyncMock()
        mock_scheduler.get_task_by_uuid = MagicMock(return_value=None)

        with patch("python.api.scheduler_task_run.TaskScheduler.get", return_value=mock_scheduler), \
             patch("python.api.scheduler_task_run.Localization"):
            result = await handler.process({"task_id": "nonexistent"}, MagicMock())

        assert "error" in result
        assert "not found" in result["error"]

    @pytest.mark.asyncio
    async def test_returns_error_when_task_already_running(self):
        handler = _make_handler()
        mock_task = MagicMock()
        mock_task.uuid = "task-123"
        mock_task.state = TaskState.RUNNING
        serialized = {"uuid": "task-123", "state": "running"}

        mock_scheduler = MagicMock()
        mock_scheduler.reload = AsyncMock()
        mock_scheduler.get_task_by_uuid = MagicMock(return_value=mock_task)
        mock_scheduler.serialize_task = MagicMock(return_value=serialized)

        with patch("python.api.scheduler_task_run.TaskScheduler.get", return_value=mock_scheduler), \
             patch("python.api.scheduler_task_run.Localization"):
            result = await handler.process({"task_id": "task-123"}, MagicMock())

        assert "error" in result
        assert "cannot be run" in result["error"]
        assert result["task"] == serialized

    @pytest.mark.asyncio
    async def test_runs_task_successfully(self):
        handler = _make_handler()
        mock_task = MagicMock()
        mock_task.uuid = "task-456"
        mock_task.state = TaskState.IDLE
        serialized = {"uuid": "task-456", "state": "idle"}

        mock_scheduler = MagicMock()
        mock_scheduler.reload = AsyncMock()
        mock_scheduler.get_task_by_uuid = MagicMock(return_value=mock_task)
        mock_scheduler.run_task_by_uuid = AsyncMock()
        mock_scheduler.serialize_task = MagicMock(return_value=serialized)

        with patch("python.api.scheduler_task_run.TaskScheduler.get", return_value=mock_scheduler), \
             patch("python.api.scheduler_task_run.Localization"):
            result = await handler.process({"task_id": "task-456"}, MagicMock())

        assert result["success"] is True
        assert "started successfully" in result["message"]
        assert result["task"] == serialized
        mock_scheduler.run_task_by_uuid.assert_called_once_with("task-456")

    @pytest.mark.asyncio
    async def test_returns_error_on_value_error(self):
        handler = _make_handler()
        mock_task = MagicMock()
        mock_task.uuid = "task-789"
        mock_task.state = TaskState.IDLE

        mock_scheduler = MagicMock()
        mock_scheduler.reload = AsyncMock()
        mock_scheduler.get_task_by_uuid = MagicMock(return_value=mock_task)
        mock_scheduler.run_task_by_uuid = AsyncMock(side_effect=ValueError("Invalid state"))

        with patch("python.api.scheduler_task_run.TaskScheduler.get", return_value=mock_scheduler), \
             patch("python.api.scheduler_task_run.Localization"):
            result = await handler.process({"task_id": "task-789"}, MagicMock())

        assert "error" in result
        assert "Invalid state" in result["error"]
