"""Tests for python/api/pause.py — Pause API handler."""

import sys
import threading
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from python.api.pause import Pause


def _make_handler(app=None, lock=None):
    return Pause(app=app or MagicMock(), thread_lock=lock or threading.Lock())


class TestPause:
    @pytest.mark.asyncio
    async def test_sets_paused_true(self):
        handler = _make_handler()
        mock_ctx = MagicMock()
        mock_ctx.paused = False
        with patch.object(handler, "use_context", return_value=mock_ctx):
            result = await handler.process({"context": "ctx-1", "paused": True}, MagicMock())
        assert mock_ctx.paused is True
        assert result["pause"] is True
        assert "paused" in result["message"].lower()

    @pytest.mark.asyncio
    async def test_sets_paused_false(self):
        handler = _make_handler()
        mock_ctx = MagicMock()
        mock_ctx.paused = True
        with patch.object(handler, "use_context", return_value=mock_ctx):
            result = await handler.process({"context": "ctx-1", "paused": False}, MagicMock())
        assert mock_ctx.paused is False
        assert result["pause"] is False
        assert "unpaused" in result["message"].lower()

    @pytest.mark.asyncio
    async def test_defaults_paused_to_false(self):
        handler = _make_handler()
        mock_ctx = MagicMock()
        mock_ctx.paused = True
        with patch.object(handler, "use_context", return_value=mock_ctx):
            result = await handler.process({"context": "ctx-1"}, MagicMock())
        assert mock_ctx.paused is False
