"""Tests for python/api/notifications_clear.py — NotificationsClear API handler."""

import sys
import threading
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from python.api.notifications_clear import NotificationsClear


def _make_handler(app=None, lock=None):
    return NotificationsClear(app=app or MagicMock(), thread_lock=lock or threading.Lock())


class TestNotificationsClear:
    def test_requires_auth_true(self):
        assert NotificationsClear.requires_auth() is True

    @pytest.mark.asyncio
    async def test_process_clears_all_notifications(self, mock_app):
        app, lock = mock_app
        handler = _make_handler(app, lock)
        mock_manager = MagicMock()

        with patch(
            "python.api.notifications_clear.AgentContext.get_notification_manager",
            return_value=mock_manager,
        ):
            result = await handler.process({}, MagicMock())

        mock_manager.clear_all.assert_called_once()
        assert result["success"] is True
        assert result["message"] == "All notifications cleared"
