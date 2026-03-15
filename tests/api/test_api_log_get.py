"""Tests for python/api/api_log_get.py — ApiLogGet API handler."""

import sys
import threading
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from python.api.api_log_get import ApiLogGet


def _make_handler(app=None, lock=None):
    return ApiLogGet(app=app or MagicMock(), thread_lock=lock or threading.Lock())


class TestApiLogGet:
    def test_get_methods_returns_get_and_post(self):
        assert set(ApiLogGet.get_methods()) == {"GET", "POST"}

    def test_requires_auth_false(self):
        assert ApiLogGet.requires_auth() is False

    def test_requires_csrf_false(self):
        assert ApiLogGet.requires_csrf() is False

    def test_requires_api_key_true(self):
        assert ApiLogGet.requires_api_key() is True

    @pytest.mark.asyncio
    async def test_process_returns_400_when_context_id_missing(self, mock_app):
        app, lock = mock_app
        handler = _make_handler(app, lock)
        request = MagicMock()
        request.method = "POST"

        result = await handler.process({}, request)

        assert result.status_code == 400
        assert b"context_id is required" in result.response[0]

    @pytest.mark.asyncio
    async def test_process_returns_404_when_context_not_found(self, mock_app):
        app, lock = mock_app
        handler = _make_handler(app, lock)
        request = MagicMock()
        request.method = "POST"

        with patch("python.api.api_log_get.AgentContext") as MockCtx:
            MockCtx.use.return_value = None
            result = await handler.process({"context_id": "nonexistent"}, request)

        assert result.status_code == 404
        assert b"Context not found" in result.response[0]

    @pytest.mark.asyncio
    async def test_process_returns_log_data_on_success(self, mock_app):
        app, lock = mock_app
        handler = _make_handler(app, lock)
        request = MagicMock()
        request.method = "POST"

        mock_context = MagicMock()
        mock_context.log = MagicMock()
        mock_context.log.logs = ["item1", "item2", "item3"]
        mock_context.log.guid = "log-guid-1"
        mock_context.log.progress = 0
        mock_context.log.progress_active = False
        mock_context.log.output = MagicMock(return_value=["item2", "item3"])

        with patch("python.api.api_log_get.AgentContext") as MockCtx:
            MockCtx.use.return_value = mock_context
            result = await handler.process(
                {"context_id": "ctx-1", "length": 10}, request
            )

        assert result["context_id"] == "ctx-1"
        assert result["log"]["guid"] == "log-guid-1"
        assert result["log"]["total_items"] == 3
        assert result["log"]["returned_items"] == 2
        assert "items" in result["log"]
