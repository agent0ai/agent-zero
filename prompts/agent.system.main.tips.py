from typing import Any

from python.helpers import files, projects, runtime, settings
from python.helpers.files import VariablesPlugin


class WorkdirPath(VariablesPlugin):
    def get_variables(
        self, file: str, backup_dirs: list[str] | None = None, **kwargs
    ) -> dict[str, Any]:

        # agent = kwargs.get("_agent")
        # if agent and getattr(agent, "context", None):
        #     project_name = projects.get_context_project_name(agent.context)
        #     if project_name:
        #         folder = projects.get_project_folder(project_name)
        #         if runtime.is_development():
        #             folder = files.normalize_a0_path(folder)
        #         return {"workdir_path": folder}

        set = settings.get_settings()
        return {"workdir_path": set["workdir_path"]}
