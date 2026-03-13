"""
Model Selector Quick Switch API

Provides a fast endpoint for switching the active chat model from the UI.
Updates both the general settings and the LLM Router defaults.
"""

from python.helpers.api import ApiHandler


class ModelSelectorQuickSwitch(ApiHandler):
    """API handler for quickly switching the active model from chat UI."""

    async def process(self, input: dict, request) -> dict:
        provider = input.get("provider")
        model_name = input.get("modelName") or input.get("model_name")
        role = input.get("role", "chat")  # Default to chat model

        if not provider or not model_name:
            return {"success": False, "error": "Both 'provider' and 'modelName' are required"}

        try:
            # Update settings for the appropriate model role
            from python.helpers import settings

            current_settings = settings.get_settings()

            # Map role to settings keys
            role_key_map = {
                "chat": ("chat_model_provider", "chat_model_name"),
                "utility": ("util_model_provider", "util_model_name"),
                "browser": ("browser_model_provider", "browser_model_name"),
                "embedding": ("embed_model_provider", "embed_model_name"),
            }

            if role in role_key_map:
                provider_key, model_key = role_key_map[role]
                current_settings[provider_key] = provider
                current_settings[model_key] = model_name
                settings.set_settings(current_settings)

            # Also update LLM Router default if router is available
            try:
                from python.helpers.llm_router import get_router

                router = get_router()
                router.set_default_model(role, provider, model_name)
            except Exception as e:
                # Router update is optional, don't fail the whole request
                import logging

                logging.warning(f"[LLMRouter] Quick switch failed to update router: {e}")

            return {
                "success": True,
                "model": {"provider": provider, "name": model_name, "role": role},
                "message": f"Switched {role} model to {provider}/{model_name}",
            }

        except Exception as e:
            return {"success": False, "error": str(e)}
