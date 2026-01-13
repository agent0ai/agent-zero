from agent import AgentContext, UserMessage
from python.helpers.api import ApiHandler, Input, Output, Request


class GenerateIdeas(ApiHandler):
    """API endpoint to trigger idea generation."""

    @classmethod
    def get_methods(cls) -> list[str]:
        return ["POST"]

    async def process(self, input: Input, request: Request) -> Output:
        topic = input.get("topic", "")
        try:
            num_ideas = int(input.get("num_ideas", 5))
        except (ValueError, TypeError):
            num_ideas = 5

        if not topic:
            return {"status": "error", "message": "Topic is required"}

        ctxid = input.get("context", "")

        # Get or create context
        context = self.use_context(ctxid)
        if not context:
            return {"status": "error", "message": "No active context"}

        # Trigger idea generation via agent message
        message = UserMessage(
            message=f"Generate {num_ideas} research ideas about: {topic}"
        )
        context.communicate(message)

        return {"status": "started", "context": context.id}
