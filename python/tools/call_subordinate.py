from agent import Agent, UserMessage, AgentContext, AgentContextType
from python.helpers.tool import Tool, Response
from initialize import initialize_agent


class Delegation(Tool):

    async def execute(self, message: str = "", reset: str | bool = "", **kwargs):
        # Single profile target: use only 'settings_profile' (empty means default profile)
        settings_profile = str(kwargs.get("settings_profile", "")).strip()
        attachments = kwargs.get("attachments", []) or []
        reset_flag = str(reset).lower().strip() in ["true", "1", "yes", "y"] or bool(reset) is True

        # Retrieve or initialize subordinate mapping on the superior agent
        subordinates: dict[str, Agent] = self.agent.get_data(Agent.DATA_NAME_SUBORDINATE) or {}

        if reset_flag and settings_profile in subordinates:
            try:
                existing = subordinates.pop(settings_profile)
                if existing and getattr(existing, "context", None):
                    try:
                        existing.context.reset()
                        AgentContext.remove(existing.context.id)
                    except Exception:
                        pass
            finally:
                self.agent.set_data(Agent.DATA_NAME_SUBORDINATE, subordinates)

        if settings_profile not in subordinates:
            # Create persistent background context for subordinate
            sub_config = initialize_agent(profile=(settings_profile or None))
            sub_context = AgentContext(
                config=sub_config,
                type=AgentContextType.BACKGROUND,
            )
            new_subordinate: Agent = Agent(self.agent.number + 1, sub_config, sub_context)
            new_subordinate.set_data(Agent.DATA_NAME_SUPERIOR, self.agent)
            subordinates[settings_profile] = new_subordinate
            self.agent.set_data(Agent.DATA_NAME_SUBORDINATE, subordinates)

        # Run single subordinate synchronously and return its response directly
        sub = subordinates.get(settings_profile)
        if sub is None:
            return Response(message="Failed to initialize subordinate agent.", break_loop=False)
        sub.hist_add_user_message(UserMessage(message=message, attachments=attachments))
        try:
            resp = await sub.monologue()
        except Exception as e:
            resp = f"Error: {e}"
        return Response(message=resp, break_loop=False)

    def get_log_object(self):
        return self.agent.context.log.log(
            type="tool",
            heading=f"icon://communication {self.agent.agent_name}: Calling Subordinate Agent",
            content="",
            kvps=self.args,
        )
