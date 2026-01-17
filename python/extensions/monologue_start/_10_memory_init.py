from python.helpers.extension import Extension
from agent import LoopData
from python.helpers import memory
import asyncio


class MemoryInit(Extension):

    async def execute(self, loop_data: LoopData = LoopData(), **kwargs):
        if self.is_stale():
            return
        db = await memory.Memory.get(self.agent)
        

   