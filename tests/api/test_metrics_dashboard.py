"""Tests for python/api/metrics_dashboard.py — MetricsDashboard API handler."""

import sys
import threading
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from python.api.metrics_dashboard import MetricsDashboard


def _make_handler(app=None, lock=None):
    return MetricsDashboard(app=app or MagicMock(), thread_lock=lock or threading.Lock())


class TestMetricsDashboard:
    @pytest.mark.asyncio
    async def test_snapshot_action_returns_collector_data(self):
        handler = _make_handler()
        mock_snapshot = {"requests": 10, "errors": 0}
        with patch("python.api.metrics_dashboard.collector.snapshot", return_value=mock_snapshot):
            result = await handler.process({"action": "snapshot"}, MagicMock())
        assert result["success"] is True
        assert result["requests"] == 10
        assert result["errors"] == 0

    @pytest.mark.asyncio
    async def test_default_action_is_snapshot(self):
        handler = _make_handler()
        with patch("python.api.metrics_dashboard.collector.snapshot", return_value={}):
            result = await handler.process({}, MagicMock())
        assert result["success"] is True

    @pytest.mark.asyncio
    async def test_clear_action_clears_and_returns_message(self):
        handler = _make_handler()
        with patch("python.api.metrics_dashboard.collector.clear"):
            result = await handler.process({"action": "clear"}, MagicMock())
        assert result["success"] is True
        assert "cleared" in result["message"].lower()

    @pytest.mark.asyncio
    async def test_unknown_action_returns_error(self):
        handler = _make_handler()
        result = await handler.process({"action": "unknown"}, MagicMock())
        assert result["success"] is False
        assert "Unknown action" in result["error"]
        assert "unknown" in result["error"]
