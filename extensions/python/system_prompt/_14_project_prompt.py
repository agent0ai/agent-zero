from typing import Any

from helpers.extension import Extension, extensible
from helpers import projects, team_access, team_projects, team_runs
from agent import Agent, LoopData


class ProjectPrompt(Extension):

    async def execute(
        self,
        system_prompt: list[str] = [],
        loop_data: LoopData = LoopData(),
        **kwargs: Any,
    ):
        if not self.agent:
            return
        prompt = await build_prompt(self.agent, loop_data=loop_data)
        if prompt:
            system_prompt.append(prompt)


@extensible
async def build_prompt(agent: Agent, loop_data: LoopData | None = None) -> str:
    result = agent.read_prompt("agent.system.projects.main.md")
    project_name = agent.context.get_data(projects.CONTEXT_DATA_KEY_PROJECT)
    if loop_data:
        loop_data.protocol_persistent.pop("agents_md_instructions", None)
        loop_data.protocol_persistent.pop("project_instructions", None)
    if project_name:
        team = team_access.is_team_chat(agent.context)
        if team:
            _, scope = team_runs.executing_scope(agent.context)
            with team_projects.project_lock(project_name, scope):
                project_vars = team_projects.prompt_variables(project_name)
        else:
            project_vars = projects.build_system_prompt_vars(project_name)
        if loop_data and not team and project_vars.get("include_agents_md", True):
            agents_md_protocol = projects.build_agents_md_protocol(project_name)
            if agents_md_protocol:
                loop_data.protocol_persistent["agents_md_instructions"] = (
                    agents_md_protocol
                )
        if loop_data and project_vars.get("project_instructions"):
            loop_data.protocol_persistent["project_instructions"] = agent.read_prompt(
                "agent.protocol.projects.instructions.md",
                **project_vars,
            )
        result += "\n\n" + agent.read_prompt(
            "agent.system.projects.active.md", **project_vars
        )
    else:
        result += "\n\n" + agent.read_prompt("agent.system.projects.inactive.md")
    return result
