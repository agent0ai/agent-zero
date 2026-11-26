from helpers.extension import Extension
from helpers.team_access import is_team_chat
from helpers.team_runs import manage_turn


class TeamTaskLifecycle(Extension):
    def execute(self, data, **kwargs) -> None:
        context, *args = data["args"]
        if not is_team_chat(context):
            return
        if args:
            func, *func_args = args
            data["args"] = (context, manage_turn(context, func), *func_args)
        else:
            data["kwargs"]["func"] = manage_turn(context, data["kwargs"]["func"])
