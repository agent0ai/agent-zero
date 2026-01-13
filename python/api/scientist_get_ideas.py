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
            except Exception as e:
                print(f"[DEBUG] Failed to get context {ctxid}: {e}")
                return {"ideas": []}
        else:
            context = AgentContext.current()

        if not context:
            print(f"[DEBUG] No context found for {ctxid}")
            return {"ideas": []}

        # Debug: Check what's in context.data
        print(f"[DEBUG] Context {context.id}, data keys: {list(context.data.keys())}")

        # Retrieve research ideas from context data
        ideas = context.get_data("research_ideas") or {}
        print(f"[DEBUG] Retrieved ideas type: {type(ideas)}, count: {len(ideas) if isinstance(ideas, dict) else 'N/A'}")

        return {"ideas": list(ideas.values())}

    @classmethod
    def get_methods(cls) -> list[str]:
        return ["GET", "POST"]
