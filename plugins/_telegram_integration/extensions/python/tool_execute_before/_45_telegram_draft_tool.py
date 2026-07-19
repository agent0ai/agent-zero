from helpers.extension import Extension
from plugins._telegram_integration.helpers.constants import CTX_TG_BOT


class TelegramDraftToolStart(Extension):

    async def execute(self, tool_name: str = "", tool_args: dict | None = None, **kwargs):
        if not self.agent or self.agent.number != 0:
            return
        if (tool_name or "").strip().lower() == "response":
            return
        context = self.agent.context
        context_data = getattr(context, "data", None)
        telegram_bot = (
            context_data.get(CTX_TG_BOT)
            if isinstance(context_data, dict)
            else context.get_data(CTX_TG_BOT)
        )
        if not telegram_bot:
            return

        from plugins._telegram_integration.helpers import draft_stream

        await draft_stream.add_tool_start(context, tool_name, tool_args or {})
