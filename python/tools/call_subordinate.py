import asyncio
from agent import Agent, UserMessage
from python.helpers.tool import Tool, Response
from initialize import initialize_agent
from python.helpers import settings
from python.helpers.errors import RepairableException
from python.extensions.hist_add_tool_result import _90_save_tool_call_file as save_tool_call_file


class Delegation(Tool):
    DATA_NAME_SUB_CALLS = "_subordinate_calls_in_turn"

    async def execute(self, message="", reset="", **kwargs):
        set = settings.get_settings()
        current_depth = self._get_current_depth()
        next_depth = current_depth + 1

        max_depth = int(set.get("subordinate_max_depth", 2))
        if max_depth > 0 and next_depth > max_depth:
            warning = self.agent.read_prompt(
                "fw.msg_subordinate_guardrail.md",
                reason="maximum subordinate depth reached",
                detail=f"requested_depth={next_depth}, limit={max_depth}",
            )
            raise RepairableException(warning)

        calls = int(self.agent.loop_data.params_persistent.get(self.DATA_NAME_SUB_CALLS, 0))
        max_calls = int(set.get("subordinate_max_calls_per_turn", 4))
        if max_calls > 0 and calls >= max_calls:
            warning = self.agent.read_prompt(
                "fw.msg_subordinate_guardrail.md",
                reason="maximum subordinate calls reached in this turn",
                detail=f"calls={calls}, limit={max_calls}",
            )
            raise RepairableException(warning)
        self.agent.loop_data.params_persistent[self.DATA_NAME_SUB_CALLS] = calls + 1

        # create subordinate agent using the data object on this agent and set superior agent to his data object
        if (
            self.agent.get_data(Agent.DATA_NAME_SUBORDINATE) is None
            or str(reset).lower().strip() == "true"
        ):
            # initialize default config
            config = initialize_agent()

            # set subordinate prompt profile if provided, if not, keep original
            agent_profile = kwargs.get("profile", kwargs.get("agent_profile", ""))
            if agent_profile:
                config.profile = agent_profile

            # crate agent
            sub = Agent(self.agent.number + 1, config, self.agent.context)
            # register superior/subordinate
            sub.set_data(Agent.DATA_NAME_SUPERIOR, self.agent)
            self.agent.set_data(Agent.DATA_NAME_SUBORDINATE, sub)

        # add user message to subordinate agent
        subordinate: Agent = self.agent.get_data(Agent.DATA_NAME_SUBORDINATE)  # type: ignore
        subordinate.hist_add_user_message(UserMessage(message=message, attachments=[]))

        # run subordinate monologue
        max_runtime_seconds = int(set.get("subordinate_max_runtime_seconds", 300))
        runtime_budget_seconds = int(set.get("runtime_subordinate_budget_seconds", 0))
        if max_runtime_seconds > 0 and runtime_budget_seconds > 0:
            max_runtime_seconds = min(max_runtime_seconds, runtime_budget_seconds)
        elif runtime_budget_seconds > 0:
            max_runtime_seconds = runtime_budget_seconds
        if max_runtime_seconds > 0:
            try:
                result = await asyncio.wait_for(
                    subordinate.monologue(), timeout=max_runtime_seconds
                )
            except asyncio.TimeoutError:
                warning = self.agent.read_prompt(
                    "fw.msg_subordinate_guardrail.md",
                    reason="subordinate runtime exceeded",
                    detail=f"timeout_seconds={max_runtime_seconds}",
                )
                raise RepairableException(warning)
        else:
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

    def _get_current_depth(self) -> int:
        depth = 0
        cursor: Agent | None = self.agent
        while cursor:
            superior = cursor.get_data(Agent.DATA_NAME_SUPERIOR)
            if not superior:
                return depth
            depth += 1
            cursor = superior
        return depth
