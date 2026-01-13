from agent import AgentContext
from python.helpers.api import ApiHandler, Input, Output, Request

# AI Scientist has 4 experiment stages
TOTAL_STAGES = 4


class GetExperiments(ApiHandler):
    """API endpoint to retrieve all experiments."""

    async def process(self, input: Input, request: Request) -> Output:
        ctxid = input.get("context", "")

        # Get context if specified, otherwise use current
        if ctxid:
            try:
                context = self.use_context(ctxid, create_if_not_exists=False)
            except Exception:
                return {"experiments": []}
        else:
            context = AgentContext.current()

        if not context:
            return {"experiments": []}

        # Retrieve experiments from context data
        experiments = context.get_data("experiments") or {}

        return {
            "experiments": [
                {
                    "idea_name": name,
                    "current_stage": exp.get("current_stage", 0),
                    "status": "completed" if exp.get("current_stage", 0) > TOTAL_STAGES else "in_progress",
                }
                for name, exp in experiments.items()
            ]
        }

    @classmethod
    def get_methods(cls) -> list[str]:
        return ["GET", "POST"]
