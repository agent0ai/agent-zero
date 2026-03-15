"""
Comprehensive unit tests for python/helpers/task_scheduler.py.

Covers: TaskState, TaskType, TaskSchedule, TaskPlan, BaseTask, AdHocTask,
ScheduledTask, PlannedTask, SchedulerTaskList, TaskScheduler, serialization
helpers, cron parsing, next-run calculation, execution, recovery, edge cases.
"""
import asyncio
import threading
from datetime import datetime, timezone, timedelta
from unittest.mock import AsyncMock, MagicMock, patch
import sys
from pathlib import Path
from types import ModuleType

import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


# ---------------------------------------------------------------------------
# Stub heavy transitive deps before importing task_scheduler.
# We save originals and restore them after the import so that other test
# modules collected in the same process are not affected.
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
    "python.helpers.files",
]

_saved_modules = {name: sys.modules[name] for name in _STUB_MODULES if name in sys.modules}

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
        "localtime_str_to_utc_dt": lambda self, s: datetime.fromisoformat(s.replace("Z", "+00:00")) if s else None,
    })()),
})
sys.modules["python.helpers.guids"].generate_id = lambda: "test-" + str(id(object()))
sys.modules["python.helpers.settings"].get_default_value = lambda name, default: default
sys.modules["python.helpers.files"].get_abs_path = lambda *a: "/tmp/test"
sys.modules["python.helpers.files"].make_dirs = lambda *a: None
sys.modules["python.helpers.files"].read_file = lambda *a: "{}"
sys.modules["python.helpers.files"].write_file = lambda *a: None

from python.helpers.task_scheduler import (
    TaskState,
    TaskType,
    TaskSchedule,
    TaskPlan,
    BaseTask,
    AdHocTask,
    ScheduledTask,
    PlannedTask,
    TaskScheduler,
    SchedulerTaskList,
    serialize_datetime,
    parse_datetime,
    serialize_task_schedule,
    parse_task_schedule,
    serialize_task_plan,
    parse_task_plan,
    serialize_task,
    serialize_tasks,
    deserialize_task,
)

# Restore original modules so other test files are not poisoned.
for _mod_name in _STUB_MODULES:
    if _mod_name in _saved_modules:
        sys.modules[_mod_name] = _saved_modules[_mod_name]
    else:
        sys.modules.pop(_mod_name, None)
del _saved_modules


# ---------------------------------------------------------------------------
# Test-friendly subclasses
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


def _make_adhoc_task(name: str = "adhoc-task", state: TaskState = TaskState.IDLE) -> AdHocTask:
    t = AdHocTask.create(
        name=name,
        system_prompt="sys",
        prompt="prompt",
        token="1234567890123456789",
    )
    t.state = state
    return t


def _make_planned_task(
    name: str = "planned-task",
    state: TaskState = TaskState.IDLE,
    todo_times: list[datetime] | None = None,
) -> PlannedTask:
    plan = TaskPlan.create(todo=todo_times or [])
    t = PlannedTask.create(name=name, system_prompt="sys", prompt="prompt", plan=plan)
    t.state = state
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
# TaskState / TaskType
# ---------------------------------------------------------------------------

class TestTaskStateAndType:
    def test_task_state_and_type_values(self):
        assert TaskState.IDLE == "idle"
        assert TaskState.RUNNING == "running"
        assert TaskType.AD_HOC == "adhoc"
        assert TaskType.SCHEDULED == "scheduled"


# ---------------------------------------------------------------------------
# TaskSchedule
# ---------------------------------------------------------------------------

class TestTaskSchedule:
    def test_to_crontab(self):
        s = TaskSchedule(minute="*/5", hour="*", day="*", month="*", weekday="*")
        assert s.to_crontab() == "*/5 * * * *"

    def test_to_crontab_specific_values_and_timezone(self):
        s = TaskSchedule(minute="30", hour="9", day="1", month="1", weekday="1", timezone="UTC")
        assert s.to_crontab() == "30 9 1 1 1"
        assert s.timezone == "UTC"


# ---------------------------------------------------------------------------
# TaskPlan
# ---------------------------------------------------------------------------

