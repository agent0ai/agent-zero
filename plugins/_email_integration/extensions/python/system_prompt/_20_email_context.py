"""Inject email conversation context into system prompt for email sessions."""

from helpers.extension import Extension
from helpers import plugins
from agent import LoopData
from plugins._email_integration.helpers.dispatcher import CTX_EMAIL_HANDLER


PLUGIN_NAME = "_email_integration"


class EmailContextPrompt(Extension):

    async def execute(
        self,
        system_prompt: list[str] = [],
        loop_data: LoopData = LoopData(),
        **kwargs,
    ):
        if not self.agent:
            return

        handler_name = self.agent.context.data.get(CTX_EMAIL_HANDLER)
        if not handler_name:
            return

        system_prompt.append(
            self.agent.read_prompt("fw.email.system_context_reply.md")
        )

        config = plugins.get_plugin_config(PLUGIN_NAME) or {}
        for h in config.get("handlers", []):
            if h.get("name") == handler_name:
                instructions = h.get("agent_instructions", "")
                if instructions:
                    system_prompt.append(
                        self.agent.read_prompt(
                            "fw.email.user_message_instructions.md",
                            instructions=instructions,
                        )
                    )
                break
