"""Inject WhatsApp conversation context into system prompt."""

from helpers.extension import Extension
from helpers import plugins
from agent import LoopData
from plugins._whatsapp_integration.helpers.handler import CTX_WA_CHAT_ID, PLUGIN_NAME


class WhatsAppContextPrompt(Extension):

    async def execute(
        self,
        system_prompt: list[str] = [],
        loop_data: LoopData = LoopData(),
        **kwargs,
    ):
        if not self.agent:
            return

        if self.agent.context.data.get(CTX_WA_CHAT_ID):
            system_prompt.append(
                self.agent.read_prompt("fw.wa.system_context_reply.md")
            )
            config = plugins.get_plugin_config(PLUGIN_NAME) or {}
            instructions = config.get("agent_instructions", "")
            if instructions:
                system_prompt.append(
                    self.agent.read_prompt(
                        "fw.wa.user_message_instructions.md",
                        instructions=instructions,
                    )
                )
