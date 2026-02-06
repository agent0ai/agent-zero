import json
from typing import Any, TYPE_CHECKING
from python.helpers.files import VariablesPlugin
from python.helpers import files, projects, subagents
from python.helpers.print_style import PrintStyle

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

        if agents:
            profiles = {}
            for name, subagent in agents.items():
                profiles[name] = {
                    "title": subagent.title,
                    "description": subagent.description,
                    "context": subagent.context,
                }
            return {"agent_profiles": profiles}
        else:
            return {"agent_profiles": None}
        
