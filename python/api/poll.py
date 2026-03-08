import contextlib
import time

from agent import AgentContext, AgentContextType
from python.helpers import cowork, perf_metrics
from python.helpers.api import ApiHandler, Request, Response
from python.helpers.dotenv import get_dotenv_value
from python.helpers.localization import Localization
from python.helpers.settings import get_settings

# Lazy import - TaskScheduler requires crontab which may not be installed
_scheduler_available = None


def _get_scheduler():
    global _scheduler_available
    if _scheduler_available is None:
        try:
            from python.helpers.task_scheduler import TaskScheduler

            _scheduler_available = TaskScheduler
        except ImportError:
            _scheduler_available = False
    return _scheduler_available.get() if _scheduler_available else None


class Poll(ApiHandler):
    async def process(self, input: dict, request: Request) -> dict | Response:
        started = time.perf_counter()
        status = "success"
        perf_metrics.increment("runtime.poll.requests")
        try:
            ctxid = input.get("context", "")
            from_no = input.get("log_from", 0)
            notifications_from = input.get("notifications_from", 0)

            # Get timezone from input (default to dotenv default or UTC if not provided)
            timezone = input.get("timezone", get_dotenv_value("DEFAULT_USER_TIMEZONE", "UTC"))
            Localization.get().set_timezone(timezone)

            # context instance - get or create only if ctxid is provided
            if ctxid:
                try:
                    context = self.use_context(ctxid, create_if_not_exists=False)
                except Exception:
                    context = None
            else:
                context = None

            # Get logs only if we have a context
            logs = context.log.output(start=from_no) if context else []

            # Get notifications from global notification manager
            notification_manager = AgentContext.get_notification_manager()
            notifications = notification_manager.output(start=notifications_from)

            # Get a task scheduler instance (may be None if crontab not installed)
            scheduler = _get_scheduler()

            # loop AgentContext._contexts and divide into contexts and tasks
            ctxs = []
            tasks = []
            processed_contexts = set()  # Track processed context IDs
            all_ctxs = list(AgentContext._contexts.values())

            # First, identify all tasks
            for ctx in all_ctxs:
                # Skip if already processed
                if ctx.id in processed_contexts:
                    continue

                # Skip BACKGROUND contexts as they should be invisible to users.
                # Legacy/persisted contexts may not have `type` set.
                ctx_type = getattr(ctx, "type", AgentContextType.USER)
                if not isinstance(ctx_type, AgentContextType):
                    with contextlib.suppress(Exception):
                        ctx_type = AgentContextType(str(ctx_type))
                if ctx_type == AgentContextType.BACKGROUND:
                    processed_contexts.add(ctx.id)
                    continue

                # Create the base context data that will be returned
                context_data = ctx.output()

                # Only check scheduler if available
                context_task = scheduler.get_task_by_uuid(ctx.id) if scheduler else None
                # Determine if this is a task-dedicated context by checking if a task with this UUID exists
                is_task_context = context_task is not None and context_task.context_id == ctx.id

                if not is_task_context:
                    ctxs.append(context_data)
                else:
                    # If this is a task, get task details from the scheduler
                    task_details = scheduler.serialize_task(ctx.id) if scheduler else None
                    if task_details:
                        # Add task details to context_data with the same field names
                        # as used in scheduler endpoints to maintain UI compatibility
                        context_data.update(
                            {
                                "task_name": task_details.get(
                                    "name"
                                ),  # name is for context, task_name for the task name
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

                        # Add type-specific fields
                        if task_details.get("type") == "scheduled":
                            context_data["schedule"] = task_details.get("schedule")
                        elif task_details.get("type") == "planned":
                            context_data["plan"] = task_details.get("plan")
                        else:
                            context_data["token"] = task_details.get("token")

                    tasks.append(context_data)

                # Mark as processed
                processed_contexts.add(ctx.id)

            # Sort tasks and chats by their creation date, descending
            ctxs.sort(key=lambda x: x["created_at"], reverse=True)
            tasks.sort(key=lambda x: x["created_at"], reverse=True)

            # cowork status
            settings = get_settings()
            cowork_enabled = bool(settings.get("cowork_enabled"))
            cowork_allowed_count = len(settings.get("cowork_allowed_paths", []))
            queue_wait_warn_seconds = int(settings.get("chat_queue_wait_warn_seconds", 60) or 60)
            cowork_pending = 0
            if context:
                approvals = cowork.get_approvals(context)
                cowork_pending = len(
                    [
                        approval
                        for approval in approvals
                        if approval.get("status") == "pending" and not approval.get("consumed")
                    ]
                )

            # data from this server
            return {
                "deselect_chat": ctxid and not context,
                "context": context.id if context else "",
                "contexts": ctxs,
                "tasks": tasks,
                "logs": logs,
                "log_guid": context.log.guid if context else "",
                "log_version": len(context.log.updates) if context else 0,
                "log_progress": context.log.progress if context else 0,
                "log_progress_active": context.log.progress_active if context else False,
                "paused": context.paused if context else False,
                "runtime_state": context.get_output_data("runtime_state") if context else "idle",
                "chat_queue_depth": context.get_output_data("chat_queue_depth") if context else 0,
                "chat_queue_oldest_age_seconds": (
                    context.get_output_data("chat_queue_oldest_age_seconds") if context else 0
                ),
                "chat_queue_wait_warning": bool(
                    context
                    and float(context.get_output_data("chat_queue_oldest_age_seconds") or 0)
                    >= float(max(1, queue_wait_warn_seconds))
                ),
                "notifications": notifications,
                "notifications_guid": notification_manager.guid,
                "notifications_version": len(notification_manager.updates),
                "cowork_enabled": cowork_enabled,
                "cowork_allowed_count": cowork_allowed_count,
                "cowork_pending": cowork_pending,
            }
        except Exception:
            status = "error"
            perf_metrics.increment("runtime.poll.errors")
            raise
        finally:
            perf_metrics.observe_ms(
                "runtime.poll.duration_ms",
                (time.perf_counter() - started) * 1000.0,
                status=status,
            )
