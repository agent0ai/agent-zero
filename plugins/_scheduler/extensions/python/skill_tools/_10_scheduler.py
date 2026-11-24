from helpers.extension import Extension
from helpers.skill_tools import SkillTool
from helpers.tool_actions import action_policy_id


def _scheduler(**kwargs):
    from plugins._scheduler.helpers.scheduler_handler import SchedulerTool

    return SchedulerTool(**kwargs)


_BINDING = SkillTool(
    "_scheduler",
    "scheduled-tasks",
    _scheduler,
    legacy_denials=tuple(
        action_policy_id("plugin:_scheduler:scheduler", action)
        for action in (
            "list_tasks", "find_task_by_name", "show_task", "run_task", "delete_task",
            "update_task", "create_scheduled_task", "create_adhoc_task",
            "create_planned_task", "wait_for_task",
        )
    ),
)


class RegisterScheduler(Extension):
    def execute(self, bindings: dict, **kwargs):
        bindings["scheduler"] = _BINDING
