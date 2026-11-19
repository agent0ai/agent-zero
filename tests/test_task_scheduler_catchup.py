"""Recurring tasks retain missed runs without replaying a backlog."""
import asyncio
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest

from agent import AgentContext
from helpers import plugins, task_scheduler as scheduler
from test_task_scheduler_recovery import runtime

UTC = timezone.utc
MONDAY = datetime(2026, 11, 16, 9, tzinfo=UTC)


def recurring(**kwargs):
    created = kwargs.pop("created_at", MONDAY-timedelta(days=7))
    return scheduler.ScheduledTask(
        name="Catch-up", system_prompt="", prompt="Run once", plugin_name=kwargs.pop("plugin_name", "test_maintenance"),
        created_at=created, updated_at=kwargs.pop("updated_at", created),
        schedule=kwargs.pop('schedule', scheduler.TaskSchedule(
            minute='0', hour='9', day='*', month='*', weekday='1', timezone='UTC')),
        **kwargs,
    )


def test_missed_weeks_collapse_to_one_run_and_repeated_checks_do_not_consume_it(monkeypatch):
    now = MONDAY + timedelta(days=22)
    monkeypatch.setattr(scheduler, '_now', lambda: now)
    task = recurring()
    assert task.get_next_run() == MONDAY
    assert task.check_schedule() and task.check_schedule()
    task.update(state=scheduler.TaskState.RUNNING)
    task.update(state=scheduler.TaskState.IDLE, last_run=now)
    assert not task.check_schedule()
    assert task.get_next_run() == MONDAY + timedelta(days=28)


def test_due_boundary_and_repeated_ticks_within_the_same_minute(monkeypatch):
    task = recurring()
    now = MONDAY - timedelta(microseconds=1)
    monkeypatch.setattr(scheduler, '_now', lambda: now)
    assert not task.check_schedule()
    now = MONDAY
    assert task.check_schedule()
    task.update(state=scheduler.TaskState.RUNNING)
    task.update(state=scheduler.TaskState.IDLE, last_run=now)
    now += timedelta(seconds=10)
    assert not task.check_schedule()


def test_editing_metadata_keeps_overdue_run_but_rescheduling_resets_it(monkeypatch):
    now = MONDAY + timedelta(days=1)
    monkeypatch.setattr(scheduler, '_now', lambda: now)
    task = recurring(plugin_name=None)
    task.update(name='Renamed', prompt='Changed instructions', schedule=task.schedule.model_copy())
    assert task.check_schedule()
    task.update(schedule=task.schedule.model_copy(update={'hour':'10'}))
    assert not task.check_schedule()
    assert task.get_next_run() == MONDAY + timedelta(days=7, hours=1)


def test_reenable_does_not_replay_disabled_period(monkeypatch):
    now = MONDAY - timedelta(days=1)
    monkeypatch.setattr(scheduler, '_now', lambda: now)
    task = recurring()
    task.update(state=scheduler.TaskState.DISABLED)
    now = MONDAY + timedelta(days=15)
    task.update(state=scheduler.TaskState.IDLE)
    assert not task.check_schedule()
    assert task.get_next_run() == MONDAY + timedelta(days=21)


@pytest.mark.parametrize('last_run', [None, MONDAY + timedelta(hours=1)])
def test_legacy_tasks_use_saved_timestamps_and_preserve_anchor_in_serializers(monkeypatch, last_run):
    now = MONDAY + timedelta(days=2)
    monkeypatch.setattr(scheduler, '_now', lambda: now)
    data = recurring(last_run=last_run).model_dump(mode='json')
    data.pop('schedule_anchor', None)
    task = scheduler.ScheduledTask.model_validate(data)
    assert task.check_schedule() == (last_run is None)
    restored = scheduler.deserialize_task(scheduler.serialize_task(task))
    assert restored.schedule_anchor == task.schedule_anchor
    assert restored.get_next_run() == task.get_next_run()


@pytest.mark.parametrize('anchor,expected', [
    ('2026-03-28T08:30:00+00:00', '2026-03-29T07:30:00+00:00'),
    ('2026-10-24T07:30:00+00:00', '2026-10-25T08:30:00+00:00'),
])
def test_catchup_uses_schedule_timezone_across_daylight_saving_changes(monkeypatch, anchor, expected):
    anchor, expected = datetime.fromisoformat(anchor), datetime.fromisoformat(expected)
    task = recurring(schedule=scheduler.TaskSchedule(
        minute='30', hour='9', day='*', month='*', weekday='*', timezone='Europe/Rome'))
    task.created_at = task.updated_at = anchor
    task = scheduler.ScheduledTask.model_validate({**task.model_dump(), 'schedule_anchor':anchor})
    monkeypatch.setattr(scheduler, '_now', lambda: expected + timedelta(hours=6))
    assert task.get_next_run() == expected
    assert task.check_schedule()


