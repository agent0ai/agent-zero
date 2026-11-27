from helpers import skill_tools, tool_policy
from helpers.extension import Extension
from tools.unknown import Unknown


class ResolveSkillTool(Extension):
    def execute(self, data: dict, **kwargs):
        tool = data["result"]
        if not self.agent or not isinstance(tool, Unknown):
            return
        binding = skill_tools.registered(self.agent).get(tool.name)
        if not binding or not tool_policy.resolve_tool(
            self.agent, tool.name, skill_tool=binding, tool_args=tool.args
        ).allowed:
            return
        instance = binding.factory(
            agent=self.agent, name=tool.name, method=tool.method, args=tool.args,
            message=tool.message, loop_data=tool.loop_data,
        )
        instance._skill_tool = binding
        data["result"] = instance
