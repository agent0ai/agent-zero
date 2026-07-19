from __future__ import annotations

from helpers.tool import Response, Tool
from plugins._goal.helpers import goals


class UpdateGoal(Tool):
    async def execute(
        self,
        status: str = "",
        objective: str = "",
        note: str = "",
        **kwargs,
    ) -> Response:
        normalized_status = str(status or "").strip().lower()
        if normalized_status not in {"complete", "blocked"}:
            return Response(
                message="Model-managed goal updates may only mark goals complete or blocked.",
                break_loop=False,
            )

        goal = goals.update_goal(
            self.agent.context.id,
            status=normalized_status,
            objective=objective if objective else None,
            note=note if note else None,
        )
        return Response(
            message=goals.summarize_goal(goal),
            break_loop=False,
        )