@pytest.mark.parametrize('file_format', ['json', 'yaml'])
@pytest.mark.parametrize('native', [False, True])
def test_tick_catches_up_after_reload_once_for_agents_and_plugins(runtime, monkeypatch, file_format, native):
    now = runtime.now
    task = recurring(created_at=now-timedelta(days=30), plugin_name='test_maintenance' if native else None)
    asyncio.run(runtime.engine.add_task(task))
    if file_format == 'yaml':
        path = Path(scheduler.SCHEDULER_FOLDER, 'tasks.json')
        path.rename(path.with_suffix('.yaml'))
    calls = []
    if native:
        monkeypatch.setattr(plugins, 'get_toggle_state', lambda name: 'enabled')
        monkeypatch.setattr(plugins, 'call_plugin_hook', lambda *args, **kwargs: calls.append('run') or 'Done')
    else:
        context = AgentContext.get(task.context_id)
        runtime.model(context.agent0, 'Done')
    asyncio.run(runtime.engine.reload())
    asyncio.run(runtime.engine.tick())
    runtime.deferred[-1].result_sync(timeout=5)
    asyncio.run(runtime.engine.reload())
    saved = runtime.engine.get_task_by_uuid(task.uuid)
    assert saved.state == scheduler.TaskState.IDLE and saved.last_result == 'Done'
    assert saved.schedule_anchor == now
    asyncio.run(runtime.engine.tick())
    assert len(runtime.deferred) == 1
    if native:
        assert calls == ['run']
    else:
        assert context.agent0.call_chat_model_turn.await_count == 1


@pytest.mark.parametrize('change', ['disable', 'reschedule', 'manual_run', 'delete'])
def test_delayed_dispatch_rechecks_disabled_or_rescheduled_tasks(runtime, monkeypatch, change):
    pending = []
    class DelayedTask:
        def __init__(self, **kwargs): pass
        def start_task(self, func, *args): pending.append((func, args))
    monkeypatch.setattr(scheduler, 'DeferredTask', DelayedTask)
    task = recurring(created_at=runtime.now-timedelta(days=30))
    asyncio.run(runtime.engine.add_task(task))
    asyncio.run(runtime.engine.tick())
    assert len(pending) == 1
    if change == 'delete':
        asyncio.run(runtime.engine.remove_task_by_uuid(task.uuid))
    elif change == 'reschedule':
        asyncio.run(runtime.engine.update_task(task.uuid, schedule=task.schedule.model_copy(update={'hour':'10'})))
    elif change == 'manual_run':
        asyncio.run(runtime.engine.update_task(task.uuid, last_run=runtime.now))
    else:
        asyncio.run(runtime.engine.update_task(task.uuid, state=scheduler.TaskState.DISABLED))
    func, args = pending.pop()
    asyncio.run(func(*args))
    asyncio.run(runtime.engine.reload())
    saved = runtime.engine.get_task_by_uuid(task.uuid)
    if change == 'delete':
        assert saved is None
    else:
        assert saved.state == (scheduler.TaskState.DISABLED if change == 'disable' else scheduler.TaskState.IDLE)
        assert saved.last_result is None
    assert not runtime.engine._running_deferred_tasks


def test_overlapping_ticks_keep_one_worker(runtime, monkeypatch):
    pending = []
    class DelayedTask:
        def __init__(self, **kwargs): pass
        def start_task(self, func, *args): pending.append((func, args))
    monkeypatch.setattr(scheduler, 'DeferredTask', DelayedTask)
    task = recurring(created_at=runtime.now-timedelta(days=30))
    asyncio.run(runtime.engine.add_task(task))
    asyncio.run(runtime.engine.tick())
    asyncio.run(runtime.engine.tick())
    assert len(pending) == 1


def test_new_task_does_not_backfill_before_creation(monkeypatch):
    now = MONDAY + timedelta(hours=1)
    monkeypatch.setattr(scheduler, '_now', lambda: now)
    task = recurring(created_at=now)
    assert not task.check_schedule()
    assert task.get_next_run() == MONDAY + timedelta(days=7)


@pytest.mark.parametrize('finish', ['cancel', 'success'])
def test_run_consumes_slots_while_it_was_busy(monkeypatch, finish):
    now = MONDAY - timedelta(minutes=1)
    monkeypatch.setattr(scheduler, '_now', lambda: now)
    task = recurring()
    task.update(state=scheduler.TaskState.RUNNING)
    now = MONDAY + timedelta(hours=1)
    task.update(state=scheduler.TaskState.IDLE, **({'last_run':now} if finish == 'success' else {}))
    assert not task.check_schedule()
    assert task.get_next_run() == MONDAY + timedelta(days=7)


@pytest.mark.parametrize('state', [scheduler.TaskState.DISABLED, scheduler.TaskState.RUNNING, scheduler.TaskState.ERROR])
def test_non_idle_tasks_do_not_catch_up(runtime, state):
    task = recurring(created_at=runtime.now-timedelta(days=30), state=state)
    asyncio.run(runtime.engine.add_task(task))
    asyncio.run(runtime.engine.tick())
    assert not runtime.deferred
