from helpers.extension import Extension
from helpers.team_access import is_team_chat
from helpers.team_runs import current_dispatch


class TeamCommunicateAuthorization(Extension):
    def execute(self, data, **kwargs) -> None:
        context = data["args"][0]
        if is_team_chat(context):
            current_dispatch(context)
