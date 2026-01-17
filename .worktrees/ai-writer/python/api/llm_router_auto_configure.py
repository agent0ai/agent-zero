"""LLM Router - Auto-configure models based on available resources"""

from python.helpers.api import ApiHandler
from python.helpers.llm_router import auto_configure_models, get_router


class LlmRouterAutoConfigure(ApiHandler):
    """Auto-configure models based on available resources"""

    async def process(self, input: dict, request) -> dict:
        try:
            models = await auto_configure_models()

            router = get_router()
            defaults = {}
            for role in ["chat", "utility", "fallback"]:
                result = router.get_default_model(role)
                if result:
                    defaults[role] = f"{result[0]}/{result[1]}"

            return {
                "success": True,
                "message": "Auto-configuration complete",
                "discovered_models": len(models),
                "configured_defaults": defaults
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
