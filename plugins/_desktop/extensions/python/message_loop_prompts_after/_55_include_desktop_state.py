from __future__ import annotations

from agent import LoopData
from helpers.extension import Extension
from plugins._desktop.helpers import prompt_context


class IncludeDesktopState(Extension):
    async def execute(self, loop_data: LoopData = LoopData(), **kwargs):
        context_id = str(getattr(getattr(self.agent, "context", None), "id", "") or "")
        context = prompt_context.build_context(context_id=context_id)
        if not context:
            loop_data.extras_temporary.pop("desktop_state", None)
            return

        loop_data.extras_temporary["desktop_state"] = self.agent.read_prompt(
            "agent.extras.desktop_state.md",
            desktop_state=context,
        ) if self.agent else context
