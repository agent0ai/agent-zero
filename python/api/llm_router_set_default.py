"""LLM Router - Set default model for a role"""

from python.helpers.api import ApiHandler
from python.helpers.llm_router import get_router


class LlmRouterSetDefault(ApiHandler):
    """Set default model for a role"""

    async def process(self, input: dict, request) -> dict:
        router = get_router()

        role = input.get("role")
        provider = input.get("provider")
        model_name = input.get("model_name") or input.get("modelName")

        if not all([role, provider, model_name]):
            return {"success": False, "error": "role, provider, and model_name are required"}

        # Validate model exists
        models = router.db.get_models(provider=provider)
        model = next((m for m in models if m.name == model_name), None)

        if not model:
            return {"success": False, "error": f"Model {provider}/{model_name} not found in registry"}

        router.set_default_model(role, provider, model_name)

        return {
            "success": True,
            "message": f"Default {role} model set to {provider}/{model_name}",
            "role": role,
            "provider": provider,
            "modelName": model_name,
        }
