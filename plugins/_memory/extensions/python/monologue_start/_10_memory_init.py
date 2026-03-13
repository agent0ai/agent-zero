from helpers.extension import Extension
from agent import LoopData

# Direct import - this extension lives inside the memory plugin
from plugins._memory.helpers import memory


class MemoryInit(Extension):

    async def execute(self, loop_data: LoopData = LoopData(), **kwargs):
        if not self.agent:
            return

        db = await memory.Memory.get(self.agent)
