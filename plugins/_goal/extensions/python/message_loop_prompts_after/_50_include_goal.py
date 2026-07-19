from __future__ import annotations

from agent import LoopData
from helpers.extension import Extension
from plugins._goal.helpers import goals


class IncludeGoal(Extension):
    async def execute(self, loop_data: LoopData = LoopData(), **kwargs):
        if not self.agent:
            return

        try:
            goal = goals.get_goal(self.agent.context.id)
        except ValueError:
            goal = None

        if not goal or goal.get("status") != "active":
            loop_data.extras_temporary.pop("current_goal", None)
            return

        loop_data.extras_temporary["current_goal"] = self.agent.read_prompt(
            "agent.extras.goal.md",
            status=goal.get("status", ""),
            objective=goal.get("objective", ""),
            created_by=goal.get("created_by", ""),
            updated_at=goal.get("updated_at", ""),
        )
