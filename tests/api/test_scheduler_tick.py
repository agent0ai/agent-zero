"""Tests for python/api/scheduler_tick.py — SchedulerTick API handler."""

import sys
import threading
from pathlib import Path
from unittest.mock import MagicMock, AsyncMock, patch

import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from python.api.scheduler_tick import SchedulerTick


def _make_handler():
    return SchedulerTick(app=MagicMock(), thread_lock=threading.Lock())


class TestSchedulerTick:
    def test_requires_loopback(self):
        assert SchedulerTick.requires_loopback() is True

    def test_requires_auth_false(self):
        assert SchedulerTick.requires_auth() is False

    def test_requires_csrf_false(self):
        assert SchedulerTick.requires_csrf() is False

    @pytest.mark.asyncio
    async def test_returns_tick_response_with_tasks(self):
        handler = _make_handler()
        mock_task = MagicMock()
        mock_task.name = "Test task"
        mock_task.uuid = "task-123"
        mock_task.state = "idle"
        serialized = [{"uuid": "task-123", "name": "Test task"}]

        mock_scheduler = MagicMock()
        mock_scheduler.reload = AsyncMock()
        mock_scheduler.get_tasks = MagicMock(return_value=[mock_task])
        mock_scheduler.tick = AsyncMock()
        mock_scheduler.serialize_all_tasks = MagicMock(return_value=serialized)

        with patch("python.api.scheduler_tick.TaskScheduler.get", return_value=mock_scheduler), \
             patch("python.api.scheduler_tick.Localization"):
            result = await handler.process({}, MagicMock())

        assert result["scheduler"] == "tick"
        assert "timestamp" in result
        assert result["tasks_count"] == 1
        assert result["tasks"] == serialized
        mock_scheduler.tick.assert_called_once()

    @pytest.mark.asyncio
    async def test_returns_empty_tasks_when_none(self):
        handler = _make_handler()
        mock_scheduler = MagicMock()
        mock_scheduler.reload = AsyncMock()
        mock_scheduler.get_tasks = MagicMock(return_value=[])
        mock_scheduler.tick = AsyncMock()
        mock_scheduler.serialize_all_tasks = MagicMock(return_value=[])

        with patch("python.api.scheduler_tick.TaskScheduler.get", return_value=mock_scheduler), \
             patch("python.api.scheduler_tick.Localization"):
            result = await handler.process({}, MagicMock())

        assert result["tasks_count"] == 0
        assert result["tasks"] == []
