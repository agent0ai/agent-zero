from helpers.extension import Extension
from agent import LoopData
from helpers import integration_commands
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
            system_prompt.append(_telegram_commands_prompt())

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


def _telegram_commands_prompt() -> str:
    lines = [
        "Telegram slash commands are handled by the integration before you see the message.",
        "Do not invent command help, unknown-command replies, or pretend to execute slash commands.",
        "If the user asks what commands exist, refer them to /commands.",
        "Current integration commands:",
    ]
    for name in integration_commands.command_names(include_aliases=False, integration="telegram"):
        definition = integration_commands.resolve_command(name, integration="telegram")
        if definition:
            args = f" {definition.args_hint}" if definition.args_hint else ""
            lines.append(f"- /{definition.name}{args}: {definition.description}")
    return "\n".join(lines)
