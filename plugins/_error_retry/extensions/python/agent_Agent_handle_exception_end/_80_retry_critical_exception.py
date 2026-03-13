import asyncio
from datetime import datetime, timezone
from helpers.extension import Extension
from agent import LoopData
from helpers.localization import Localization
from helpers.errors import RepairableException, HandledException
from helpers import errors
from helpers.print_style import PrintStyle

from plugins._error_retry.extensions.python.agent_Agent_monologue_start._10_reset_critical_exception_counter import DATA_NAME_COUNTER

class RetryCriticalException(Extension):
    async def execute(self, data: dict = {}, **kwargs):
        if not self.agent:
            return

        exception = data.get("exception")
        if not exception:
            return

        if isinstance(exception, (HandledException, RepairableException)):
            return

        max_retries = 1
        delay = 3

        counter = self.agent.get_data(DATA_NAME_COUNTER) or 0
        if counter >= max_retries:
            return

        self.agent.set_data(DATA_NAME_COUNTER, counter + 1)

        error_message = errors.format_error(exception)
        self.agent.context.log.log(
            type="warning",
            heading="Critical error occurred, retrying...",
            content=error_message,
        )
        PrintStyle(font_color="orange", padding=True).print(
            "Critical error occurred, retrying..."
        )
        await asyncio.sleep(delay)
        await self.agent.handle_intervention()
        agent_facing_error = self.agent.read_prompt(
            "fw.msg_critical_error.md", error_message=error_message
        )
        self.agent.hist_add_warning(message=agent_facing_error)
        PrintStyle(font_color="orange", padding=True).print(agent_facing_error)

        data["exception"] = None

        
