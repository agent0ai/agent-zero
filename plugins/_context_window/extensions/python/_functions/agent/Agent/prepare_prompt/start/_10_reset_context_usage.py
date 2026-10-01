from helpers.extension import Extension
from plugins._context_window.helpers import usage


class ResetContextUsage(Extension):
    def execute(self, **kwargs):
        usage.reset(self.agent)
