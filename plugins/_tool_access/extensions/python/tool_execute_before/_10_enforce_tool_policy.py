from helpers.extension import Extension
from helpers.tool_policy import ensure_tool_allowed


class EnforceToolPolicy(Extension):
    async def execute(self, tool_name: str = "", tool_args: dict | None = None, **kwargs) -> None:
        if self.agent and tool_name:
            tool = getattr(getattr(self.agent, "loop_data", None), "current_tool", None)
            ensure_tool_allowed(
                self.agent, tool_name, tool_args=tool_args or {},
                tool_path=getattr(tool, "_tool_source_path", ""),
                skill_tool=getattr(tool, "_skill_tool", None),
            )
