import asyncio

from helpers import login
from helpers.extension import Extension


class TeamRunRecovery(Extension):
    def execute(self, **kwargs) -> None:
        if login.team_mode_enabled():
            from helpers.team_runs import recover_on_startup

            recover_on_startup()
            asyncio.run(recover_team_tasks())


async def recover_team_tasks():
    from helpers.task_scheduler import TaskScheduler, TaskState

    scheduler = TaskScheduler.get()
    await scheduler.reload()
    for task in list(scheduler.get_tasks()):
        if task.team_project_id and task.state == TaskState.RUNNING:
            await scheduler.update_task_checked(
                task.uuid, lambda current: current.state == TaskState.RUNNING,
                state=TaskState.ERROR, last_result="The runtime interrupted this task.",
            )
