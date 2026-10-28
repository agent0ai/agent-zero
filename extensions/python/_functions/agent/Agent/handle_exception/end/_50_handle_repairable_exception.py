from helpers import errors, extension
from helpers.errors import RepairableException
from helpers.extension import Extension
from helpers.print_style import PrintStyle
from helpers.response_recovery import record_unusable_response
from helpers.settings import get_settings


class HandleRepairableException(Extension):
    async def execute(self, data: dict | None = None, **kwargs):
        if not self.agent or not isinstance(data, dict):
            return

        if not data.get("exception"):
            return

        if isinstance(data["exception"], RepairableException):
            msg = {"message": errors.format_error(data["exception"])}
            await extension.call_extensions_async(
                "error_format", agent=self.agent, msg=msg
            )
            wmsg = self.agent.hist_add_warning(msg["message"])
            PrintStyle(font_color="red", padding=True).print(msg["message"])
            self.agent.context.log.log(
                type="warning", content=msg["message"], id=wmsg.id
            )
            data["exception"] = record_unusable_response(
                self.agent, get_settings()["max_consecutive_unusable_responses"]
            )
