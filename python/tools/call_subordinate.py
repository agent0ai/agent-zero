from agent import Agent, UserMessage
from python.helpers.tool import Tool, Response
from initialize import initialize_agent


class Delegation(Tool):

    async def execute(self, message="", reset="", **kwargs):
        # create subordinate agent using the data object on this agent and set superior agent to his data object
        if (
            self.agent.get_data(Agent.DATA_NAME_SUBORDINATE) is None
            or str(reset).lower().strip() == "true"
        ):
            # initialize config using provided profile as settings profile name
            # initialize_agent(profile=...) will apply full settings profile if it exists,
            # otherwise it will fall back to selecting the agent profile only
            profile_name = str(kwargs.get("profile", "")).strip() if kwargs.get("profile") is not None else ""
            config = initialize_agent(profile=profile_name or None)

            # crate agent
            sub = Agent(self.agent.number + 1, config, self.agent.context)
            # register superior/subordinate
            sub.set_data(Agent.DATA_NAME_SUPERIOR, self.agent)
            self.agent.set_data(Agent.DATA_NAME_SUBORDINATE, sub)

        # add user message to subordinate agent
        subordinate: Agent = self.agent.get_data(Agent.DATA_NAME_SUBORDINATE)  # type: ignore
        attachments = kwargs.get("attachments", []) or []
        subordinate.hist_add_user_message(UserMessage(message=message, attachments=attachments))

        # run subordinate monologue
        result = await subordinate.monologue()

        # result
        return Response(message=result, break_loop=False)

    def get_log_object(self):
        return self.agent.context.log.log(
            type="tool",
            heading=f"icon://communication {self.agent.agent_name}: Calling Subordinate Agent",
            content="",
            kvps=self.args,
        )
