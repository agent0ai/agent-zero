from helpers.extension import Extension

# Direct import - this extension lives inside the memory plugin
from plugins._memory.helpers.memory import reload as memory_reload


class MemoryReload(Extension):

    async def execute(self, **kwargs):
        memory_reload()
