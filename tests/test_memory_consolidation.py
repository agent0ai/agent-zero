import asyncio
import sys
from pathlib import Path

import pytest
from langchain_core.documents import Document

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from plugins._memory.helpers import memory_consolidation as mc  # noqa: E402
from plugins._memory.helpers.memory_consolidation import (  # noqa: E402
    ConsolidationConfig,
    MemoryConsolidator,
)


class _FakeAgent:
    """Minimal stand-in for Agent: prompts + utility-model calls only."""

    def __init__(self, responses):
        self._responses = iter(responses)
        self.utility_calls = []

    def read_prompt(self, name, **kwargs):
        return ""

    async def call_utility_model(self, **kwargs):
        self.utility_calls.append(kwargs)
        response = next(self._responses)
        if isinstance(response, BaseException):
            raise response
        return response


class _FakeInnerDB:
    def __init__(self, docs):
        self._docs = list(docs)

    def get_by_ids(self, ids):
        wanted = set(ids)
        return [doc for doc in self._docs if doc.metadata.get("id") in wanted]

    async def aget_by_ids(self, ids):
        return self.get_by_ids(ids)


class _FakeMemory:
    def __init__(self, existing):
        self.db = _FakeInnerDB(existing)
        self.inserts = []
        self.fail_inserts = False

    async def insert_text(self, text, metadata=None):
        if self.fail_inserts:
            raise RuntimeError("vector DB unavailable")
        self.inserts.append((text, dict(metadata or {})))
        return f"id-{len(self.inserts)}"


def _existing_doc():
    return Document(
        page_content="Existing memory about deployment steps.",
        metadata={"id": "existing-1", "timestamp": "2026-11-04T00:00:00"},
    )


def _make_consolidator(monkeypatch, agent, fake_memory, similar):
    async def _fake_get(_agent):
        return fake_memory

    monkeypatch.setattr(mc.Memory, "get", _fake_get)
    consolidator = MemoryConsolidator(agent)
    if similar is None:
        similar = [_existing_doc()]

    async def _fake_similar(new_memory, area, log_item=None):
        return list(similar)

    consolidator._find_similar_memories = _fake_similar
    return consolidator


@pytest.mark.parametrize(
    "response",
    [
        "[]",
        "null",
        "42",
        "",
        "   ",
        "This is prose, not JSON",
        '{"action":',
        "{",
        '{"action": "unknown_action"}',
        '{"action": "skip"}',
    ],
)
@pytest.mark.asyncio
async def test_invalid_llm_response_skips_but_still_inserts_memory(
    monkeypatch, response
):
    """Invalid consolidation output must never lose the new memory.

    Regression coverage for #1909 (crash part): on current `ready` the
    invalid-JSON failure is contained inside _analyze_memory_consolidation
    and the SKIP path inserts the ORIGINAL memory exactly once.
    """
    agent = _FakeAgent([response])
    fake_memory = _FakeMemory([_existing_doc()])
    consolidator = _make_consolidator(monkeypatch, agent, fake_memory, None)

    result = await consolidator.process_new_memory(
        "User prefers concise answers.",
        "FRAGMENTS",
        {"area": "FRAGMENTS", "source": "test"},
    )

    assert result == {"success": True, "memory_ids": ["id-1"]}
    assert len(fake_memory.inserts) == 1
    text, metadata = fake_memory.inserts[0]
    assert text == "User prefers concise answers."
    assert metadata["area"] == "FRAGMENTS"
    assert metadata["source"] == "test"


@pytest.mark.asyncio
async def test_keep_separate_normal_behavior_preserved(monkeypatch):
    agent = _FakeAgent(
        ['{"action": "keep_separate", "new_memory_content": "consolidated text"}']
    )
    fake_memory = _FakeMemory([_existing_doc()])
    consolidator = _make_consolidator(monkeypatch, agent, fake_memory, None)

    result = await consolidator.process_new_memory(
        "User prefers concise answers.", "FRAGMENTS", {"area": "FRAGMENTS"}
    )

    assert result["success"] is True
    assert fake_memory.inserts[0][0] == "consolidated text"


