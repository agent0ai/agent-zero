from python.helpers.extension import Extension
from python.helpers.tokens import approximate_tokens


class BenchmarkOutputTokens(Extension):
    """Track approximate output tokens from streamed assistant response deltas."""

    async def execute(self, text: str = "", **kwargs):
        if not self.agent or self.agent.number == 0:
            return

        state = self.agent.context.get_data("benchmark_project_state")
        if not state:
            return

        stats = state.get("stats", {})
        prev = int(stats.get("_last_response_chars", 0))
        current = len(text or "")

        if current >= prev:
            delta = (text or "")[prev:]
        else:
            # New stream likely started; treat full text as delta.
            delta = text or ""

        if delta:
            stats["output_tokens"] = int(stats.get("output_tokens", 0) or 0) + int(approximate_tokens(delta))

        stats["_last_response_chars"] = current
        state["stats"] = stats
        self.agent.context.set_data("benchmark_project_state", state)