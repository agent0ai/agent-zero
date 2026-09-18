import asyncio
import sys
import threading
import types
from pathlib import Path

import pytest


PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

# AgentContext.run_task does not use embeddings. Avoid importing the optional
# sentence-transformers stack just to exercise this scheduler seam.
sentence_transformers = types.ModuleType("sentence_transformers")
sentence_transformers.SentenceTransformer = object
sys.modules.setdefault("sentence_transformers", sentence_transformers)

from agent import AgentContext


def _bare_context(context_id: str) -> AgentContext:
    context = AgentContext.__new__(AgentContext)
    context.id = context_id
    context.task = None
    return context


def test_blocked_chat_does_not_stall_another_chat():
    blocked = _bare_context("blocked-chat")
    healthy = _bare_context("healthy-chat")
    blocker_started = threading.Event()
    release_blocker = threading.Event()

    async def block_event_loop():
        blocker_started.set()
        release_blocker.wait()

    async def finish_immediately():
        await asyncio.sleep(0)
        return "healthy chat completed"

    blocked_task = blocked.run_task(block_event_loop)
    assert blocker_started.wait(timeout=1)

    healthy_task = healthy.run_task(finish_immediately)
    try:
        assert healthy_task.result_sync(timeout=0.5) == "healthy chat completed"
    finally:
        release_blocker.set()
        blocked_task.result_sync(timeout=1)
