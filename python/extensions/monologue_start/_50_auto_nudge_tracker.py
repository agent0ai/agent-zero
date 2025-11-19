import time
from python.helpers.extension import Extension

class AutoNudgeTracker(Extension):
    async def execute(self, **kwargs):
        # Update last activity time
        self.agent.context.set_data("last_activity_time", time.time())
