"""
Hot-Reload Status API

Provides status information and control for the hot-reload system.
"""

from python.helpers.api import ApiHandler
from python.helpers.hot_reload_integration import get_hot_reload_integration


class HotReloadStatus(ApiHandler):
    """API handler for hot-reload status"""

    async def process(self, input: dict, request) -> dict:
        """Process hot-reload status request"""
        action = input.get("action", "status")

        integration = get_hot_reload_integration()

        if action == "status":
            return self._get_status(integration)
        elif action == "stats":
            return self._get_stats(integration)
        else:
            return {"error": f"Unknown action: {action}"}

    def _get_status(self, integration) -> dict:
        """Get hot-reload system status"""
        is_running = integration.is_running()

        return {
            "enabled": is_running,
            "status": "running" if is_running else "stopped",
            "message": "Hot-reload system is operational" if is_running else "Hot-reload system is not running"
        }

    def _get_stats(self, integration) -> dict:
        """Get hot-reload statistics"""
        stats = integration.get_stats()

        return {
            "success": True,
            "stats": stats
        }

    @classmethod
    def get_methods(cls) -> list[str]:
        return ["POST", "GET"]

    @classmethod
    def requires_auth(cls) -> bool:
        return True

    @classmethod
    def requires_csrf(cls) -> bool:
        return False

    @classmethod
    def requires_loopback(cls) -> bool:
        return False
