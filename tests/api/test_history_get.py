"""Tests for python/api/history_get.py — GetHistory API handler."""

import sys
import threading
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from python.api.history_get import GetHistory


def _make_handler(app=None, lock=None):
    return GetHistory(app=app or MagicMock(), thread_lock=lock or threading.Lock())


class TestGetHistory:
    @pytest.mark.asyncio
    async def test_returns_history_and_tokens(self):
        handler = _make_handler()
        mock_ctx = MagicMock()
        mock_agent = MagicMock()
        mock_agent.history.output_text.return_value = "msg1\nmsg2"
        mock_agent.history.get_tokens.return_value = 42
        mock_ctx.streaming_agent = None
        mock_ctx.agent0 = mock_agent
        with patch.object(handler, "use_context", return_value=mock_ctx):
            result = await handler.process({"context": "ctx-1"}, MagicMock())
        assert result["history"] == "msg1\nmsg2"
        assert result["tokens"] == 42

    @pytest.mark.asyncio
    async def test_uses_streaming_agent_when_present(self):
        handler = _make_handler()
        mock_ctx = MagicMock()
        mock_streaming = MagicMock()
        mock_streaming.history.output_text.return_value = "streaming history"
        mock_streaming.history.get_tokens.return_value = 10
        mock_ctx.streaming_agent = mock_streaming
        mock_ctx.agent0 = MagicMock()
        with patch.object(handler, "use_context", return_value=mock_ctx):
            result = await handler.process({"context": "ctx-1"}, MagicMock())
        assert result["history"] == "streaming history"
        assert result["tokens"] == 10
