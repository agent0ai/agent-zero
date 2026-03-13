"""
Tests for task self-recovery logic:
- ERROR tasks are included in get_due_tasks and auto-retried
- Orphaned RUNNING tasks (no live thread) are reset to IDLE
- Timed-out RUNNING tasks are killed and reset to IDLE
"""
import asyncio
import threading
from datetime import datetime, timezone, timedelta
from unittest.mock import AsyncMock, MagicMock, patch
import sys
from pathlib import Path
from types import ModuleType

import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


# ---------------------------------------------------------------------------
# Stub heavy transitive deps before importing task_scheduler
# ---------------------------------------------------------------------------
_STUB_MODULES = [
    "agent", "initialize",
    "python.helpers.persist_chat",
    "python.helpers.print_style",
    "python.helpers.defer",
    "python.helpers.state_monitor_integration",
    "python.helpers.localization",
    "python.helpers.projects",
    "python.helpers.guids",
    "python.helpers.settings",
    "python.helpers.dotenv",
    "python.helpers.runtime",
    "python.helpers.secrets",
    "python.helpers.notification",
    "python.helpers.providers",
    "python.helpers.dirty_json",
    "python.helpers.whisper",
    "python.helpers.git",
]

for mod_name in _STUB_MODULES:
    stub = ModuleType(mod_name)
    stub.__dict__.setdefault("__all__", [])
    sys.modules[mod_name] = stub

sys.modules["agent"].Agent = MagicMock
sys.modules["agent"].AgentContext = type("AgentContext", (), {
    "_contexts": {}, "get": classmethod(lambda cls, x: None),
})
sys.modules["agent"].UserMessage = MagicMock
sys.modules["initialize"].initialize_agent = MagicMock(return_value=MagicMock())
sys.modules["python.helpers.persist_chat"].save_tmp_chat = MagicMock()
sys.modules["python.helpers.print_style"].PrintStyle = type("PrintStyle", (), {
    "info": staticmethod(lambda *a, **kw: None),
    "warning": staticmethod(lambda *a, **kw: None),
    "error": staticmethod(lambda *a, **kw: None),
    "success": staticmethod(lambda *a, **kw: None),
    "__init__": lambda self, **kw: None,
    "print": lambda self, *a, **kw: None,
})
sys.modules["python.helpers.defer"].DeferredTask = MagicMock
sys.modules["python.helpers.state_monitor_integration"].mark_dirty_all = MagicMock()
sys.modules["python.helpers.localization"].Localization = type("Localization", (), {
    "get": classmethod(lambda cls: type("L", (), {
        "get_timezone": lambda self: "UTC",
        "serialize_datetime": lambda self, dt: dt.isoformat() if dt else None,
        "localtime_str_to_utc_dt": lambda self, s: datetime.fromisoformat(s),
    })()),
})
sys.modules["python.helpers.guids"].generate_id = lambda: "test-" + str(id(object()))
sys.modules["python.helpers.settings"].get_default_value = lambda name, default: default
sys.modules["python.helpers.files"] = ModuleType("python.helpers.files")
sys.modules["python.helpers.files"].get_abs_path = lambda *a: "/tmp/test"
sys.modules["python.helpers.files"].make_dirs = lambda *a: None
sys.modules["python.helpers.files"].read_file = lambda *a: "{}"
sys.modules["python.helpers.files"].write_file = lambda *a: None

from python.helpers.task_scheduler import (
    TaskState,
    ScheduledTask,
    TaskSchedule,
    TaskScheduler,
    SchedulerTaskList,
)


# ---------------------------------------------------------------------------
# Test-friendly subclass: overrides async methods that Pydantic won't let
# us patch on the real BaseModel subclass.
# ---------------------------------------------------------------------------

class TestableTaskList(SchedulerTaskList):
    model_config = {"extra": "allow"}

    async def reload(self):
        return self

    async def save(self):
        return self


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_scheduled_task(
    name: str = "test-task",
    state: TaskState = TaskState.IDLE,
    updated_at: datetime | None = None,
) -> ScheduledTask:
    t = ScheduledTask.create(
        name=name,
        system_prompt="sys",
        prompt="do something",
        schedule=TaskSchedule(minute="*/5", hour="*", day="*", month="*", weekday="*"),
    )
    t.state = state
    if updated_at:
        t.updated_at = updated_at
    return t


def _make_task_list(tasks: list) -> TestableTaskList:
    tl = TestableTaskList(tasks=tasks)
    tl._lock = threading.RLock()
    return tl


def _make_scheduler(tasks: list) -> TaskScheduler:
    TaskScheduler._instance = None
    tl = _make_task_list(tasks)
    with patch.object(SchedulerTaskList, "get", return_value=tl):
        sched = TaskScheduler.get()
    sched._tasks = tl
    sched.update_task = AsyncMock()
    sched.save = AsyncMock()
    return sched


# ---------------------------------------------------------------------------
# get_due_tasks: which states are eligible
# ---------------------------------------------------------------------------

