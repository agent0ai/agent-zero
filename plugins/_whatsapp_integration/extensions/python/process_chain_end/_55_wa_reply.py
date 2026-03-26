"""Auto-send WhatsApp reply when agent responds in a WhatsApp session."""

import asyncio
from helpers.extension import Extension
from helpers.print_style import PrintStyle
from agent import AgentContext, LoopData, UserMessage
from plugins._whatsapp_integration.helpers.handler import CTX_WA_CHAT_ID, CTX_WA_ATTACHMENTS, CTX_WA_REPLY_TO

MAX_SEND_RETRIES: int = 2
CTX_SEND_FAILURES: str = "_wa_send_failures"


class WhatsAppAutoReply(Extension):

    async def execute(self, loop_data: LoopData = LoopData(), **kwargs):
        if not self.agent or self.agent.number != 0:
            return

        context = self.agent.context
        if not context.data.get(CTX_WA_CHAT_ID):
            return

        response_text = _extract_last_response(context)
        if not response_text:
            return

        attachments = context.data.pop(CTX_WA_ATTACHMENTS, [])
        reply_to = context.data.pop(CTX_WA_REPLY_TO, "")
        if attachments:
            PrintStyle.info(f"WhatsApp: sending reply with {len(attachments)} attachment(s)")
        asyncio.create_task(self._send_reply(context, response_text, attachments, reply_to))

    async def _send_reply(
        self, context: AgentContext, response_text: str, attachments: list[str],
        reply_to: str = "",
    ):
        from plugins._whatsapp_integration.helpers.handler import send_wa_reply
        error = await send_wa_reply(context, response_text, attachments, reply_to=reply_to)
        if not error:
            context.data[CTX_SEND_FAILURES] = 0
            return
        failures = context.data.get(CTX_SEND_FAILURES, 0) + 1
        context.data[CTX_SEND_FAILURES] = failures
        if failures <= MAX_SEND_RETRIES:
            _notify_agent_of_failure(context, error, failures)
        else:
            PrintStyle.error(
                f"WhatsApp send failed {failures} times, giving up: {error}"
            )
            context.log.log(
                type="error",
                heading="WhatsApp send failed (max retries reached)",
                content=error,
            )


# ------------------------------------------------------------------
# Helpers
# ------------------------------------------------------------------

def _extract_last_response(context: AgentContext) -> str:
    with context.log._lock:
        logs = list(context.log.logs)
    if not logs:
        return ""
    for item in reversed(logs):
        if item.type == "response":
            return item.content or ""
    return ""


def _notify_agent_of_failure(
    context: AgentContext, error: str, attempt: int,
):
    msg = context.agent0.read_prompt(
        "fw.wa.send_failed.md", error=error, attempt=str(attempt),
        max_retries=str(MAX_SEND_RETRIES),
    )
    context.log.log(type="error", heading="WhatsApp send failed", content=error)
    context.communicate(UserMessage(message="", system_message=[msg]))
