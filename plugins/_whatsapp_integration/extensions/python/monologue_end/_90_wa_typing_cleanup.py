from helpers.extension import Extension
from helpers import plugins
from plugins._whatsapp_integration.helpers.handler import (
    CTX_WA_CHAT_ID,
    CTX_WA_TYPING_ACTIVE,
)
from plugins._whatsapp_integration.helpers import bridge_manager, wa_client


PLUGIN_NAME = "_whatsapp_integration"


class WhatsAppTypingCleanup(Extension):

    async def execute(self, **kwargs):  # type: ignore[override]
        if not self.agent:
            return

        context = self.agent.context

        if not context.data.get(CTX_WA_TYPING_ACTIVE):
            return

        chat_id = context.data.get(CTX_WA_CHAT_ID, "")
        if not chat_id:
            return

        config = plugins.get_plugin_config(PLUGIN_NAME) or {}
        port = int(config.get("bridge_port", 3100))
        base_url = bridge_manager.get_bridge_url(port)

        await wa_client.send_typing(base_url, chat_id, paused=True)
        context.data[CTX_WA_TYPING_ACTIVE] = False
