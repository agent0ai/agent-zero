from python.helpers.api import ApiHandler, Input, Output, Request
from python.helpers.task_scheduler import (
    TaskScheduler, ScheduledTask, AdHocTask, PlannedTask, TaskSchedule,
    serialize_task, parse_task_schedule, parse_task_plan, parse_datetime
)
from python.helpers.localization import Localization
from python.helpers.print_style import PrintStyle
from python.helpers import settings
import random


class SchedulerTaskCreate(ApiHandler):
    async def process(self, input: Input, request: Request) -> Output:
        """
        Create a new task in the scheduler
        """
        printer = PrintStyle(italic=True, font_color="blue", padding=False)

        # Get timezone from input (do not set if not provided, we then rely on poll() to set it)
        if timezone := input.get("timezone", None):
            Localization.get().set_timezone(timezone)

        scheduler = TaskScheduler.get()
        await scheduler.reload()

        # Get common fields from input
        name = input.get("name")
        system_prompt = input.get("system_prompt", "")
        prompt = input.get("prompt")
        attachments = input.get("attachments", [])
        context_id = input.get("context_id", None)
        agent_profile = input.get("agent_profile", settings.get_settings()["agent_profile"])

        # Check if schedule is provided (for ScheduledTask)
        schedule = input.get("schedule", {})
        token: str = input.get("token", "")
        execute_at_raw = input.get("execute_at", None)

        # Debug log the token value
        printer.print(f"Token received from frontend: '{token}' (type: {type(token)}, length: {len(token) if token else 0})")

        plan = input.get("plan", {})

        # Validate required fields
        if not name or not prompt:
            raise ValueError("Missing required fields: name, system_prompt, prompt")

        task = None
        if schedule:
            # Create a scheduled task
            # Handle different schedule formats (string or object)
            if isinstance(schedule, str):
                # Parse the string schedule
                parts = schedule.split(' ')
                task_schedule = TaskSchedule(
                    minute=parts[0] if len(parts) > 0 else "*",
                    hour=parts[1] if len(parts) > 1 else "*",
                    day=parts[2] if len(parts) > 2 else "*",
                    month=parts[3] if len(parts) > 3 else "*",
                    weekday=parts[4] if len(parts) > 4 else "*"
                )
            elif isinstance(schedule, dict):
                # Use our standardized parsing function
                try:
                    task_schedule = parse_task_schedule(schedule)
                except ValueError as e:
                    raise ValueError(str(e))
            else:
                raise ValueError("Invalid schedule format. Must be string or object.")

            task = ScheduledTask.create(
                name=name,
                system_prompt=system_prompt,
                prompt=prompt,
                schedule=task_schedule,
                attachments=attachments,
                context_id=context_id,
                timezone=timezone,
                agent_profile=agent_profile,
            )
        elif plan:
            # Create a planned task
            try:
                # Use our standardized parsing function
                task_plan = parse_task_plan(plan)
            except ValueError as e:
                return {"error": str(e)}

            task = PlannedTask.create(
                name=name,
                system_prompt=system_prompt,
                prompt=prompt,
                plan=task_plan,
                attachments=attachments,
                context_id=context_id,
                agent_profile=agent_profile,
            )
        elif execute_at_raw:
            # Create a one-shot task via TaskPlan with single todo entry
            try:
                execute_at_dt = parse_datetime(execute_at_raw)
                if execute_at_dt is None:
                    raise ValueError("Invalid execute_at datetime")
            except ValueError as e:
                return {"error": str(e)}

            from python.helpers.task_scheduler import OneShotTask, TaskPlan  # local import to avoid circular typing
            task_plan = TaskPlan.create(todo=[execute_at_dt], in_progress=None, done=[])
            task = OneShotTask.create(
                name=name,
                system_prompt=system_prompt,
                prompt=prompt,
                plan=task_plan,
                attachments=attachments,
                context_id=context_id,
                agent_profile=agent_profile,
            )
        else:
            # Create an ad-hoc task
            if not token:
                token = str(random.randint(1000000000000000000, 9999999999999999999))
            printer.print(f"Creating AdHocTask with token: '{token}'")
            task = AdHocTask.create(
                name=name,
                system_prompt=system_prompt,
                prompt=prompt,
                token=token,
                attachments=attachments,
                context_id=context_id
            )

        # Add the task to the scheduler
        await scheduler.add_task(task)

        # Return the created task using our standardized serialization function
        task_dict = serialize_task(task)

        return {
            "task": task_dict
        }
