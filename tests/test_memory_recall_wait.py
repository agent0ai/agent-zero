import asyncio
import sys
from types import SimpleNamespace
from collections import OrderedDict

import pytest

DATA_NAME_TASK_MEMORIES = "_recall_memories_task"
DATA_NAME_ITER_MEMORIES = "_recall_memories_iter"


class LoopData:
    def __init__(self, **kwargs):
        self.iteration = -1
        self.extras_temporary = OrderedDict()
        for key, value in kwargs.items():
            setattr(self, key, value)


sys.modules.setdefault("agent", SimpleNamespace(LoopData=LoopData))
sys.modules.setdefault(
    "python.extensions.message_loop_prompts_after._50_recall_memories",
    SimpleNamespace(
        DATA_NAME_TASK=DATA_NAME_TASK_MEMORIES,
        DATA_NAME_ITER=DATA_NAME_ITER_MEMORIES,
    ),
)

from python.extensions.message_loop_prompts_after._91_recall_wait import RecallWait


@pytest.mark.asyncio
async def test_recall_wait_logs_and_continues_when_recall_task_fails(monkeypatch) -> None:
    monkeypatch.setattr(
        "python.extensions.message_loop_prompts_after._91_recall_wait.settings.get_settings",
        lambda: {"memory_recall_delayed": False},
    )

    logged = []

    class FakeLog:
        def log(self, **kwargs):
            logged.append(kwargs)

    class FakeAgent:
        def __init__(self, task):
            self.context = SimpleNamespace(log=FakeLog())
            self._task = task

        def get_data(self, key):
            if key == DATA_NAME_TASK_MEMORIES:
                return self._task
            if key == DATA_NAME_ITER_MEMORIES:
                return 0
            return None

        def read_prompt(self, *_args, **_kwargs):
            return "delayed"

    async def fail_recall():
        await asyncio.sleep(0)
        raise RuntimeError("embedding backend unavailable")

    task = asyncio.create_task(fail_recall())
    extension = RecallWait(agent=FakeAgent(task))

    await extension.execute(loop_data=LoopData(iteration=1))

    assert logged
    assert logged[0]["type"] == "warning"
    assert logged[0]["heading"] == "Recall memories skipped"
    assert "embedding backend unavailable" in logged[0]["content"]
