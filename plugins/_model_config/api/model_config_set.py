from copy import deepcopy

from helpers.api import ApiHandler, Request, Response
from helpers import plugins, defer, dotenv
from helpers.extension import call_extensions_async

API_KEY_PLACEHOLDER = "************"


class ModelConfigSet(ApiHandler):
    async def process(self, input: dict, request: Request) -> dict | Response:
        project_name = input.get("project_name", "")
        agent_profile = input.get("agent_profile", "")
        config = input.get("config")

        if not config or not isinstance(config, dict):
            return Response(status=400, response="Missing or invalid config")

        config_to_save = deepcopy(config)
        for section_name in ("chat_model", "utility_model", "embedding_model"):
            section = config_to_save.get(section_name, {})
            if not isinstance(section, dict):
                continue
            provider = str(section.get("provider", "")).strip()
            api_key = section.get("api_key", "")
            if (
                provider
                and isinstance(api_key, str)
                and api_key.strip()
                and api_key != API_KEY_PLACEHOLDER
            ):
                dotenv.save_dotenv_value(f"API_KEY_{provider.upper()}", api_key)
            section.pop("api_key", None)

        # Read previous config BEFORE saving so we can detect changes
        prev_config = plugins.get_plugin_config(
            "_model_config",
            project_name=project_name or None,
            agent_profile=agent_profile or None,
        ) or {}

        plugins.save_plugin_config(
            "_model_config",
            project_name=project_name,
            agent_profile=agent_profile,
            settings=config_to_save,
        )

        # Check if embedding model changed and notify
        prev_embed = prev_config.get("embedding_model", {})
        new_embed = config_to_save.get("embedding_model", {})
        if (
            prev_embed.get("provider") != new_embed.get("provider")
            or prev_embed.get("name") != new_embed.get("name")
            or prev_embed.get("kwargs") != new_embed.get("kwargs")
        ):
            defer.DeferredTask().start_task(
                call_extensions_async, "embedding_model_changed"
            )

        return {"ok": True}