class TestTaskPlan:
    def test_create_empty(self):
        plan = TaskPlan.create()
        assert plan.todo == []
        assert plan.in_progress is None
        assert plan.done == []

    def test_add_todo(self):
        plan = TaskPlan.create()
        dt = datetime(2025, 3, 15, 10, 0, 0, tzinfo=timezone.utc)
        plan.add_todo(dt)
        assert plan.todo == [dt]

    def test_add_todo_sorts(self):
        plan = TaskPlan.create()
        dt1 = datetime(2025, 3, 16, 10, 0, 0, tzinfo=timezone.utc)
        dt2 = datetime(2025, 3, 15, 10, 0, 0, tzinfo=timezone.utc)
        plan.add_todo(dt1)
        plan.add_todo(dt2)
        assert plan.todo == [dt2, dt1]

    def test_set_in_progress(self):
        plan = TaskPlan.create(todo=[datetime(2025, 3, 15, 10, 0, 0, tzinfo=timezone.utc)])
        dt = plan.todo[0]
        plan.set_in_progress(dt)
        assert plan.in_progress == dt
        assert plan.todo == []

    def test_set_in_progress_raises_if_not_in_todo(self):
        plan = TaskPlan.create()
        dt = datetime(2025, 3, 15, 10, 0, 0, tzinfo=timezone.utc)
        with pytest.raises(ValueError, match="not in todo list"):
            plan.set_in_progress(dt)

    def test_set_done(self):
        dt = datetime(2025, 3, 15, 10, 0, 0, tzinfo=timezone.utc)
        plan = TaskPlan.create(in_progress=dt)
        plan.set_done(dt)
        assert plan.in_progress is None
        assert plan.done == [dt]

    def test_set_done_raises_if_not_in_progress(self):
        plan = TaskPlan.create()
        dt = datetime(2025, 3, 15, 10, 0, 0, tzinfo=timezone.utc)
        with pytest.raises(ValueError, match="not the same as in progress"):
            plan.set_done(dt)

    def test_get_next_launch_time_and_empty(self):
        dt = datetime(2025, 3, 15, 10, 0, 0, tzinfo=timezone.utc)
        plan = TaskPlan.create(todo=[dt])
        assert plan.get_next_launch_time() == dt
        plan2 = TaskPlan.create()
        assert plan2.get_next_launch_time() is None

    def test_should_launch_past_due(self):
        dt = datetime(2020, 1, 1, 0, 0, 0, tzinfo=timezone.utc)
        plan = TaskPlan.create(todo=[dt])
        assert plan.should_launch() == dt

    def test_should_launch_future(self):
        dt = datetime(2030, 1, 1, 0, 0, 0, tzinfo=timezone.utc)
        plan = TaskPlan.create(todo=[dt])
        assert plan.should_launch() is None


# ---------------------------------------------------------------------------
# BaseTask / AdHocTask / ScheduledTask / PlannedTask
# ---------------------------------------------------------------------------

class TestBaseTask:
    def test_update_sets_fields(self):
        t = _make_scheduled_task()
        t.update(name="new-name", state=TaskState.DISABLED)
        assert t.name == "new-name"
        assert t.state == TaskState.DISABLED

    def test_is_dedicated(self):
        t = _make_scheduled_task()
        t.context_id = t.uuid
        assert t.is_dedicated() is True
        t.context_id = "other-context"
        assert t.is_dedicated() is False

    def test_get_next_run_minutes_returns_none_for_base_task(self):
        t = _make_adhoc_task()
        assert t.get_next_run_minutes() is None

class TestAdHocTask:
    def test_create(self):
        t = AdHocTask.create(
            name="adhoc",
            system_prompt="sys",
            prompt="prompt",
            token="1234567890123456789",
        )
        assert t.type == TaskType.AD_HOC
        assert t.token == "1234567890123456789"
        assert t.context_id == t.uuid

    def test_check_schedule_returns_false(self):
        t = _make_adhoc_task()
        assert t.check_schedule() is False


class TestScheduledTask:
    def test_create(self):
        sched = TaskSchedule(minute="0", hour="*", day="*", month="*", weekday="*")
        t = ScheduledTask.create(
            name="scheduled",
            system_prompt="sys",
            prompt="prompt",
            schedule=sched,
        )
        assert t.type == TaskType.SCHEDULED
        assert t.schedule.minute == "0"

    def test_get_next_run_and_check_schedule(self):
        t = _make_scheduled_task()
        next_run = t.get_next_run()
        assert next_run is None or isinstance(next_run, datetime)
        assert isinstance(t.check_schedule(frequency_seconds=86400), bool)


