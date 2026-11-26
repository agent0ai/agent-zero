from agent import AgentContext
from helpers import team_access
from helpers.api import ApiHandler, Request, Response


class GetHistory(ApiHandler):
    async def process(self, input: dict, request: Request) -> dict | Response:
        ctxid = input.get("context", "")
        scope = team_access.request_scope()
        if scope is None:
            context = self.use_context(ctxid)
        else:
            context = AgentContext.get(ctxid) if isinstance(ctxid, str) and ctxid else None
            if context is None or not scope.permits_chat(context) or not team_access.has_chat_history(context):
                return Response("Chat access denied.", 403)
        agent = context.streaming_agent or context.agent0
        history = agent.history.output_text()
        size = agent.history.get_tokens()

        return {
            "history": history,
            "tokens": size
        }
