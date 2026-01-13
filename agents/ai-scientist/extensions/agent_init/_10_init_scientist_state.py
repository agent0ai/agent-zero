from python.helpers.extension import Extension


class InitScientistState(Extension):
    """Initialize AI Scientist state containers in context.data."""

    async def execute(self, **kwargs) -> None:
        if not self.agent:
            return

        # Initialize research state containers
        self.agent.context.data.setdefault("research_ideas", {})
        self.agent.context.data.setdefault("experiments", {})
        self.agent.context.data.setdefault("papers", {})

        # Set default evaluation metrics template
        self.agent.context.data.setdefault(
            "default_eval_metrics",
            """
            Track and print validation loss at each epoch.
            Track additional metrics relevant to the task (accuracy, F1, etc.).
            Save all metrics to experiment_data.npy using the standard format.
            """,
        )

        # Log initialization
        if self.agent.context:
            self.agent.context.log.log(
                type="info",
                heading="AI Scientist Initialized",
                content="Research state containers ready.",
            )
