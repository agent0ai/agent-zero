"""Tests for python/helpers/notification.py."""

import sys
from datetime import datetime, timezone
from pathlib import Path
from unittest.mock import patch

import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import python.helpers.notification as _notification_mod


@pytest.fixture(autouse=True)
def patch_mark_dirty():
    """Mock state_monitor_integration to avoid side effects."""
    with patch("python.helpers.state_monitor_integration.mark_dirty_all"):
        yield


# --- NotificationType & NotificationPriority ---


class TestNotificationEnums:
    def test_notification_type_values(self):
        from python.helpers.notification import NotificationType

        assert NotificationType.INFO.value == "info"
        assert NotificationType.SUCCESS.value == "success"
        assert NotificationType.WARNING.value == "warning"
        assert NotificationType.ERROR.value == "error"
        assert NotificationType.PROGRESS.value == "progress"

    def test_notification_priority_values(self):
        from python.helpers.notification import NotificationPriority

        assert NotificationPriority.NORMAL.value == 10
        assert NotificationPriority.HIGH.value == 20


# --- NotificationItem ---


class TestNotificationItem:
    def test_notification_item_auto_generates_id(self):
        from python.helpers.notification import NotificationItem, NotificationManager, NotificationType, NotificationPriority

        manager = NotificationManager()
        item = NotificationItem(
            manager=manager,
            no=0,
            type=NotificationType.INFO,
            priority=NotificationPriority.NORMAL,
            title="Test",
            message="Message",
            detail="",
            timestamp=datetime.now(timezone.utc),
        )
        assert item.id != ""
        assert len(item.id) == 36  # UUID format

    def test_notification_item_accepts_custom_id(self):
        from python.helpers.notification import NotificationItem, NotificationManager, NotificationType, NotificationPriority

        manager = NotificationManager()
        item = NotificationItem(
            manager=manager,
            no=0,
            type=NotificationType.INFO,
            priority=NotificationPriority.NORMAL,
            title="Test",
            message="Message",
            detail="",
            timestamp=datetime.now(timezone.utc),
            id="custom-id-123",
        )
        assert item.id == "custom-id-123"

    def test_notification_item_coerces_type_from_str(self):
        from python.helpers.notification import NotificationItem, NotificationManager, NotificationPriority

        manager = NotificationManager()
        item = NotificationItem(
            manager=manager,
            no=0,
            type="info",
            priority=NotificationPriority.NORMAL,
            title="Test",
            message="Message",
            detail="",
            timestamp=datetime.now(timezone.utc),
        )
        assert item.type.value == "info"

    def test_notification_item_output_shape(self):
        from python.helpers.notification import NotificationItem, NotificationManager, NotificationType, NotificationPriority

        manager = NotificationManager()
        ts = datetime.now(timezone.utc)
        item = NotificationItem(
            manager=manager,
            no=1,
            type=NotificationType.WARNING,
            priority=NotificationPriority.HIGH,
            title="Title",
            message="Message",
            detail="<p>Detail</p>",
            timestamp=ts,
            display_time=5,
            group="group1",
        )
        out = item.output()
        assert out["no"] == 1
        assert out["type"] == "warning"
        assert out["priority"] == 20
        assert out["title"] == "Title"
        assert out["message"] == "Message"
        assert out["detail"] == "<p>Detail</p>"
        assert out["display_time"] == 5
        assert out["read"] is False
        assert out["group"] == "group1"
        assert "timestamp" in out


# --- NotificationManager ---


