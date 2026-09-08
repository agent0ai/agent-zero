import sys
from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from helpers.history import Bulk, History, Message, Topic


class _FailingUtilityAgent:
    async def call_utility_model(self, **_kwargs):
        raise RuntimeError("utility model unavailable")

    def read_prompt(self, name, **kwargs):
        return f"{name}: {kwargs}"

    def parse_prompt(self, name, **kwargs):
        return f"{name}: {kwargs['summary']}"


class _EmptyUtilityAgent(_FailingUtilityAgent):
    async def call_utility_model(self, **_kwargs):
        return ""


@pytest.mark.parametrize("agent_cls", [_FailingUtilityAgent, _EmptyUtilityAgent])
@pytest.mark.asyncio
async def test_topic_compression_falls_back_when_utility_model_fails(agent_cls):
    history = History(agent_cls())
    topic = Topic(history)
    topic.messages = [
        Message(False, "opening"),
        Message(False, "a" * 4_000),
        Message(True, "b" * 4_000),
        Message(True, "closing"),
    ]
    before_tokens = topic.get_tokens()

    compressed = await topic.compress_attention(ratio=0)

    assert compressed is True
    assert topic.get_tokens() < before_tokens
    assert "emergency fallback compression" in topic.messages[1].output_text()


@pytest.mark.parametrize("agent_cls", [_FailingUtilityAgent, _EmptyUtilityAgent])
@pytest.mark.asyncio
async def test_bulk_summary_falls_back_when_utility_model_fails(agent_cls):
    history = History(agent_cls())
    bulk = Bulk(history)
    topic = Topic(history)
    topic.messages = [Message(False, "a" * 4_000), Message(True, "b" * 4_000)]
    bulk.records = [topic]
    original = bulk.output_text()

    summary = await bulk.summarize()

    assert summary == bulk.summary
    assert "emergency fallback compression" in summary
    assert len(summary) < len(original)


@pytest.mark.asyncio
async def test_compress_bulks_returns_false_when_no_bulks_exist():
    history = History(_FailingUtilityAgent())

    assert await history.compress_bulks() is False
