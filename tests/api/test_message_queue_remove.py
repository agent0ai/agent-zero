"""Tests for python/api/message_queue_remove.py — MessageQueueRemove API handler."""

import sys
import threading
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from flask import Response

from python.api.message_queue_remove import MessageQueueRemove


def _make_handler(app=None, lock=None):
    return MessageQueueRemove(app=app or MagicMock(), thread_lock=lock or threading.Lock())


class TestMessageQueueRemove:
    @pytest.mark.asyncio
    async def test_removes_item_and_returns_remaining(self, mock_app):
        app, lock = mock_app
        handler = _make_handler(app, lock)
        mock_ctx = MagicMock()

        with patch("python.api.message_queue_remove.AgentContext") as MockCtx, \
             patch("python.api.message_queue_remove.mq") as mock_mq, \
             patch("python.api.message_queue_remove.mark_dirty_for_context"):
            MockCtx.get.return_value = mock_ctx
            mock_mq.remove.return_value = 2

            result = await handler.process({
                "context": "ctx-123",
                "item_id": "item-1",
            }, MagicMock())

        assert result["ok"] is True
        assert result["remaining"] == 2
        mock_mq.remove.assert_called_once_with(mock_ctx, "item-1")

    @pytest.mark.asyncio
    async def test_context_not_found_returns_404(self, mock_app):
        app, lock = mock_app
        handler = _make_handler(app, lock)

        with patch("python.api.message_queue_remove.AgentContext") as MockCtx:
            MockCtx.get.return_value = None
            result = await handler.process({"context": "nonexistent"}, MagicMock())

        assert isinstance(result, Response)
        assert result.status_code == 404
        assert b"Context not found" in result.data

    @pytest.mark.asyncio
    async def test_item_id_none_clears_all(self, mock_app):
        app, lock = mock_app
        handler = _make_handler(app, lock)
        mock_ctx = MagicMock()

        with patch("python.api.message_queue_remove.AgentContext") as MockCtx, \
             patch("python.api.message_queue_remove.mq") as mock_mq, \
             patch("python.api.message_queue_remove.mark_dirty_for_context"):
            MockCtx.get.return_value = mock_ctx
            mock_mq.remove.return_value = 0

            result = await handler.process({"context": "ctx-1"}, MagicMock())

        assert result["ok"] is True
        assert result["remaining"] == 0
        mock_mq.remove.assert_called_once_with(mock_ctx, None)
