from typing import Any
from python.helpers.extension import Extension
from agent import LoopData


class SequentialThinkingPrompt(Extension):
    """Injects Sequential Thinking MCP behavioral guidance into system prompt.

    This extension provides WHEN-to-use guidance for the sequential_thinking
    MCP tool, complementing the tool's capability documentation with usage
    philosophy. The guidance is optional - if the prompt file doesn't exist,
    the agent functions normally without it.
    """

    async def execute(
        self,
        system_prompt: list[str] = [],
        loop_data: LoopData = LoopData(),
        **kwargs: Any
    ):
        try:
            seq_thinking_prompt = self.agent.read_prompt("agent.system.sequential_thinking.md")
            if seq_thinking_prompt and seq_thinking_prompt.strip():
                system_prompt.append(seq_thinking_prompt)
        except Exception:
            # INTENTIONAL GRACEFUL DEGRADATION:
            # This prompt is an optional enhancement. If the file is missing,
            # has permission issues, or encoding problems, the agent should
            # continue working - just without the behavioral guidance.
            # This is NOT lazy error handling; it's deliberate fault tolerance
            # for a non-critical feature.
            pass
