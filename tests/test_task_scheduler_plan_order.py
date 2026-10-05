from __future__ import annotations

import asyncio
from datetime import datetime, timedelta, timezone, tzinfo
from pathlib import Path
import sys
from types import SimpleNamespace
from unittest.mock import AsyncMock
from zoneinfo import ZoneInfo

import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from helpers import task_scheduler
from helpers.task_scheduler import PlannedTask, SchedulerTaskList, TaskPlan


NOW = datetime(2026, 10, 5, 12, tzinfo=timezone.utc)
EARLIER = NOW - timedelta(hours=2)
LATER = NOW + timedelta(days=1)


@pytest.fixture(autouse=True)
def fixed_now(monkeypatch):
    monkeypatch.setattr(task_scheduler, "_now", lambda: NOW)


def make_task(plan):
    return PlannedTask(
        name="Planned reminders",
        system_prompt="",
        prompt="Prepare the requested summary",
        plan=plan,
        created_at=NOW,
        updated_at=NOW,
    )


@pytest.mark.parametrize("create_plan", [TaskPlan.create, TaskPlan])
def test_next_launch_is_earliest_without_reordering_input(create_plan):
    todo = [LATER, EARLIER]
    plan = create_plan(todo=todo)

    assert plan.get_next_launch_time() == EARLIER
    assert plan.should_launch() == EARLIER
    assert todo == [LATER, EARLIER]
    assert plan.todo == [LATER, EARLIER]


def test_next_launch_compares_absolute_instants_across_offsets():
    earlier = datetime(2026, 10, 5, 14, tzinfo=timezone(timedelta(hours=5)))
    later = datetime(2026, 10, 5, 10, tzinfo=timezone.utc)
    plan = TaskPlan(todo=[later, earlier])

    assert plan.get_next_launch_time() == earlier
    assert plan.should_launch() == earlier


@pytest.mark.parametrize("todo", [[], [LATER], [LATER + timedelta(days=1), LATER]])
def test_empty_or_future_plan_is_not_due(todo):
    plan = TaskPlan(todo=todo)

    assert plan.get_next_launch_time() == (LATER if todo else None)
    assert plan.should_launch() is None


@pytest.mark.parametrize("extension", ["json", "yaml"])
def test_restored_unsorted_plan_reports_and_runs_earliest_time(monkeypatch, extension):
    original = SchedulerTaskList(tasks=[make_task(TaskPlan(todo=[LATER, EARLIER]))])
    content = original.model_dump_json()
    if extension == "yaml":
        content = task_scheduler.yaml.from_json(content)
    monkeypatch.setattr(task_scheduler, "read_file", lambda _path: content)

    restored = SchedulerTaskList._load(f"tasks.{extension}")
    task = restored.tasks[0]

    assert task.get_next_run() == EARLIER
    assert task.get_next_run_minutes() == -120
    assert task.check_schedule() is True
    assert task.plan.todo == [LATER, EARLIER]


def test_unsorted_plan_completes_selected_time_then_advances(monkeypatch):
    task = make_task(TaskPlan(todo=[LATER, EARLIER]))
    scheduler = SimpleNamespace(
        reload=AsyncMock(),
        update_task=AsyncMock(),
        save=AsyncMock(),
    )
    monkeypatch.setattr(task_scheduler.TaskScheduler, "get", lambda: scheduler)

    asyncio.run(task.on_run())

    assert task.plan.in_progress == EARLIER
    assert task.plan.todo == [LATER]
    assert task.plan.done == []

    asyncio.run(task.on_finish())

    assert task.plan.in_progress is None
    assert task.plan.done == [EARLIER]
    assert task.plan.todo == [LATER]
    assert task.get_next_run() == LATER
    assert task.check_schedule() is False
    scheduler.update_task.assert_any_await(task.uuid, plan=task.plan)
    scheduler.save.assert_awaited_once()


def test_sorted_plan_still_advances_in_chronological_order():
    plan = TaskPlan(todo=[EARLIER, LATER])

    assert plan.get_next_launch_time() == EARLIER
    plan.set_in_progress(EARLIER)
    plan.set_done(EARLIER)
    assert plan.get_next_launch_time() == LATER
    assert plan.done == [EARLIER]


@pytest.mark.parametrize("create_plan", [TaskPlan.create, TaskPlan])
@pytest.mark.parametrize("reverse", [False, True])
@pytest.mark.parametrize("later_minute", [15, 30])
def test_next_launch_orders_dst_folds_by_instant(create_plan, reverse, later_minute):
    zone = ZoneInfo("America/New_York")
    earlier = datetime(2026, 11, 1, 1, 30, tzinfo=zone, fold=0)
    later = datetime(2026, 11, 1, 1, later_minute, tzinfo=zone, fold=1)
    todo = [later, earlier] if reverse else [earlier, later]
    plan = create_plan(todo=todo)

    assert plan.get_next_launch_time() is earlier
    assert all(actual is expected for actual, expected in zip(plan.todo, todo))
    assert todo[0] is (later if reverse else earlier)


@pytest.mark.parametrize("boundary, offset", [
    (datetime.min, timedelta(hours=1)),
    (datetime.max, -timedelta(hours=1)),
])
def test_next_launch_preserves_precision_at_datetime_boundaries(boundary, offset):
    boundary = boundary.replace(tzinfo=timezone(offset))
    earlier = boundary if boundary.year == 1 else boundary - timedelta(microseconds=1)
    later = earlier + timedelta(microseconds=1)
    plan = TaskPlan(todo=[later, earlier])

    assert plan.get_next_launch_time() is earlier
    assert plan.todo[0] is later


class OffsetlessTimezone(tzinfo):
    def utcoffset(self, dt):
        return None


@pytest.mark.parametrize("zone", [None, OffsetlessTimezone()])
def test_next_launch_keeps_naive_datetime_comparison(zone):
    earlier = datetime(2026, 10, 5, 10, tzinfo=zone)
    later = datetime(2026, 10, 6, 10, tzinfo=zone)
    plan = TaskPlan(todo=[later, earlier])

    assert plan.get_next_launch_time() is earlier
    assert plan.todo[0] is later
