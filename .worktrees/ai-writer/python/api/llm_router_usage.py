"""LLM Router - Get usage statistics"""

from python.helpers.api import ApiHandler
from python.helpers.llm_router import get_router


class LlmRouterUsage(ApiHandler):
    """Get usage statistics"""

    async def process(self, input: dict, request) -> dict:
        router = get_router()
        hours = input.get("hours", 24)

        stats = router.get_usage_stats(hours=hours)

        return {
            "success": True,
            "stats": stats
        }