@pytest.mark.asyncio
async def test_direct_insert_when_no_similar_memories(monkeypatch):
    agent = _FakeAgent([])
    fake_memory = _FakeMemory([])
    consolidator = _make_consolidator(monkeypatch, agent, fake_memory, [])

    result = await consolidator.process_new_memory(
        "Brand new fact.", "FRAGMENTS", {"area": "FRAGMENTS"}
    )

    assert result == {"success": True, "memory_ids": ["id-1"]}
    assert agent.utility_calls == []
    assert fake_memory.inserts[0][0] == "Brand new fact."


@pytest.mark.asyncio
async def test_utility_model_failure_still_inserts_memory(monkeypatch):
    agent = _FakeAgent([RuntimeError("provider unavailable")])
    fake_memory = _FakeMemory([_existing_doc()])
    consolidator = _make_consolidator(monkeypatch, agent, fake_memory, None)

    result = await consolidator.process_new_memory(
        "User prefers concise answers.", "FRAGMENTS", {"area": "FRAGMENTS"}
    )

    assert result == {"success": True, "memory_ids": ["id-1"]}
    assert fake_memory.inserts[0][0] == "User prefers concise answers."


@pytest.mark.asyncio
async def test_step4_db_failure_returns_failure_without_raising(monkeypatch):
    agent = _FakeAgent(
        ['{"action": "keep_separate", "new_memory_content": "consolidated text"}']
    )
    fake_memory = _FakeMemory([_existing_doc()])
    fake_memory.fail_inserts = True
    consolidator = _make_consolidator(monkeypatch, agent, fake_memory, None)

    result = await consolidator.process_new_memory(
        "User prefers concise answers.", "FRAGMENTS", {"area": "FRAGMENTS"}
    )

    assert result == {"success": False, "memory_ids": []}


@pytest.mark.asyncio
async def test_cancellation_propagates_and_is_not_suppressed(monkeypatch):
    """Cancellation must propagate: swallowing it would break task control.

    CancelledError is a BaseException and is intentionally NOT caught by
    process_new_memory. This test fails if a future change suppresses it
    into a failure dict.
    """
    agent = _FakeAgent([asyncio.CancelledError()])
    fake_memory = _FakeMemory([_existing_doc()])
    consolidator = _make_consolidator(monkeypatch, agent, fake_memory, None)

    with pytest.raises(asyncio.CancelledError):
        await consolidator.process_new_memory(
            "User prefers concise answers.", "FRAGMENTS", {"area": "FRAGMENTS"}
        )
    assert fake_memory.inserts == []


@pytest.mark.asyncio
async def test_timeout_returns_failure_without_insert(monkeypatch):
    """Timeout converts to a failure dict; no fallback insertion happens.

    Documented current behavior (separate durability note for #1909):
    unlike the SKIP path, a timeout does NOT insert the new memory.
    """

    class _SlowAgent(_FakeAgent):
        async def call_utility_model(self, **kwargs):
            await asyncio.sleep(2)
            return "{}"

    agent = _SlowAgent([])
    fake_memory = _FakeMemory([_existing_doc()])
    consolidator = MemoryConsolidator(
        agent, ConsolidationConfig(processing_timeout_seconds=0.05)
    )

    async def _fake_get(_agent):
        return fake_memory

    monkeypatch.setattr(mc.Memory, "get", _fake_get)

    async def _fake_similar(new_memory, area, log_item=None):
        return [_existing_doc()]

    consolidator._find_similar_memories = _fake_similar

    result = await consolidator.process_new_memory(
        "User prefers concise answers.", "FRAGMENTS", {"area": "FRAGMENTS"}
    )

    assert result == {"success": False, "memory_ids": []}
    assert fake_memory.inserts == []
