from helpers.extension import Extension
from helpers.team_access import is_team_chat


class TeamToolResolution(Extension):
    def execute(self, data, **kwargs) -> None:
        if not self.agent or not is_team_chat(self.agent.context):
            return
        args = data["args"]
        tool_kwargs = data["kwargs"]
        name = tool_kwargs.get("name", args[1] if len(args) > 1 else "")
        tool = None
        if name == "response":
            from plugins._goal.tools.response import ResponseTool

            tool = ResponseTool
        elif name == "goal":
            from plugins._goal.tools.goal import GoalTool

            tool = GoalTool
        elif name == "text_editor":
            from plugins._text_editor.tools.text_editor import TextEditor

            tool = TextEditor
        elif name == "memory":
            from plugins._memory.tools.memory import MemoryTool

            tool = MemoryTool
        data["result"] = tool(*args, **tool_kwargs) if tool else None
