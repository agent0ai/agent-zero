import asyncio
import importlib
import sys
import time
import types
from types import SimpleNamespace

import pytest

PROJECT_ROOT = __import__("pathlib").Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

# --- stub heavy modules before importing the extension under test -------------
# agent.py pulls the whole framework; only LoopData is needed at import time.
agent_stub = types.ModuleType("agent")
agent_stub.LoopData = object
original_agent_module = sys.modules.get("agent")
sys.modules["agent"] = agent_stub

# _50_recall_memories imports the memory helper chain (faiss, langchain FAISS).
# _91 only needs its two data-name constants, so stub the module.
RECALL_MODULE_NAME = (
    "plugins._memory.extensions.python.message_loop_prompts_after._50_recall_memories"
)
recall_stub = types.ModuleType(RECALL_MODULE_NAME)
recall_stub.DATA_NAME_TASK = "_recall_memories_task"
recall_stub.DATA_NAME_ITER = "_recall_memories_iter"
recall_stub.DATA_NAME_RESULT = "_recall_memories_result"
recall_stub.DATA_NAME_RESULT_SCOPE = "_recall_memories_result_scope"
recall_stub.apply_recall_result = lambda loop_data, result: None
recall_stub.get_recall_scope = lambda agent: "default"
original_recall_module = sys.modules.get(RECALL_MODULE_NAME)
sys.modules[RECALL_MODULE_NAME] = recall_stub

try:
    recall_wait_module = importlib.import_module(
        "plugins._memory.extensions.python.message_loop_prompts_after._91_recall_wait"
    )
finally:
    if original_agent_module is None:
        sys.modules.pop("agent", None)
    else:
        sys.modules["agent"] = original_agent_module
    if original_recall_module is None:
        sys.modules.pop(RECALL_MODULE_NAME, None)
    else:
        sys.modules[RECALL_MODULE_NAME] = original_recall_module

RecallWait = recall_wait_module.RecallWait
DATA_NAME_TASK = recall_stub.DATA_NAME_TASK
DATA_NAME_ITER = recall_stub.DATA_NAME_ITER


class FakeAgent:
    def __init__(self, task=None, iteration=0):
        self._data = {DATA_NAME_TASK: task, DATA_NAME_ITER: iteration}
        self.warnings = []

    def get_data(self, key):
        return self._data.get(key)

    def set_data(self, key, value):
        self._data[key] = value

    def hist_add_warning(self, message):
        self.warnings.append(message)


class FakeLoopData:
    def __init__(self, iteration=0):
        self.iteration = iteration
        self.extras_temporary = {}


@pytest.fixture
def plugin_config(monkeypatch):
    cfg = {"memory_recall_delayed": False}
    monkeypatch.setattr(
        recall_wait_module,
        "plugins",
        SimpleNamespace(get_plugin_config=lambda name, agent: cfg),
    )
    return cfg


def test_hung_recall_task_returns_within_ceiling(plugin_config, monkeypatch):
    """A recall task slower than the ceiling must not stall prompt prep.

    Regression for dev-ticket-2026-08-22-memory-recall-embedding-timeout:
    _91_recall_wait used a bare `await task`, so a hung embedding call
    parked prompt preparation forever.
    """
    monkeypatch.setattr(recall_wait_module, "RECALL_WAIT_TIMEOUT_S", 0.2)

    async def hung_recall():
        await asyncio.sleep(30)

    async def run():
        task = asyncio.get_running_loop().create_task(hung_recall())
        agent = FakeAgent(task=task, iteration=0)
        ext = RecallWait(agent=agent)
        started = time.monotonic()
        await ext.execute(loop_data=FakeLoopData(iteration=1))  # must not raise
        return time.monotonic() - started, agent, task

    elapsed, agent, task = asyncio.run(run())

    assert elapsed < 5, f"execute() blocked for {elapsed:.1f}s despite ceiling"
    assert len(agent.warnings) == 1
    assert "timed out" in agent.warnings[0].lower()
    # wait_for cancels the hung task before raising TimeoutError
    assert task.cancelled() or task.done()


def test_inner_search_timeout_does_not_crash_prompt_prep(plugin_config, monkeypatch):
    """TimeoutError raised inside the recall task must be swallowed.

    This is the live crash: _50_recall_memories wraps search in its own
    asyncio.wait_for(SEARCH_TIMEOUT=30); when that fires the completed
    task carries a TimeoutError which previously propagated through the
    bare `await task` in _91 and crashed prepare_prompt.
    """
    monkeypatch.setattr(recall_wait_module, "RECALL_WAIT_TIMEOUT_S", 5)

    async def inner_timed_out():
        # pending task that raises mid-await, mirroring the live crash:
        # _91 awaits while the inner SEARCH_TIMEOUT wait_for fires
        await asyncio.sleep(0.05)
        raise TimeoutError("inner SEARCH_TIMEOUT fired")

    async def run():
        task = asyncio.get_running_loop().create_task(inner_timed_out())
        agent = FakeAgent(task=task, iteration=0)
        ext = RecallWait(agent=agent)
        await ext.execute(loop_data=FakeLoopData(iteration=1))  # must not raise
        return agent

    agent = asyncio.run(run())

    assert len(agent.warnings) == 1
    assert "timed out" in agent.warnings[0].lower()


def test_fast_recall_task_awaits_normally(plugin_config, monkeypatch):
    """A recall task finishing inside the ceiling must not warn."""
    monkeypatch.setattr(recall_wait_module, "RECALL_WAIT_TIMEOUT_S", 5)

    async def fast_recall():
        return "memories"

    async def run():
        task = asyncio.get_running_loop().create_task(fast_recall())
        agent = FakeAgent(task=task, iteration=0)
        ext = RecallWait(agent=agent)
        await ext.execute(loop_data=FakeLoopData(iteration=1))
        return agent, task

    agent, task = asyncio.run(run())

    assert agent.warnings == []
    assert task.done() and not task.cancelled()
    assert task.result() == "memories"
