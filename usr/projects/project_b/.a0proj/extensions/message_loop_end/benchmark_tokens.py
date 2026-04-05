from agent import Agent
from python.helpers.extension import Extension


class BenchmarkTokens(Extension):
    """Track approximate input tokens once per LLM call."""

    async def execute(self, **kwargs):
        if not self.agent or self.agent.number == 0:
            return

        state = self.agent.context.get_data("benchmark_project_state")
        if not state:
            return

        stats = state.get("stats", {})
        call_no = int(stats.get("llm_calls", 0))
        last_counted_call = int(stats.get("_last_input_counted_call", 0))

        # Count input tokens once per call (message_loop_end is once per iteration)
        if call_no > last_counted_call:
            ctx_data = self.agent.get_data(Agent.DATA_NAME_CTX_WINDOW) or {}
            input_tokens = int(ctx_data.get("tokens", 0) or 0)
            stats["input_tokens"] = int(stats.get("input_tokens", 0) or 0) + max(0, input_tokens)
            stats["_last_input_counted_call"] = call_no

        state["stats"] = stats
        self.agent.context.set_data("benchmark_project_state", state)