class TestGetDueTasks:
    @pytest.mark.asyncio
    async def test_idle_task_due(self):
        task = _make_scheduled_task(state=TaskState.IDLE)
        tl = _make_task_list([task])
        with patch.object(ScheduledTask, "check_schedule", return_value=True):
            due = await tl.get_due_tasks()
        assert task in due

    @pytest.mark.asyncio
    async def test_error_task_due(self):
        task = _make_scheduled_task(state=TaskState.ERROR)
        tl = _make_task_list([task])
        with patch.object(ScheduledTask, "check_schedule", return_value=True):
            due = await tl.get_due_tasks()
        assert task in due, "ERROR tasks should be retried on next schedule"

    @pytest.mark.asyncio
    async def test_running_task_not_due(self):
        task = _make_scheduled_task(state=TaskState.RUNNING)
        tl = _make_task_list([task])
        with patch.object(ScheduledTask, "check_schedule", return_value=True):
            due = await tl.get_due_tasks()
        assert task not in due, "RUNNING tasks must not be double-scheduled"

    @pytest.mark.asyncio
    async def test_disabled_task_not_due(self):
        task = _make_scheduled_task(state=TaskState.DISABLED)
        tl = _make_task_list([task])
        with patch.object(ScheduledTask, "check_schedule", return_value=True):
            due = await tl.get_due_tasks()
        assert task not in due

    @pytest.mark.asyncio
    async def test_not_scheduled_task_not_due(self):
        task = _make_scheduled_task(state=TaskState.IDLE)
        tl = _make_task_list([task])
        with patch.object(ScheduledTask, "check_schedule", return_value=False):
            due = await tl.get_due_tasks()
        assert task not in due


# ---------------------------------------------------------------------------
# _recover_stuck_tasks
# ---------------------------------------------------------------------------

class TestRecoverStuckTasks:

    @pytest.mark.asyncio
    async def test_orphaned_running_task_reset(self):
        """RUNNING task with no DeferredTask → reset to IDLE."""
        task = _make_scheduled_task(name="orphaned", state=TaskState.RUNNING)
        sched = _make_scheduler([task])

        await sched._recover_stuck_tasks()

        sched.update_task.assert_called_once_with(task.uuid, state=TaskState.IDLE)

    @pytest.mark.asyncio
    async def test_alive_running_task_not_reset(self):
        """RUNNING task with live DeferredTask within timeout → left alone."""
        task = _make_scheduled_task(
            name="alive",
            state=TaskState.RUNNING,
            updated_at=datetime.now(timezone.utc) - timedelta(minutes=5),
        )
        sched = _make_scheduler([task])

        mock_deferred = MagicMock()
        mock_deferred.is_alive.return_value = True
        sched._running_deferred_tasks[task.uuid] = mock_deferred

        await sched._recover_stuck_tasks()

        sched.update_task.assert_not_called()

    @pytest.mark.asyncio
    async def test_timed_out_running_task_reset(self):
        """RUNNING task with live DeferredTask but past timeout → killed and reset."""
        task = _make_scheduled_task(
            name="stuck",
            state=TaskState.RUNNING,
            updated_at=datetime.now(timezone.utc) - timedelta(minutes=60),
        )
        sched = _make_scheduler([task])

        mock_deferred = MagicMock()
        mock_deferred.is_alive.return_value = True
        sched._running_deferred_tasks[task.uuid] = mock_deferred

        with patch("python.helpers.task_scheduler._stuck_timeout", return_value=1800):
            await sched._recover_stuck_tasks()

        mock_deferred.kill.assert_called_once_with(terminate_thread=True)
        sched.update_task.assert_called_once_with(task.uuid, state=TaskState.IDLE)

    @pytest.mark.asyncio
    async def test_dead_deferred_task_reset(self):
        """RUNNING task whose DeferredTask.is_alive() == False → reset."""
        task = _make_scheduled_task(name="dead-thread", state=TaskState.RUNNING)
        sched = _make_scheduler([task])

        mock_deferred = MagicMock()
        mock_deferred.is_alive.return_value = False
        sched._running_deferred_tasks[task.uuid] = mock_deferred

        await sched._recover_stuck_tasks()

        sched.update_task.assert_called_once_with(task.uuid, state=TaskState.IDLE)

    @pytest.mark.asyncio
    async def test_idle_task_not_touched(self):
        """IDLE task should not be affected by recovery."""
        task = _make_scheduled_task(name="idle", state=TaskState.IDLE)
        sched = _make_scheduler([task])

        await sched._recover_stuck_tasks()

        sched.update_task.assert_not_called()

    @pytest.mark.asyncio
    async def test_error_task_not_touched_by_recovery(self):
        """ERROR tasks are handled by get_due_tasks, not by _recover_stuck_tasks."""
        task = _make_scheduled_task(name="errored", state=TaskState.ERROR)
        sched = _make_scheduler([task])

        await sched._recover_stuck_tasks()

        sched.update_task.assert_not_called()

    @pytest.mark.asyncio
    async def test_multiple_stuck_tasks(self):
        """Multiple orphaned RUNNING tasks should all be recovered."""
        t1 = _make_scheduled_task(name="stuck-1", state=TaskState.RUNNING)
        t2 = _make_scheduled_task(name="stuck-2", state=TaskState.RUNNING)
        t3 = _make_scheduled_task(name="healthy", state=TaskState.IDLE)
        sched = _make_scheduler([t1, t2, t3])

        await sched._recover_stuck_tasks()

        assert sched.update_task.call_count == 2
