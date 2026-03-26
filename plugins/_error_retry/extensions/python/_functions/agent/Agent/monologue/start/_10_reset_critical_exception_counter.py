from datetime import datetime, timezone
from helpers.extension import Extension
from agent import LoopData
from helpers.localization import Localization
from helpers.errors import RepairableException
from helpers import errors
from helpers.print_style import PrintStyle

DATA_NAME_COUNTER = "_plugin.error_retry.critical_exception_counter"

class ResetCriticalExceptionCounter(Extension):
    async def execute(self, exception_data: dict = {}, **kwargs):
        if not self.agent:
            return
        
        self.agent.set_data(DATA_NAME_COUNTER, 0)

        