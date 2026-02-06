from python.helpers.tool import Tool, Response

# Import Memory from plugin
import sys
from pathlib import Path
_plugin_root = Path(__file__).parent.parent
if str(_plugin_root) not in sys.path:
    sys.path.insert(0, str(_plugin_root))
from helpers.memory import Memory


class MemorySave(Tool):

    async def execute(self, text="", area="", **kwargs):

        if not area:
            area = Memory.Area.MAIN.value

        metadata = {"area": area, **kwargs}

        db = await Memory.get(self.agent)
        id = await db.insert_text(text, metadata)

        result = self.agent.read_prompt("fw.memory_saved.md", memory_id=id)
        return Response(message=result, break_loop=False)
