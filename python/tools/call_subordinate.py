from agent import Agent, UserMessage
from python.helpers.tool import Tool, Response
from initialize import initialize_agent
from python.extensions.hist_add_tool_result import _90_save_tool_call_file as save_tool_call_file


class Delegation(Tool):

    async def execute(self, message="", reset="", **kwargs):
        slot = (kwargs.get("slot") or "").strip()
        subordinate_data_key = (
            Agent.DATA_NAME_SUBORDINATE if not slot else f"{Agent.DATA_NAME_SUBORDINATE}:{slot}"
        )

        # set subordinate prompt profile if provided, if not, keep original
        requested_profile = kwargs.get("profile", kwargs.get("agent_profile", ""))

        # create subordinate agent using the data object on this agent and set superior agent to his data object
        if (
            self.agent.get_data(subordinate_data_key) is None
            or str(reset).lower().strip() == "true"
            or (
                requested_profile
                and (
                    (
                        self.agent.get_data(subordinate_data_key) is not None
                        and getattr(self.agent.get_data(subordinate_data_key).config, "profile", "")  # type: ignore[union-attr]
                        != requested_profile
                    )
                )
            )
        ):
            # initialize default config
            config = initialize_agent()

            if requested_profile:
                config.profile = requested_profile

            # crate agent
            sub = Agent(self.agent.number + 1, config, self.agent.context)
            # register superior/subordinate
            sub.set_data(Agent.DATA_NAME_SUPERIOR, self.agent)
            self.agent.set_data(subordinate_data_key, sub)

        # add user message to subordinate agent
        subordinate: Agent = self.agent.get_data(subordinate_data_key)  # type: ignore
        subordinate.hist_add_user_message(UserMessage(message=message, attachments=[]))

        # run subordinate monologue
        result = await subordinate.monologue()

        # seal the subordinate's current topic so messages move to `topics` for compression
        subordinate.history.new_topic()

        # hint to use includes for long responses
        additional = None
        if len(result) >= save_tool_call_file.LEN_MIN:
            hint = self.agent.read_prompt("fw.hint.call_sub.md")
            if hint:
                additional = {"hint": hint}

        # result
        return Response(message=result, break_loop=False, additional=additional)

    def get_log_object(self):
        return self.agent.context.log.log(
            type="subagent",
            heading=f"icon://communication {self.agent.agent_name}: Calling Subordinate Agent",
            content="",
            kvps=self.args,
        )
