from helpers.extension import Extension
from helpers.tool_policy import ensure_tool_allowed


class EnforceToolPolicy(Extension):
    async def execute(self, tool_name: str = "", **kwargs) -> None:
        if self.agent and tool_name:
            ensure_tool_allowed(self.agent, tool_name)
