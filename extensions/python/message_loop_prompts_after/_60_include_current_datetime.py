from helpers.extension import Extension
from agent import LoopData
from helpers.localization import Localization


class IncludeCurrentDatetime(Extension):
    async def execute(self, loop_data: LoopData = LoopData(), **kwargs):
        if not self.agent:
            return

        current_datetime = Localization.get().now().strftime("%Y-%m-%d %H:%M:%S %Z")

        # read prompt
        datetime_prompt = self.agent.read_prompt(
            "agent.system.datetime.md", date_time=current_datetime
        )

        # add current datetime to the loop data
        loop_data.extras_temporary["current_datetime"] = datetime_prompt
