from agent import AgentContext
from helpers.api import ApiHandler, Input, Output, Request, Response

from helpers import team_access


class GetCtxWindow(ApiHandler):
    async def process(self, input: Input, request: Request) -> Output:
        ctxid = input.get("context", "")
        scope = team_access.request_scope()
        if scope is None:
            context = self.use_context(ctxid)
        else:
            context = AgentContext.get(ctxid) if isinstance(ctxid, str) and ctxid else None
            if context is None or not scope.permits_chat(context) or not team_access.has_chat_history(context):
                return Response("Chat access denied.", 403)
        agent = context.streaming_agent or context.agent0
        window = agent.get_data(agent.DATA_NAME_CTX_WINDOW)
        if not window or not isinstance(window, dict):
            return {"content": "", "tokens": 0}

        text = window["text"]
        tokens = window["tokens"]

        return {"content": text, "tokens": tokens}
