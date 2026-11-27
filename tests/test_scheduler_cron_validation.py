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
    ("day", ""),
    ("day", "   "),
]

EMPTY_FIELD_CASES = [
    ("minute", ""),
    ("hour", ""),
    ("day", ""),
    ("day", "   "),
    ("month", ""),
    ("weekday", ""),
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
    now = datetime(2026, 10, 30, 6, 0, 30, tzinfo=UTC)
    anchor = datetime(2026, 10, 30, 5, 59, 0, tzinfo=UTC)
    monkeypatch.setattr(scheduler, "_now", lambda: now)
    monkeypatch.setattr(
        "helpers.state_monitor_integration.mark_dirty_all", lambda **kwargs: None
    )
    task = scheduler.ScheduledTask.create(
        name="Existing task",
        system_prompt="",
        prompt="Keep this prompt",
        schedule=scheduler.TaskSchedule(**schedule_data(timezone="UTC")),
    )
    task.created_at = anchor
    task.updated_at = anchor
    task.schedule_anchor = anchor
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


@pytest.mark.parametrize("field,value", EMPTY_FIELD_CASES)
def test_empty_cron_field_error_guides_wildcard_usage(runtime, field, value):
    before = runtime.path.read_bytes()
    original = runtime.task.model_dump()

    with pytest.raises(ValueError) as create_exc:
        asyncio.run(
            SchedulerTaskCreate(None, None).process(
                {
                    "name": "Empty field create",
                    "prompt": "Never save",
                    "schedule": schedule_data(**{field: value}),
                },
                None,
            )
        )
    create_msg = str(create_exc.value)
    assert field in create_msg
    assert '"*"' in create_msg

    with pytest.raises(ValueError) as update_exc:
        asyncio.run(
            SchedulerTaskUpdate(None, None).process(
                {
                    "task_id": runtime.task.uuid,
                    "name": "Do not rename",
                    "schedule": schedule_data(**{field: value}),
                },
                None,
            )
        )
    update_msg = str(update_exc.value)
    assert field in update_msg
    assert '"*"' in update_msg

    assert runtime.path.read_bytes() == before
    assert runtime.engine.get_task_by_uuid(runtime.task.uuid).model_dump() == original


def test_empty_string_slot_and_whitespace_token_do_not_shift_fields(runtime):
    before = runtime.path.read_bytes()

    with pytest.raises(ValueError) as str_exc:
        asyncio.run(
            SchedulerTaskCreate(None, None).process(
                {
                    "name": "Double space cron",
                    "prompt": "Never save",
                    "schedule": "* *  * *",
                },
                None,
            )
        )
    assert "day" in str(str_exc.value)
    assert '"*"' in str(str_exc.value)

    with pytest.raises(ValueError) as shift_exc:
        asyncio.run(
            SchedulerTaskCreate(None, None).process(
                {
                    "name": "Shifted columns",
                    "prompt": "Never save",
                    "schedule": schedule_data(minute="0 1", day=""),
                },
                None,
            )
        )
    assert "day" in str(shift_exc.value)
    assert '"*"' in str(shift_exc.value)

    with pytest.raises(ValueError) as ws_exc:
        asyncio.run(
            SchedulerTaskCreate(None, None).process(
                {
                    "name": "Whitespace token",
                    "prompt": "Never save",
                    "schedule": schedule_data(minute="0 1"),
                },
                None,
            )
        )
    assert "minute" in str(ws_exc.value)
    assert '"*"' in str(ws_exc.value)
    assert runtime.path.read_bytes() == before
