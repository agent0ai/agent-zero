from python.helpers.api import ApiHandler, Request, Response

from agent import AgentContext, AgentContextType

from python.helpers.task_scheduler import TaskScheduler
from python.helpers.localization import Localization
from python.helpers.dotenv import get_dotenv_value


class Poll(ApiHandler):

    async def process(self, input: dict, request: Request) -> dict | Response:
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
            except Exception as e:
                context = None
        else:
            context = None

        # Get logs only if we have a context
        logs = context.log.output(start=from_no) if context else []

        # Get notifications from global notification manager
        notification_manager = AgentContext.get_notification_manager()
        notifications = notification_manager.output(start=notifications_from)

        # loop AgentContext._contexts

        # Get a task scheduler instance
        scheduler = TaskScheduler.get()

        # Always reload the scheduler on each poll to ensure we have the latest task state
        # await scheduler.reload() # does not seem to be needed

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

            # Skip BACKGROUND contexts as they should be invisible to users
            if ctx.type == AgentContextType.BACKGROUND:
                processed_contexts.add(ctx.id)
                continue

            # Create the base context data that will be returned
            context_data = ctx.output()

            context_task = scheduler.get_task_by_uuid(ctx.id)
            # Determine if this is a task-dedicated context by checking if a task with this UUID exists
            is_task_context = (
                context_task is not None and context_task.context_id == ctx.id
            )

            if not is_task_context:
                ctxs.append(context_data)
            else:
                # If this is a task, get task details from the scheduler
                task_details = scheduler.serialize_task(ctx.id)
                if task_details:
                    # Add task details to context_data with the same field names
                    # as used in scheduler endpoints to maintain UI compatibility
                    context_data.update({
                        "task_name": task_details.get("name"),  # name is for context, task_name for the task name
                        "uuid": task_details.get("uuid"),
                        "state": task_details.get("state"),
                        "type": task_details.get("type"),
                        "system_prompt": task_details.get("system_prompt"),
                        "prompt": task_details.get("prompt"),
                        "last_run": task_details.get("last_run"),
                        "last_result": task_details.get("last_result"),
                        "attachments": task_details.get("attachments", []),
                        "context_id": task_details.get("context_id"),
                    })

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
            "notifications": notifications,
            "notifications_guid": notification_manager.guid,
            "notifications_version": len(notification_manager.updates),
        }
