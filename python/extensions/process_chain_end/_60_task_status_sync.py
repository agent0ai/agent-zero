from python.helpers.extension import Extension
from python.helpers.task_scheduler import TaskScheduler, TaskState
from python.helpers.print_style import PrintStyle
from agent import LoopData


class TaskStatusSync(Extension):
    """Reset task ERROR/stuck-RUNNING state when a user manually interacts with a task chat."""

    async def execute(self, loop_data: LoopData = LoopData(), **kwargs):
        if self.agent.number != 0:
            return

        context = self.agent.context
        scheduler = TaskScheduler.get()
        tasks = scheduler.get_tasks_by_context_id(context.id)

        if not tasks:
            return

        for task in tasks:
            if task.state in (TaskState.ERROR, TaskState.RUNNING):
                PrintStyle.info(
                    f"Task '{task.name}' recovered via user interaction — "
                    f"resetting {task.state.value.upper()} → IDLE"
                )
                scheduler.cancel_running_task(task.uuid, terminate_thread=True)
                await scheduler.update_task(task.uuid, state=TaskState.IDLE)
                await scheduler.save()
