import asyncio
import contextlib
import sys
import threading
import time
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from agent import AgentConfig, AgentContext, UserMessage
from api.stop import stop_context
from helpers import extension, task_scheduler as scheduler
from helpers.llm_result import LLMResult


def wait_until(predicate, timeout=5.0):
    deadline = time.monotonic() + timeout
    while not predicate():
        if time.monotonic() > deadline:
            return False
        time.sleep(0.01)
    return True


@pytest.fixture
def runtime(monkeypatch, tmp_path):
    fired = []

    def probe(point):
        class Probe(extension.Extension):
            def execute(self, **kwargs):
                fired.append(point)

        return Probe

    # Probe the end-of-turn points; the core monologue_end hook resets the progress bar.
    hooks = {
        "message_loop_end": [probe("message_loop_end")],
        "monologue_end": [
            *extension._get_extensions(str(PROJECT_ROOT / "extensions/python/monologue_end")),
            probe("monologue_end"),
        ],
    }
    monkeypatch.setattr(extension, "_get_extension_classes", lambda name, **kwargs: hooks.get(name, []))
    monkeypatch.setattr(AgentContext, "_contexts", {})
    monkeypatch.setattr(scheduler, "SCHEDULER_FOLDER", str(tmp_path / "scheduler"))
    monkeypatch.setattr(scheduler, "save_tmp_chat", lambda context: None)
    monkeypatch.setattr(scheduler.TaskScheduler, "_instance", None)
    monkeypatch.setattr(scheduler.SchedulerTaskList, "_SchedulerTaskList__instance", None)
    monkeypatch.setattr("helpers.state_monitor_integration.mark_dirty_all", lambda **kwargs: None)
    config = AgentConfig(mcp_servers="")
    monkeypatch.setattr(scheduler, "initialize_agent", lambda: config)

    runs = []
    deferred_class = scheduler.DeferredTask

    def capture_task(**kwargs):
        task = deferred_class(**kwargs)
        runs.append(task)
        return task

    monkeypatch.setattr(scheduler, "DeferredTask", capture_task)
    engine = scheduler.TaskScheduler.get()
    release = threading.Event()
    turns = []

    def mock_model(context):
        """Model turns record their thread and wait for release, like a slow LLM call."""
        agent = context.agent0

        async def call_chat_model_turn(*args, **kwargs):
            turns.append(threading.current_thread().name)
            context.log.log(type="agent", heading="A0: Calling LLM...")
            while not release.is_set():
                await asyncio.sleep(0.01)
            return LLMResult(response="Done")

        agent.prepare_prompt = AsyncMock(return_value=[])
        agent.handle_intervention = AsyncMock()
        agent.call_chat_model_turn = call_chat_model_turn
        agent.process_llm_result_tools = AsyncMock(side_effect=lambda result: result.response)

    def start_run(context_id=None):
        """Run a task until its first model turn has started."""
        task = scheduler.AdHocTask(name="Report", system_prompt="", prompt="Write the report", context_id=context_id)
        asyncio.run(engine.add_task(task))
        context = AgentContext.get(task.context_id)
        mock_model(context)
        started = len(turns)
        asyncio.run(engine.run_task_by_uuid(task.uuid))
        assert wait_until(lambda: len(turns) > started)
        return task, context, runs[-1]

    yield SimpleNamespace(
        engine=engine, mock_model=mock_model, start_run=start_run,
        release=release, turns=turns, fired=fired,
    )

    # Let every run finish before the patched paths are restored.
    release.set()
    wait_until(lambda: not engine._running_deferred_tasks, timeout=10)
    for context in AgentContext.all():
        if context.task:
            with contextlib.suppress(Exception):
                context.task.result_sync(timeout=10)


def test_running_scheduled_task_is_the_chat_task(runtime):
    _, context, run = runtime.start_run()

    assert context.is_running()
    assert context.output()["running"] is True

    message = UserMessage("Also list the sources")
    assert context.communicate(message) is run
    assert context.agent0.intervention is message

    runtime.release.set()
    assert run.result_sync(timeout=5) == "Done"
    assert runtime.turns == ["TaskScheduler"]


def test_finished_scheduled_task_fires_end_hooks_and_returns_chat_to_idle(runtime):
    runtime.release.set()
    task, context, run = runtime.start_run()
    run.result_sync(timeout=5)

    assert runtime.fired == ["message_loop_end", "monologue_end"]
    assert (context.log.progress, context.log.progress_active) == ("Waiting for input", False)
    asyncio.run(runtime.engine.reload())
    assert runtime.engine.get_task_by_uuid(task.uuid).state == scheduler.TaskState.IDLE

    # The chat gets its own task back, so the next message starts a normal chat turn.
    assert wait_until(lambda: context.task is None)
    follow_up = context.communicate(UserMessage("Thanks"))
    assert follow_up is not run
    assert follow_up.result_sync(timeout=5) == "Done"
    assert len(runtime.turns) == 2
    assert runtime.turns[0] == "TaskScheduler" and runtime.turns[1].startswith("AgentContext")


def test_finished_scheduled_task_marks_state_dirty_after_chat_is_idle(runtime, monkeypatch):
    _, context, run = runtime.start_run()
    marks = []
    monkeypatch.setattr(
        "helpers.state_monitor_integration.mark_dirty_all",
        lambda *, reason=None: marks.append((reason, context.is_running())),
    )
    # Done callbacks run in the order they were added, so this one runs after the scheduler's.
    callbacks_done = threading.Event()
    run.add_done_callback(lambda _future: callbacks_done.set())

    runtime.release.set()
    assert callbacks_done.wait(5)
    # Without a dirty mark after the run ends, the WebUI's last push can still show the chat running.
    assert marks[-1] == ("task_scheduler.TaskScheduler._run_task_done", False)


def test_stop_cancels_running_scheduled_task(runtime):
    task, context, run = runtime.start_run()

    assert stop_context(context)["stopped"] is True
    assert not run.is_alive() and not context.is_running()
    assert wait_until(lambda: runtime.engine.get_task_by_uuid(task.uuid).state == scheduler.TaskState.IDLE)
    assert runtime.fired == []
    assert runtime.turns == ["TaskScheduler"]


def test_nudge_restarts_scheduled_task_on_a_chat_task(runtime):
    _, context, run = runtime.start_run()

    nudged = context.nudge()
    assert nudged is not run and not run.is_alive()

    runtime.release.set()
    assert nudged.result_sync(timeout=5) == "Done"
    assert len(runtime.turns) == 2
    assert runtime.turns[0] == "TaskScheduler" and runtime.turns[1].startswith("AgentContext")


def test_scheduled_task_leaves_busy_chat_task_in_place(runtime):
    chat = AgentContext(AgentConfig(mcp_servers=""), id="shared")
    runtime.mock_model(chat)
    chat_turn = chat.communicate(UserMessage("Keep going"))
    assert wait_until(lambda: runtime.turns)

    _, context, run = runtime.start_run(context_id=chat.id)
    assert context is chat and chat.task is chat_turn

    runtime.release.set()
    run.result_sync(timeout=5)
    assert chat_turn.result_sync(timeout=5) == "Done"
    assert chat.task is chat_turn
