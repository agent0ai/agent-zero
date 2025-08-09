from agent import Agent, UserMessage
from python.helpers.tool import Tool, Response


class Delegation(Tool):

    async def execute(self, task: str, objectives: list[str] = None, parent_task: str = None, context: str = None, scopes: list[str] = None, non_goals: list[str] = None, success_criteria: list[str] = None, errors_to_avoid: list[str] = None, reset: str = "", **kwargs):
        # create subordinate agent using the data object on this agent and set superior agent to his data object
        if (
            self.agent.get_data(Agent.DATA_NAME_SUBORDINATE) is None
            or str(reset).lower().strip() == "true"
        ):
            # crate agent
            sub = Agent(self.agent.number + 1, self.agent.config, self.agent.context)
            # register superior/subordinate
            sub.set_data(Agent.DATA_NAME_SUPERIOR, self.agent)
            self.agent.set_data(Agent.DATA_NAME_SUBORDINATE, sub)
            # set default prompt profile to new agents
            sub.config.prompts_subdir = "default"

        subordinate: Agent = self.agent.get_data(Agent.DATA_NAME_SUBORDINATE)

        # store task details in subordinate agent's data
        task_details = {
            "task": task,
            "objectives": objectives,
            "parent_task": parent_task,
            "context": context,
            "scopes": scopes,
            "non_goals": non_goals,
            "success_criteria": success_criteria,
            "errors_to_avoid": errors_to_avoid,
        }
        subordinate.set_data("task_details", task_details)

        # add user message to subordinate agent
        subordinate.hist_add_user_message(UserMessage(message=task, attachments=[]))

        # set subordinate prompt profile if provided, if not, keep original
        prompt_profile = kwargs.get("prompt_profile")
        if prompt_profile:
            subordinate.config.prompts_subdir = prompt_profile

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