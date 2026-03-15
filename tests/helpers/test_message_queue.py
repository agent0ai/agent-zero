"""Tests for python/helpers/message_queue.py."""

import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


# --- Fixtures ---


@pytest.fixture
def mock_context():
    ctx = MagicMock()
    ctx.get_data = MagicMock(return_value=[])
    ctx.set_data = MagicMock()
    ctx.set_output_data = MagicMock()
    return ctx


# --- get_queue ---


class TestGetQueue:
    def test_get_queue_returns_empty_when_no_data(self, mock_context):
        from python.helpers import message_queue

        mock_context.get_data.return_value = None
        result = message_queue.get_queue(mock_context)
        assert result == []

    def test_get_queue_returns_stored_queue(self, mock_context):
        from python.helpers import message_queue

        queue = [{"id": "1", "text": "hello"}]
        mock_context.get_data.return_value = queue
        result = message_queue.get_queue(mock_context)
        assert result == queue


# --- add ---


class TestAdd:
    def test_add_appends_item_with_generated_id(self, mock_context):
        from python.helpers import message_queue

        mock_context.get_data.return_value = []
        item = message_queue.add(mock_context, "Hello world")
        assert item["text"] == "Hello world"
        assert "id" in item
        assert item["seq"] == 1
        mock_context.set_data.assert_called()
        mock_context.set_output_data.assert_called()

    def test_add_with_attachments_converts_to_full_paths(self, mock_context):
        from python.helpers import message_queue

        mock_context.get_data.return_value = []
        item = message_queue.add(
            mock_context,
            "Text",
            attachments=["file1.txt", "/abs/path/file2.txt"],
        )
        assert "/a0/usr/uploads/file1.txt" in item["attachments"]
        assert "/abs/path/file2.txt" in item["attachments"]

    def test_add_with_custom_item_id(self, mock_context):
        from python.helpers import message_queue

        mock_context.get_data.return_value = []
        item = message_queue.add(mock_context, "Text", item_id="custom-123")
        assert item["id"] == "custom-123"


# --- remove ---


class TestRemove:
    def test_remove_without_id_clears_all(self, mock_context):
        from python.helpers import message_queue

        mock_context.get_data.return_value = [{"id": "1"}, {"id": "2"}]
        count = message_queue.remove(mock_context)
        assert count == 0
        mock_context.set_data.assert_called_with(message_queue.QUEUE_KEY, [])
        mock_context.set_output_data.assert_called_with(message_queue.QUEUE_KEY, [])

    def test_remove_by_id(self, mock_context):
        from python.helpers import message_queue

        mock_context.get_data.return_value = [
            {"id": "1", "text": "a"},
            {"id": "2", "text": "b"},
        ]
        count = message_queue.remove(mock_context, item_id="1")
        assert count == 1
        call_args = mock_context.set_data.call_args[0]
        assert call_args[1][0]["id"] == "2"


# --- pop_first ---


class TestPopFirst:
    def test_pop_first_returns_none_when_empty(self, mock_context):
        from python.helpers import message_queue

        mock_context.get_data.return_value = []
        result = message_queue.pop_first(mock_context)
        assert result is None

    def test_pop_first_returns_and_removes_first(self, mock_context):
        from python.helpers import message_queue

        first = {"id": "1", "text": "first"}
        mock_context.get_data.return_value = [first, {"id": "2", "text": "second"}]
        result = message_queue.pop_first(mock_context)
        assert result == first
        call_args = mock_context.set_data.call_args[0]
        assert len(call_args[1]) == 1
        assert call_args[1][0]["id"] == "2"


# --- pop_item ---


class TestPopItem:
    def test_pop_item_returns_none_when_not_found(self, mock_context):
        from python.helpers import message_queue

        mock_context.get_data.return_value = [{"id": "1", "text": "a"}]
        result = message_queue.pop_item(mock_context, "nonexistent")
        assert result is None

    def test_pop_item_removes_and_returns_matching(self, mock_context):
        from python.helpers import message_queue

        target = {"id": "target", "text": "target text"}
        mock_context.get_data.return_value = [
            {"id": "1", "text": "a"},
            target,
            {"id": "2", "text": "b"},
        ]
        result = message_queue.pop_item(mock_context, "target")
        assert result == target
        call_args = mock_context.set_data.call_args[0]
        assert len(call_args[1]) == 2


