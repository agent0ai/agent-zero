from __future__ import annotations

from agent import LoopData
from helpers.extension import Extension
from plugins._code_execution.helpers.destinations import (
    get_code_execution_destinations,
)


class IncludeCodeExecutionDestinations(Extension):
    async def execute(self, loop_data: LoopData = LoopData(), **kwargs) -> None:
        if self.agent is None:
            return
        destinations = await get_code_execution_destinations(self.agent)
        lines = [
            f"- `{item.id}` — {item.label} ({item.status}): {item.description}"
            for item in destinations
        ]
        loop_data.extras_temporary["code_execution_destinations"] = self.agent.read_prompt(
            "agent.extras.code_execution_destinations.md",
            destinations="\n".join(lines),
        )
