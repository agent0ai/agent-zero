from python.helpers.extension import Extension
from agent import LoopData, AgentContextType
from python.helpers import memory
import asyncio


class MemoryInit(Extension):

    async def execute(self, loop_data: LoopData = LoopData(), **kwargs):
        # Avoid blocking startup for background agents; initialize lazily
        if self.agent.context.type == AgentContextType.BACKGROUND:
            asyncio.create_task(memory.Memory.get(self.agent))
            return
        await memory.Memory.get(self.agent)
