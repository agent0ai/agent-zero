from __future__ import annotations

from helpers.tool import Response, Tool
from plugins._goal.helpers import goals


class GetGoal(Tool):
    async def execute(self, **kwargs) -> Response:
        goal = goals.get_goal(self.agent.context.id)
        return Response(message=goals.summarize_goal(goal), break_loop=False)
