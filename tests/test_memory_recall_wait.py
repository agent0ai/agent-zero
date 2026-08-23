from __future__ import annotations

import asyncio
import importlib.util
import sys
import types
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch


PROJECT_ROOT = Path(__file__).resolve().parents[1]
TARGET_PATH = (
    PROJECT_ROOT
    / "plugins"
    / "_memory"
    / "extensions"
    / "python"
    / "message_loop_prompts_after"
    / "_91_recall_wait.py"
)
DATA_NAME_TASK = "_recall_memories_task"
DATA_NAME_ITER = "_recall_memories_iter"


def load_recall_wait_module():
    extension_module = types.ModuleType("helpers.extension")

    class Extension:
        def __init__(self, agent=None, **_kwargs) -> None:
            self.agent = agent

    extension_module.Extension = Extension

    agent_module = types.ModuleType("agent")
    agent_module.LoopData = object

    recall_memories_module = types.ModuleType(
        "plugins._memory.extensions.python.message_loop_prompts_after._50_recall_memories"
    )
    recall_memories_module.DATA_NAME_TASK = DATA_NAME_TASK
    recall_memories_module.DATA_NAME_ITER = DATA_NAME_ITER

    plugins_module = types.ModuleType("helpers.plugins")
    plugins_module.get_plugin_config = lambda *_args, **_kwargs: {
        "memory_recall_delayed": False,
    }
    errors_module = types.ModuleType("helpers.errors")

    class HandledException(Exception):
        pass

    errors_module.HandledException = HandledException
    helpers_module = types.ModuleType("helpers")
    helpers_module.plugins = plugins_module

    modules = {
        "agent": agent_module,
        "helpers": helpers_module,
        "helpers.extension": extension_module,
        "helpers.errors": errors_module,
        "helpers.plugins": plugins_module,
        "plugins._memory.extensions.python.message_loop_prompts_after._50_recall_memories": recall_memories_module,
    }
    with patch.dict(sys.modules, modules):
        spec = importlib.util.spec_from_file_location("test_recall_wait", TARGET_PATH)
        assert spec and spec.loader
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module


class FakeLog:
    def __init__(self) -> None:
        self.entries: list[dict] = []

    def log(self, **entry) -> None:
        self.entries.append(entry)


class FakeAgent:
    def __init__(self, task: asyncio.Task) -> None:
        self.data = {DATA_NAME_TASK: task}
        self.context = SimpleNamespace(log=FakeLog())

    def get_data(self, key):
        return self.data.get(key)

    def set_data(self, key, value) -> None:
        self.data[key] = value


class RecallWaitTests(unittest.TestCase):
    def setUp(self) -> None:
        self.recall_wait = load_recall_wait_module()

    def test_timeout_logs_visible_block_and_prevents_agent_turn(self) -> None:
        async def run() -> FakeAgent:
            async def timed_out_recall() -> None:
                await asyncio.sleep(0)
                raise asyncio.TimeoutError

            task = asyncio.create_task(timed_out_recall())
            agent = FakeAgent(task)

            with self.assertRaises(self.recall_wait.HandledException) as exc:
                await self.recall_wait.RecallWait(agent).execute(
                    SimpleNamespace(iteration=0)
                )
            self.assertEqual(
                str(exc.exception),
                "Required memory recall timed out; agent response blocked.",
            )
            return agent

        agent = asyncio.run(run())

        assert agent.data[DATA_NAME_TASK] is None
        assert agent.context.log.entries == [
            {
                "type": "error",
                "heading": "Memory recall timed out",
                "content": (
                    "No response was generated because required memory recall did "
                    "not finish within 30 seconds. Retry the request after the "
                    "memory service recovers."
                ),
            }
        ]

    def test_completed_timeout_task_still_blocks_agent_turn(self) -> None:
        async def run() -> FakeAgent:
            async def timed_out_recall() -> None:
                raise asyncio.TimeoutError

            task = asyncio.create_task(timed_out_recall())
            try:
                await task
            except asyncio.TimeoutError:
                pass
            self.assertTrue(task.done())

            agent = FakeAgent(task)
            with self.assertRaises(self.recall_wait.HandledException):
                await self.recall_wait.RecallWait(agent).execute(
                    SimpleNamespace(iteration=0)
                )
            return agent

        agent = asyncio.run(run())

        assert agent.data[DATA_NAME_TASK] is None
        assert agent.context.log.entries[0]["type"] == "error"

    def test_cancellation_still_propagates(self) -> None:
        async def run() -> FakeAgent:
            async def cancelled_recall() -> None:
                await asyncio.sleep(0)
                raise asyncio.CancelledError

            task = asyncio.create_task(cancelled_recall())
            agent = FakeAgent(task)

            with self.assertRaises(asyncio.CancelledError):
                await self.recall_wait.RecallWait(agent).execute(
                    SimpleNamespace(iteration=0)
                )
            return agent

        agent = asyncio.run(run())

        assert agent.data[DATA_NAME_TASK] is not None
        assert agent.context.log.entries == []


if __name__ == "__main__":
    unittest.main()
