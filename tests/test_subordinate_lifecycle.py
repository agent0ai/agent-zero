import asyncio
import threading

import pytest

from agent import Agent, AgentConfig, AgentContext, UserMessage
from api.stop import stop_context
from helpers import extension
from helpers.errors import RepairableException
from tools import call_subordinate


@pytest.mark.parametrize("outcome", ["success", "error", "stop_child", "stop_parent"])
@pytest.mark.parametrize("depth", [1, 2])
def test_direct_subordinate_task_lifecycle(monkeypatch, outcome, depth):
    monkeypatch.setattr(extension, "call_extensions_sync", lambda *args, **kwargs: None)
    monkeypatch.setattr(AgentContext, "_contexts", {})
    monkeypatch.setattr(Agent, "hist_add_user_message", lambda *args: None)
    monkeypatch.setattr(call_subordinate.message_queue, "log_user_message", lambda *args, **kwargs: None)
    saved = []
    monkeypatch.setattr(call_subordinate.persist_chat, "save_tmp_chat", lambda ctx: saved.append(ctx.id))
    agents = [Agent(number, AgentConfig(mcp_servers="")) for number in range(depth + 1)]
    monkeypatch.setattr(call_subordinate, "get_or_create_subordinate", lambda parent, **kwargs: agents[parent.number + 1])
    started = threading.Event()
    leaf_finished = threading.Event()
    parent_resumed = threading.Event()
    parent_finished = threading.Event()
    release_leaf = asyncio.Event()
    release_parent = asyncio.Event()
    results = []

    async def delegate(parent):
        tool = call_subordinate.Delegation(parent, "call_subordinate", None, {}, "", None)
        return await tool.execute(message="work")

    async def leaf():
        started.set()
        try:
            await release_leaf.wait()
            if outcome == "error":
                raise ValueError("test failure")
            return "done"
        finally:
            leaf_finished.set()

    async def nested():
        return (await delegate(agents[1])).message

    async def parent_run():
        try:
            try:
                results.append((await delegate(agents[0])).message)
            except (RepairableException, ValueError) as error:
                results.append(error)
            parent_resumed.set()
            await release_parent.wait()
        finally:
            parent_finished.set()

    monkeypatch.setattr(agents[-1], "monologue", leaf)
    if depth == 2:
        monkeypatch.setattr(agents[1], "monologue", nested)
    parent_task = agents[0].context.run_task(parent_run)
    loop = parent_task.event_loop_thread.loop
    try:
        assert started.wait(2)
        assert all(agent.context.output()["running"] for agent in agents)
        assert len({id(agent.context.task) for agent in agents}) == len(agents)

        if outcome == "success":
            context = agents[-1].context
            task = context.task
            context.paused = True
            assert context.output()["paused"] is True
            assert context.output()["running"] is True
            assert context.communicate(UserMessage("intervention")) is task
            assert agents[-1].intervention.message == "intervention"
            assert context.paused is False

        if outcome == "stop_parent":
            assert stop_context(agents[0].context)["stopped"] is True
            assert parent_finished.wait(2)
            assert leaf_finished.wait(2)
            assert not parent_resumed.is_set()
        else:
            if outcome == "stop_child":
                assert stop_context(agents[-1].context)["stopped"] is True
            else:
                loop.call_soon_threadsafe(release_leaf.set)
            assert parent_resumed.wait(2)
            assert leaf_finished.wait(2)
            assert agents[0].context.is_running()
            if outcome == "success":
                assert results == ["done"]
            else:
                assert isinstance(results[0], RepairableException if outcome == "stop_child" else ValueError)
            assert all(not agent.context.is_running() for agent in agents[1:])
            loop.call_soon_threadsafe(release_parent.set)
            assert parent_task.result_sync(timeout=2) is None
        asyncio.run_coroutine_threadsafe(asyncio.sleep(0), loop).result(2)
        assert all(not agent.context.is_running() for agent in agents)
        assert all(saved.count(agent.context.id) == 2 for agent in agents[1:])
    finally:
        loop.call_soon_threadsafe(release_leaf.set)
        loop.call_soon_threadsafe(release_parent.set)
        for agent in reversed(agents):
            agent.context.kill_process()
        assert parent_finished.wait(2)
        assert leaf_finished.wait(2)


@pytest.mark.asyncio
async def test_legacy_subordinate_keeps_shared_task(monkeypatch):
    monkeypatch.setattr(extension, "call_extensions_sync", lambda *args, **kwargs: None)
    monkeypatch.setattr(AgentContext, "_contexts", {})
    monkeypatch.setattr(Agent, "hist_add_user_message", lambda *args: None)
    parent = Agent(0, AgentConfig(mcp_servers=""))
    child = Agent(1, parent.config, parent.context)
    monkeypatch.setattr(call_subordinate, "get_or_create_subordinate", lambda *args, **kwargs: child)

    async def monologue():
        assert asyncio.current_task() is caller
        return "legacy"

    monkeypatch.setattr(child, "monologue", monologue)
    caller = asyncio.current_task()
    tool = call_subordinate.Delegation(parent, "call_subordinate", None, {}, "", None)
    assert (await tool.execute(message="work")).message == "legacy"
    assert parent.context.task is None
