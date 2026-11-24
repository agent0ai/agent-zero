from helpers import tool_policy
from helpers.extension import Extension


class BrowserSkillPrompt(Extension):
    def execute(self, data: dict, **kwargs):
        args = data["args"]
        name = args[1] if len(args) > 1 else data["kwargs"].get("file")
        if self.agent and name == "agent.system.tool.browser.md":
            decision = tool_policy.resolve_tool(self.agent, "browser")
            if decision.source == "plugin" and not decision.allowed:
                data["result"] = ""
