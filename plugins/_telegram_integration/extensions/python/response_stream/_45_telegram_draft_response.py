from agent import LoopData
from helpers.extension import Extension
from plugins._telegram_integration.helpers.constants import CTX_TG_BOT


class TelegramDraftResponse(Extension):

    async def execute(
        self,
        loop_data: LoopData = LoopData(),
        parsed: dict | None = None,
        **kwargs,
    ):
        if not self.agent or self.agent.number != 0:
            return
        context = self.agent.context
        if not context.data.get(CTX_TG_BOT):
            return

        parsed = parsed or {}
        if parsed.get("tool_name") != "response":
            return
        tool_args = parsed.get("tool_args") or {}
        text = tool_args.get("text") or tool_args.get("message") or ""
        if not text:
            return

        from plugins._telegram_integration.helpers import draft_stream

        await draft_stream.update_response(context, str(text))
