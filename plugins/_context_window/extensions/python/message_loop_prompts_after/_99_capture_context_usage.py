from agent import LoopData
from helpers.extension import Extension
from plugins._context_window.helpers.usage import capture_context


class CaptureContextUsage(Extension):
    def execute(self, loop_data: LoopData | None = None, **kwargs):
        capture_context(self.agent, loop_data)
