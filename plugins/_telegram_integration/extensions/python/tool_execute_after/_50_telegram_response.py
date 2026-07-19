from helpers.extension import Extension
from helpers.tool import Response
from plugins._telegram_integration.helpers.constants import (
    CTX_TG_BOT,
    CTX_TG_ATTACHMENTS,
    CTX_TG_KEYBOARD,
)
from plugins._telegram_integration.helpers.dependencies import ensure_dependencies


class TelegramResponseIntercept(Extension):

    async def execute(
        self, tool_name: str = "", response: Response | None = None, **kwargs,
    ):
        if tool_name != "response":
            return
        if not self.agent:
            return
        context = self.agent.context
        if not context.data.get(CTX_TG_BOT):
            return

        tool = self.agent.loop_data.current_tool
        if not tool:
            return

        # Capture attachments for later (process_chain_end) or inline send
        attachments = tool.args.get("attachments", [])
        if attachments:
            context.data[CTX_TG_ATTACHMENTS] = attachments

        # Capture inline keyboard if provided
        keyboard = tool.args.get("keyboard", None)
        if keyboard:
            context.data[CTX_TG_KEYBOARD] = keyboard

        # Check break_loop arg from agent
        agent_break = tool.args.get("break_loop", True)
        if agent_break is False and response:
            await self._send_inline(context, tool, response)

    async def _send_inline(self, context, tool, response: Response):
        ensure_dependencies()
        from plugins._telegram_integration.helpers.handler import send_telegram_reply

        agent = self.agent
        assert agent is not None

        text = tool.args.get("text", tool.args.get("message", ""))
        attachments = context.data.pop(CTX_TG_ATTACHMENTS, [])
        keyboard = context.data.pop(CTX_TG_KEYBOARD, None)

        error = await send_telegram_reply(context, text, attachments or None, keyboard)

        if error:
            result = agent.read_prompt("fw.telegram.update_error.md", error=error)
        else:
            result = agent.read_prompt("fw.telegram.update_ok.md")

        # Override response: don't break loop, add result to history
        response.break_loop = False
        response.message = result
        agent.hist_add_tool_result("response", result)
