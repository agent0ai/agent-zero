from helpers import persist_chat, team_access
from helpers.extension import Extension


class SaveTeamInput(Extension):
    def execute(self, **kwargs):
        if self.agent and team_access.is_team_chat(self.agent.context):
            persist_chat.save_tmp_chat(self.agent.context)
