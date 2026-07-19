from agent import LoopData
from helpers.extension import Extension
from plugins._telegram_integration.helpers.constants import CTX_TG_BOT


class TelegramDraftStart(Extension):

    async def execute(self, loop_data: LoopData = LoopData(), **kwargs):
        if not self.agent or self.agent.number != 0:
            return
        context = self.agent.context
        if not context.data.get(CTX_TG_BOT):
            return

        from plugins._telegram_integration.helpers import draft_stream, heartbeat

        await draft_stream.start(context)
        await heartbeat.start(context)
