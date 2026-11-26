from helpers.api import ApiHandler, Input, Output, Request
from helpers.task_scheduler import TaskScheduler
import traceback
from helpers.print_style import PrintStyle
from helpers.localization import Localization
from helpers import team_access, team_tasks
from helpers.task_scheduler import serialize_task


class SchedulerTasksList(ApiHandler):
    async def process(self, input: Input, request: Request) -> Output:
        """
        List all tasks in the scheduler with their types
        """
        try:
            scope = team_access.request_scope()
            # Get timezone from input (do not set if not provided, we then rely on poll() to set it)
            if scope is None and (timezone := input.get("timezone", None)):
                Localization.get().set_timezone(timezone)

            # Get task scheduler
            scheduler = TaskScheduler.get()
            await scheduler.reload()
            if scope is not None:
                tasks = [serialize_task(task, include_team_data=True) for task in scheduler.get_tasks() if team_tasks.permits_task(task, scope)]
                return {"ok": True, "tasks": tasks}

            # Use the scheduler's convenience method for task serialization
            tasks_list = scheduler.serialize_all_tasks()

            return {"ok": True, "tasks": tasks_list}

        except Exception as e:
            PrintStyle.error(f"Failed to list tasks: {str(e)} {traceback.format_exc()}")
            return {"ok": False, "error": f"Failed to list tasks: {str(e)} {traceback.format_exc()}", "tasks": []}
