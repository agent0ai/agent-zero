from typing import Any, TYPE_CHECKING
from helpers.files import VariablesPlugin
from helpers import projects, subagents

if TYPE_CHECKING:
    from agent import Agent


class CallSubordinate(VariablesPlugin):
    def get_variables(
        self, file: str, backup_dirs: list[str] | None = None, **kwargs
    ) -> dict[str, Any]:

        # current agent instance
        agent: Agent | None = kwargs.get("_agent", None)
        # current project
        project = projects.get_context_project_name(agent.context) if agent else None
        # available agents in project (or global)
        agents = subagents.get_available_agents_dict(project)

        profiles = [
            " ".join(
                f"- {name} ({profile.title}): {profile.context.strip() or profile.description}".split()
            )
            for name, profile in agents.items()
        ]
        return {"agent_profiles": "\n".join(profiles) or None}
