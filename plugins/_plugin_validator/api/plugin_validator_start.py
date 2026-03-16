from agent import AgentContext, UserMessage
from helpers.api import ApiHandler, Input, Output, Request, Response


class PluginValidatorStart(ApiHandler):
    """Start the agent on a context whose validation prompt was already logged by the queue API."""

    async def process(self, input: Input, request: Request) -> Output:
        ctxid: str = input.get("context", "")
        text: str = input.get("text", "")

        if not ctxid or not text:
            return Response("Missing 'context' or 'text'.", 400)

        context = AgentContext.get(ctxid)
        if context is None:
            return Response(f"Context {ctxid} not found.", 404)

        context.communicate(UserMessage(text, []))

        return {"ok": True, "context": ctxid}
