import asyncio
from agent import Agent, AgentContext
from python.helpers.tool import Tool, Response


class SubordinateFinish(Tool):

    async def execute(self, **kwargs) -> Response:
        # Identify superior and profile key
        superior: Agent | None = self.agent.get_data(Agent.DATA_NAME_SUPERIOR)
        profile_key: str = getattr(self.agent.config, "profile", "")

        # Remove from superior's subordinate mapping if present
        if isinstance(superior, Agent):
            subordinates: dict[str, Agent] = superior.get_data(Agent.DATA_NAME_SUBORDINATE) or {}
            # Remove only if the exact agent is stored for the profile
            if profile_key in subordinates and subordinates.get(profile_key) is self.agent:
                subordinates.pop(profile_key, None)
                superior.set_data(Agent.DATA_NAME_SUBORDINATE, subordinates)

        # Schedule context cleanup after short delay to let logging complete
        context_id = getattr(self.agent.context, "id", None)

        async def deferred_cleanup(cid: str | None):
            await asyncio.sleep(0.2)
            try:
                if cid:
                    # Reset and remove context by id
                    ctx = AgentContext.get(cid)
                    if ctx:
                        ctx.reset()
                        AgentContext.remove(cid)
            except Exception:
                pass

        asyncio.create_task(deferred_cleanup(context_id))

        # End subordinate monologue
        return Response(message="Subordinate finished. Cleaning up context and removing from registry.", break_loop=True)

    def get_log_object(self):
        return self.agent.context.log.log(
            type="tool",
            heading=f"icon://construction {self.agent.agent_name}: Subordinate Finish",
            content="",
            kvps=self.args,
        )
