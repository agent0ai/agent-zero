from helpers.api import ApiHandler, Request, Response
from helpers.providers import get_raw_providers
from plugins._model_config.helpers import model_config
from agent import AgentContext
import models


class ModelConfigGet(ApiHandler):
    async def process(self, input: dict, request: Request) -> dict | Response:
        project_name = input.get("project_name", "")
        agent_profile = input.get("agent_profile", "")
        context_id = str(input.get("context_id") or "").strip()
        context = AgentContext.get(context_id) if context_id else None
        agent = context.agent0 if context else None

        if agent:
            config = model_config.get_effective_config(agent)
            configured_preset = model_config.get_configured_preset_name(agent=agent)
            selected_preset = model_config.get_effective_preset_name(agent)
        else:
            config = model_config.get_config(
                project_name=project_name or None,
                agent_profile=agent_profile or None,
            )
            configured_preset = model_config.get_configured_preset_name(
                project_name=project_name or None,
                agent_profile=agent_profile or None,
            )
            selected_preset = str(
                config.get(model_config.MODEL_PRESET_CONFIG_KEY)
                or model_config.DEFAULT_PRESET_NAME
            )

        # Add provider lists for UI dropdowns
        chat_providers = model_config.get_chat_providers()
        embedding_providers = model_config.get_embedding_providers()
        chat_provider_details = get_raw_providers("chat")
        embedding_provider_details = get_raw_providers("embedding")

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

        chat_model = config.get("chat_model", {}) if isinstance(config, dict) else {}
        chat_provider = str(chat_model.get("provider") or "").strip()
        chat_name = str(chat_model.get("name") or "").strip()

        return {
            "config": config,
            "chat_providers": chat_providers,
            "embedding_providers": embedding_providers,
            "chat_provider_details": chat_provider_details,
            "embedding_provider_details": embedding_provider_details,
            "api_key_status": api_key_status,
            "model_configured": model_config.is_chat_model_configured(config),
            "model_configured_label": " / ".join(
                part for part in (chat_provider, chat_name) if part
            ),
            "presets": model_config.get_presets(),
            "configured_preset": configured_preset,
            "selected_preset": selected_preset,
        }
