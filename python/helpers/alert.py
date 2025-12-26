from __future__ import annotations

from typing import Literal

from python.helpers import settings
from python.helpers.notification import (
    NotificationManager,
    NotificationPriority,
    NotificationType,
)


AlertType = Literal["task_complete", "input_needed", "subagent_complete"]


def _should_emit_alert(sett: settings.Settings, alert_type: AlertType) -> bool:
    if not sett.get("alert_enabled", False):
        return False

    if alert_type == "task_complete":
        return bool(sett.get("alert_on_task_complete", False))
    if alert_type == "input_needed":
        return bool(sett.get("alert_on_user_input_needed", False))
    if alert_type == "subagent_complete":
        return bool(sett.get("alert_on_subagent_complete", False))

    return False


def _get_default_message(alert_type: AlertType) -> str:
    if alert_type == "task_complete":
        return "Task completed"
    if alert_type == "input_needed":
        return "Waiting for your input"
    if alert_type == "subagent_complete":
        return "Subordinate agent completed"
    return "Alert"


def _get_message(sett: settings.Settings, alert_type: AlertType) -> str:
    if alert_type == "task_complete":
        return str(sett.get("alert_tts_message_task_complete") or "").strip()
    if alert_type == "input_needed":
        return str(sett.get("alert_tts_message_input_needed") or "").strip()
    if alert_type == "subagent_complete":
        return str(sett.get("alert_tts_message_subagent_complete") or "").strip()
    return ""


def _get_title(alert_type: AlertType) -> str:
    if alert_type == "task_complete":
        return "Task complete"
    if alert_type == "input_needed":
        return "Waiting for input"
    if alert_type == "subagent_complete":
        return "Subagent complete"
    return "Alert"


def _get_notification_type(alert_type: AlertType) -> NotificationType:
    if alert_type == "task_complete":
        return NotificationType.SUCCESS
    if alert_type == "input_needed":
        return NotificationType.INFO
    if alert_type == "subagent_complete":
        return NotificationType.SUCCESS
    return NotificationType.INFO


def emit_alert(
    alert_type: AlertType,
    *,
    force: bool = False,
    message_override: str | None = None,
    display_time: int = 5,
) -> None:
    """
    Emit an alert notification (no audio playback server-side).

    WebUI will observe notifications via /poll and play sound/tts based on its settings.
    """
    sett = settings.get_settings()
    if not force and not _should_emit_alert(sett, alert_type):
        return

    group = f"alert.{alert_type}"
    message = (message_override or _get_message(sett, alert_type)).strip()
    if not message:
        message = _get_default_message(alert_type)

    NotificationManager.send_notification(
        _get_notification_type(alert_type),
        NotificationPriority.NORMAL,
        message=message,
        title=_get_title(alert_type),
        detail="",
        display_time=display_time,
        group=group,
    )


