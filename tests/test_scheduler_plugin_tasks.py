import asyncio
import threading

import pytest

from agent import AgentContext
from helpers import plugins, task_scheduler as scheduler
from test_task_scheduler_recovery import runtime


def native_task():
    return scheduler.ScheduledTask(
        name="Housekeeping", plugin_name="test_cleaner", system_prompt="", prompt="Clean caches",
        schedule=scheduler.TaskSchedule(minute="0", hour="9", day="*", month="*", weekday="1", timezone="UTC"),
    )


def test_plugin_task_runs_without_a_chat_or_model_and_persists_result(runtime, monkeypatch):
    task = native_task()
    monkeypatch.setattr(plugins, "get_toggle_state", lambda name: "enabled")
    calls = []

    def run(name, hook, *, task, cancel_event):
        calls.append((name, hook, task.uuid, cancel_event.is_set()))
        return "Freed 42 MB"

    monkeypatch.setattr(plugins, "call_plugin_hook", run)
    asyncio.run(runtime.engine.add_task(task))
    assert AgentContext.get(task.context_id) is None
    asyncio.run(runtime.engine.run_task_by_uuid(task.uuid))
    runtime.deferred[-1].result_sync(timeout=5)
    asyncio.run(runtime.engine.reload())
    saved = runtime.engine.get_task_by_uuid(task.uuid)
    assert saved.state == scheduler.TaskState.IDLE
    assert saved.last_result == "Freed 42 MB"
    assert calls == [("test_cleaner", "run_scheduled_task", task.uuid, False)]
    assert AgentContext.get(task.context_id) is None
    restored = scheduler.deserialize_task(scheduler.serialize_task(saved))
    assert restored.plugin_name == "test_cleaner"
    assert restored.schedule == task.schedule


@pytest.mark.parametrize("mode", ["disabled", "missing", "error"])
def test_plugin_execution_fails_closed_without_agent_fallback(runtime, monkeypatch, mode):
    task = native_task()
    monkeypatch.setattr(plugins, "get_toggle_state", lambda name: "disabled" if mode == "disabled" else "enabled")

    def run(*args, **kwargs):
        assert mode != "disabled"
        if mode == "error":
            raise RuntimeError("cleanup failed")

    monkeypatch.setattr(plugins, "call_plugin_hook", run)
    asyncio.run(runtime.engine.add_task(task))
    asyncio.run(runtime.engine.run_task_by_uuid(task.uuid))
    runtime.deferred[-1].result_sync(timeout=5)
    asyncio.run(runtime.engine.reload())
    assert runtime.engine.get_task_by_uuid(task.uuid).state == scheduler.TaskState.ERROR
    assert AgentContext.get(task.context_id) is None


@pytest.mark.parametrize('raises_on_cancel', [False, True])
def test_plugin_task_cancellation_waits_for_worker_to_stop(monkeypatch, raises_on_cancel):
    started, finished = threading.Event(), threading.Event()
    monkeypatch.setattr(plugins, "get_toggle_state", lambda name: "enabled")

    def run(*args, cancel_event, **kwargs):
        started.set()
        assert cancel_event.wait(timeout=3)
        finished.set()
        if raises_on_cancel:
            raise RuntimeError('Stopped')
        return "Stopped"

    monkeypatch.setattr(plugins, "call_plugin_hook", run)

    async def check():
        worker = asyncio.create_task(scheduler._execute_plugin_task(native_task()))
        assert await asyncio.to_thread(started.wait, 2)
        worker.cancel()
        with pytest.raises(asyncio.CancelledError):
            await worker
        assert finished.is_set()

    asyncio.run(check())


def test_plugin_task_preserves_owner_and_only_edits_applicable_fields():
    task = native_task()
    task.update(name="Weekly maintenance", prompt=task.prompt, attachments=[])
    assert task.name == "Weekly maintenance"
    with pytest.raises(ValueError, match="owning plugin"):
        task.update(prompt="Run arbitrary instructions")
    legacy = scheduler.serialize_task(task)
    legacy.pop("plugin_name")
    assert scheduler.deserialize_task(legacy).plugin_name is None
