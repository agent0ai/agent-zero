"""LLM Router - Select the best model based on criteria"""

from python.helpers.api import ApiHandler
from python.helpers.llm_router import RoutingPriority, get_router


class LlmRouterSelect(ApiHandler):
    """Select the best model based on criteria"""

    async def process(self, input: dict, request) -> dict:
        router = get_router()

        role = input.get("role", "chat")
        context_type = input.get("contextType") or input.get("context_type", "user")
        required_capabilities = input.get("requiredCapabilities") or input.get("required_capabilities", [])
        priority_str = input.get("priority", "balanced")
        min_context_length = input.get("minContextLength") or input.get("min_context_length", 0)
        max_cost_per_1k = input.get("maxCostPer1k") or input.get("max_cost_per_1k", 0)
        preferred_provider = input.get("preferredProvider") or input.get("preferred_provider")
        excluded_providers = input.get("excludedProviders") or input.get("excluded_providers", [])

        # Convert priority string to enum
        priority_map = {
            "cost": RoutingPriority.COST,
            "speed": RoutingPriority.SPEED,
            "quality": RoutingPriority.QUALITY,
            "balanced": RoutingPriority.BALANCED,
        }
        priority = priority_map.get(priority_str, RoutingPriority.BALANCED)

        model = router.select_model(
            role=role,
            context_type=context_type,
            required_capabilities=required_capabilities,
            priority=priority,
            min_context_length=min_context_length,
            max_cost_per_1k=max_cost_per_1k,
            preferred_provider=preferred_provider,
            excluded_providers=excluded_providers,
        )

        if model:
            return {
                "success": True,
                "model": model.to_camel_dict(),
                "selectionCriteria": {"role": role, "contextType": context_type, "priority": priority_str},
            }
        else:
            return {
                "success": False,
                "error": "No matching model found",
                "selectionCriteria": {
                    "role": role,
                    "contextType": context_type,
                    "priority": priority_str,
                    "requiredCapabilities": required_capabilities,
                },
            }
