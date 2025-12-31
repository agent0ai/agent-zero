from python.helpers.alert import emit_alert
from python.helpers.extension import Extension
from agent import AgentContextType, LoopData


class AlertSubagentComplete(Extension):
    async def execute(self, loop_data: LoopData = LoopData(), **kwargs):
        # Only subagents should emit this alert
        if self.agent.number <= 0:
            return

        # Never alert for background contexts
        if self.agent.context and self.agent.context.type == AgentContextType.BACKGROUND:
            return

        emit_alert("subagent_complete")


