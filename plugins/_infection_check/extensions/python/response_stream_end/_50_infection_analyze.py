from helpers.extension import Extension
from agent import LoopData
from plugins._infection_check.helpers.checker import get_checker


class InfectionAnalyzeEnd(Extension):
    async def execute(self, loop_data=LoopData(), **kwargs):
        if not self.agent:
            return
        get_checker(self.agent).start_analysis(self.agent)
