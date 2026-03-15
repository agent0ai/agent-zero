"""Tests for python/api/notifications_history.py — NotificationsHistory API handler."""

import sys
import threading
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from python.api.notifications_history import NotificationsHistory


def _make_handler(app=None, lock=None):
    return NotificationsHistory(app=app or MagicMock(), thread_lock=lock or threading.Lock())


class TestNotificationsHistory:
    def test_requires_auth_true(self):
        assert NotificationsHistory.requires_auth() is True

    @pytest.mark.asyncio
    async def test_process_returns_notifications_and_metadata(self, mock_app):
        app, lock = mock_app
        handler = _make_handler(app, lock)
        mock_manager = MagicMock()
        mock_manager.guid = "history-guid"
        mock_manager.output_all.return_value = [
            {"id": "n1", "message": "First"},
            {"id": "n2", "message": "Second"},
        ]

        with patch(
            "python.api.notifications_history.AgentContext.get_notification_manager",
            return_value=mock_manager,
        ):
            result = await handler.process({}, MagicMock())

        mock_manager.output_all.assert_called_once()
        assert result["notifications"] == [
            {"id": "n1", "message": "First"},
            {"id": "n2", "message": "Second"},
        ]
        assert result["guid"] == "history-guid"
        assert result["count"] == 2
