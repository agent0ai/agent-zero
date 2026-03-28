from agent import LoopData
from python.extensions.message_loop_prompts_after._50_recall_memories import RecallMemories as BaseRecallMemories


def _skip(agent) -> bool:
    if not agent:
        return False
    if agent.number == 0:
        return False
    if not agent.get_data("_benchmark_skip_memory"):
        return False
    return bool(agent.context.get_data("benchmark_project_state"))


class RecallMemories(BaseRecallMemories):
    async def execute(self, loop_data: LoopData = LoopData(), **kwargs):
        if _skip(self.agent):
            return
        return await super().execute(loop_data=loop_data, **kwargs)