from agent import LoopData
from python.extensions.monologue_end._50_memorize_fragments import MemorizeMemories as BaseMemorizeMemories


def _skip(agent) -> bool:
    if not agent:
        return False
    if agent.number == 0:
        return False
    if not agent.get_data("_benchmark_skip_memory"):
        return False
    return bool(agent.context.get_data("benchmark_project_state"))


class MemorizeMemories(BaseMemorizeMemories):
    async def execute(self, loop_data: LoopData = LoopData(), **kwargs):
        if _skip(self.agent):
            return
        return await super().execute(loop_data=loop_data, **kwargs)