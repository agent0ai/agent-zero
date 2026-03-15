"""Tests for python/api/api_reset_chat.py — ApiResetChat API handler."""

import sys
import threading
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from flask import Response

from python.api.api_reset_chat import ApiResetChat


def _make_handler(app=None, lock=None):
    return ApiResetChat(app=app or MagicMock(), thread_lock=lock or threading.Lock())


class TestApiResetChat:
    @pytest.mark.asyncio
    async def test_missing_context_id_returns_400(self, mock_app):
        app, lock = mock_app
        handler = _make_handler(app, lock)

        result = await handler.process({}, MagicMock())

        assert isinstance(result, Response)
        assert result.status_code == 400
        assert b"context_id is required" in result.data

    @pytest.mark.asyncio
    async def test_context_not_found_returns_404(self, mock_app):
        app, lock = mock_app
        handler = _make_handler(app, lock)

        with patch("python.api.api_reset_chat.AgentContext") as MockCtx:
            MockCtx.use.return_value = None
            result = await handler.process({"context_id": "nonexistent"}, MagicMock())

        assert isinstance(result, Response)
        assert result.status_code == 404
        assert b"Chat context not found" in result.data

    @pytest.mark.asyncio
    async def test_resets_context_and_returns_success(self, mock_app):
        app, lock = mock_app
        handler = _make_handler(app, lock)
        mock_ctx = MagicMock()

        with patch("python.api.api_reset_chat.AgentContext") as MockCtx, \
             patch("python.api.api_reset_chat.persist_chat") as mock_persist:
            MockCtx.use.return_value = mock_ctx
            result = await handler.process({"context_id": "ctx-123"}, MagicMock())

        assert result["success"] is True
        assert result["message"] == "Chat reset successfully"
        assert result["context_id"] == "ctx-123"
        mock_ctx.reset.assert_called_once()
        mock_persist.save_tmp_chat.assert_called_once_with(mock_ctx)
        mock_persist.remove_msg_files.assert_called_once_with("ctx-123")

    @pytest.mark.asyncio
    async def test_exception_returns_500(self, mock_app):
        app, lock = mock_app
        handler = _make_handler(app, lock)

        with patch("python.api.api_reset_chat.AgentContext") as MockCtx:
            MockCtx.use.side_effect = Exception("Unexpected error")
            result = await handler.process({"context_id": "ctx-1"}, MagicMock())

        assert isinstance(result, Response)
        assert result.status_code == 500
        assert b"Unexpected error" in result.data

    def test_requires_api_key_true(self):
        assert ApiResetChat.requires_api_key() is True

    def test_get_methods_returns_post(self):
        assert ApiResetChat.get_methods() == ["POST"]
