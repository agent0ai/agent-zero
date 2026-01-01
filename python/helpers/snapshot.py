from __future__ import annotations

from typing import Any

from agent import AgentContext, AgentContextType

from python.helpers.dotenv import get_dotenv_value
from python.helpers.localization import Localization
from python.helpers.task_scheduler import TaskScheduler


SNAPSHOT_SCHEMA_V1_KEYS: tuple[str, ...] = (
    "deselect_chat",
    "context",
    "contexts",
    "tasks",
    "logs",
    "log_guid",
    "log_version",
    "log_progress",
    "log_progress_active",
    "paused",
    "notifications",
    "notifications_guid",
    "notifications_version",
)


def validate_snapshot_schema_v1(snapshot: dict[str, Any]) -> None:
    if not isinstance(snapshot, dict):
        raise TypeError("snapshot must be a dict")
    expected = set(SNAPSHOT_SCHEMA_V1_KEYS)
    actual = set(snapshot.keys())
    missing = sorted(expected - actual)
    extra = sorted(actual - expected)
    if missing or extra:
        raise ValueError(
            "snapshot schema mismatch"
            + (f"; missing={missing}" if missing else "")
            + (f"; unexpected={extra}" if extra else "")
        )


def _coerce_non_negative_int(value: Any, default: int = 0) -> int:
    try:
        as_int = int(value)
    except (TypeError, ValueError):
        return default
    return as_int if as_int >= 0 else default


async def build_snapshot(
    *,
    context: str | None,
    log_from: int,
    notifications_from: int,
    timezone: str | None,
) -> dict[str, Any]:
    """Build a poll-shaped snapshot for both /poll and state_push."""

    tz = timezone if isinstance(timezone, str) and timezone else None
    tz = tz or get_dotenv_value("DEFAULT_USER_TIMEZONE", "UTC")
    Localization.get().set_timezone(tz)

    ctxid = context if isinstance(context, str) else ""
    ctxid = ctxid.strip()

    from_no = _coerce_non_negative_int(log_from, default=0)
    notifications_from_no = _coerce_non_negative_int(notifications_from, default=0)

    active_context = AgentContext.get(ctxid) if ctxid else None

    logs = (
        active_context.log.output(start=from_no)
        if active_context
        else []
    )

    notification_manager = AgentContext.get_notification_manager()
    notifications = notification_manager.output(start=notifications_from_no)

    scheduler = TaskScheduler.get()

    ctxs: list[dict[str, Any]] = []
    tasks: list[dict[str, Any]] = []
    processed_contexts: set[str] = set()

    all_ctxs = AgentContext.all()
    for ctx in all_ctxs:
        if ctx.id in processed_contexts:
            continue

        if ctx.type == AgentContextType.BACKGROUND:
            processed_contexts.add(ctx.id)
            continue

        context_data = ctx.output()

        context_task = scheduler.get_task_by_uuid(ctx.id)
        is_task_context = context_task is not None and context_task.context_id == ctx.id

        if not is_task_context:
            ctxs.append(context_data)
        else:
            task_details = scheduler.serialize_task(ctx.id)
            if task_details:
                context_data.update(
                    {
                        "task_name": task_details.get("name"),
                        "uuid": task_details.get("uuid"),
                        "state": task_details.get("state"),
                        "type": task_details.get("type"),
                        "system_prompt": task_details.get("system_prompt"),
                        "prompt": task_details.get("prompt"),
                        "last_run": task_details.get("last_run"),
                        "last_result": task_details.get("last_result"),
                        "attachments": task_details.get("attachments", []),
                        "context_id": task_details.get("context_id"),
                    }
                )

                if task_details.get("type") == "scheduled":
                    context_data["schedule"] = task_details.get("schedule")
                elif task_details.get("type") == "planned":
                    context_data["plan"] = task_details.get("plan")
                else:
                    context_data["token"] = task_details.get("token")

            tasks.append(context_data)

        processed_contexts.add(ctx.id)

    ctxs.sort(key=lambda x: x["created_at"], reverse=True)
    tasks.sort(key=lambda x: x["created_at"], reverse=True)

    snapshot = {
        "deselect_chat": bool(ctxid) and active_context is None,
        "context": active_context.id if active_context else "",
        "contexts": ctxs,
        "tasks": tasks,
        "logs": logs,
        "log_guid": active_context.log.get_guid() if active_context else "",
        "log_version": active_context.log.get_version() if active_context else 0,
        "log_progress": active_context.log.get_progress() if active_context else 0,
        "log_progress_active": active_context.log.get_progress_active() if active_context else False,
        "paused": active_context.paused if active_context else False,
        "notifications": notifications,
        "notifications_guid": notification_manager.get_guid(),
        "notifications_version": notification_manager.get_version(),
    }

    validate_snapshot_schema_v1(snapshot)
    return snapshot
