"""Tests for python/api/notification_create.py — NotificationCreate API handler."""

import sys
import threading
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from python.api.notification_create import NotificationCreate


def _make_handler(app=None, lock=None):
    return NotificationCreate(app=app or MagicMock(), thread_lock=lock or threading.Lock())


class TestNotificationCreate:
    def test_requires_auth_true(self):
        assert NotificationCreate.requires_auth() is True

    @pytest.mark.asyncio
    async def test_process_returns_error_when_message_missing(self, mock_app):
        app, lock = mock_app
        handler = _make_handler(app, lock)

        result = await handler.process(
            {"title": "Title", "type": "info"}, MagicMock()
        )

        assert result["success"] is False
        assert result["error"] == "Message is required"

    @pytest.mark.asyncio
    async def test_process_returns_success_with_notification_id(self, mock_app):
        app, lock = mock_app
        handler = _make_handler(app, lock)
        mock_notification = MagicMock()
        mock_notification.id = "notif-123"

        with patch(
            "python.api.notification_create.NotificationManager.send_notification",
            return_value=mock_notification,
        ):
            result = await handler.process(
                {"message": "Test message", "type": "info"}, MagicMock()
            )

        assert result["success"] is True
        assert result["notification_id"] == "notif-123"
        assert "Notification created successfully" in result["message"]

    @pytest.mark.asyncio
    async def test_process_returns_error_for_invalid_type(self, mock_app):
        app, lock = mock_app
        handler = _make_handler(app, lock)

        result = await handler.process(
            {"message": "Msg", "type": "invalid_type"}, MagicMock()
        )

        assert result["success"] is False
        assert "Invalid notification type" in result["error"]

    @pytest.mark.asyncio
    async def test_process_uses_defaults_for_optional_fields(self, mock_app):
        app, lock = mock_app
        handler = _make_handler(app, lock)
        mock_notification = MagicMock()
        mock_notification.id = "n1"

        with patch(
            "python.api.notification_create.NotificationManager.send_notification",
            return_value=mock_notification,
        ) as mock_send:
            await handler.process({"message": "Minimal"}, MagicMock())

        mock_send.assert_called_once()
        call_positional = mock_send.call_args[0]
        assert call_positional[5] == 3   # display_time
        assert call_positional[6] == ""  # group

    @pytest.mark.asyncio
    async def test_process_returns_error_on_exception(self, mock_app):
        app, lock = mock_app
        handler = _make_handler(app, lock)

        with patch(
            "python.api.notification_create.NotificationManager.send_notification",
            side_effect=Exception("Send failed"),
        ):
            result = await handler.process(
                {"message": "Test", "type": "info"}, MagicMock()
            )

        assert result["success"] is False
        assert "Send failed" in result["error"]
