"""Tests for python/api/message_queue_add.py — MessageQueueAdd API handler."""

import sys
import threading
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from flask import Response

from python.api.message_queue_add import MessageQueueAdd


def _make_handler(app=None, lock=None):
    return MessageQueueAdd(app=app or MagicMock(), thread_lock=lock or threading.Lock())


class TestMessageQueueAdd:
    @pytest.mark.asyncio
    async def test_adds_message_and_returns_item_id(self, mock_app):
        app, lock = mock_app
        handler = _make_handler(app, lock)
        mock_ctx = MagicMock()
        mock_ctx.id = "ctx-123"

        with patch("python.api.message_queue_add.AgentContext") as MockCtx, \
             patch("python.api.message_queue_add.mq") as mock_mq, \
             patch("python.api.message_queue_add.mark_dirty_for_context"):
            MockCtx.get.return_value = mock_ctx
            mock_mq.add.return_value = {"id": "item-1"}
            mock_mq.get_queue.return_value = [{"id": "item-1"}]

            result = await handler.process({
                "context": "ctx-123",
                "text": "Hello",
            }, MagicMock())

        assert result["ok"] is True
        assert result["item_id"] == "item-1"
        assert result["queue_length"] == 1
        mock_mq.add.assert_called_once_with(mock_ctx, "Hello", [], None)

    @pytest.mark.asyncio
    async def test_context_not_found_returns_404(self, mock_app):
        app, lock = mock_app
        handler = _make_handler(app, lock)

        with patch("python.api.message_queue_add.AgentContext") as MockCtx:
            MockCtx.get.return_value = None
            result = await handler.process({"context": "nonexistent", "text": "Hi"}, MagicMock())

        assert isinstance(result, Response)
        assert result.status_code == 404
        assert b"Context not found" in result.data

    @pytest.mark.asyncio
    async def test_empty_message_returns_400(self, mock_app):
        app, lock = mock_app
        handler = _make_handler(app, lock)
        mock_ctx = MagicMock()

        with patch("python.api.message_queue_add.AgentContext") as MockCtx:
            MockCtx.get.return_value = mock_ctx
            result = await handler.process({
                "context": "ctx-1",
                "text": "   ",
                "attachments": [],
            }, MagicMock())

        assert isinstance(result, Response)
        assert result.status_code == 400
        assert b"Empty message" in result.data

    @pytest.mark.asyncio
    async def test_attachments_only_allowed(self, mock_app):
        app, lock = mock_app
        handler = _make_handler(app, lock)
        mock_ctx = MagicMock()

        with patch("python.api.message_queue_add.AgentContext") as MockCtx, \
             patch("python.api.message_queue_add.mq") as mock_mq, \
             patch("python.api.message_queue_add.mark_dirty_for_context"):
            MockCtx.get.return_value = mock_ctx
            mock_mq.add.return_value = {"id": "item-2"}
            mock_mq.get_queue.return_value = [{"id": "item-2"}]

            result = await handler.process({
                "context": "ctx-1",
                "text": "",
                "attachments": ["file1.txt"],
            }, MagicMock())

        assert result["ok"] is True
        mock_mq.add.assert_called_once_with(mock_ctx, "", ["file1.txt"], None)
