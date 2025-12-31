from python.helpers.alert import emit_alert
from python.helpers.extension import Extension
from python.helpers.task_scheduler import TaskScheduler
from python.helpers.tool import Response
from agent import AgentContextType


class AlertTaskComplete(Extension):
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

        # Only when the agent finishes via the response tool
        if tool_name != "response":
            return
        if not response or not getattr(response, "break_loop", False):
            return

        # Only for scheduler task contexts
        scheduler = TaskScheduler.get()
        task = scheduler.get_task_by_uuid(self.agent.context.id)
        if not task:
            return

        emit_alert("task_complete")


