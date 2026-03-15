"""Tests for python/api/ctx_window_get.py — GetCtxWindow API handler."""

import sys
import threading
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from python.api.ctx_window_get import GetCtxWindow


def _make_handler(app=None, lock=None):
    return GetCtxWindow(app=app or MagicMock(), thread_lock=lock or threading.Lock())


class TestGetCtxWindow:
    @pytest.mark.asyncio
    async def test_returns_content_and_tokens_from_window(self):
        handler = _make_handler()
        mock_ctx = MagicMock()
        mock_agent = MagicMock()
        mock_agent.DATA_NAME_CTX_WINDOW = "ctx_window"
        mock_agent.get_data.return_value = {"text": "context text", "tokens": 100}
        mock_ctx.streaming_agent = None
        mock_ctx.agent0 = mock_agent
        with patch.object(handler, "use_context", return_value=mock_ctx):
            result = await handler.process({"context": "ctx-1"}, MagicMock())
        assert result["content"] == "context text"
        assert result["tokens"] == 100

    @pytest.mark.asyncio
    async def test_returns_empty_when_no_window(self):
        handler = _make_handler()
        mock_ctx = MagicMock()
        mock_agent = MagicMock()
        mock_agent.DATA_NAME_CTX_WINDOW = "ctx_window"
        mock_agent.get_data.return_value = None
        mock_ctx.streaming_agent = None
        mock_ctx.agent0 = mock_agent
        with patch.object(handler, "use_context", return_value=mock_ctx):
            result = await handler.process({"context": "ctx-1"}, MagicMock())
        assert result["content"] == ""
        assert result["tokens"] == 0

    @pytest.mark.asyncio
    async def test_returns_empty_when_window_not_dict(self):
        handler = _make_handler()
        mock_ctx = MagicMock()
        mock_agent = MagicMock()
        mock_agent.DATA_NAME_CTX_WINDOW = "ctx_window"
        mock_agent.get_data.return_value = "invalid"
        mock_ctx.streaming_agent = None
        mock_ctx.agent0 = mock_agent
        with patch.object(handler, "use_context", return_value=mock_ctx):
            result = await handler.process({"context": "ctx-1"}, MagicMock())
        assert result["content"] == ""
        assert result["tokens"] == 0

    @pytest.mark.asyncio
    async def test_uses_streaming_agent_when_present(self):
        handler = _make_handler()
        mock_ctx = MagicMock()
        mock_streaming = MagicMock()
        mock_streaming.DATA_NAME_CTX_WINDOW = "ctx_window"
        mock_streaming.get_data.return_value = {"text": "streaming ctx", "tokens": 50}
        mock_ctx.streaming_agent = mock_streaming
        mock_ctx.agent0 = MagicMock()
        with patch.object(handler, "use_context", return_value=mock_ctx):
            result = await handler.process({"context": "ctx-1"}, MagicMock())
        assert result["content"] == "streaming ctx"
        assert result["tokens"] == 50
