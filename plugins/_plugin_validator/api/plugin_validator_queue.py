from agent import AgentContext
from helpers.api import ApiHandler, Input, Output, Request, Response
from helpers import message_queue as mq


class PluginValidatorQueue(ApiHandler):
    """Log the validation prompt into a chat. Optionally set progress to 'Queued'."""

    async def process(self, input: Input, request: Request) -> Output:
        ctxid: str = input.get("context", "")
        text: str = input.get("text", "")
        queued: bool = input.get("queued", False)

        if not ctxid or not text:
            return Response("Missing 'context' or 'text'.", 400)

        context = AgentContext.get(ctxid)
        if context is None:
            return Response(f"Context {ctxid} not found.", 404)

        mq.log_user_message(context, text, [])

        if queued:
            context.log.set_progress("icon://hourglass_empty Queued - waiting for another validation to finish", 0, True)

        return {"ok": True, "context": ctxid}
