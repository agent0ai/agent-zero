from helpers.extension import Extension
from agent import LoopData


class CodeExecutionPrompt(Extension):

    async def execute(
        self,
        system_prompt: list[str] = [],
        loop_data: LoopData = LoopData(),
        **kwargs,
    ):
        if not self.agent:
            return
            
        system_prompt.append(self.agent.read_prompt("agent.system.tool.code_exe.md"))
        system_prompt.append(self.agent.read_prompt("agent.system.tool.input.md"))
