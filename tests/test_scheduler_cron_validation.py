"""Reject invalid cron schedules before changing saved tasks."""

import asyncio
from datetime import UTC, datetime
from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest

from helpers import task_scheduler as scheduler
from plugins._scheduler.api.scheduler_task_create import SchedulerTaskCreate
from plugins._scheduler.api.scheduler_task_update import SchedulerTaskUpdate

INVALID_FIELDS = [
    ("minute", "60"),
    ("hour", "24"),
    ("day", "32"),
    ("month", "13"),
    ("weekday", "8"),
    ("minute", "*/0"),
    ("minute", "not-a-minute"),
]


def schedule_data(**overrides):
    return {
        "minute": "*",
        "hour": "*",
        "day": "*",
        "month": "*",
        "weekday": "*",
    } | overrides


@pytest.fixture(params=["json", "yaml"])
def runtime(request, monkeypatch, tmp_path):
    monkeypatch.setattr(scheduler, "SCHEDULER_FOLDER", str(tmp_path))
    monkeypatch.setattr(
        scheduler, "_now", lambda: datetime(2026, 10, 30, 6, 0, 30, tzinfo=UTC)
    )
    monkeypatch.setattr(
        "helpers.state_monitor_integration.mark_dirty_all", lambda **kwargs: None
    )
    task = scheduler.ScheduledTask.create(
        name="Existing task",
        system_prompt="",
        prompt="Keep this prompt",
        schedule=scheduler.TaskSchedule(**schedule_data(timezone="UTC")),
    )
    tasks = scheduler.SchedulerTaskList(tasks=[task])
    path = tmp_path / f"tasks.{request.param}"
    path.write_text(
        tasks.model_dump_json()
        if request.param == "json"
        else scheduler.yaml.from_json(tasks.model_dump_json()),
        encoding="utf-8",
    )
    engine = object.__new__(scheduler.TaskScheduler)
    engine._tasks = tasks
    engine._get_chat_context = AsyncMock()
    monkeypatch.setattr(scheduler.TaskScheduler, "get", lambda: engine)
    return SimpleNamespace(engine=engine, path=path, task=task)


@pytest.mark.parametrize("field,value", INVALID_FIELDS)
@pytest.mark.parametrize("as_string", [False, True])
def test_create_invalid_schedule_does_not_persist(runtime, field, value, as_string):
    schedule = schedule_data(**{field: value})
    if as_string:
        schedule = " ".join(schedule.values())
    before = runtime.path.read_bytes()
    with pytest.raises(ValueError):
        asyncio.run(
            SchedulerTaskCreate(None, None).process(
                {
                    "name": "Invalid task",
                    "prompt": "Never save",
                    "schedule": schedule,
                },
                None,
            )
        )
    assert runtime.path.read_bytes() == before
    assert [task.uuid for task in runtime.engine.get_tasks()] == [runtime.task.uuid]
    runtime.engine._get_chat_context.assert_not_awaited()
    due = asyncio.run(runtime.engine._tasks.get_due_tasks())
    assert [task.uuid for task in due] == [runtime.task.uuid]


@pytest.mark.parametrize("field,value", INVALID_FIELDS)
def test_update_invalid_schedule_preserves_other_fields_and_storage(
    runtime, field, value
):
    before = runtime.path.read_bytes()
    original = runtime.task.model_dump()
    with pytest.raises(ValueError):
        asyncio.run(
            SchedulerTaskUpdate(None, None).process(
                {
                    "task_id": runtime.task.uuid,
                    "name": "Do not rename",
                    "prompt": "Do not replace",
                    "schedule": schedule_data(**{field: value}),
                },
                None,
            )
        )
    assert runtime.path.read_bytes() == before
    assert runtime.engine.get_task_by_uuid(runtime.task.uuid).model_dump() == original
    due = asyncio.run(runtime.engine._tasks.get_due_tasks())
    assert [task.uuid for task in due] == [runtime.task.uuid]


@pytest.mark.parametrize(
    "fields",
    [
        {},
        {"minute": "*/15"},
        {"hour": "9-17", "weekday": "MON-FRI"},
        {"minute": "5,35"},
        {"weekday": "7"},
        {"month": "JAN"},
    ],
)
def test_valid_schedules_still_create_and_update(runtime, fields):
    schedule = schedule_data(timezone="UTC", **fields)
    created = asyncio.run(
        SchedulerTaskCreate(None, None).process(
            {
                "name": "Valid task",
                "prompt": "Run later",
                "schedule": schedule,
            },
            None,
        )
    )
    assert created["ok"]
    updated = asyncio.run(
        SchedulerTaskUpdate(None, None).process(
            {
                "task_id": runtime.task.uuid,
                "schedule": schedule,
                "name": "Renamed",
            },
            None,
        )
    )
    assert updated["ok"]
    asyncio.run(runtime.engine.reload())
    assert runtime.engine.get_task_by_uuid(runtime.task.uuid).name == "Renamed"
    assert runtime.engine.get_task_by_uuid(created["task"]["uuid"]) is not None


def test_prompt_only_update_does_not_validate_legacy_schedule(runtime):
    # Loading and repairing existing storage remains possible; this change only
    # guards newly supplied schedules rather than tightening model loading.
    runtime.task.schedule.minute = "60"
    asyncio.run(runtime.engine.save())
    updated = asyncio.run(
        runtime.engine.update_task(runtime.task.uuid, prompt="Repair later")
    )
    assert updated.prompt == "Repair later"
    assert updated.schedule.minute == "60"
