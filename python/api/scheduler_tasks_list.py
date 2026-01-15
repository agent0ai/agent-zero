from python.helpers.api import ApiHandler, Input, Output, Request
import traceback
from python.helpers.print_style import PrintStyle
from python.helpers.localization import Localization


class SchedulerTasksList(ApiHandler):
    async def process(self, input: Input, request: Request) -> Output:
        """
        List all tasks in the scheduler with their types
        """
        # Lazy import - TaskScheduler requires crontab which may not be installed
        try:
            from python.helpers.task_scheduler import TaskScheduler
        except ImportError as e:
            return {"ok": False, "error": f"Scheduler not available: {e}", "tasks": []}

        try:
            # Get timezone from input (do not set if not provided, we then rely on poll() to set it)
            if timezone := input.get("timezone", None):
                Localization.get().set_timezone(timezone)

            # Get task scheduler
            scheduler = TaskScheduler.get()
            await scheduler.reload()

            # Use the scheduler's convenience method for task serialization
            tasks_list = scheduler.serialize_all_tasks()

            return {"ok": True, "tasks": tasks_list}

        except Exception as e:
            PrintStyle.error(f"Failed to list tasks: {str(e)} {traceback.format_exc()}")
            return {"ok": False, "error": f"Failed to list tasks: {str(e)} {traceback.format_exc()}", "tasks": []}
