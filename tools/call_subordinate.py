from agent import Agent, UserMessage
from helpers import projects, subagents
from helpers.errors import RepairableException
from helpers.tool import Tool, Response
from initialize import initialize_agent
from extensions.python.hist_add_tool_result import _90_save_tool_call_file as save_tool_call_file


def _subordinate_profile_labels(agent: Agent) -> dict[str, str]:
    project = projects.get_context_project_name(agent.context) if agent.context else None
    return {
        name: subagent.title or name
        for name, subagent in subagents.get_available_agents_dict(project).items()
    }


def _validate_subordinate_profile(agent: Agent, profile: str) -> str:
    agent_profile = str(profile or "").strip()
    if not agent_profile:
        return ""

    labels = _subordinate_profile_labels(agent)
    if agent_profile in labels:
        return agent_profile

    available = ", ".join(
        f"{key} ({label})" if label and label != key else key
        for key, label in sorted(labels.items())
    )
    if not available:
        available = "none"
    raise RepairableException(
        f"Agent profile '{agent_profile}' not found. Use one of the available profiles: {available}."
    )


class Delegation(Tool):

    async def execute(self, message="", reset="", **kwargs):
        requested_profile = _validate_subordinate_profile(
            self.agent, kwargs.get("profile", kwargs.get("agent_profile", ""))
        )
        existing_subordinate = self.agent.get_data(Agent.DATA_NAME_SUBORDINATE)
        reset_requested = str(reset).lower().strip() == "true"

        if existing_subordinate and requested_profile and not reset_requested:
            current_profile = str(
                getattr(getattr(existing_subordinate, "config", None), "profile", "")
                or ""
            )
            if current_profile != requested_profile:
                raise RepairableException(
                    f"Subordinate already uses profile '{current_profile or 'default'}'. "
                    f"Set reset=true to switch to '{requested_profile}'."
                )

        # create subordinate agent using the data object on this agent and set superior agent to his data object
        if (
            existing_subordinate is None
            or reset_requested
        ):
            # set subordinate prompt profile if provided, otherwise use the default profile
            override_settings = (
                {"agent_profile": requested_profile} if requested_profile else None
            )
            config = initialize_agent(override_settings=override_settings)

            # create agent
            sub = Agent(self.agent.number + 1, config, self.agent.context)
            # register superior/subordinate
            sub.set_data(Agent.DATA_NAME_SUPERIOR, self.agent)
            self.agent.set_data(Agent.DATA_NAME_SUBORDINATE, sub)

        # add user message to subordinate agent
        subordinate: Agent = self.agent.get_data(Agent.DATA_NAME_SUBORDINATE)  # type: ignore
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
