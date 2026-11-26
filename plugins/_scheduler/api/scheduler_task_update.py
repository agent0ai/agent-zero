from helpers.api import ApiHandler, Input, Output, Request, Response
from helpers import team_access, team_projects, team_tasks
from helpers.task_scheduler import (
    TaskScheduler, ScheduledTask, AdHocTask, PlannedTask, TaskState,
    serialize_task, parse_task_schedule, parse_task_plan
)
from helpers.localization import Localization


class SchedulerTaskUpdate(ApiHandler):
    async def process(self, input: Input, request: Request) -> Output:
        """
        Update an existing task in the scheduler
        """
        scope = team_access.request_scope()
        # Get timezone from input (do not set if not provided, we then rely on poll() to set it)
        timezone = input.get("timezone")
        if scope is None and timezone:
            Localization.get().set_timezone(timezone)

        scheduler = TaskScheduler.get()
        await scheduler.reload()

        # Get task ID from input
        task_id: str = input.get("task_id", "")

        if not task_id:
            return {"error": "Missing required field: task_id"}

        # Get the task to update
        task = scheduler.get_task_by_uuid(task_id)
        if (scope is not None and not task) or (task is not None and not team_tasks.permits_task(task, scope)):
            return Response("Project task access denied.", 403)

        if not task:
            return {"error": f"Task with ID {task_id} not found"}
        if scope:
            try:
                team_tasks.validate_fields(input)
            except ValueError as error:
                return Response(str(error), 400)

        # Update fields if provided using the task's update method
        update_params = {}

        if "name" in input:
            update_params["name"] = input.get("name", "")

        if "state" in input:
            update_params["state"] = TaskState(input.get("state", TaskState.IDLE))

        if "system_prompt" in input:
            update_params["system_prompt"] = input.get("system_prompt", "")

        if "prompt" in input:
            update_params["prompt"] = input.get("prompt", "")

        if "attachments" in input:
            update_params["attachments"] = input.get("attachments", [])

        if "project_name" in input or "project_color" in input:
            return {"error": "Project changes are not allowed"}

        # Update schedule if this is a scheduled task and schedule is provided
        if isinstance(task, ScheduledTask) and "schedule" in input:
            schedule_data = input.get("schedule", {})
            try:
                # Parse the schedule with timezone handling
                task_schedule = parse_task_schedule(schedule_data)

                # Set the timezone from the request if not already in schedule_data
                if not schedule_data.get('timezone', None) and timezone:
                    task_schedule.timezone = timezone

                update_params["schedule"] = task_schedule
            except ValueError as e:
                return {"error": f"Invalid schedule format: {str(e)}"}
        elif isinstance(task, AdHocTask) and "token" in input:
            token_value = input.get("token", "")
            if token_value:  # Only update if non-empty
                update_params["token"] = token_value
        elif isinstance(task, PlannedTask) and "plan" in input:
            plan_data = input.get("plan", {})
            try:
                # Parse the plan data
                task_plan = parse_task_plan(plan_data)
                update_params["plan"] = task_plan
            except ValueError as e:
                return {"error": f"Invalid plan format: {str(e)}"}

        # Use atomic update method to apply changes
        if scope:
            try:
                with team_projects.activity("task.update", scope.account_id, task.team_project_id, context_id=task.context_id):
                    updated_task = await scheduler.update_task_checked(
                        task_id, lambda current: current.state != TaskState.RUNNING and bool(team_tasks.scope_for_task(current, scope.account_id)),
                        **update_params,
                    )
                    if updated_task is None:
                        raise team_projects.RevisionConflict("The project task is running or changed. Refresh before editing.")
            except team_projects.RevisionConflict as error:
                return Response(str(error), 409)
        else:
            updated_task = await scheduler.update_task(task_id, **update_params)

        if not updated_task:
            return {"error": f"Task with ID {task_id} not found or could not be updated"}

        # Return the updated task using our standardized serialization function
        task_dict = serialize_task(updated_task, include_team_data=True) if scope else serialize_task(updated_task)

        return {
            "ok": True,
            "task": task_dict
        }
