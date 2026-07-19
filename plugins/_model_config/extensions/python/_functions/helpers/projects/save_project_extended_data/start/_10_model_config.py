from helpers.extension import Extension
from plugins._model_config.helpers import model_config


class ProjectLlmSettingsSaver(Extension):
    def execute(self, data: dict = {}, **kwargs):
        args = data.get("args") or ()
        call_kwargs = data.get("kwargs") or {}
        project_name = args[0] if args else call_kwargs.get("name", "")
        project_data = args[1] if len(args) > 1 else call_kwargs.get("project_data")
        llm_data = project_data.get("llm") if isinstance(project_data, dict) else None
        model_config.save_project_llm_settings(str(project_name or ""), llm_data)
