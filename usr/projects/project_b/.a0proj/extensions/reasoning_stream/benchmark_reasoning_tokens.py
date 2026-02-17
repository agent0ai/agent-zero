from python.helpers.extension import Extension
from python.helpers.tokens import approximate_tokens


class BenchmarkReasoningTokens(Extension):
    """Track approximate reasoning tokens from streamed reasoning deltas."""

    async def execute(self, text: str = "", **kwargs):
        if not self.agent or self.agent.number == 0:
            return

        state = self.agent.context.get_data("benchmark_project_state")
        if not state:
            return

        stats = state.get("stats", {})
        prev = int(stats.get("_last_reasoning_chars", 0))
        current = len(text or "")

        if current >= prev:
            delta = (text or "")[prev:]
        else:
            # New stream likely started; treat full text as delta.
            delta = text or ""

        if delta:
            stats["reasoning_tokens"] = int(stats.get("reasoning_tokens", 0) or 0) + int(approximate_tokens(delta))

        stats["_last_reasoning_chars"] = current
        state["stats"] = stats
        self.agent.context.set_data("benchmark_project_state", state)