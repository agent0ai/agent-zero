"""LLM Router - Get router dashboard data (models, usage, defaults)"""

from python.helpers.api import ApiHandler
from python.helpers.llm_router import get_router


class LlmRouterDashboard(ApiHandler):
    """Get router dashboard data (models, usage, defaults)"""

    async def process(self, input: dict, request) -> dict:
        router = get_router()

        # Get models
        models = router.db.get_models(available_only=True)

        # Group by provider
        by_provider = {}
        for model in models:
            if model.provider not in by_provider:
                by_provider[model.provider] = []
            by_provider[model.provider].append(
                {
                    "name": model.name,
                    "displayName": model.display_name,
                    "sizeGb": model.size_gb,
                    "contextLength": model.context_length,
                    "capabilities": model.capabilities,
                    "isLocal": model.is_local,
                    "costPer1kInput": model.cost_per_1k_input,
                    "costPer1kOutput": model.cost_per_1k_output,
                }
            )

        # Get defaults
        defaults = {}
        for role in ["chat", "utility", "browser", "embedding", "fallback"]:
            result = router.get_default_model(role)
            if result:
                defaults[role] = {"provider": result[0], "modelName": result[1]}

        # Get usage stats
        usage_24h = router.get_usage_stats(hours=24)
        usage_1h = router.get_usage_stats(hours=1)

        return {
            "success": True,
            "models": {
                "byProvider": by_provider,
                "totalCount": len(models),
                "localCount": len([m for m in models if m.is_local]),
                "cloudCount": len([m for m in models if not m.is_local]),
            },
            "defaults": defaults,
            "usage": {
                "lastHour": {"calls": usage_1h["totalCalls"], "costUsd": round(usage_1h["totalCost"], 4)},
                "last24h": {
                    "calls": usage_24h["totalCalls"],
                    "costUsd": round(usage_24h["totalCost"], 4),
                    "byModel": usage_24h["byModel"],
                },
            },
        }
