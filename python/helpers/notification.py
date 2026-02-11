import threading
import uuid
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from enum import Enum


class NotificationType(Enum):
    INFO = "info"
    SUCCESS = "success"
    WARNING = "warning"
    ERROR = "error"
    PROGRESS = "progress"


class NotificationPriority(Enum):
    NORMAL = 10
    HIGH = 20


@dataclass
class NotificationItem:
    manager: "NotificationManager"
    no: int
    type: NotificationType
    priority: NotificationPriority
    title: str
    message: str
    detail: str  # HTML content for expandable details
    timestamp: datetime
    display_time: int = 3  # Display duration in seconds, default 3 seconds
    read: bool = False
    id: str = ""
    group: str = ""  # Group identifier for grouping related notifications

    def __post_init__(self):
        if not self.id:
            self.id = str(uuid.uuid4())
        # Ensure type is always NotificationType
        if isinstance(self.type, str):
            self.type = NotificationType(self.type)

    def mark_read(self):
        self.read = True
        self.manager.update_item(self.no, read=True)

    def output(self):
        return {
            "no": self.no,
            "id": self.id,
            "type": self.type.value
            if isinstance(self.type, NotificationType)
            else self.type,
            "priority": self.priority.value
            if isinstance(self.priority, NotificationPriority)
            else self.priority,
            "title": self.title,
            "message": self.message,
            "detail": self.detail,
            "timestamp": self.timestamp.isoformat(),
            "display_time": self.display_time,
            "read": self.read,
            "group": self.group,
        }


class NotificationManager:
    def __init__(self, max_notifications: int = 100):
        self._lock = threading.RLock()
        self.guid: str = str(uuid.uuid4())
        self.updates: list[int] = []
        self.notifications: list[NotificationItem] = []
        self.max_notifications = max_notifications

    @staticmethod
    def send_notification(
        type: NotificationType,
        priority: NotificationPriority,
        message: str,
        title: str = "",
        detail: str = "",
        display_time: int = 3,
        group: str = "",
    ) -> NotificationItem:
        from agent import AgentContext

        return AgentContext.get_notification_manager().add_notification(
            type, priority, message, title, detail, display_time, group
        )

    def add_notification(
        self,
        type: NotificationType,
        priority: NotificationPriority,
        message: str,
        title: str = "",
        detail: str = "",
        display_time: int = 3,
        group: str = "",
    ) -> NotificationItem:
        with self._lock:
            # Create notification item
            item = NotificationItem(
                manager=self,
                no=len(self.notifications),
                type=NotificationType(type),
                priority=NotificationPriority(priority),
                title=title,
                message=message,
                detail=detail,
                timestamp=datetime.now(timezone.utc),
                display_time=display_time,
                group=group,
            )

            # Add to notifications
            self.notifications.append(item)
            self.updates.append(item.no)

            # Enforce limit
            self._enforce_limit()

        from python.helpers.state_monitor_integration import mark_dirty_all

        mark_dirty_all(reason="notification.NotificationManager.add_notification")
        return item

    def _enforce_limit(self):
        with self._lock:
            if len(self.notifications) > self.max_notifications:
                # Remove oldest notifications
                to_remove = len(self.notifications) - self.max_notifications
                self.notifications = self.notifications[to_remove:]
                # Adjust notification numbers
                for i, notification in enumerate(self.notifications):
                    notification.no = i
                # Adjust updates list
                self.updates = [
                    no - to_remove for no in self.updates if no >= to_remove
                ]

    def get_recent_notifications(self, seconds: int = 30) -> list[NotificationItem]:
        cutoff = datetime.now(timezone.utc) - timedelta(seconds=seconds)
        with self._lock:
            return [n for n in self.notifications if n.timestamp >= cutoff]

    def output(self, start: int | None = None, end: int | None = None) -> list[dict]:
        with self._lock:
            if start is None:
                start = 0
            if end is None:
                end = len(self.updates)
            updates = self.updates[start:end]
            notifications = list(self.notifications)

        out = []
        seen = set()
        for update in updates:
            if update not in seen and update < len(notifications):
                out.append(notifications[update].output())
                seen.add(update)
        return out

    def output_all(self) -> list[dict]:
        with self._lock:
            notifications = list(self.notifications)
        return [n.output() for n in notifications]

    def mark_read_by_ids(self, notification_ids: list[str]) -> int:
        ids = {nid for nid in notification_ids if isinstance(nid, str) and nid.strip()}
        if not ids:
            return 0

        changed_nos: list[int] = []
        with self._lock:
            for notification in self.notifications:
                if notification.id in ids and not notification.read:
                    notification.read = True
                    changed_nos.append(notification.no)
            if changed_nos:
                self.updates.extend(changed_nos)

        if not changed_nos:
            return 0

        from python.helpers.state_monitor_integration import mark_dirty_all

        mark_dirty_all(reason="notification.NotificationManager.mark_read_by_ids")
        return len(changed_nos)

    def update_item(self, no: int, **kwargs) -> None:
        self._update_item(no, **kwargs)

    def _update_item(self, no: int, **kwargs):
        changed = False
        with self._lock:
            if no < len(self.notifications):
                item = self.notifications[no]
                for key, value in kwargs.items():
                    if hasattr(item, key):
                        setattr(item, key, value)
                self.updates.append(no)
                changed = True

        if not changed:
            return

        from python.helpers.state_monitor_integration import mark_dirty_all

        mark_dirty_all(reason="notification.NotificationManager._update_item")

    def mark_all_read(self):
        changed_nos: list[int] = []
        with self._lock:
            for notification in self.notifications:
                if not notification.read:
                    notification.read = True
                    changed_nos.append(notification.no)
            if changed_nos:
                self.updates.extend(changed_nos)

        if not changed_nos:
            return

        from python.helpers.state_monitor_integration import mark_dirty_all

        mark_dirty_all(reason="notification.NotificationManager.mark_all_read")

    def clear_all(self):
        with self._lock:
            self.notifications = []
            self.updates = []
            self.guid = str(uuid.uuid4())
        from python.helpers.state_monitor_integration import mark_dirty_all

        mark_dirty_all(reason="notification.NotificationManager.clear_all")

    def get_notifications_by_type(
        self, type: NotificationType
    ) -> list[NotificationItem]:
        with self._lock:
            return [n for n in self.notifications if n.type == type]
