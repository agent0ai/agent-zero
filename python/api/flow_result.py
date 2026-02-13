from agent import AgentContext
from python.helpers.api import ApiHandler, Input, Output, Request


class FlowResult(ApiHandler):
    async def process(self, input: Input, request: Request) -> Output:
        context_id = input.get("context_id", "")
        content = input.get("content", "")
        heading = input.get("heading", "Flow Result")

        if not context_id:
            return {"ok": False, "error": "Missing required field: context_id"}
        if not content:
            return {"ok": False, "error": "No content to post"}

        context = AgentContext.get(context_id)
        if not context:
            return {"ok": False, "error": f"Context not found: {context_id}"}

        context.log.log(
            type="response",
            heading=heading,
            content=content,
        )

        return {"ok": True}
