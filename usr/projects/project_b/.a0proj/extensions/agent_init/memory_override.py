from python.helpers.extension import Extension


class MemoryOverride(Extension):
    """Flag subordinate benchmark agents to skip memory behavior."""

    async def execute(self, **kwargs):
        if not self.agent or self.agent.number == 0:
            return

        state = self.agent.context.get_data("benchmark_project_state")
        if not state:
            return

        self.agent.set_data("_benchmark_skip_memory", True)