class TestPlannedTask:
    def test_check_schedule_true_when_past_due(self):
        dt = datetime(2020, 1, 1, 0, 0, 0, tzinfo=timezone.utc)
        t = _make_planned_task(todo_times=[dt])
        assert t.check_schedule() is True

    def test_check_schedule_false_when_future(self):
        dt = datetime(2030, 1, 1, 0, 0, 0, tzinfo=timezone.utc)
        t = _make_planned_task(todo_times=[dt])
        assert t.check_schedule() is False

    def test_get_next_run_returns_next_launch_time(self):
        dt = datetime(2025, 3, 20, 10, 0, 0, tzinfo=timezone.utc)
        t = _make_planned_task(todo_times=[dt])
        assert t.get_next_run() == dt


# ---------------------------------------------------------------------------
# SchedulerTaskList CRUD
# ---------------------------------------------------------------------------

class TestSchedulerTaskListCrud:
    @pytest.mark.asyncio
    async def test_add_task(self):
        task = _make_scheduled_task()
        tl = _make_task_list([])
        tl.save = AsyncMock(return_value=tl)
        await tl.add_task(task)
        assert task in tl.tasks
        tl.save.assert_called_once()

    @pytest.mark.asyncio
    async def test_remove_task_by_uuid(self):
        task = _make_scheduled_task()
        tl = _make_task_list([task])
        tl.save = AsyncMock(return_value=tl)
        await tl.remove_task_by_uuid(task.uuid)
        assert task not in tl.tasks

    @pytest.mark.asyncio
    async def test_remove_task_by_name(self):
        task = _make_scheduled_task(name="unique-name")
        tl = _make_task_list([task])
        tl.save = AsyncMock(return_value=tl)
        await tl.remove_task_by_name("unique-name")
        assert len(tl.tasks) == 0

    def test_get_task_by_uuid(self):
        task = _make_scheduled_task()
        tl = _make_task_list([task])
        assert tl.get_task_by_uuid(task.uuid) == task
        assert tl.get_task_by_uuid("nonexistent") is None

    def test_get_task_by_name(self):
        task = _make_scheduled_task(name="my-task")
        tl = _make_task_list([task])
        assert tl.get_task_by_name("my-task") == task
        assert tl.get_task_by_name("other") is None

    def test_find_task_by_name(self):
        t1 = _make_scheduled_task(name="Alpha Task")
        t2 = _make_scheduled_task(name="Beta Alpha")
        tl = _make_task_list([t1, t2])
        found = tl.find_task_by_name("alpha")
        assert len(found) == 2
        assert t1 in found and t2 in found

    def test_get_tasks_by_context_id(self):
        t1 = _make_scheduled_task()
        t1.context_id = "ctx-1"
        t2 = _make_scheduled_task()
        t2.context_id = "ctx-2"
        t3 = _make_scheduled_task()
        t3.context_id = "ctx-1"
        tl = _make_task_list([t1, t2, t3])
        by_ctx = tl.get_tasks_by_context_id("ctx-1")
        assert len(by_ctx) == 2

    @pytest.mark.asyncio
    async def test_update_task_by_uuid(self):
        task = _make_scheduled_task(name="old")
        tl = _make_task_list([task])
        tl.save = AsyncMock(return_value=tl)
        updated = await tl.update_task_by_uuid(task.uuid, lambda t: t.update(name="new"))
        assert updated is not None
        assert updated.name == "new"

# ---------------------------------------------------------------------------
# get_due_tasks
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
        assert task in due

    @pytest.mark.asyncio
    async def test_running_task_not_due(self):
        task = _make_scheduled_task(state=TaskState.RUNNING)
        tl = _make_task_list([task])
        with patch.object(ScheduledTask, "check_schedule", return_value=True):
            due = await tl.get_due_tasks()
        assert task not in due

    @pytest.mark.asyncio
    async def test_disabled_and_not_scheduled_not_due(self):
        task_disabled = _make_scheduled_task(state=TaskState.DISABLED)
        task_idle = _make_scheduled_task(state=TaskState.IDLE)
        tl = _make_task_list([task_disabled, task_idle])
        with patch.object(ScheduledTask, "check_schedule", side_effect=[True, False]):
            due = await tl.get_due_tasks()
        assert task_disabled not in due
        assert task_idle not in due


# ---------------------------------------------------------------------------
# _recover_stuck_tasks
# ---------------------------------------------------------------------------

