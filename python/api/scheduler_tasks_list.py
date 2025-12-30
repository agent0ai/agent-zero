from python.helpers.api import ApiHandler, Input, Output, Request
from python.helpers.task_scheduler import TaskScheduler
import traceback
from python.helpers.print_style import PrintStyle


class SchedulerTasksList(ApiHandler):
    async def process(self, input: Input, request: Request) -> Output:
        """
        List all tasks in the scheduler with their types
        """
        try:
            # Timezone is now initialized once from .env, not set on every request

            # Get task scheduler
            scheduler = TaskScheduler.get()
            await scheduler.reload()

            # Use the scheduler's convenience method for task serialization
            tasks_list = scheduler.serialize_all_tasks()

            return {"ok": True, "tasks": tasks_list}

        except Exception as e:
            PrintStyle.error(f"Failed to list tasks: {str(e)} {traceback.format_exc()}")
            return {"ok": False, "error": f"Failed to list tasks: {str(e)} {traceback.format_exc()}", "tasks": []}
