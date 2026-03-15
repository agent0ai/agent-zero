"""Tests for python/api/notifications_mark_read.py — NotificationsMarkRead API handler."""

import sys
import threading
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from python.api.notifications_mark_read import NotificationsMarkRead


def _make_handler(app=None, lock=None):
    return NotificationsMarkRead(app=app or MagicMock(), thread_lock=lock or threading.Lock())


class TestNotificationsMarkRead:
    def test_requires_auth_true(self):
        assert NotificationsMarkRead.requires_auth() is True

    @pytest.mark.asyncio
    async def test_process_mark_all_returns_success(self, mock_app):
        app, lock = mock_app
        handler = _make_handler(app, lock)
        mock_manager = MagicMock()

        with patch(
            "python.api.notifications_mark_read.AgentContext.get_notification_manager",
            return_value=mock_manager,
        ):
            result = await handler.process({"mark_all": True}, MagicMock())

        mock_manager.mark_all_read.assert_called_once()
        assert result["success"] is True
        assert "All notifications marked as read" in result["message"]

    @pytest.mark.asyncio
    async def test_process_returns_error_when_no_ids_and_not_mark_all(self, mock_app):
        app, lock = mock_app
        handler = _make_handler(app, lock)
        mock_manager = MagicMock()

        with patch(
            "python.api.notifications_mark_read.AgentContext.get_notification_manager",
            return_value=mock_manager,
        ):
            result = await handler.process({}, MagicMock())

        assert result["success"] is False
        assert result["error"] == "No notification IDs provided"

    @pytest.mark.asyncio
    async def test_process_returns_error_when_ids_not_list(self, mock_app):
        app, lock = mock_app
        handler = _make_handler(app, lock)
        mock_manager = MagicMock()

        with patch(
            "python.api.notifications_mark_read.AgentContext.get_notification_manager",
            return_value=mock_manager,
        ):
            result = await handler.process(
                {"notification_ids": "not-a-list"}, MagicMock()
            )

        assert result["success"] is False
        assert "must be a list" in result["error"]

    @pytest.mark.asyncio
    async def test_process_marks_specific_ids_and_returns_count(self, mock_app):
        app, lock = mock_app
        handler = _make_handler(app, lock)
        mock_manager = MagicMock()
        mock_manager.mark_read_by_ids.return_value = 2

        with patch(
            "python.api.notifications_mark_read.AgentContext.get_notification_manager",
            return_value=mock_manager,
        ):
            result = await handler.process(
                {"notification_ids": ["n1", "n2"]}, MagicMock()
            )

        mock_manager.mark_read_by_ids.assert_called_once_with(["n1", "n2"])
        assert result["success"] is True
        assert result["marked_count"] == 2
        assert "Marked 2 notifications" in result["message"]
