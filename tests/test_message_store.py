"""Tests for MessageStore persistence and replay."""

import time

import pytest

from python.helpers.channel_bridge import NormalizedMessage
from python.helpers.message_store import MessageStore


def _make_msg(
    msg_id: str = "msg1",
    channel: str = "telegram",
    text: str = "hello",
    sender_id: str = "u1",
) -> NormalizedMessage:
    return NormalizedMessage(
        id=msg_id,
        channel=channel,
        sender_id=sender_id,
        sender_name="User",
        text=text,
        timestamp=time.time(),
    )


@pytest.mark.unit
class TestMessageStore:
    def test_store_and_get_history(self):
        ms = MessageStore(":memory:")
        ms.store(_make_msg("m1", text="first"))
        ms.store(_make_msg("m2", text="second"))
        history = ms.get_history("telegram")
        assert len(history) == 2

    def test_get_history_filters_by_channel(self):
        ms = MessageStore(":memory:")
        ms.store(_make_msg("m1", channel="telegram"))
        ms.store(_make_msg("m2", channel="discord"))
        assert len(ms.get_history("telegram")) == 1
        assert len(ms.get_history("discord")) == 1

    def test_get_history_limit(self):
        ms = MessageStore(":memory:")
        for i in range(10):
            ms.store(_make_msg(f"m{i}"))
        assert len(ms.get_history("telegram", limit=3)) == 3

    def test_get_history_before_ts(self):
        ms = MessageStore(":memory:")
        now = time.time()
        ms.store(NormalizedMessage(id="old", channel="ch", text="old", timestamp=now - 100))
        ms.store(NormalizedMessage(id="new", channel="ch", text="new", timestamp=now))
        history = ms.get_history("ch", before_ts=now - 50)
        assert len(history) == 1
        assert history[0]["id"] == "old"

    def test_store_with_response(self):
        ms = MessageStore(":memory:")
        ms.store(_make_msg("m1"), response="bot reply")
        history = ms.get_history("telegram")
        assert history[0]["response"] == "bot reply"

    def test_replay(self):
        ms = MessageStore(":memory:")
        original = _make_msg("replay1", text="replay me")
        ms.store(original)
        replayed = ms.replay("replay1")
        assert replayed is not None
        assert replayed.id == "replay1"
        assert replayed.text == "replay me"
        assert replayed.channel == "telegram"

    def test_replay_nonexistent_returns_none(self):
        ms = MessageStore(":memory:")
        assert ms.replay("nope") is None

    def test_metadata_roundtrip(self):
        ms = MessageStore(":memory:")
        msg = NormalizedMessage(
            id="meta1",
            channel="ch",
            text="hi",
            timestamp=time.time(),
            metadata={"source": "api", "priority": 5},
        )
        ms.store(msg)
        history = ms.get_history("ch")
        assert history[0]["metadata"] == {"source": "api", "priority": 5}
