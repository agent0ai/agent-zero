"""Tests for python/api/nudge.py — Nudge API handler."""

import sys
import threading
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from python.api.nudge import Nudge


def _make_handler(app=None, lock=None):
    return Nudge(app=app or MagicMock(), thread_lock=lock or threading.Lock())


class TestNudge:
    @pytest.mark.asyncio
    async def test_nudge_calls_context_nudge(self):
        handler = _make_handler()
        mock_ctx = MagicMock()
        mock_ctx.id = "ctx-123"
        with patch.object(handler, "use_context", return_value=mock_ctx):
            result = await handler.process({"ctxid": "ctx-123"}, MagicMock())
        mock_ctx.nudge.assert_called_once()
        assert result["message"] == "Process reset, agent nudged."
        assert result["ctxid"] == "ctx-123"

    @pytest.mark.asyncio
    async def test_nudge_logs_message(self):
        handler = _make_handler()
        mock_ctx = MagicMock()
        mock_ctx.id = "ctx-1"
        with patch.object(handler, "use_context", return_value=mock_ctx):
            await handler.process({"ctxid": "ctx-1"}, MagicMock())
        mock_ctx.log.log.assert_called_once()
        call_args = mock_ctx.log.log.call_args
        assert call_args[1]["type"] == "info"
        assert "nudged" in call_args[1]["content"]

    @pytest.mark.asyncio
    async def test_raises_when_no_ctxid(self):
        handler = _make_handler()
        with pytest.raises(Exception, match="No context id provided"):
            await handler.process({}, MagicMock())

    @pytest.mark.asyncio
    async def test_raises_when_empty_ctxid(self):
        handler = _make_handler()
        with pytest.raises(Exception, match="No context id provided"):
            await handler.process({"ctxid": ""}, MagicMock())
