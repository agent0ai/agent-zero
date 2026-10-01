import asyncio
import sys
from pathlib import Path
from types import SimpleNamespace

import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from agent import LoopData
from plugins._memory.extensions.python.message_loop_prompts_after import (
    _50_recall_memories as recall_module,
    _91_recall_wait as wait_module,
)


class _LogItem:
    def update(self, **_kwargs):
        pass


class _Agent:
    def __init__(self):
        self.data = {}
        self.project = "project-a"
        self.config = SimpleNamespace(profile="agent0")
        self.context = SimpleNamespace(
            log=SimpleNamespace(log=lambda **_kwargs: _LogItem()),
            get_data=lambda *_args, **_kwargs: self.project,
        )

    def get_data(self, key):
        return self.data.get(key)

    def set_data(self, key, value):
        self.data[key] = value

    def read_prompt(self, _name):
        return "Recall is running in the background."


def _settings():
    return {
        "memory_recall_enabled": True,
        "memory_recall_delayed": True,
        "memory_recall_interval": 1,
    }


@pytest.mark.asyncio
async def test_delayed_recall_result_reaches_the_next_monologue(monkeypatch):
    agent = _Agent()
    recall = recall_module.RecallMemories(agent=agent)
    monkeypatch.setattr(
        recall_module.plugins, "get_plugin_config", lambda *_args: _settings()
    )

    async def search_memories(**_kwargs):
        return {"memories": "recalled context"}

    monkeypatch.setattr(recall, "search_memories", search_memories)

    first_loop = LoopData()
    first_loop.iteration = 0
    await recall.execute(loop_data=first_loop)
    await agent.get_data(recall_module.DATA_NAME_TASK)

    next_loop = LoopData()
    next_loop.iteration = 0
    await recall.execute(loop_data=next_loop)
    await agent.get_data(recall_module.DATA_NAME_TASK)

    assert next_loop.extras_persistent["memories"] == "recalled context"


@pytest.mark.asyncio
async def test_delayed_recall_task_survives_the_next_internal_iteration(monkeypatch):
    agent = _Agent()
    recall = recall_module.RecallMemories(agent=agent)
    wait = wait_module.RecallWait(agent=agent)
    settings = _settings()
    monkeypatch.setattr(
        recall_module.plugins, "get_plugin_config", lambda *_args: settings
    )

    release = asyncio.Event()

    async def search_memories(**_kwargs):
        await release.wait()
        return {"solutions": "recalled solution"}

    monkeypatch.setattr(recall, "search_memories", search_memories)

    loop_data = LoopData()
    loop_data.iteration = 0
    await recall.execute(loop_data=loop_data)
    first_task = agent.get_data(recall_module.DATA_NAME_TASK)
    await wait.execute(loop_data=loop_data)
    assert "memory_recall_delayed" in loop_data.extras_temporary

    loop_data.iteration = 1
    await recall.execute(loop_data=loop_data)
    next_task = agent.get_data(recall_module.DATA_NAME_TASK)
    release.set()
    await first_task
    if next_task is not first_task:
        await next_task

    assert next_task is first_task
    await wait.execute(loop_data=loop_data)
    assert loop_data.extras_persistent["solutions"] == "recalled solution"


@pytest.mark.asyncio
async def test_completed_blocking_recall_is_applied(monkeypatch):
    agent = _Agent()
    recall = recall_module.RecallMemories(agent=agent)
    wait = wait_module.RecallWait(agent=agent)
    settings = {**_settings(), "memory_recall_delayed": False}
    monkeypatch.setattr(
        recall_module.plugins, "get_plugin_config", lambda *_args: settings
    )

    async def search_memories(**_kwargs):
        return {"memories": "ready before wait"}

    monkeypatch.setattr(recall, "search_memories", search_memories)

    loop_data = LoopData()
    loop_data.iteration = 0
    await recall.execute(loop_data=loop_data)
    await agent.get_data(recall_module.DATA_NAME_TASK)
    await wait.execute(loop_data=loop_data)

    assert loop_data.extras_persistent["memories"] == "ready before wait"


@pytest.mark.asyncio
async def test_delayed_recall_result_does_not_cross_profile_or_project(monkeypatch):
    agent = _Agent()
    recall = recall_module.RecallMemories(agent=agent)
    monkeypatch.setattr(
        recall_module.plugins, "get_plugin_config", lambda *_args: _settings()
    )

    release = asyncio.Event()

    async def search_memories(**_kwargs):
        await release.wait()
        return {"memories": "project-a memory"}

    monkeypatch.setattr(recall, "search_memories", search_memories)

    first_loop = LoopData()
    first_loop.iteration = 0
    await recall.execute(loop_data=first_loop)
    first_task = agent.get_data(recall_module.DATA_NAME_TASK)

    agent.project = "project-b"
    agent.config.profile = "developer"
    release.set()
    await first_task

    next_loop = LoopData()
    next_loop.iteration = 0
    await recall.execute(loop_data=next_loop)

    assert "memories" not in next_loop.extras_persistent
    await agent.get_data(recall_module.DATA_NAME_TASK)
