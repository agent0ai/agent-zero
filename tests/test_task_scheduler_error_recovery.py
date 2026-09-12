import asyncio
from datetime import datetime, timezone
from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from helpers import task_scheduler
from helpers.task_scheduler import (
    AdHocTask,
    ScheduledTask,
    SchedulerTaskList,
    TaskSchedule,
    TaskState,
)


class RecordingPrintStyle:
    calls: list[tuple[str, str]] = []

    @staticmethod
    def error(message):
        RecordingPrintStyle.calls.append(("error", message))

    @staticmethod
    def info(message):
        RecordingPrintStyle.calls.append(("info", message))

    @staticmethod
    def warning(message):
        RecordingPrintStyle.calls.append(("warning", message))

    @staticmethod
    def success(message):
        RecordingPrintStyle.calls.append(("success", message))


class FakeScheduler:
    """In-memory TaskScheduler stand-in; never touches live tasks.json."""

    def __init__(self, tasks):
        self.tasks = tasks
        self.saved = 0

    async def reload(self):
        return None

    def get_task_by_uuid(self, task_uuid):
        return next((t for t in self.tasks if t.uuid == task_uuid), None)

    async def update_task(self, task_uuid, **params):
        task = self.get_task_by_uuid(task_uuid)
        if task is None:
            return None
        task.update(**params)
        return task

    async def save(self):
        self.saved += 1
        return None


class StaticTaskList(SchedulerTaskList):
    """SchedulerTaskList whose reload is a no-op, for in-memory due-task tests."""

    async def reload(self):
        return self


def make_scheduled_task(
    name="watcher",
    state=TaskState.IDLE,
    last_run=None,
    consecutive_failures=0,
):
    return ScheduledTask(
        name=name,
        system_prompt="",
        prompt="run",
        schedule=TaskSchedule(minute="*", hour="*", day="*", month="*", weekday="*", timezone="UTC"),
        state=state,
        last_run=last_run,
        consecutive_failures=consecutive_failures,
    )


def fixed_now(dt):
    return lambda: dt


# --- (a) ERROR tasks become eligible again at their next cron slot ---


def test_error_task_not_retryable_within_failed_slot(monkeypatch):
    monkeypatch.setattr(task_scheduler, "_now", fixed_now(datetime(2026, 9, 8, 12, 0, 45, tzinfo=timezone.utc)))
    task = make_scheduled_task(
        state=TaskState.ERROR,
        last_run=datetime(2026, 9, 8, 12, 0, 30, tzinfo=timezone.utc),
    )
    assert task.is_retry_due() is False


def test_error_task_retryable_at_next_cron_slot(monkeypatch):
    monkeypatch.setattr(task_scheduler, "_now", fixed_now(datetime(2026, 9, 8, 12, 1, 5, tzinfo=timezone.utc)))
    task = make_scheduled_task(
        state=TaskState.ERROR,
        last_run=datetime(2026, 9, 8, 12, 0, 30, tzinfo=timezone.utc),
    )
    assert task.is_retry_due() is True


def test_due_tasks_include_error_task_once_slot_arrives(monkeypatch):
    task = make_scheduled_task(
        state=TaskState.ERROR,
        last_run=datetime(2026, 9, 8, 12, 0, 30, tzinfo=timezone.utc),
    )
    task_list = StaticTaskList(tasks=[task])

    monkeypatch.setattr(task_scheduler, "_now", fixed_now(datetime(2026, 9, 8, 12, 0, 45, tzinfo=timezone.utc)))
    assert asyncio.run(task_list.get_due_tasks()) == []

    monkeypatch.setattr(task_scheduler, "_now", fixed_now(datetime(2026, 9, 8, 12, 1, 5, tzinfo=timezone.utc)))
    due = asyncio.run(task_list.get_due_tasks())
    assert [t.uuid for t in due] == [task.uuid]


def test_disabled_task_never_auto_fires(monkeypatch):
    monkeypatch.setattr(task_scheduler, "_now", fixed_now(datetime(2026, 9, 8, 12, 5, 5, tzinfo=timezone.utc)))
    task = make_scheduled_task(
        state=TaskState.DISABLED,
        last_run=datetime(2026, 9, 8, 12, 0, 30, tzinfo=timezone.utc),
    )
    task_list = StaticTaskList(tasks=[task])
    assert asyncio.run(task_list.get_due_tasks()) == []


def test_adhoc_error_task_never_auto_retries(monkeypatch):
    monkeypatch.setattr(task_scheduler, "_now", fixed_now(datetime(2026, 9, 8, 12, 5, 5, tzinfo=timezone.utc)))
    task = AdHocTask.create(name="adhoc", system_prompt="", prompt="run", token="123")
    task.update(state=TaskState.ERROR, last_run=datetime(2026, 9, 8, 12, 0, 30, tzinfo=timezone.utc))
    assert task.is_retry_due() is False


