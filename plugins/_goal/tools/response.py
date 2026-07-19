from __future__ import annotations

from helpers.tool import Response
from plugins._goal.helpers import goals
from tools import response as core_response


_CONTINUE_MARKER = "_goal_continue"


class ResponseTool(core_response.ResponseTool):
    async def execute(self, **kwargs) -> Response:
        response = await super().execute(**kwargs)
        goal = goals.get_goal(self.agent.context.id)
        if not goal or goal.get("status") != "active":
            return response

        response.break_loop = False
        response.message = (
            "Goal still active. Continue working autonomously and make safe, in-scope "
            "choices yourself. Call update_goal complete when satisfied, or blocked only "
            "when no viable in-scope path remains."
        )
        response.additional = {**(response.additional or {}), _CONTINUE_MARKER: True}
        return response

    async def after_execution(self, response: Response, **kwargs):
        additional = response.additional or {}
        if additional.pop(_CONTINUE_MARKER, False):
            self.agent.hist_add_tool_result(self.name, response.message, **additional)
        await super().after_execution(response, **kwargs)
