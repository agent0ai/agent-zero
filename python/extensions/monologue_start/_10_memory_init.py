from agent import LoopData
from python.helpers import memory, settings
from python.helpers.extension import Extension


class MemoryInit(Extension):
    async def execute(self, loop_data: LoopData = LoopData(), **kwargs):
        cfg = settings.get_settings()
        # In lightweight/free mode, avoid cold-start VectorDB work unless memory
        # features are actually enabled.
        if not cfg.get("memory_recall_enabled", False) and not cfg.get("memory_memorize_enabled", False):
            return
        await memory.Memory.get(self.agent)
