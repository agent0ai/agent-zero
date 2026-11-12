from helpers.extension import Extension
from helpers.tool_policy import ensure_tool_allowed


class EnforceToolPolicy(Extension):
    async def execute(self, tool_name: str = "", tool_args: dict | None = None, **kwargs) -> None:
        if self.agent and tool_name:
            ensure_tool_allowed(self.agent, tool_name, tool_args=tool_args or {})
