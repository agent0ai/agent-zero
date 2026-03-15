"""Tests for python/api/scheduler_task_create.py — SchedulerTaskCreate API handler."""

import sys
import threading
from pathlib import Path
from unittest.mock import MagicMock, AsyncMock, patch

import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from python.api.scheduler_task_create import SchedulerTaskCreate


def _make_handler():
    return SchedulerTaskCreate(app=MagicMock(), thread_lock=threading.Lock())


class TestSchedulerTaskCreate:
    @pytest.mark.asyncio
    async def test_creates_adhoc_task_success(self):
        handler = _make_handler()
        mock_task = MagicMock()
        mock_task.uuid = "task-123"
        mock_task.type = "adhoc"
        mock_task.token = "token-456"
        task_dict = {"uuid": "task-123", "type": "adhoc", "token": "token-456"}

        mock_scheduler = MagicMock()
        mock_scheduler.reload = AsyncMock()
        mock_scheduler.add_task = AsyncMock()
        mock_scheduler.get_task_by_uuid = MagicMock(return_value=mock_task)

        with patch("python.api.scheduler_task_create.TaskScheduler.get", return_value=mock_scheduler), \
             patch("python.api.scheduler_task_create.AdHocTask.create", return_value=mock_task), \
             patch("python.api.scheduler_task_create.serialize_task", return_value=task_dict), \
             patch("python.api.scheduler_task_create.Localization"):
            result = await handler.process({
                "name": "Test task",
                "prompt": "Do something",
                "token": "token-456",
            }, MagicMock())

        assert result["ok"] is True
        assert result["task"] == task_dict
        mock_scheduler.add_task.assert_called_once()

    @pytest.mark.asyncio
    async def test_raises_when_name_missing(self):
        handler = _make_handler()
        mock_scheduler = MagicMock()
        mock_scheduler.reload = AsyncMock()

        with patch("python.api.scheduler_task_create.TaskScheduler.get", return_value=mock_scheduler), \
             patch("python.api.scheduler_task_create.Localization"):
            with pytest.raises(ValueError, match="Missing required fields"):
                await handler.process({"prompt": "Do something"}, MagicMock())

    @pytest.mark.asyncio
    async def test_raises_when_prompt_missing(self):
        handler = _make_handler()
        mock_scheduler = MagicMock()
        mock_scheduler.reload = AsyncMock()

        with patch("python.api.scheduler_task_create.TaskScheduler.get", return_value=mock_scheduler), \
             patch("python.api.scheduler_task_create.Localization"):
            with pytest.raises(ValueError, match="Missing required fields"):
                await handler.process({"name": "Test"}, MagicMock())

    @pytest.mark.asyncio
    async def test_creates_scheduled_task_with_dict_schedule(self):
        handler = _make_handler()
        mock_task = MagicMock()
        mock_task.uuid = "sched-123"
        mock_schedule = MagicMock()
        task_dict = {"uuid": "sched-123", "type": "scheduled"}

        mock_scheduler = MagicMock()
        mock_scheduler.reload = AsyncMock()
        mock_scheduler.add_task = AsyncMock()
        mock_scheduler.get_task_by_uuid = MagicMock(return_value=mock_task)

        with patch("python.api.scheduler_task_create.TaskScheduler.get", return_value=mock_scheduler), \
             patch("python.api.scheduler_task_create.parse_task_schedule", return_value=mock_schedule), \
             patch("python.api.scheduler_task_create.ScheduledTask.create", return_value=mock_task), \
             patch("python.api.scheduler_task_create.serialize_task", return_value=task_dict), \
             patch("python.api.scheduler_task_create.Localization"):
            result = await handler.process({
                "name": "Scheduled",
                "prompt": "Run daily",
                "schedule": {"minute": "0", "hour": "9"},
            }, MagicMock())

        assert result["ok"] is True
        assert result["task"]["type"] == "scheduled"

    @pytest.mark.asyncio
    async def test_creates_scheduled_task_with_string_schedule(self):
        handler = _make_handler()
        mock_task = MagicMock()
        mock_task.uuid = "sched-456"
        task_dict = {"uuid": "sched-456", "type": "scheduled"}

        mock_scheduler = MagicMock()
        mock_scheduler.reload = AsyncMock()
        mock_scheduler.add_task = AsyncMock()
        mock_scheduler.get_task_by_uuid = MagicMock(return_value=mock_task)

        with patch("python.api.scheduler_task_create.TaskScheduler.get", return_value=mock_scheduler), \
             patch("python.api.scheduler_task_create.ScheduledTask.create", return_value=mock_task), \
             patch("python.api.scheduler_task_create.serialize_task", return_value=task_dict), \
             patch("python.api.scheduler_task_create.Localization"):
            result = await handler.process({
                "name": "Cron task",
                "prompt": "Run",
                "schedule": "0 9 * * *",
            }, MagicMock())

        assert result["ok"] is True

    @pytest.mark.asyncio
    async def test_returns_error_when_project_load_fails(self):
        handler = _make_handler()
        mock_scheduler = MagicMock()
        mock_scheduler.reload = AsyncMock()

        with patch("python.api.scheduler_task_create.TaskScheduler.get", return_value=mock_scheduler), \
             patch("python.api.scheduler_task_create.load_basic_project_data", side_effect=Exception("Project not found")), \
             patch("python.api.scheduler_task_create.Localization"):
            result = await handler.process({
                "name": "Task",
                "prompt": "Do it",
                "project_name": "bad-project",
            }, MagicMock())

        assert "error" in result
        assert "bad-project" in result["error"]

    @pytest.mark.asyncio
    async def test_generates_token_when_empty(self):
        handler = _make_handler()
        mock_task = MagicMock()
        mock_task.uuid = "task-789"
        mock_task.type = "adhoc"
        mock_task.token = "generated-token"
        task_dict = {"uuid": "task-789", "type": "adhoc", "token": "generated-token"}

        mock_scheduler = MagicMock()
        mock_scheduler.reload = AsyncMock()
        mock_scheduler.add_task = AsyncMock()
        mock_scheduler.get_task_by_uuid = MagicMock(return_value=mock_task)

        with patch("python.api.scheduler_task_create.TaskScheduler.get", return_value=mock_scheduler), \
             patch("python.api.scheduler_task_create.AdHocTask.create", return_value=mock_task), \
             patch("python.api.scheduler_task_create.serialize_task", return_value=task_dict), \
             patch("python.api.scheduler_task_create.Localization"):
            result = await handler.process({
                "name": "Task",
                "prompt": "Do it",
            }, MagicMock())

        assert result["ok"] is True
        mock_scheduler.add_task.assert_called_once()
