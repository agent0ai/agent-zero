from agent import AgentContext, UserMessage
from python.helpers.api import ApiHandler, Input, Output, Request


class StartExperiment(ApiHandler):
    """API endpoint to start an experiment for a research idea."""

    @classmethod
    def get_methods(cls) -> list[str]:
        return ["POST"]

    async def process(self, input: Input, request: Request) -> Output:
        idea_name = input.get("idea_name", "")
        if not idea_name:
            return {"status": "error", "message": "idea_name is required"}

        resume = input.get("resume", False)
        ctxid = input.get("context", "")

        # Get or create context
        context = self.use_context(ctxid)
        if not context:
            return {"status": "error", "message": "No active context"}

        # Verify the idea exists
        ideas = context.get_data("research_ideas") or {}
        if idea_name not in ideas:
            return {
                "status": "error",
                "message": f"Idea '{idea_name}' not found. Generate ideas first.",
            }

        # Trigger experiment via agent message
        resume_flag = " --resume" if resume else ""
        message = UserMessage(
            message=f"Run experiment for idea: {idea_name}{resume_flag}"
        )
        context.communicate(message)

        return {"status": "started", "idea_name": idea_name, "context": context.id}
