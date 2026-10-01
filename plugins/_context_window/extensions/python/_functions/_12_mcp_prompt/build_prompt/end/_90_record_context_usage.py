from helpers.extension import Extension
from plugins._context_window.helpers.usage import record_prompt


class RecordMcpToolsUsage(Extension):
    def execute(self, data: dict | None = None, **kwargs):
        record_prompt(self.agent, "mcp_tools", (data or {}).get("result"))
