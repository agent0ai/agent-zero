from helpers.extension import Extension
from agent import LoopData
from plugins._telegram_integration.helpers.constants import CTX_TG_BOT, CTX_TG_BOT_CFG


class TelegramContextPrompt(Extension):

    async def execute(
        self,
        system_prompt: list[str] = [],
        loop_data: LoopData = LoopData(),
        **kwargs,
    ):
        if not self.agent:
            return

        if self.agent.context.data.get(CTX_TG_BOT):
            system_prompt.append(
                self.agent.read_prompt("fw.telegram.system_context_reply.md")
            )

            # Inject per-bot agent instructions (once in system prompt)
            bot_cfg = self.agent.context.data.get(CTX_TG_BOT_CFG, {})
            instructions = bot_cfg.get("agent_instructions", "")
            if instructions:
                system_prompt.append(
                    self.agent.read_prompt(
                        "fw.telegram.user_message_instructions.md",
                        instructions=instructions,
                    )
                )
