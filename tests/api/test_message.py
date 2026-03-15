"""Tests for python/api/message.py — Message API handler."""

import sys
import threading
from pathlib import Path
from unittest.mock import MagicMock, AsyncMock, patch

import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from python.api.message import Message


def _make_handler(app=None, lock=None):
    return Message(app=app or MagicMock(), thread_lock=lock or threading.Lock())


class TestMessage:
    @pytest.mark.asyncio
    async def test_process_delegates_to_communicate_and_respond(self, mock_app):
        app, lock = mock_app
        handler = _make_handler(app, lock)
        mock_task = MagicMock()
        mock_task.result = AsyncMock(return_value="Agent response")
        mock_ctx = MagicMock()
        mock_ctx.id = "ctx-123"

        with patch.object(handler, "communicate", AsyncMock(return_value=(mock_task, mock_ctx))):
            result = await handler.process(
                {},
                MagicMock(content_type="application/json", get_json=MagicMock(return_value={"text": "Hello", "context": "ctx-123"}))
            )

        assert result["message"] == "Agent response"
        assert result["context"] == "ctx-123"

    @pytest.mark.asyncio
    async def test_respond_returns_message_and_context(self, mock_app):
        app, lock = mock_app
        handler = _make_handler(app, lock)
        mock_task = MagicMock()
        mock_task.result = AsyncMock(return_value="Reply")
        mock_ctx = MagicMock()
        mock_ctx.id = "ctx-456"

        result = await handler.respond(mock_task, mock_ctx)

        assert result["message"] == "Reply"
        assert result["context"] == "ctx-456"

    @pytest.mark.asyncio
    async def test_communicate_json_calls_use_context_and_mq(self, mock_app):
        app, lock = mock_app
        handler = _make_handler(app, lock)
        mock_ctx = MagicMock()
        mock_ctx.id = "ctx-1"
        mock_ctx.get_agent = MagicMock(return_value=MagicMock())
        mock_task = MagicMock()
        mock_ctx.communicate = MagicMock(return_value=mock_task)

        request = MagicMock()
        request.content_type = "application/json"
        request.get_json = MagicMock(return_value={"text": "Hi", "context": "ctx-1"})

        with patch.object(handler, "use_context", return_value=mock_ctx) as use_ctx, \
             patch("python.api.message.extension") as mock_ext, \
             patch("python.api.message.mq") as mock_mq:
            mock_ext.call_extensions = AsyncMock()
            task, ctx = await handler.communicate({}, request)

        use_ctx.assert_called_once_with("ctx-1")
        mock_mq.log_user_message.assert_called_once()
        assert ctx.id == "ctx-1"

    @pytest.mark.asyncio
    async def test_communicate_calls_extension_point(self, mock_app):
        app, lock = mock_app
        handler = _make_handler(app, lock)
        mock_agent = MagicMock()
        mock_ctx = MagicMock()
        mock_ctx.id = "ctx-1"
        mock_ctx.get_agent = MagicMock(return_value=mock_agent)
        mock_ctx.communicate = MagicMock(return_value=MagicMock())

        request = MagicMock()
        request.content_type = "application/json"
        request.get_json = MagicMock(return_value={"text": "Hi", "context": "ctx-1"})

        with patch.object(handler, "use_context", return_value=mock_ctx), \
             patch("python.api.message.extension") as mock_ext, \
             patch("python.api.message.mq"):
            mock_ext.call_extensions = AsyncMock()
            await handler.communicate({}, request)

        mock_ext.call_extensions.assert_called_once()
        call_kw = mock_ext.call_extensions.call_args[1]
        assert call_kw["agent"] == mock_agent
        assert call_kw["data"]["message"] == "Hi"
        assert call_kw["data"]["attachment_paths"] == []
