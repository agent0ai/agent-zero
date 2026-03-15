"""Tests for python/tools/scheduler.py — SchedulerTool."""

import sys
import json
from pathlib import Path
from unittest.mock import MagicMock, AsyncMock, patch

import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


@pytest.fixture
def mock_agent():
    agent = MagicMock()
    agent.context = MagicMock()
    agent.context.id = "ctx-001"
    return agent


@pytest.fixture
def mock_scheduler():
    scheduler = MagicMock()
    scheduler.get_tasks = MagicMock(return_value=[])
    scheduler.find_task_by_name = MagicMock(return_value=[])
    scheduler.get_task_by_uuid = MagicMock(return_value=None)
    scheduler.add_task = AsyncMock()
    scheduler.remove_task_by_uuid = MagicMock()
    scheduler.run_task_by_uuid = AsyncMock()
    scheduler.update_task = AsyncMock()
    scheduler.save = AsyncMock()
    scheduler.reload = AsyncMock()
    return scheduler


@pytest.fixture
def tool(mock_agent):
    from python.tools.scheduler import SchedulerTool
    return SchedulerTool(
        agent=mock_agent,
        name="scheduler",
        method="list_tasks",
        args={},
        message="",
        loop_data=None,
    )


class TestSchedulerToolUnknownMethod:
    @pytest.mark.asyncio
    async def test_unknown_method_returns_error(self, tool):
        tool.method = "invalid_method"
        resp = await tool.execute()
        assert "Unknown method" in resp.message
        assert resp.break_loop is False


class TestSchedulerToolListTasks:
    @pytest.mark.asyncio
    async def test_list_tasks_returns_json(self, tool, mock_scheduler):
        with patch("python.tools.scheduler.TaskScheduler.get", return_value=mock_scheduler):
            resp = await tool.execute(method="list_tasks")
        assert resp.break_loop is False
        data = json.loads(resp.message)
        assert isinstance(data, list)


class TestSchedulerToolFindTaskByName:
    @pytest.mark.asyncio
    async def test_find_task_requires_name(self, tool, mock_scheduler):
        with patch("python.tools.scheduler.TaskScheduler.get", return_value=mock_scheduler):
            resp = await tool.execute(method="find_task_by_name", name="")
        assert "Task name is required" in resp.message

    @pytest.mark.asyncio
    async def test_find_task_not_found(self, tool, mock_scheduler):
        with patch("python.tools.scheduler.TaskScheduler.get", return_value=mock_scheduler):
            resp = await tool.execute(method="find_task_by_name", name="missing")
        assert "Task not found" in resp.message


class TestSchedulerToolShowTask:
    @pytest.mark.asyncio
    async def test_show_task_requires_uuid(self, tool, mock_scheduler):
        with patch("python.tools.scheduler.TaskScheduler.get", return_value=mock_scheduler):
            resp = await tool.execute(method="show_task", uuid="")
        assert "Task UUID is required" in resp.message


class TestSchedulerToolRunTask:
    @pytest.mark.asyncio
    async def test_run_task_requires_uuid(self, tool, mock_scheduler):
        with patch("python.tools.scheduler.TaskScheduler.get", return_value=mock_scheduler):
            resp = await tool.execute(method="run_task", uuid="")
        assert "Task UUID is required" in resp.message


class TestSchedulerToolDeleteTask:
    @pytest.mark.asyncio
    async def test_delete_task_requires_uuid(self, tool, mock_scheduler):
        with patch("python.tools.scheduler.TaskScheduler.get", return_value=mock_scheduler):
            resp = await tool.execute(method="delete_task", uuid="")
        assert "Task UUID is required" in resp.message


class TestSchedulerToolCreateScheduledTask:
    @pytest.mark.asyncio
    async def test_create_scheduled_task_invalid_cron(self, tool, mock_scheduler):
        with patch("python.tools.scheduler.TaskScheduler.get", return_value=mock_scheduler):
            with patch("python.tools.scheduler.get_context_project_name", return_value=None):
                with patch("python.tools.scheduler.load_basic_project_data", side_effect=Exception):
                    resp = await tool.execute(
                        method="create_scheduled_task",
                        name="Test",
                        system_prompt="",
                        prompt="",
                        schedule={"minute": "invalid", "hour": "*", "day": "*", "month": "*", "weekday": "*"},
                    )
        assert "Invalid cron" in resp.message or "invalid" in resp.message.lower()


class TestSchedulerToolCreateAdhocTask:
    @pytest.mark.asyncio
    async def test_create_adhoc_task_success(self, tool, mock_scheduler):
        with patch("python.tools.scheduler.TaskScheduler.get", return_value=mock_scheduler):
            with patch("python.tools.scheduler.get_context_project_name", return_value=None):
                with patch("python.tools.scheduler.load_basic_project_data", return_value={}):
                    with patch("python.tools.scheduler.AdHocTask") as MockTask:
                        mock_task = MagicMock()
                        mock_task.uuid = "task-123"
                        MockTask.create = MagicMock(return_value=mock_task)
                        resp = await tool.execute(
                            method="create_adhoc_task",
                            name="Adhoc",
                            system_prompt="",
                            prompt="Do something",
                            attachments=[],
                        )
        assert "created" in resp.message.lower()
        assert "task-123" in resp.message


class TestSchedulerToolCreatePlannedTask:
    @pytest.mark.asyncio
    async def test_create_planned_task_invalid_datetime(self, tool, mock_scheduler):
        with patch("python.tools.scheduler.TaskScheduler.get", return_value=mock_scheduler):
            with patch("python.tools.scheduler.get_context_project_name", return_value=None):
                with patch("python.tools.scheduler.load_basic_project_data", return_value={}):
                    with patch("python.tools.scheduler.parse_datetime", return_value=None):
                        resp = await tool.execute(
                            method="create_planned_task",
                            name="Planned",
                            system_prompt="",
                            prompt="",
                            plan=["not-a-date"],
                        )
        assert "Invalid datetime" in resp.message


class TestSchedulerToolWaitForTask:
    @pytest.mark.asyncio
    async def test_wait_for_task_requires_uuid(self, tool, mock_scheduler):
        with patch("python.tools.scheduler.TaskScheduler.get", return_value=mock_scheduler):
            resp = await tool.execute(method="wait_for_task", uuid="")
        assert "Task UUID is required" in resp.message
