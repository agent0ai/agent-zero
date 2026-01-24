"""
Health Check API - Monitor model availability
"""

from python.helpers.api import ApiHandler, Request, Response
from python.helpers.llm_router import get_router


class HealthCheck(ApiHandler):
    """API handler for checking model provider health"""

    async def process(self, input: dict, request: Request) -> dict | Response:
        """
        Get health status of all model providers

        Input:
            providers: Optional list of providers to check (default: all)

        Returns:
            healthy: List of healthy providers
            degraded: List of degraded providers
            unavailable: List of unavailable providers with error messages
            baseline_available: Whether baseline model is available
            recommendations: List of actionable recommendations
        """
        router = get_router()
        providers = input.get("providers")

        try:
            status = await router.health_check_models(providers=providers)
            return status
        except Exception as e:
            return {"success": False, "error": f"Health check failed: {e!s}"}


class BaselineStatus(ApiHandler):
    """API handler for checking baseline model status"""

    async def process(self, input: dict, request: Request) -> dict | Response:
        """
        Get baseline model status

        Returns:
            available: Whether baseline model is available
            model: Model display name (if available)
            provider: Provider name (if available)
            size_gb: Model size in GB (if available)
            is_local: Whether model is local (if available)
        """
        router = get_router()

        try:
            baseline = router.get_baseline_model()

            if baseline:
                return {
                    "available": True,
                    "model": baseline.display_name,
                    "provider": baseline.provider,
                    "size_gb": baseline.size_gb,
                    "is_local": baseline.is_local,
                }
            else:
                return {"available": False, "message": "No baseline model configured"}
        except Exception as e:
            return {"success": False, "error": f"Failed to get baseline status: {e!s}"}
