from python.helpers.extension import Extension
from agent import LoopData
import asyncio

# Import memory from plugin
import sys
from pathlib import Path
_plugin_root = Path(__file__).parent.parent.parent
if str(_plugin_root) not in sys.path:
    sys.path.insert(0, str(_plugin_root))
from helpers import memory


class MemoryInit(Extension):

    async def execute(self, loop_data: LoopData = LoopData(), **kwargs):
        db = await memory.Memory.get(self.agent)
        

   