# --- (b) failure cap -> DISABLED with loud logging ---


def run_on_error(task, error="boom"):
    asyncio.run(task.on_error(error))


def test_below_cap_failure_stays_error_and_logs_loudly(monkeypatch):
    RecordingPrintStyle.calls.clear()
    task = make_scheduled_task(name="github-watch")
    fake = FakeScheduler([task])
    monkeypatch.setattr(task_scheduler, "PrintStyle", RecordingPrintStyle)
    monkeypatch.setattr(task_scheduler.TaskScheduler, "get", classmethod(lambda cls: fake))

    run_on_error(task)

    assert task.state == TaskState.ERROR
    assert task.consecutive_failures == 1
    errors = [msg for level, msg in RecordingPrintStyle.calls if level == "error"]
    assert any("github-watch" in msg and "1/3" in msg and "retry at its next scheduled slot" in msg for msg in errors)


def test_three_consecutive_failures_disable_task_loudly(monkeypatch):
    RecordingPrintStyle.calls.clear()
    task = make_scheduled_task(name="gate-heartbeat")
    fake = FakeScheduler([task])
    monkeypatch.setattr(task_scheduler, "PrintStyle", RecordingPrintStyle)
    monkeypatch.setattr(task_scheduler.TaskScheduler, "get", classmethod(lambda cls: fake))

    run_on_error(task, "Connection error 1")
    run_on_error(task, "Connection error 2")
    assert task.state == TaskState.ERROR
    assert task.consecutive_failures == 2

    run_on_error(task, "Connection error 3")
    assert task.state == TaskState.DISABLED
    assert task.consecutive_failures == 3
    errors = [msg for level, msg in RecordingPrintStyle.calls if level == "error"]
    assert any(
        "gate-heartbeat" in msg
        and task.uuid in msg
        and "disabled after 3 consecutive failures" in msg
        and "Connection error 3" in msg
        for msg in errors
    )


# --- (c) success resets the failure counter ---


def test_success_resets_failure_counter(monkeypatch):
    RecordingPrintStyle.calls.clear()
    task = make_scheduled_task(state=TaskState.ERROR, consecutive_failures=2)
    fake = FakeScheduler([task])
    monkeypatch.setattr(task_scheduler, "PrintStyle", RecordingPrintStyle)
    monkeypatch.setattr(task_scheduler.TaskScheduler, "get", classmethod(lambda cls: fake))

    asyncio.run(task.on_success("ok"))

    assert task.state == TaskState.IDLE
    assert task.consecutive_failures == 0


# --- (d) IDLE semantics unchanged ---


def test_idle_task_due_only_when_schedule_matches(monkeypatch):
    due_task = make_scheduled_task(name="every-minute")
    daily_task = ScheduledTask(
        name="daily",
        system_prompt="",
        prompt="run",
        schedule=TaskSchedule(minute="0", hour="13", day="*", month="*", weekday="*", timezone="UTC"),
    )
    task_list = StaticTaskList(tasks=[due_task, daily_task])

    # 12:05:10 UTC: every-minute task is due, 13:00 daily task is not
    monkeypatch.setattr(task_scheduler, "_now", fixed_now(datetime(2026, 9, 8, 12, 5, 10, tzinfo=timezone.utc)))
    due = asyncio.run(task_list.get_due_tasks())
    assert [t.uuid for t in due] == [due_task.uuid]


def test_error_task_does_not_fire_via_idle_check_schedule_path(monkeypatch):
    # ERROR task whose cron matches right now, but whose retry slot has not
    # arrived, must stay excluded: only is_retry_due unlocks ERROR tasks.
    task = make_scheduled_task(
        state=TaskState.ERROR,
        last_run=datetime(2026, 9, 8, 12, 5, 5, tzinfo=timezone.utc),
    )
    task_list = StaticTaskList(tasks=[task])

    monkeypatch.setattr(task_scheduler, "_now", fixed_now(datetime(2026, 9, 8, 12, 5, 10, tzinfo=timezone.utc)))
    assert task.check_schedule() is True  # cron matches now
    assert task.is_retry_due() is False  # next slot (12:06) not arrived
    assert asyncio.run(task_list.get_due_tasks()) == []


# --- serialization round-trip of the new field ---


def test_consecutive_failures_serialization_roundtrip():
    task = make_scheduled_task(state=TaskState.ERROR, consecutive_failures=2)
    data = task_scheduler.serialize_task(task)
    assert data["consecutive_failures"] == 2
    restored = task_scheduler.deserialize_task(dict(data))
    assert restored.consecutive_failures == 2
    assert restored.state == TaskState.ERROR


def test_legacy_task_dict_without_counter_defaults_to_zero():
    task = make_scheduled_task()
    data = task_scheduler.serialize_task(task)
    del data["consecutive_failures"]
    restored = task_scheduler.deserialize_task(dict(data))
    assert restored.consecutive_failures == 0