# --- has_queue ---


class TestHasQueue:
    def test_has_queue_false_when_empty(self, mock_context):
        from python.helpers import message_queue

        mock_context.get_data.return_value = []
        assert message_queue.has_queue(mock_context) is False

    def test_has_queue_true_when_not_empty(self, mock_context):
        from python.helpers import message_queue

        mock_context.get_data.return_value = [{"id": "1"}]
        assert message_queue.has_queue(mock_context) is True


# --- log_user_message ---


class TestLogUserMessage:
    def test_log_user_message_calls_print_and_log(self, mock_context):
        from python.helpers import message_queue

        mock_context.log = MagicMock()
        mock_context.log.log = MagicMock()
        with patch("python.helpers.message_queue.PrintStyle") as mock_ps:
            mock_ps.return_value.print = MagicMock()
            message_queue.log_user_message(mock_context, "Hello", [])
            assert mock_context.log.log.called
            call_kwargs = mock_context.log.log.call_args[1]
            assert call_kwargs["type"] == "user"
            assert call_kwargs["content"] == "Hello"

    def test_log_user_message_includes_attachments_in_log(self, mock_context):
        from python.helpers import message_queue

        mock_context.log = MagicMock()
        mock_context.log.log = MagicMock()
        with patch("python.helpers.message_queue.PrintStyle"):
            message_queue.log_user_message(
                mock_context,
                "Msg",
                ["/path/to/file1.txt", "/other/file2.pdf"],
            )
            call_kwargs = mock_context.log.log.call_args[1]
            assert call_kwargs["kvps"]["attachments"] == ["file1.txt", "file2.pdf"]


# --- send_message, send_next, send_all_aggregated ---


class TestSendMessage:
    def test_send_message_calls_log_and_communicate(self, mock_context):
        from python.helpers import message_queue

        mock_context.log = MagicMock()
        mock_context.log.log = MagicMock()
        mock_context.communicate = MagicMock()
        with patch("python.helpers.message_queue.PrintStyle"):
            with patch("agent.UserMessage") as mock_um:
                message_queue.send_message(
                    mock_context,
                    {"text": "Hello", "attachments": []},
                )
                mock_context.communicate.assert_called_once()
                mock_um.assert_called_once_with("Hello", [])


class TestSendNext:
    def test_send_next_returns_false_when_empty(self, mock_context):
        from python.helpers import message_queue

        mock_context.get_data.return_value = []
        result = message_queue.send_next(mock_context)
        assert result is False

    def test_send_next_pops_and_sends_when_not_empty(self, mock_context):
        from python.helpers import message_queue

        mock_context.get_data.return_value = [{"id": "1", "text": "Hi", "attachments": []}]
        mock_context.log = MagicMock()
        mock_context.log.log = MagicMock()
        mock_context.communicate = MagicMock()
        with patch("python.helpers.message_queue.PrintStyle"):
            with patch("agent.UserMessage"):
                result = message_queue.send_next(mock_context)
                assert result is True
                mock_context.communicate.assert_called_once()


class TestSendAllAggregated:
    def test_send_all_aggregated_returns_zero_when_empty(self, mock_context):
        from python.helpers import message_queue

        mock_context.get_data.return_value = []
        result = message_queue.send_all_aggregated(mock_context)
        assert result == 0

    def test_send_all_aggregated_combines_and_sends(self, mock_context):
        from python.helpers import message_queue

        mock_context.get_data.side_effect = [
            [{"id": "1", "text": "A", "attachments": []}, {"id": "2", "text": "B", "attachments": []}],
            [],
        ]
        mock_context.log = MagicMock()
        mock_context.log.log = MagicMock()
        mock_context.communicate = MagicMock()
        with patch("python.helpers.message_queue.PrintStyle"):
            with patch("agent.UserMessage") as mock_um:
                result = message_queue.send_all_aggregated(mock_context)
                assert result == 2
                mock_um.assert_called_once()
                args = mock_um.call_args[0]
                assert "---" in args[0]
                assert "A" in args[0] and "B" in args[0]
