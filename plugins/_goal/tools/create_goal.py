from __future__ import annotations

from helpers.tool import Response, Tool
from plugins._goal.helpers import goals


class CreateGoal(Tool):
    async def execute(
        self,
        objective: str = "",
        token_budget: int | None = None,
        **kwargs,
    ) -> Response:
        goal = goals.create_goal(
            self.agent.context.id,
            objective,
            created_by="model",
            token_budget=token_budget,
        )
        return Response(
            message=f"Goal created: {goal['objective']}",
            break_loop=False,
        )
