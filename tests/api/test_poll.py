"""Tests for python/api/poll.py — Poll API handler."""

import sys
import threading
from pathlib import Path
from unittest.mock import MagicMock, AsyncMock, patch

import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from python.api.poll import Poll


def _make_handler(app=None, lock=None):
    return Poll(app=app or MagicMock(), thread_lock=lock or threading.Lock())


class TestPoll:
    @pytest.mark.asyncio
    async def test_process_calls_build_snapshot(self):
        handler = _make_handler()
        mock_snapshot = {"state": "idle", "log": []}
        with patch("python.api.poll.build_snapshot", new_callable=AsyncMock, return_value=mock_snapshot):
            result = await handler.process({"context": "ctx-1"}, MagicMock())
        assert result == mock_snapshot

    @pytest.mark.asyncio
    async def test_process_passes_context_to_build_snapshot(self):
        handler = _make_handler()
        with patch("python.api.poll.build_snapshot", new_callable=AsyncMock) as mock_build:
            await handler.process({"context": "ctx-123"}, MagicMock())
        mock_build.assert_called_once_with(context="ctx-123", log_from=0, notifications_from=0, timezone=None)

    @pytest.mark.asyncio
    async def test_process_passes_log_from_and_notifications_from(self):
        handler = _make_handler()
        with patch("python.api.poll.build_snapshot", new_callable=AsyncMock) as mock_build:
            await handler.process({
                "context": "ctx-1",
                "log_from": 10,
                "notifications_from": 5,
                "timezone": "UTC"
            }, MagicMock())
        mock_build.assert_called_once_with(context="ctx-1", log_from=10, notifications_from=5, timezone="UTC")
