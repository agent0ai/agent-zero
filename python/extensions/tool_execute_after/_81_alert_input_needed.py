from python.helpers.alert import emit_alert
from python.helpers.extension import Extension
from python.helpers.task_scheduler import TaskScheduler
from python.helpers.tool import Response
from agent import AgentContextType


class AlertInputNeeded(Extension):
    async def execute(
        self,
        response: Response | None = None,
        tool_name: str | None = None,
        **kwargs,
    ):
        # Only main agent should emit alerts
        if self.agent.number != 0:
            return

        # Never alert for background contexts
        if self.agent.context and self.agent.context.type == AgentContextType.BACKGROUND:
            return

        # Only when the agent finishes via the response tool (end of a chat turn)
        if tool_name != "response":
            return
        if not response or not getattr(response, "break_loop", False):
            return

        # Exclude scheduler task contexts (those are handled by task-complete alert)
        scheduler = TaskScheduler.get()
        task = scheduler.get_task_by_uuid(self.agent.context.id)
        if task:
            return

        emit_alert("input_needed")


