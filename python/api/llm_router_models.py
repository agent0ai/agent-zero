"""LLM Router - Get registered models with optional filtering"""

from python.helpers.api import ApiHandler
from python.helpers.llm_router import get_router


class LlmRouterModels(ApiHandler):
    """Get registered models with optional filtering"""

    async def process(self, input: dict, request) -> dict:
        router = get_router()

        provider = input.get("provider")
        available_only = input.get("available_only", True)

        models = router.db.get_models(provider=provider, available_only=available_only)

        return {"success": True, "models": [m.to_camel_dict() for m in models], "count": len(models)}
