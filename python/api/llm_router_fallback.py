"""LLM Router - Get fallback chain for a model or role"""

from python.helpers.api import ApiHandler
from python.helpers.llm_router import RoutingPriority, get_router


class LlmRouterFallback(ApiHandler):
    """Get fallback chain for a model or role

    Usage:
    - By role: {"role": "chat"} - Returns default model + fallbacks for role
    - By model: {"provider": "openai", "model_name": "gpt-4"} - Returns specific model + fallbacks
    """

    async def process(self, input: dict, request) -> dict:
        router = get_router()

        role = input.get("role")
        provider = input.get("provider")
        model_name = input.get("model_name")
        required_capabilities = input.get("required_capabilities", [])
        max_fallbacks = input.get("max_fallbacks", 3)

        # If role is provided, get default model for that role
        if role:
            priority_str = input.get("priority", "BALANCED").upper()
            priority_map = {
                "COST": RoutingPriority.COST,
                "SPEED": RoutingPriority.SPEED,
                "QUALITY": RoutingPriority.QUALITY,
                "BALANCED": RoutingPriority.BALANCED,
            }
            priority = priority_map.get(priority_str, RoutingPriority.BALANCED)
            primary = router.select_model(role=role, priority=priority, required_capabilities=required_capabilities)

            if not primary:
                return {"success": False, "error": f"No model available for role '{role}'"}

            fallbacks = router.get_fallback_chain(
                primary_model=primary, required_capabilities=required_capabilities, max_fallbacks=max_fallbacks
            )

            return {
                "success": True,
                "role": role,
                "primary": primary.to_camel_dict(),
                "fallbacks": [m.to_camel_dict() for m in fallbacks],
            }

        # Otherwise require provider and model_name
        if not provider or not model_name:
            return {"success": False, "error": "Either 'role' or both 'provider' and 'model_name' are required"}

        # Get primary model by provider/name
        models = router.db.get_models(provider=provider)
        primary = next((m for m in models if m.name == model_name), None)

        if not primary:
            return {"success": False, "error": f"Model {provider}/{model_name} not found"}

        fallbacks = router.get_fallback_chain(
            primary_model=primary, required_capabilities=required_capabilities, max_fallbacks=max_fallbacks
        )

        return {
            "success": True,
            "primary": primary.to_camel_dict(),
            "fallbacks": [m.to_camel_dict() for m in fallbacks],
        }
