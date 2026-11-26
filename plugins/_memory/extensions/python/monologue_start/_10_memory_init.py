from helpers.extension import Extension
from helpers.team_access import is_team_chat
from agent import LoopData

# Direct import - this extension lives inside the memory plugin
from plugins._memory.helpers import memory


class MemoryInit(Extension):

    async def execute(self, loop_data: LoopData = LoopData(), **kwargs):
        if not self.agent or is_team_chat(getattr(self.agent, "context", None)):
            return

        db = await memory.Memory.get(self.agent)
