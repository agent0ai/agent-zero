from helpers.extension import Extension
from plugins._context_window.helpers.usage import record_prompt


class RecordSkillsUsage(Extension):
    def execute(self, data: dict | None = None, **kwargs):
        record_prompt(self.agent, "skills", (data or {}).get("result"))
