"""Isolate persisted tasks whose cron schedule no longer parses.

A task saved before cron validation existed can carry a field the current parser
rejects (for example ``day: "100"``). Evaluated eagerly, such a task either kills
the whole UI state snapshot (``serialize_task`` -> ``get_next_run``) or aborts the
scheduler tick for every other due task (``get_due_tasks`` -> ``check_schedule``).
"""

from __future__ import annotations

from datetime import datetime, timezone

import pytest

from helpers import task_scheduler as scheduler


def _schedule(**overrides: str) -> scheduler.TaskSchedule:
    data = {
        "minute": "*",
        "hour": "*",
        "day": "*",
        "month": "*",
        "weekday": "*",
        "timezone": "UTC",
    }
    return scheduler.TaskSchedule(**{**data, **overrides})


def _task(name: str, **overrides: str) -> scheduler.ScheduledTask:
    return scheduler.ScheduledTask(
        name=name,
        system_prompt="",
        prompt=name,
        schedule=_schedule(**overrides),
    )


@pytest.fixture(autouse=True)
def frozen_now(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        scheduler,
        "_now",
        lambda: datetime(2026, 10, 30, 6, 0, 30, tzinfo=timezone.utc),
    )


def test_serialize_task_reports_missing_next_run_for_invalid_schedule() -> None:
    broken = _task("legacy-broken", day="100")

    payload = scheduler.serialize_task(broken)

    assert payload["uuid"] == broken.uuid
    assert payload["name"] == "legacy-broken"
    assert payload["type"] == "scheduled"
    assert payload["schedule"]["day"] == "100"
    assert payload["next_run"] is None


def test_serialize_tasks_keeps_healthy_entries_alongside_invalid_schedule() -> None:
    broken = _task("legacy-broken", day="100")
    healthy = _task("healthy")

    payloads = scheduler.serialize_tasks([broken, healthy])

    assert [payload["name"] for payload in payloads] == ["legacy-broken", "healthy"]
    assert payloads[0]["next_run"] is None
    assert payloads[1]["next_run"] is not None


@pytest.mark.asyncio
async def test_get_due_tasks_skips_invalid_schedule_and_returns_healthy_tasks(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    async def keep_tasks(self: scheduler.SchedulerTaskList) -> scheduler.SchedulerTaskList:
        return self

    monkeypatch.setattr(scheduler.SchedulerTaskList, "reload", keep_tasks)
    task_list = scheduler.SchedulerTaskList(
        tasks=[_task("legacy-broken", day="100"), _task("healthy")]
    )

    due = await task_list.get_due_tasks()

    assert [task.name for task in due] == ["healthy"]
