"""Tests for python/helpers/history.py — History, Message, Topic, Bulk, and helpers."""

import sys
import json
import asyncio
from pathlib import Path
from unittest.mock import MagicMock, AsyncMock, patch

import pytest
from langchain_core.messages import HumanMessage, AIMessage

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


# ─── Fixtures ────────────────────────────────────────────────────────────────


@pytest.fixture
def mock_settings_for_history():
    """Settings dict with chat_model_ctx fields required by history."""
    return {
        "chat_model_ctx_length": 4096,
        "chat_model_ctx_history": 0.5,
    }


@pytest.fixture
def patch_settings_history(mock_settings_for_history):
    """Patch get_settings to return dict usable by history helpers."""
    with patch("python.helpers.history.settings.get_settings") as m:
        m.return_value = mock_settings_for_history
        yield m


@pytest.fixture
def patch_tokens():
    """Patch tokens.approximate_tokens for predictable counts."""
    with patch("python.helpers.history.tokens.approximate_tokens") as m:
        m.side_effect = lambda t: max(1, len(str(t)) // 4)  # simple approx
        yield m


# ─── Message ────────────────────────────────────────────────────────────────


class TestMessage:
    def test_message_init_with_content(self, patch_tokens):
        from python.helpers.history import Message

        msg = Message(ai=False, content="Hello world")
        assert msg.ai is False
        assert msg.content == "Hello world"
        assert msg.summary == ""
        assert msg.tokens >= 0

    def test_message_init_with_tokens_provided(self):
        from python.helpers.history import Message

        with patch("python.helpers.history.tokens.approximate_tokens", return_value=42):
            msg = Message(ai=True, content="Hi", tokens=42)
        assert msg.tokens == 42

    def test_message_get_tokens_recalculates_when_zero(self):
        from python.helpers.history import Message

        with patch("python.helpers.history.tokens.approximate_tokens", return_value=10):
            msg = Message(ai=False, content="x")
            msg.tokens = 0
            assert msg.get_tokens() == 10

    def test_message_set_summary(self):
        from python.helpers.history import Message

        with patch("python.helpers.history.tokens.approximate_tokens", return_value=5):
            msg = Message(ai=False, content="long content")
            msg.set_summary("short summary")
            assert msg.summary == "short summary"
            assert msg.output()[0]["content"] == "short summary"

    def test_message_compress_returns_false(self):
        from python.helpers.history import Message

        msg = Message(ai=False, content="x")
        result = asyncio.run(msg.compress())
        assert result is False

    def test_message_output_uses_summary_when_set(self):
        from python.helpers.history import Message

        msg = Message(ai=True, content="original")
        msg.summary = "summarized"
        out = msg.output()
        assert len(out) == 1
        assert out[0]["ai"] is True
        assert out[0]["content"] == "summarized"

    def test_message_output_uses_content_when_no_summary(self):
        from python.helpers.history import Message

        msg = Message(ai=False, content="raw content")
        out = msg.output()
        assert out[0]["content"] == "raw content"

    def test_message_to_dict_from_dict_roundtrip(self, mock_agent):
        from python.helpers.history import Message, History

        msg = Message(ai=True, content="test", tokens=7)
        msg.summary = "s"
        data = msg.to_dict()
        assert data["_cls"] == "Message"
        assert data["ai"] is True
        assert data["content"] == "test"
        assert data["summary"] == "s"
        assert data["tokens"] == 7

        history = History(agent=mock_agent)
        restored = Message.from_dict(data, history=history)
        assert restored.ai == msg.ai
        assert restored.content == msg.content
        assert restored.summary == msg.summary
        assert restored.tokens == msg.tokens

    def test_message_from_dict_missing_content_uses_default(self, mock_agent):
        from python.helpers.history import Message, History

        history = History(agent=mock_agent)
        data = {"_cls": "Message", "ai": False, "summary": "", "tokens": 0}
        restored = Message.from_dict(data, history=history)
        assert restored.content == "Content lost"

    def test_message_output_text_custom_labels(self):
        from python.helpers.history import Message

        msg = Message(ai=True, content="hi")
        text = msg.output_text(human_label="human", ai_label="assistant")
        assert "assistant:" in text
        assert "hi" in text


# ─── Topic ──────────────────────────────────────────────────────────────────


class TestTopic:
    def test_topic_init(self, mock_agent):
        from python.helpers.history import Topic, History

        history = History(agent=mock_agent)
        topic = Topic(history=history)
        assert topic.summary == ""
        assert topic.messages == []

    def test_topic_add_message(self, mock_agent):
        from python.helpers.history import Topic, History

        history = History(agent=mock_agent)
        topic = Topic(history=history)
        msg = topic.add_message(ai=False, content="user msg")
        assert len(topic.messages) == 1
        assert msg.ai is False
        assert msg.content == "user msg"

    def test_topic_get_tokens_from_messages_when_no_summary(self, patch_tokens):
        from python.helpers.history import Topic, History

        agent = MagicMock()
        history = History(agent=agent)
        topic = Topic(history=history)
        topic.add_message(ai=False, content="hello")
        topic.add_message(ai=True, content="hi")
        assert topic.get_tokens() > 0

    def test_topic_get_tokens_from_summary_when_set(self, patch_tokens):
        from python.helpers.history import Topic, History

        agent = MagicMock()
        history = History(agent=agent)
        topic = Topic(history=history)
        topic.summary = "Summary of conversation"
        with patch("python.helpers.history.tokens.approximate_tokens", return_value=6):
            assert topic.get_tokens() == 6

    def test_topic_output_with_summary(self, mock_agent):
        from python.helpers.history import Topic, History

        history = History(agent=mock_agent)
        topic = Topic(history=history)
        topic.summary = "Topic summary"
        out = topic.output()
        assert len(out) == 1
        assert out[0]["ai"] is False
        assert out[0]["content"] == "Topic summary"

    def test_topic_output_without_summary(self, mock_agent):
        from python.helpers.history import Topic, History

        history = History(agent=mock_agent)
        topic = Topic(history=history)
        topic.add_message(ai=False, content="a")
        topic.add_message(ai=True, content="b")
        out = topic.output()
        assert len(out) == 2

    def test_topic_compress_attention_too_few_messages(self, mock_agent):
        from python.helpers.history import Topic, History

        history = History(agent=mock_agent)
        topic = Topic(history=history)
        topic.add_message(ai=False, content="1")
        topic.add_message(ai=True, content="2")
        result = asyncio.run(topic.compress_attention())
        assert result is False

    def test_topic_compress_attention_with_enough_messages(self, mock_agent):
        from python.helpers.history import Topic, History

        history = History(agent=mock_agent)
        topic = Topic(history=history)
        for i in range(5):
            topic.add_message(ai=(i % 2 == 1), content=f"msg {i}")

        mock_agent.call_utility_model = AsyncMock(return_value="Summarized")
        mock_agent.read_prompt = MagicMock(return_value="prompt")
        mock_agent.parse_prompt = MagicMock(return_value="parsed")

        result = asyncio.run(topic.compress_attention())
        assert result is True
        assert len(topic.messages) < 5

    def test_topic_to_dict_from_dict_roundtrip(self, mock_agent):
        from python.helpers.history import Topic, History, Message

        history = History(agent=mock_agent)
        topic = Topic(history=history)
        topic.add_message(ai=False, content="x")
        topic.summary = "s"
        data = topic.to_dict()
        assert data["_cls"] == "Topic"
        assert "messages" in data

        restored = Topic.from_dict(data, history=history)
        assert restored.summary == topic.summary
        assert len(restored.messages) == len(topic.messages)


# ─── Bulk ───────────────────────────────────────────────────────────────────


class TestBulk:
    def test_bulk_init(self, mock_agent):
        from python.helpers.history import Bulk, History

        history = History(agent=mock_agent)
        bulk = Bulk(history=history)
        assert bulk.summary == ""
        assert bulk.records == []

    def test_bulk_get_tokens_from_records(self, patch_tokens, mock_agent):
        from python.helpers.history import Bulk, History, Message

        history = History(agent=mock_agent)
        bulk = Bulk(history=history)
        bulk.records.append(Message(ai=False, content="a"))
        bulk.records.append(Message(ai=True, content="b"))
        assert bulk.get_tokens() > 0

    def test_bulk_output_with_summary(self, mock_agent):
        from python.helpers.history import Bulk, History

        history = History(agent=mock_agent)
        bulk = Bulk(history=history)
        bulk.summary = "Bulk summary"
        out = bulk.output()
        assert len(out) == 1
        assert out[0]["content"] == "Bulk summary"

    def test_bulk_compress_returns_false(self, mock_agent):
        from python.helpers.history import Bulk, History

        history = History(agent=mock_agent)
        bulk = Bulk(history=history)
        result = asyncio.run(bulk.compress())
        assert result is False

    def test_bulk_summarize(self, mock_agent):
        from python.helpers.history import Bulk, History, Message

        history = History(agent=mock_agent)
        bulk = Bulk(history=history)
        bulk.records.append(Message(ai=False, content="a"))
        bulk.records.append(Message(ai=True, content="b"))
        mock_agent.call_utility_model = AsyncMock(return_value="Bulk summary")
        mock_agent.read_prompt = MagicMock(return_value="prompt")

        result = asyncio.run(bulk.summarize())
        assert result == "Bulk summary"
        assert bulk.summary == "Bulk summary"

    def test_bulk_to_dict_from_dict_roundtrip(self, mock_agent):
        from python.helpers.history import Bulk, History, Message

        history = History(agent=mock_agent)
        bulk = Bulk(history=history)
        bulk.summary = "Bulk summary"
        bulk.records.append(Message(ai=False, content="x"))
        data = bulk.to_dict()
        assert data["_cls"] == "Bulk"
        assert data["summary"] == "Bulk summary"

        restored = Bulk.from_dict(data, history=history)
        assert restored.summary == bulk.summary
        assert len(restored.records) == 1


# ─── History ────────────────────────────────────────────────────────────────


class TestHistory:
    def test_history_init(self, mock_agent):
        from python.helpers.history import History

        with patch("agent.Agent", MagicMock):
            history = History(agent=mock_agent)
        assert history.counter == 0
        assert history.bulks == []
        assert history.topics == []
        assert history.current is not None

    def test_history_add_message(self, mock_agent):
        from python.helpers.history import History

        history = History(agent=mock_agent)
        msg = history.add_message(ai=False, content="hello")
        assert history.counter == 1
        assert msg.content == "hello"
        assert len(history.current.messages) == 1

    def test_history_new_topic_moves_current_to_topics(self, mock_agent):
        from python.helpers.history import History

        history = History(agent=mock_agent)
        history.add_message(ai=False, content="first")
        history.new_topic()
        assert len(history.topics) == 1
        assert len(history.current.messages) == 0

    def test_history_new_topic_empty_current_does_nothing(self, mock_agent):
        from python.helpers.history import History

        history = History(agent=mock_agent)
        history.new_topic()
        assert len(history.topics) == 0

    def test_history_get_tokens(self, patch_tokens, mock_agent):
        from python.helpers.history import History

        history = History(agent=mock_agent)
        history.add_message(ai=False, content="a")
        history.add_message(ai=True, content="b")
        total = history.get_tokens()
        assert total > 0

    def test_history_is_over_limit(self, patch_settings_history, mock_agent):
        from python.helpers.history import History

        history = History(agent=mock_agent)
        # ctx_size = 4096 * 0.5 = 2048
        # With small history, should be under
        history.add_message(ai=False, content="short")
        with patch("python.helpers.history.tokens.approximate_tokens", return_value=10):
            assert history.is_over_limit() is False

    def test_history_output_combines_bulks_topics_current(self, mock_agent):
        from python.helpers.history import History

        history = History(agent=mock_agent)
        history.add_message(ai=False, content="msg")
        out = history.output()
        assert len(out) >= 1

    def test_history_serialize_deserialize_roundtrip(self, mock_agent):
        from python.helpers.history import History, deserialize_history

        history = History(agent=mock_agent)
        history.add_message(ai=False, content="hello")
        history.add_message(ai=True, content="hi")
        serialized = history.serialize()
        data = json.loads(serialized)
        assert "bulks" in data
        assert "topics" in data
        assert "current" in data

        restored = deserialize_history(serialized, mock_agent)
        assert restored.counter == history.counter
        assert len(restored.current.messages) == 2

    def test_deserialize_history_empty_string_returns_fresh_history(self, mock_agent):
        from python.helpers.history import deserialize_history

        history = deserialize_history("", mock_agent)
        assert history.counter == 0
        assert history.bulks == []
        assert history.topics == []

    def test_history_from_dict_restores_state(self, mock_agent):
        from python.helpers.history import History

        history = History(agent=mock_agent)
        data = {
            "_cls": "History",
            "counter": 5,
            "bulks": [],
            "topics": [{"_cls": "Topic", "summary": "", "messages": []}],
            "current": {
                "_cls": "Topic",
                "summary": "",
                "messages": [
                    {"_cls": "Message", "ai": False, "content": "x", "summary": "", "tokens": 0}
                ],
            },
        }
        History.from_dict(data, history=history)
        assert history.counter == 5
        assert len(history.topics) == 1
        assert len(history.current.messages) == 1


# ─── Record.from_dict ───────────────────────────────────────────────────────


class TestRecordFromDict:
    def test_record_from_dict_message(self, mock_agent):
        from python.helpers.history import Record, History

        history = History(agent=mock_agent)
        data = {"_cls": "Message", "ai": True, "content": "x", "summary": "", "tokens": 0}
        restored = Record.from_dict(data, history=history)
        assert restored.ai is True
        assert restored.content == "x"

    def test_record_from_dict_topic(self, mock_agent):
        from python.helpers.history import Record, History

        history = History(agent=mock_agent)
        data = {"_cls": "Topic", "summary": "", "messages": []}
        restored = Record.from_dict(data, history=history)
        assert restored.summary == ""
        assert restored.messages == []

    def test_record_from_dict_bulk(self, mock_agent):
        from python.helpers.history import Record, History

        history = History(agent=mock_agent)
        data = {"_cls": "Bulk", "summary": "s", "records": []}
        restored = Record.from_dict(data, history=history)
        assert restored.summary == "s"
        assert restored.records == []


# ─── output_text, output_langchain ───────────────────────────────────────────


class TestOutputHelpers:
    def test_output_text_single_message(self):
        from python.helpers.history import output_text, OutputMessage

        msgs = [OutputMessage(ai=False, content="hello")]
        text = output_text(msgs, human_label="user", ai_label="ai")
        assert "user:" in text
        assert "hello" in text

    def test_output_text_custom_labels(self):
        from python.helpers.history import output_text, OutputMessage

        msgs = [OutputMessage(ai=True, content="reply")]
        text = output_text(msgs, human_label="human", ai_label="assistant")
        assert "assistant:" in text
        assert "reply" in text

    def test_output_text_multiple_messages(self):
        from python.helpers.history import output_text, OutputMessage

        msgs = [
            OutputMessage(ai=False, content="q"),
            OutputMessage(ai=True, content="a"),
        ]
        text = output_text(msgs)
        assert "user:" in text or "human:" in text
        assert "ai:" in text
        assert "q" in text
        assert "a" in text

    def test_output_langchain_produces_alternating_types(self):
        from python.helpers.history import output_langchain, OutputMessage

        msgs = [
            OutputMessage(ai=False, content="hi"),
            OutputMessage(ai=True, content="hello"),
        ]
        result = output_langchain(msgs)
        assert len(result) >= 1
        assert isinstance(result[0], (HumanMessage, AIMessage))

    def test_output_langchain_skips_empty_messages(self):
        from python.helpers.history import output_langchain, OutputMessage

        msgs = [
            OutputMessage(ai=False, content=""),
            OutputMessage(ai=True, content="   "),
        ]
        result = output_langchain(msgs)
        assert len(result) == 0

    def test_output_text_with_raw_message_uses_preview(self):
        from python.helpers.history import output_text, OutputMessage

        raw_content = {"raw_content": {"type": "text", "text": "long content"}, "preview": "short"}
        msgs = [OutputMessage(ai=False, content=raw_content)]
        text = output_text(msgs)
        assert "short" in text


# ─── group_outputs_abab, group_messages_abab ────────────────────────────────


class TestGroupOutputsAbab:
    def test_group_outputs_abab_merges_consecutive_same(self):
        from python.helpers.history import group_outputs_abab, OutputMessage

        outputs = [
            OutputMessage(ai=False, content="a"),
            OutputMessage(ai=False, content="b"),
            OutputMessage(ai=True, content="c"),
        ]
        result = group_outputs_abab(outputs)
        assert len(result) == 2
        assert result[0]["ai"] is False
        assert result[1]["ai"] is True

    def test_group_outputs_abab_alternating_unchanged(self):
        from python.helpers.history import group_outputs_abab, OutputMessage

        outputs = [
            OutputMessage(ai=False, content="a"),
            OutputMessage(ai=True, content="b"),
            OutputMessage(ai=False, content="c"),
        ]
        result = group_outputs_abab(outputs)
        assert len(result) == 3


class TestGroupMessagesAbab:
    def test_group_messages_abab_merges_consecutive_same_type(self):
        from python.helpers.history import group_messages_abab

        msgs = [
            HumanMessage(content="a"),
            HumanMessage(content="b"),
            AIMessage(content="c"),
        ]
        result = group_messages_abab(msgs)
        assert len(result) == 2
        assert isinstance(result[0], HumanMessage)
        assert isinstance(result[1], AIMessage)


# ─── compress_large_messages, compress_topics, compress_bulks ───────────────


class TestHistoryCompression:
    def test_compress_topics_empty(self, mock_agent):
        from python.helpers.history import History

        history = History(agent=mock_agent)
        result = asyncio.run(history.compress_topics())
        assert result is False

    def test_compress_bulks_empty_raises_index_error(self, mock_agent):
        from python.helpers.history import History

        history = History(agent=mock_agent)
        # merge_bulks_by returns False when bulks empty, then pop(0) raises
        with pytest.raises(IndexError):
            asyncio.run(history.compress_bulks())

    def test_merge_bulks_by_empty_returns_false(self, mock_agent):
        from python.helpers.history import History

        history = History(agent=mock_agent)
        result = asyncio.run(history.merge_bulks_by(3))
        assert result is False

    def test_topic_compress_large_messages_no_large_returns_false(
        self, patch_settings_history, mock_agent
    ):
        from python.helpers.history import Topic, History

        history = History(agent=mock_agent)
        topic = Topic(history=history)
        topic.add_message(ai=False, content="short")
        with patch("python.helpers.history.tokens.approximate_tokens", return_value=10):
            result = topic.compress_large_messages()
        assert result is False