class TestRecoverStuckTasks:
    @pytest.mark.asyncio
    async def test_orphaned_running_task_reset(self):
        task = _make_scheduled_task(name="orphaned", state=TaskState.RUNNING)
        sched = _make_scheduler([task])
        await sched._recover_stuck_tasks()
        sched.update_task.assert_called_once_with(task.uuid, state=TaskState.IDLE)

    @pytest.mark.asyncio
    async def test_alive_running_task_not_reset(self):
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
    async def test_idle_task_not_touched(self):
        task = _make_scheduled_task(name="idle", state=TaskState.IDLE)
        sched = _make_scheduler([task])
        await sched._recover_stuck_tasks()
        sched.update_task.assert_not_called()

    @pytest.mark.asyncio
    async def test_multiple_stuck_tasks(self):
        t1 = _make_scheduled_task(name="stuck-1", state=TaskState.RUNNING)
        t2 = _make_scheduled_task(name="stuck-2", state=TaskState.RUNNING)
        t3 = _make_scheduled_task(name="healthy", state=TaskState.IDLE)
        sched = _make_scheduler([t1, t2, t3])
        await sched._recover_stuck_tasks()
        assert sched.update_task.call_count == 2


# ---------------------------------------------------------------------------
# TaskScheduler run_task_by_uuid / run_task_by_name
# ---------------------------------------------------------------------------

class TestTaskSchedulerRun:
    @pytest.mark.asyncio
    async def test_run_task_by_uuid_not_found_raises(self):
        sched = _make_scheduler([])
        with pytest.raises(ValueError, match="not found"):
            await sched.run_task_by_uuid("nonexistent-uuid")

    @pytest.mark.asyncio
    async def test_run_task_by_uuid_already_running_raises(self):
        task = _make_scheduled_task(state=TaskState.RUNNING)
        sched = _make_scheduler([task])
        with pytest.raises(ValueError, match="already running"):
            await sched.run_task_by_uuid(task.uuid)

    @pytest.mark.asyncio
    async def test_run_task_by_uuid_disabled_raises(self):
        task = _make_scheduled_task(state=TaskState.DISABLED)
        sched = _make_scheduler([task])
        with pytest.raises(ValueError, match="disabled"):
            await sched.run_task_by_uuid(task.uuid)

    @pytest.mark.asyncio
    async def test_run_task_by_name_not_found_raises(self):
        sched = _make_scheduler([])
        with pytest.raises(ValueError, match="not found"):
            await sched.run_task_by_name("nonexistent")


# ---------------------------------------------------------------------------
# TaskScheduler cancel
# ---------------------------------------------------------------------------

class TestTaskSchedulerCancel:
    def test_cancel_running_task_not_found_returns_false(self):
        sched = _make_scheduler([])
        assert sched.cancel_running_task("nonexistent") is False

    def test_cancel_running_task_found_returns_true(self):
        task = _make_scheduled_task()
        sched = _make_scheduler([task])
        mock_deferred = MagicMock()
        sched._running_deferred_tasks[task.uuid] = mock_deferred
        result = sched.cancel_running_task(task.uuid)
        assert result is True
        mock_deferred.kill.assert_called_once()


# ---------------------------------------------------------------------------
# Serialization helpers
# ---------------------------------------------------------------------------

class TestSerializeDatetime:
    def test_serialize_datetime(self):
        dt = datetime(2025, 3, 15, 10, 30, 0, tzinfo=timezone.utc)
        result = serialize_datetime(dt)
        assert "2025" in result
        assert serialize_datetime(None) is None


class TestParseDatetime:
    def test_parse_datetime(self):
        s = "2025-03-15T10:30:00+00:00"
        result = parse_datetime(s)
        assert result is not None
        assert result.year == 2025
        assert parse_datetime(None) is None
        assert parse_datetime("") is None


class TestSerializeTaskSchedule:
    def test_serialize_task_schedule(self):
        s = TaskSchedule(minute="*/5", hour="*", day="*", month="*", weekday="*", timezone="UTC")
        d = serialize_task_schedule(s)
        assert d["minute"] == "*/5"
        assert d["hour"] == "*"
        assert d["timezone"] == "UTC"


class TestParseTaskSchedule:
    def test_parse_task_schedule(self):
        d = {"minute": "0", "hour": "9", "day": "*", "month": "*", "weekday": "*", "timezone": "America/New_York"}
        s = parse_task_schedule(d)
        assert s.minute == "0"
        assert s.hour == "9"
        assert s.timezone == "America/New_York"
        d_empty = {}
        s2 = parse_task_schedule(d_empty)
        assert s2.minute == "*"
        assert s2.hour == "*"


