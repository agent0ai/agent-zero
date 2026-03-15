"""Tests for python/api/message_async.py — MessageAsync API handler."""

import sys
import threading
from pathlib import Path
from unittest.mock import MagicMock, AsyncMock, patch

import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from python.api.message_async import MessageAsync


def _make_handler(app=None, lock=None):
    return MessageAsync(app=app or MagicMock(), thread_lock=lock or threading.Lock())


class TestMessageAsync:
    @pytest.mark.asyncio
    async def test_respond_returns_received_message_not_result(self, mock_app):
        app, lock = mock_app
        handler = _make_handler(app, lock)
        mock_task = MagicMock()
        mock_ctx = MagicMock()
        mock_ctx.id = "ctx-123"

        result = await handler.respond(mock_task, mock_ctx)

        assert result["message"] == "Message received."
        assert result["context"] == "ctx-123"

    @pytest.mark.asyncio
    async def test_process_delegates_to_communicate(self, mock_app):
        app, lock = mock_app
        handler = _make_handler(app, lock)
        mock_task = MagicMock()
        mock_ctx = MagicMock()
        mock_ctx.id = "ctx-456"

        with patch.object(handler, "communicate", AsyncMock(return_value=(mock_task, mock_ctx))):
            result = await handler.process(
                {},
                MagicMock(content_type="application/json", get_json=MagicMock(return_value={"text": "Hi", "context": "ctx-456"}))
            )

        assert result["message"] == "Message received."
        assert result["context"] == "ctx-456"

    def test_inherits_from_message(self):
        from python.api.message import Message
        assert issubclass(MessageAsync, Message)
