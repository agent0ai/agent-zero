from agent import LoopData
from python.helpers import memory
from python.helpers.extension import Extension


class MemoryInit(Extension):
    async def execute(self, loop_data: LoopData = LoopData(), **kwargs):
        await memory.Memory.get(self.agent)
