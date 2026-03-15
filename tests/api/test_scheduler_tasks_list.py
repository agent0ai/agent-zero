"""Tests for python/api/scheduler_tasks_list.py — SchedulerTasksList API handler."""

import sys
import threading
from pathlib import Path
from unittest.mock import MagicMock, AsyncMock, patch

import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from python.api.scheduler_tasks_list import SchedulerTasksList


def _make_handler():
    return SchedulerTasksList(app=MagicMock(), thread_lock=threading.Lock())


class TestSchedulerTasksList:
    @pytest.mark.asyncio
    async def test_returns_tasks_list_successfully(self):
        handler = _make_handler()
        tasks_list = [
            {"uuid": "task-1", "name": "Task 1", "type": "adhoc"},
            {"uuid": "task-2", "name": "Task 2", "type": "scheduled"},
        ]

        mock_scheduler = MagicMock()
        mock_scheduler.reload = AsyncMock()
        mock_scheduler.serialize_all_tasks = MagicMock(return_value=tasks_list)

        with patch("python.api.scheduler_tasks_list.TaskScheduler.get", return_value=mock_scheduler), \
             patch("python.api.scheduler_tasks_list.Localization"):
            result = await handler.process({}, MagicMock())

        assert result["ok"] is True
        assert result["tasks"] == tasks_list
        assert len(result["tasks"]) == 2

    @pytest.mark.asyncio
    async def test_returns_empty_list_when_no_tasks(self):
        handler = _make_handler()
        mock_scheduler = MagicMock()
        mock_scheduler.reload = AsyncMock()
        mock_scheduler.serialize_all_tasks = MagicMock(return_value=[])

        with patch("python.api.scheduler_tasks_list.TaskScheduler.get", return_value=mock_scheduler), \
             patch("python.api.scheduler_tasks_list.Localization"):
            result = await handler.process({}, MagicMock())

        assert result["ok"] is True
        assert result["tasks"] == []

    @pytest.mark.asyncio
    async def test_handles_exception_gracefully(self):
        handler = _make_handler()
        mock_scheduler = MagicMock()
        mock_scheduler.reload = AsyncMock(side_effect=Exception("Scheduler error"))

        with patch("python.api.scheduler_tasks_list.TaskScheduler.get", return_value=mock_scheduler), \
             patch("python.api.scheduler_tasks_list.Localization"):
            result = await handler.process({}, MagicMock())

        assert result["ok"] is False
        assert "error" in result
        assert "Scheduler error" in result["error"]
        assert result["tasks"] == []
