from agent import AgentContext
from python.helpers.api import ApiHandler, Input, Output, Request


class GetIdeas(ApiHandler):
    """API endpoint to retrieve generated research ideas."""

    async def process(self, input: Input, request: Request) -> Output:
        ctxid = input.get("context", "")

        # Get context if specified, otherwise use current
        if ctxid:
            try:
                context = self.use_context(ctxid, create_if_not_exists=False)
            except Exception:
                return {"ideas": []}
        else:
            context = AgentContext.current()

        if not context:
            return {"ideas": []}

        # Retrieve research ideas from context data
        ideas = context.get_data("research_ideas") or {}

        return {"ideas": list(ideas.values())}

    @classmethod
    def get_methods(cls) -> list[str]:
        return ["GET", "POST"]
