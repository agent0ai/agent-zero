from datetime import datetime
from python.helpers.extension import Extension


class BenchmarkStats(Extension):
    """Track benchmark call stats for subordinate agents only."""

    async def execute(self, **kwargs):
        if not self.agent or self.agent.number == 0:
            return

        state = self.agent.context.get_data("benchmark_project_state")
        if not state:
            return

        stats = state.get("stats", {})
        stats["llm_calls"] = stats.get("llm_calls", 0) + 1
        stats.setdefault("timestamps", []).append(datetime.now().isoformat())

        # Reset per-call stream cursors so stream token extensions can track deltas.
        stats["_last_response_chars"] = 0
        stats["_last_reasoning_chars"] = 0

        state["stats"] = stats
        self.agent.context.set_data("benchmark_project_state", state)