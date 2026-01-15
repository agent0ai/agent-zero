"""LLM Router - Get fallback chain for a model"""

from python.helpers.api import ApiHandler
from python.helpers.llm_router import get_router


class LlmRouterFallback(ApiHandler):
    """Get fallback chain for a model"""

    async def process(self, input: dict, request) -> dict:
        router = get_router()

        provider = input.get("provider")
        model_name = input.get("model_name")
        required_capabilities = input.get("required_capabilities", [])
        max_fallbacks = input.get("max_fallbacks", 3)

        if not provider or not model_name:
            return {
                "success": False,
                "error": "provider and model_name are required"
            }

        # Get primary model
        models = router.db.get_models(provider=provider)
        primary = next((m for m in models if m.name == model_name), None)

        if not primary:
            return {
                "success": False,
                "error": f"Model {provider}/{model_name} not found"
            }

        fallbacks = router.get_fallback_chain(
            primary_model=primary,
            required_capabilities=required_capabilities,
            max_fallbacks=max_fallbacks
        )

        return {
            "success": True,
            "primary": primary.to_dict(),
            "fallbacks": [m.to_dict() for m in fallbacks]
        }
