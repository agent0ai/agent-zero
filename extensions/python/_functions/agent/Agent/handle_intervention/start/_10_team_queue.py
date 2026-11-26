from helpers.extension import Extension
from helpers.team_runs import next_interjection


class TeamQueueInterjection(Extension):
    def execute(self, **kwargs) -> None:
        if self.agent and self.agent.number == 0 and self.agent.intervention is None:
            message = next_interjection(self.agent.context)
            if message is not None:
                self.agent.intervention = message
