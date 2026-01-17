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
            by_provider[model.provider].append({
                "name": model.name,
                "display_name": model.display_name,
                "size_gb": model.size_gb,
                "context_length": model.context_length,
                "capabilities": model.capabilities,
                "is_local": model.is_local,
                "cost_per_1k_input": model.cost_per_1k_input,
                "cost_per_1k_output": model.cost_per_1k_output
            })

        # Get defaults
        defaults = {}
        for role in ["chat", "utility", "browser", "embedding", "fallback"]:
            result = router.get_default_model(role)
            if result:
                defaults[role] = {"provider": result[0], "model_name": result[1]}

        # Get usage stats
        usage_24h = router.get_usage_stats(hours=24)
        usage_1h = router.get_usage_stats(hours=1)

        return {
            "success": True,
            "models": {
                "by_provider": by_provider,
                "total_count": len(models),
                "local_count": len([m for m in models if m.is_local]),
                "cloud_count": len([m for m in models if not m.is_local])
            },
            "defaults": defaults,
            "usage": {
                "last_hour": {
                    "calls": usage_1h["total_calls"],
                    "cost_usd": round(usage_1h["total_cost"], 4)
                },
                "last_24h": {
                    "calls": usage_24h["total_calls"],
                    "cost_usd": round(usage_24h["total_cost"], 4),
                    "by_model": usage_24h["by_model"]
                }
            }
        }
