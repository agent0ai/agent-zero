from helpers.api import ApiHandler, Request, Response
from helpers import plugins
from plugins._model_config.helpers import model_config
import models


class ModelConfigGet(ApiHandler):
    async def process(self, input: dict, request: Request) -> dict | Response:
        project_name = input.get("project_name", "")
        agent_profile = input.get("agent_profile", "")

        config = model_config.get_config(
            project_name=project_name or None,
            agent_profile=agent_profile or None,
        )

        # Provide default if no config found
        if not config:
            config = plugins.get_default_plugin_config("_model_config") or {}

        # Add provider lists for UI dropdowns
        chat_providers = model_config.get_chat_providers()
        embedding_providers = model_config.get_embedding_providers()

        # Mask API keys - show status only
        api_key_status = {}
        all_providers = chat_providers + embedding_providers
        seen = set()
        for p in all_providers:
            pid = p.get("value", "")
            if pid and pid not in seen:
                seen.add(pid)
                key = models.get_api_key(pid)
                api_key_status[pid] = bool(key and key.strip() and key != "None")

        return {
            "config": config,
            "chat_providers": chat_providers,
            "embedding_providers": embedding_providers,
            "api_key_status": api_key_status,
        }
