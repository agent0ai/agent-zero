"""Tests for python/api/chat_create.py — CreateChat API handler."""

import sys
import threading
from pathlib import Path
from unittest.mock import MagicMock, AsyncMock, patch

import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from python.api.chat_create import CreateChat


def _make_handler(app=None, lock=None):
    return CreateChat(app=app or MagicMock(), thread_lock=lock or threading.Lock())


class TestCreateChat:
    @pytest.mark.asyncio
    async def test_creates_new_context_and_returns_ctxid(self, mock_app):
        app, lock = mock_app
        handler = _make_handler(app, lock)
        mock_ctx = MagicMock()
        mock_ctx.id = "new-ctx-123"

        with patch.object(handler, "use_context", return_value=mock_ctx), \
             patch("python.api.chat_create.AgentContext") as MockCtx, \
             patch("python.helpers.state_monitor_integration.mark_dirty_all"):
            MockCtx.get.return_value = None
            result = await handler.process({"current_context": "", "new_context": ""}, MagicMock())

        assert result["ok"] is True
        assert result["ctxid"] == "new-ctx-123"
        assert "message" in result

    @pytest.mark.asyncio
    async def test_uses_provided_new_context_id(self, mock_app):
        app, lock = mock_app
        handler = _make_handler(app, lock)
        mock_ctx = MagicMock()
        mock_ctx.id = "provided-ctx-456"

        with patch.object(handler, "use_context", return_value=mock_ctx) as use_ctx, \
             patch("python.api.chat_create.AgentContext"), \
             patch("python.helpers.state_monitor_integration.mark_dirty_all"):
            await handler.process({"current_context": "old", "new_context": "provided-ctx-456"}, MagicMock())
            use_ctx.assert_called_once_with("provided-ctx-456")

    @pytest.mark.asyncio
    async def test_calls_mark_dirty_all_on_success(self, mock_app):
        app, lock = mock_app
        handler = _make_handler(app, lock)
        mock_ctx = MagicMock()
        mock_ctx.id = "ctx-1"

        with patch.object(handler, "use_context", return_value=mock_ctx), \
             patch("python.api.chat_create.AgentContext"), \
             patch("python.helpers.state_monitor_integration.mark_dirty_all") as mark_dirty:
            await handler.process({}, MagicMock())
            mark_dirty.assert_called_once_with(reason="api.chat_create.CreateChat")

    @pytest.mark.asyncio
    async def test_response_format(self, mock_app):
        app, lock = mock_app
        handler = _make_handler(app, lock)
        mock_ctx = MagicMock()
        mock_ctx.id = "ctx-id"

        with patch.object(handler, "use_context", return_value=mock_ctx), \
             patch("python.api.chat_create.AgentContext"), \
             patch("python.helpers.state_monitor_integration.mark_dirty_all"):
            result = await handler.process({}, MagicMock())

        assert "ok" in result
        assert "ctxid" in result
        assert "message" in result
        assert isinstance(result["message"], str)
