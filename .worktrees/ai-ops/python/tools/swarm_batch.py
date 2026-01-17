import asyncio

from agent import Agent, UserMessage
from initialize import initialize_agent
from python.helpers.tool import Response, Tool


class SwarmBatch(Tool):
    """
    Executes multiple independent tasks in parallel by spawning a swarm of sub-agents.
    Useful for architectural discovery, multi-file analysis, or complex problem decomposition.
    """

    parallel_safe = False # Spawning sub-agents involves heavy I/O and state management

    async def execute(self, tasks: list[str] | None = None, profile: str | None = None, **kwargs):
        if tasks is None:
            tasks = []
        if not tasks:
            return Response(message="No tasks provided for the swarm.", break_loop=False)

        num_tasks = len(tasks)
        self.progress = f"Spawning {num_tasks} agents..."

        async def run_task(task_text, index):
            try:
                # Initialize a clean agent for each task
                config = initialize_agent()
                if profile:
                    config.profile = profile

                # Each sub-agent gets a unique context but shared logs
                sub = Agent(self.agent.number + 10 + index, config, self.agent.context)
                sub.set_data(Agent.DATA_NAME_SUPERIOR, self.agent)

                sub.hist_add_user_message(UserMessage(message=task_text, attachments=[]))
                result = await sub.monologue()
                return f"### [Agent {index+1}] Result for: '{task_text[:50]}...'\n\n{result}"
            except Exception as e:
                return f"### [Agent {index+1}] Failed: {e!s}"

        # Run all delegates in parallel
        self.agent.context.log.log(type="info", content=f"🚀 Swarm launched with {num_tasks} sub-agents.")

        # We use asyncio.gather to run all monologues concurrently
        results = await asyncio.gather(*(run_task(task, i) for i, task in enumerate(tasks)))

        combined_report = "# Swarm Execution Report\n\n"
        combined_report += "\n\n---\n\n".join(results)

        return Response(message=combined_report, break_loop=False)

    def get_log_object(self):
        return self.agent.context.log.log(
            type="tool",
            heading=f"icon://groups {self.agent.agent_name}: Swarm Parallel Delegate",
            content=f"Decomposing task into {len(self.args.get('tasks', []))} parallel operations.",
            kvps=self.args,
        )