class TestSerializeTaskPlan:
    def test_serialize_task_plan(self):
        dt = datetime(2025, 3, 15, 10, 0, 0, tzinfo=timezone.utc)
        plan = TaskPlan.create(todo=[dt])
        d = serialize_task_plan(plan)
        assert "todo" in d
        assert len(d["todo"]) == 1
        assert d["in_progress"] is None


class TestParseTaskPlan:
    def test_parse_task_plan_empty_and_none(self):
        plan = parse_task_plan({})
        assert plan.todo == []
        assert plan.in_progress is None
        assert plan.done == []
        plan2 = parse_task_plan(None)
        assert plan2.todo == []
        assert plan2.in_progress is None


class TestSerializeTask:
    def test_serialize_all_task_types(self):
        t_sched = _make_scheduled_task()
        d = serialize_task(t_sched)
        assert d["uuid"] == t_sched.uuid
        assert d["type"] == "scheduled"
        assert "schedule" in d
        t_adhoc = _make_adhoc_task()
        d2 = serialize_task(t_adhoc)
        assert d2["type"] == "adhoc"
        assert "token" in d2
        t_planned = _make_planned_task()
        d3 = serialize_task(t_planned)
        assert d3["type"] == "planned"
        assert "plan" in d3


class TestSerializeTasks:
    def test_serialize_tasks_list(self):
        t1 = _make_scheduled_task(name="a")
        t2 = _make_adhoc_task(name="b")
        result = serialize_tasks([t1, t2])
        assert len(result) == 2
        assert result[0]["name"] == "a"
        assert result[1]["name"] == "b"


class TestDeserializeTask:
    _NOW = datetime.now(timezone.utc).isoformat()

    def test_deserialize_scheduled_task(self):
        d = {
            "type": "scheduled",
            "uuid": "u1",
            "name": "sched",
            "system_prompt": "sys",
            "prompt": "prompt",
            "schedule": {"minute": "0", "hour": "*", "day": "*", "month": "*", "weekday": "*", "timezone": "UTC"},
            "state": "idle",
            "created_at": self._NOW,
            "updated_at": self._NOW,
        }
        t = deserialize_task(d)
        assert isinstance(t, ScheduledTask)
        assert t.name == "sched"

    def test_deserialize_adhoc_task(self):
        d = {
            "type": "adhoc",
            "uuid": "u2",
            "name": "adhoc",
            "system_prompt": "sys",
            "prompt": "prompt",
            "token": "1234567890123456789",
            "state": "idle",
            "created_at": self._NOW,
            "updated_at": self._NOW,
        }
        t = deserialize_task(d)
        assert isinstance(t, AdHocTask)
        assert t.token == "1234567890123456789"

    def test_deserialize_planned_task(self):
        d = {
            "type": "planned",
            "uuid": "u4",
            "name": "planned",
            "system_prompt": "sys",
            "prompt": "prompt",
            "plan": {"todo": [], "in_progress": None, "done": []},
            "state": "idle",
            "created_at": self._NOW,
            "updated_at": self._NOW,
        }
        t = deserialize_task(d)
        assert isinstance(t, PlannedTask)

    def test_deserialize_unknown_type_raises(self):
        d = {"type": "unknown", "uuid": "u5", "name": "x", "system_prompt": "", "prompt": ""}
        with pytest.raises(ValueError, match="Unknown task type"):
            deserialize_task(d)


# ---------------------------------------------------------------------------
# TaskScheduler serialize_all_tasks / serialize_task
# ---------------------------------------------------------------------------

class TestTaskSchedulerSerialize:
    def test_serialize_all_tasks(self):
        t = _make_scheduled_task()
        sched = _make_scheduler([t])
        result = sched.serialize_all_tasks()
        assert len(result) == 1
        assert result[0]["name"] == t.name

    def test_serialize_task_by_id(self):
        t = _make_scheduled_task()
        sched = _make_scheduler([t])
        result = sched.serialize_task(t.uuid)
        assert result is not None
        assert result["uuid"] == t.uuid
        assert sched.serialize_task("nonexistent") is None


# ---------------------------------------------------------------------------
# Edge cases
# ---------------------------------------------------------------------------

class TestEdgeCases:
    def test_task_plan_set_done_already_in_done_raises(self):
        dt = datetime(2025, 3, 15, 10, 0, 0, tzinfo=timezone.utc)
        plan = TaskPlan.create(in_progress=dt, done=[dt])
        with pytest.raises(ValueError, match="already in done list"):
            plan.set_done(dt)
