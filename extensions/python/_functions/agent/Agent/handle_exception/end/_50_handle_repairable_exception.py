from datetime import datetime, timezone
from helpers.extension import Extension
from agent import LoopData
from helpers.localization import Localization
from helpers.errors import RepairableException
from helpers import errors, extension
from helpers.print_style import PrintStyle

class HandleRepairableException(Extension):
    async def execute(self, data: dict = {}, **kwargs):
        if not self.agent:
            return

        if not data.get("exception"):
            return

        if isinstance(data["exception"], RepairableException):
            msg = {"message": errors.format_error(data["exception"])}
            await extension.call_extensions_async("error_format", agent=self.agent, msg=msg)
            wmsg = self.agent.hist_add_warning(msg["message"])
            PrintStyle(font_color="red", padding=True).print(msg["message"])
            self.agent.context.log.log(type="warning", content=msg["message"], id=wmsg.id)
            data["exception"] = None

        
