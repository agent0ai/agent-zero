"""Inject email conversation context into system prompt for email sessions."""

from helpers.extension import Extension
from agent import LoopData
from plugins._email_integration.helpers.dispatcher import CTX_EMAIL_HANDLER


class EmailContextPrompt(Extension):

    async def execute(
        self,
        system_prompt: list[str] = [],
        loop_data: LoopData = LoopData(),
        **kwargs,
    ):
        if not self.agent:
            return

        if self.agent.context.data.get(CTX_EMAIL_HANDLER):
            system_prompt.append(
                self.agent.read_prompt("fw.email.system_context_reply.md")
            )
