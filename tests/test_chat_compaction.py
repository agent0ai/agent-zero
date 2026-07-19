import sys
from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from plugins._chat_compaction.helpers import compactor


class _FakeAgent:
    def read_prompt(self, name: str, **kwargs):
        if name == "compact.sys.md":
            return "system"
        if name == "compact.msg.md":
            return kwargs.get("conversation", "")
        raise AssertionError(f"Unexpected prompt: {name}")


class _FakeLog:
    def __init__(self):
        self.updates = []
        self.streams = []

    def update(self, **kwargs):
        self.updates.append(kwargs)

    def stream(self, **kwargs):
        self.streams.append(kwargs)


class _RecordingModel:
    def __init__(self):
        self.user_messages = []

    async def unified_call(self, system_message, user_message, response_callback=None):
        self.user_messages.append(user_message)
        if response_callback:
            await response_callback("done", "done")
        return f"summary-{len(self.user_messages)}", None


def test_compaction_splitter_wraps_single_line_85k_payload(monkeypatch):
    monkeypatch.setattr(
        compactor.tokens, "approximate_tokens", lambda text: len(text or "")
    )

    agent = _FakeAgent()
    chunks = compactor._split_text_for_compaction(
        agent,
        "x" * 85_000,
        token_count=85_000,
        max_input_tokens=10_000,
    )

    assert len(chunks) > 2
    assert all(chunks)
    assert "".join(chunks) == "x" * 85_000
    assert all(
        compactor._compaction_input_tokens(agent, chunk) <= 10_000
        for chunk in chunks
    )


@pytest.mark.asyncio
async def test_large_compaction_does_not_send_unsplit_single_line_payload(monkeypatch):
    monkeypatch.setattr(
        compactor.tokens, "approximate_tokens", lambda text: len(text or "")
    )

    agent = _FakeAgent()
    model = _RecordingModel()

    summary = await compactor._compact_large_history(
        agent,
        "x" * 85_000,
        token_count=85_000,
        max_input_tokens=10_000,
        log_item=_FakeLog(),
        model=model,
    )

    chunk_messages = model.user_messages[:-1]
    assert summary == f"summary-{len(model.user_messages)}"
    assert len(chunk_messages) > 2
    assert all(chunk_messages)
    assert all(len(message) <= 10_000 for message in chunk_messages)
