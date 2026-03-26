"""Auto-send email reply when agent responds in an email session."""

import asyncio
from helpers.extension import Extension
from helpers.print_style import PrintStyle
from agent import AgentContext, LoopData, UserMessage
from plugins._email_integration.helpers.dispatcher import CTX_EMAIL_HANDLER, CTX_EMAIL_ATTACHMENTS

MAX_SEND_RETRIES: int = 2
CTX_SEND_FAILURES: str = "_email_send_failures"


class EmailAutoReply(Extension):

    async def execute(self, loop_data: LoopData = LoopData(), **kwargs):
        if not self.agent or self.agent.number != 0:
            return

        context = self.agent.context
        if not context.data.get(CTX_EMAIL_HANDLER):
            return

        response_text = _extract_last_response(context)
        if not response_text:
            return

        attachments = context.data.pop(CTX_EMAIL_ATTACHMENTS, [])
        if attachments:
            PrintStyle.info(f"Email: sending reply with {len(attachments)} attachment(s)")
        asyncio.create_task(self._send_reply(context, response_text, attachments))

    async def _send_reply(
        self, context: AgentContext, response_text: str, attachments: list[str],
    ):
        from plugins._email_integration.helpers.handler import send_email_reply
        error = await send_email_reply(context, response_text, attachments)
        if not error:
            context.data[CTX_SEND_FAILURES] = 0
            return
        failures = context.data.get(CTX_SEND_FAILURES, 0) + 1
        context.data[CTX_SEND_FAILURES] = failures
        if failures <= MAX_SEND_RETRIES:
            _notify_agent_of_failure(context, error, failures)
        else:
            PrintStyle.error(
                f"Email send failed {failures} times, giving up: {error}"
            )
            context.log.log(
                type="error",
                heading="Email send failed (max retries reached)",
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
        "fw.email.send_failed.md", error=error, attempt=str(attempt),
        max_retries=str(MAX_SEND_RETRIES),
    )
    context.log.log(type="error", heading="Email send failed", content=error)
    context.communicate(UserMessage(message="", system_message=[msg]))
