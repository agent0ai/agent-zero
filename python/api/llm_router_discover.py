"""LLM Router - Discover available models from all configured providers"""

from python.helpers.api import ApiHandler
from python.helpers.llm_router import get_router


class LlmRouterDiscover(ApiHandler):
    """Discover available models from all configured providers"""

    async def process(self, input: dict, request) -> dict:
        router = get_router()
        force = input.get("force", False)

        models = await router.discover_models(force=force)

        return {
            "success": True,
            "models": [m.to_camel_dict() for m in models],
            "count": len(models),
            "providers": list({m.provider for m in models}),
        }
