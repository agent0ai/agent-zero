from helpers.api import ApiHandler, Request, Response


class Stop(ApiHandler):
    async def process(self, input: dict, request: Request) -> dict | Response:
        ctxid = input.get("context", "")
        if not ctxid:
            raise Exception("No context id provided")
        context = self.use_context(ctxid)
        context.stop()
        return {
            "message": "Agent stopped.",
            "context": context.id,
        }
