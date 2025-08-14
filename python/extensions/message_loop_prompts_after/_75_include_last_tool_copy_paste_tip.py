from agent import LoopData
from python.helpers.extension import Extension


class IncludeLastToolCopyPasteTip(Extension):
    async def execute(self, loop_data: LoopData = LoopData(), **kwargs):
        last_call = self.agent.get_data("last_tool_call")
        if not last_call:
            return

        tool_name: str = last_call.get("tool_name", "")
        last_output: str = last_call.get("last_tool_output", "")
        if not last_output:
            return

        preview = (last_output[:50] or "").replace("\n", " ").strip()
        tip = self.agent.read_prompt(
            "fw.extras.last_tool_copy.md",
            tool_name=tool_name,
            last_tool_output_preview=preview,
        )
        loop_data.extras_temporary["last_tool_copy_paste"] = tip
