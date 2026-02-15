from python.helpers.tool import Tool, Response

# Import Memory and DEFAULT_THRESHOLD from plugin
import sys
from pathlib import Path
_plugin_root = Path(__file__).parent.parent
if str(_plugin_root) not in sys.path:
    sys.path.insert(0, str(_plugin_root))
from helpers.memory import Memory
from tools.memory_load import DEFAULT_THRESHOLD


class MemoryForget(Tool):

    async def execute(self, query="", threshold=DEFAULT_THRESHOLD, filter="", **kwargs):
        db = await Memory.get(self.agent)
        dels = await db.delete_documents_by_query(query=query, threshold=threshold, filter=filter)

        result = self.agent.read_prompt("fw.memories_deleted.md", memory_count=len(dels))
        return Response(message=result, break_loop=False)
