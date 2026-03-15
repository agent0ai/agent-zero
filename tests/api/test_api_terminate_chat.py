"""Tests for python/api/api_terminate_chat.py — ApiTerminateChat API handler."""

import sys
import threading
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from flask import Response

from python.api.api_terminate_chat import ApiTerminateChat


def _make_handler(app=None, lock=None):
    return ApiTerminateChat(app=app or MagicMock(), thread_lock=lock or threading.Lock())


class TestApiTerminateChat:
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

        with patch("python.api.api_terminate_chat.AgentContext") as MockCtx:
            MockCtx.use.return_value = None
            result = await handler.process({"context_id": "nonexistent"}, MagicMock())

        assert isinstance(result, Response)
        assert result.status_code == 404
        assert b"Chat context not found" in result.data

    @pytest.mark.asyncio
    async def test_removes_context_and_returns_success(self, mock_app):
        app, lock = mock_app
        handler = _make_handler(app, lock)
        mock_ctx = MagicMock()
        mock_ctx.id = "ctx-123"

        with patch("python.api.api_terminate_chat.AgentContext") as MockCtx, \
             patch("python.api.api_terminate_chat.remove_chat") as mock_remove:
            MockCtx.use.return_value = mock_ctx
            result = await handler.process({"context_id": "ctx-123"}, MagicMock())

        assert result["success"] is True
        assert result["message"] == "Chat deleted successfully"
        assert result["context_id"] == "ctx-123"
        MockCtx.remove.assert_called_once_with("ctx-123")
        mock_remove.assert_called_once_with("ctx-123")

    @pytest.mark.asyncio
    async def test_exception_returns_500(self, mock_app):
        app, lock = mock_app
        handler = _make_handler(app, lock)

        with patch("python.api.api_terminate_chat.AgentContext") as MockCtx:
            MockCtx.use.side_effect = Exception("DB error")
            result = await handler.process({"context_id": "ctx-1"}, MagicMock())

        assert isinstance(result, Response)
        assert result.status_code == 500
        assert b"DB error" in result.data

    def test_requires_api_key_true(self):
        assert ApiTerminateChat.requires_api_key() is True

    def test_get_methods_returns_post(self):
        assert ApiTerminateChat.get_methods() == ["POST"]
