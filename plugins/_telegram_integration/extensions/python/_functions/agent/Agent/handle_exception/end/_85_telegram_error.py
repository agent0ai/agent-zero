from helpers.errors import HandledException
from helpers.extension import Extension
from helpers.print_style import PrintStyle
from plugins._telegram_integration.helpers.constants import (
    CTX_TG_BOT,
    CTX_TG_ERROR_SENT,
    CTX_TG_REPLY_TO,
    CTX_TG_TYPING_STOP,
)


class TelegramFriendlyError(Extension):
    async def execute(self, data: dict = {}, **kwargs):
        if not self.agent or self.agent.number != 0:
            return

        context = self.agent.context
        if not context.data.get(CTX_TG_BOT):
            return

        exception = data.get("exception")
        if not exception or isinstance(exception, HandledException):
            return

        if context.data.get(CTX_TG_ERROR_SENT):
            return

        context.data[CTX_TG_ERROR_SENT] = True

        from plugins._telegram_integration.helpers import draft_stream, error_ui, heartbeat
        from plugins._telegram_integration.helpers.handler import send_telegram_reply

        text = error_ui.friendly_error_message(exception)
        error = await send_telegram_reply(context, text)
        if error:
            PrintStyle.debug(f"Telegram error reply failed: {error}")

        typing_stop = context.data.pop(CTX_TG_TYPING_STOP, None)
        if typing_stop:
            typing_stop.set()
        await heartbeat.stop(context)
        draft_stream.clear(context)
        context.data.pop(CTX_TG_REPLY_TO, None)
