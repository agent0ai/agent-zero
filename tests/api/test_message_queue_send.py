"""Tests for python/api/message_queue_send.py — MessageQueueSend API handler."""

import sys
import threading
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from flask import Response

from python.api.message_queue_send import MessageQueueSend


def _make_handler(app=None, lock=None):
    return MessageQueueSend(app=app or MagicMock(), thread_lock=lock or threading.Lock())


class TestMessageQueueSend:
    @pytest.mark.asyncio
    async def test_empty_queue_returns_message(self, mock_app):
        app, lock = mock_app
        handler = _make_handler(app, lock)
        mock_ctx = MagicMock()

        with patch("python.api.message_queue_send.AgentContext") as MockCtx, \
             patch("python.api.message_queue_send.mq") as mock_mq:
            MockCtx.get.return_value = mock_ctx
            mock_mq.has_queue.return_value = False

            result = await handler.process({"context": "ctx-123"}, MagicMock())

        assert result["ok"] is True
        assert result["message"] == "Queue empty"

    @pytest.mark.asyncio
    async def test_send_all_aggregated(self, mock_app):
        app, lock = mock_app
        handler = _make_handler(app, lock)
        mock_ctx = MagicMock()

        with patch("python.api.message_queue_send.AgentContext") as MockCtx, \
             patch("python.api.message_queue_send.mq") as mock_mq, \
             patch("python.api.message_queue_send.mark_dirty_for_context"):
            MockCtx.get.return_value = mock_ctx
            mock_mq.has_queue.return_value = True
            mock_mq.send_all_aggregated.return_value = 3

            result = await handler.process({
                "context": "ctx-123",
                "send_all": True,
            }, MagicMock())

        assert result["ok"] is True
        assert result["sent_count"] == 3
        mock_mq.send_all_aggregated.assert_called_once_with(mock_ctx)

    @pytest.mark.asyncio
    async def test_send_single_item(self, mock_app):
        app, lock = mock_app
        handler = _make_handler(app, lock)
        mock_ctx = MagicMock()
        item = {"id": "item-1", "text": "Hi"}

        with patch("python.api.message_queue_send.AgentContext") as MockCtx, \
             patch("python.api.message_queue_send.mq") as mock_mq, \
             patch("python.api.message_queue_send.mark_dirty_for_context"):
            MockCtx.get.return_value = mock_ctx
            mock_mq.has_queue.return_value = True
            mock_mq.pop_item.return_value = item
            mock_mq.send_message = MagicMock()

            result = await handler.process({
                "context": "ctx-123",
                "item_id": "item-1",
            }, MagicMock())

        assert result["ok"] is True
        assert result["sent_item_id"] == "item-1"
        mock_mq.send_message.assert_called_once_with(mock_ctx, item)

    @pytest.mark.asyncio
    async def test_item_not_found_returns_404(self, mock_app):
        app, lock = mock_app
        handler = _make_handler(app, lock)
        mock_ctx = MagicMock()

        with patch("python.api.message_queue_send.AgentContext") as MockCtx, \
             patch("python.api.message_queue_send.mq") as mock_mq:
            MockCtx.get.return_value = mock_ctx
            mock_mq.has_queue.return_value = True
            mock_mq.pop_item.return_value = None
            mock_mq.pop_first.return_value = None

            result = await handler.process({
                "context": "ctx-123",
                "item_id": "nonexistent",
            }, MagicMock())

        assert isinstance(result, Response)
        assert result.status_code == 404
        assert b"Item not found" in result.data

    @pytest.mark.asyncio
    async def test_context_not_found_returns_404(self, mock_app):
        app, lock = mock_app
        handler = _make_handler(app, lock)

        with patch("python.api.message_queue_send.AgentContext") as MockCtx:
            MockCtx.get.return_value = None
            result = await handler.process({"context": "nonexistent"}, MagicMock())

        assert isinstance(result, Response)
        assert result.status_code == 404
        assert b"Context not found" in result.data
