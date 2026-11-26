from helpers.api import ApiHandler, Input, Output, Request, Response
from helpers.task_scheduler import TaskScheduler, TaskState
from helpers.localization import Localization
from agent import AgentContext
from helpers import persist_chat, team_access, team_projects, team_tasks


class SchedulerTaskDelete(ApiHandler):
    async def process(self, input: Input, request: Request) -> Output:
        """
        Delete a task from the scheduler by ID
        """
        scope = team_access.request_scope()
        # Get timezone from input (do not set if not provided, we then rely on poll() to set it)
        if scope is None and (timezone := input.get("timezone", None)):
            Localization.get().set_timezone(timezone)

        scheduler = TaskScheduler.get()
        await scheduler.reload()

        # Get task ID from input
        task_id: str = input.get("task_id", "")

        if not task_id:
            return {"error": "Missing required field: task_id"}

        # Check if the task exists first
        task = scheduler.get_task_by_uuid(task_id)
        if (scope is not None and not task) or (task is not None and not team_tasks.permits_task(task, scope)):
            return Response("Project task access denied.", 403)
        if not task:
            return {"error": f"Task with ID {task_id} not found"}
        if scope:
            try:
                with team_projects.project_lock(task.project_name, scope), team_projects.activity(
                    "task.delete", scope.account_id, task.team_project_id, context_id=task.context_id,
                ):
                    if not await scheduler.remove_idle_team_task(task_id, task.team_project_id):
                        raise team_projects.RevisionConflict("Stop the running task before deleting it.")
            except team_projects.RevisionConflict as error:
                return Response(str(error), 409)
            except PermissionError:
                return Response("Project task access denied.", 403)
            return {"success": True, "message": "Task removed. Its project chat is retained."}

        context = None
        if task.context_id:
            context = self.use_context(task.context_id)

        # If the task is running, update its state to IDLE first
        if task.state == TaskState.RUNNING:
            scheduler.cancel_running_task(task_id, terminate_thread=True)
            if context:
                context.reset()
            # Update the state to IDLE so any ongoing processes know to terminate
            await scheduler.update_task(task_id, state=TaskState.IDLE)
            # Force a save to ensure the state change is persisted
            await scheduler.save()

        # This is a dedicated context for the task, so we remove it
        if context and context.id == task.uuid:
            AgentContext.remove(context.id)
            persist_chat.remove_chat(context.id)

        # Remove the task
        await scheduler.remove_task_by_uuid(task_id)

        return {"success": True, "message": f"Task {task_id} deleted successfully"}
