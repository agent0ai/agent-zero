from helpers.extension import Extension
from agent import LoopData
from plugins._infection_check.helpers.checker import get_checker


class InfectionAnalyzeThoughts(Extension):
    async def execute(self, loop_data=LoopData(), text="", parsed={}, **kwargs):
        if not self.agent or not parsed:
            return
        checker = get_checker(self.agent)
        if checker.mode != "thoughts":
            return
        # Start background analysis once thoughts are complete
        if parsed.get("heading") or parsed.get("tool_name"):
            checker.start_analysis(self.agent)
