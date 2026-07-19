from helpers.extension import Extension
from plugins._model_config.helpers import model_config


class ProjectLlmDataProvider(Extension):
    def execute(self, data: dict = {}, **kwargs):
        result = data.get("result")
        if not isinstance(result, dict):
            result = {}
            data["result"] = result

        args = data.get("args") or ()
        project_name = args[0] if args else data.get("kwargs", {}).get("name", "")
        result["llm"] = model_config.load_project_llm_data(str(project_name or ""))