class TestNotificationManager:
    def test_add_notification(self):
        from python.helpers.notification import NotificationManager, NotificationType, NotificationPriority

        mgr = NotificationManager()
        item = mgr.add_notification(
            NotificationType.INFO,
            NotificationPriority.NORMAL,
            "Test message",
            title="Title",
            detail="Detail",
        )
        assert item.message == "Test message"
        assert item.title == "Title"
        assert len(mgr.notifications) == 1
        assert mgr.updates == [0]

    def test_add_notification_with_group(self):
        from python.helpers.notification import NotificationManager, NotificationType, NotificationPriority

        mgr = NotificationManager()
        mgr.add_notification(
            NotificationType.INFO,
            NotificationPriority.NORMAL,
            "Msg 1",
            group="batch",
        )
        mgr.add_notification(
            NotificationType.INFO,
            NotificationPriority.NORMAL,
            "Msg 2",
            group="batch",
        )
        assert all(n.group == "batch" for n in mgr.notifications)

    def test_enforce_limit_removes_oldest(self):
        from python.helpers.notification import NotificationManager, NotificationType, NotificationPriority

        mgr = NotificationManager(max_notifications=3)
        for i in range(5):
            mgr.add_notification(
                NotificationType.INFO,
                NotificationPriority.NORMAL,
                f"Message {i}",
            )
        assert len(mgr.notifications) == 3
        assert mgr.notifications[0].message == "Message 2"
        assert mgr.notifications[0].no == 0

    def test_get_recent_notifications(self):
        from python.helpers.notification import NotificationManager, NotificationType, NotificationPriority

        mgr = NotificationManager()
        mgr.add_notification(
            NotificationType.INFO,
            NotificationPriority.NORMAL,
            "Recent",
        )
        recent = mgr.get_recent_notifications(seconds=60)
        assert len(recent) == 1
        assert recent[0].message == "Recent"

    def test_output_returns_updates_slice(self):
        from python.helpers.notification import NotificationManager, NotificationType, NotificationPriority

        mgr = NotificationManager()
        mgr.add_notification(NotificationType.INFO, NotificationPriority.NORMAL, "A")
        mgr.add_notification(NotificationType.INFO, NotificationPriority.NORMAL, "B")
        out = mgr.output(start=0, end=2)
        assert len(out) == 2

    def test_output_all_returns_all_notifications(self):
        from python.helpers.notification import NotificationManager, NotificationType, NotificationPriority

        mgr = NotificationManager()
        mgr.add_notification(NotificationType.INFO, NotificationPriority.NORMAL, "A")
        mgr.add_notification(NotificationType.INFO, NotificationPriority.NORMAL, "B")
        out = mgr.output_all()
        assert len(out) == 2

    def test_mark_read_by_ids(self):
        from python.helpers.notification import NotificationManager, NotificationType, NotificationPriority

        mgr = NotificationManager()
        item1 = mgr.add_notification(NotificationType.INFO, NotificationPriority.NORMAL, "A")
        item2 = mgr.add_notification(NotificationType.INFO, NotificationPriority.NORMAL, "B")
        count = mgr.mark_read_by_ids([item1.id])
        assert count == 1
        assert mgr.notifications[0].read is True

    def test_mark_read_by_ids_returns_zero_for_empty(self):
        from python.helpers.notification import NotificationManager, NotificationType, NotificationPriority

        mgr = NotificationManager()
        mgr.add_notification(NotificationType.INFO, NotificationPriority.NORMAL, "A")
        count = mgr.mark_read_by_ids([])
        assert count == 0

    def test_update_item(self):
        from python.helpers.notification import NotificationManager, NotificationType, NotificationPriority

        mgr = NotificationManager()
        mgr.add_notification(NotificationType.INFO, NotificationPriority.NORMAL, "A")
        mgr.update_item(0, read=True)
        assert mgr.notifications[0].read is True

    def test_mark_all_read(self):
        from python.helpers.notification import NotificationManager, NotificationType, NotificationPriority

        mgr = NotificationManager()
        mgr.add_notification(NotificationType.INFO, NotificationPriority.NORMAL, "A")
        mgr.add_notification(NotificationType.INFO, NotificationPriority.NORMAL, "B")
        mgr.mark_all_read()
        assert all(n.read for n in mgr.notifications)

    def test_clear_all(self):
        from python.helpers.notification import NotificationManager, NotificationType, NotificationPriority

        mgr = NotificationManager()
        mgr.add_notification(NotificationType.INFO, NotificationPriority.NORMAL, "A")
        old_guid = mgr.guid
        mgr.clear_all()
        assert len(mgr.notifications) == 0
        assert len(mgr.updates) == 0
        assert mgr.guid != old_guid

    def test_get_notifications_by_type(self):
        from python.helpers.notification import NotificationManager, NotificationType, NotificationPriority

        mgr = NotificationManager()
        mgr.add_notification(NotificationType.INFO, NotificationPriority.NORMAL, "Info")
        mgr.add_notification(NotificationType.ERROR, NotificationPriority.NORMAL, "Error")
        errors = mgr.get_notifications_by_type(NotificationType.ERROR)
        assert len(errors) == 1
        assert errors[0].message == "Error"
