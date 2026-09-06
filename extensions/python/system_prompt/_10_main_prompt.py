from typing import Any

from helpers.extension import Extension, extensible
from agent import Agent, LoopData


class MainPrompt(Extension):

    async def execute(
        self,
        system_prompt: list[str] = [],
        loop_data: LoopData = LoopData(),
        **kwargs: Any,
    ):
        if not self.agent:
            return
        prompt = await build_prompt(self.agent)
        system_prompt.append(prompt)
        communication = self.agent.read_prompt("agent.system.main.communication.md")
        if communication in prompt:
            loop_data.responses_prompt_replacements[communication] = self.agent.read_prompt(
                "agent.system.main.communication.native.md"
            )


@extensible
async def build_prompt(agent: Agent) -> str:
    return agent.read_prompt("agent.system.main.md")
