"""LLM Router - Get default models for all roles"""

from python.helpers.api import ApiHandler
from python.helpers.llm_router import get_router


class LlmRouterGetDefaults(ApiHandler):
    """Get default models for all roles"""

    async def process(self, input: dict, request) -> dict:
        router = get_router()

        roles = ["chat", "utility", "browser", "embedding", "fallback"]
        defaults = {}

        for role in roles:
            result = router.get_default_model(role)
            if result:
                defaults[role] = {"provider": result[0], "modelName": result[1]}
            else:
                defaults[role] = None

        return {"success": True, "defaults": defaults}
