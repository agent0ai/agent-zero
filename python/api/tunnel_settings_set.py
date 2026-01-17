from python.helpers import dotenv
from python.helpers.api import ApiHandler, Request, Response


class TunnelSettingsSet(ApiHandler):
    async def process(self, input: dict, request: Request) -> dict | Response:
        settings = input.get("settings", {})
        if not isinstance(settings, dict):
            return {"success": False, "error": "settings must be an object"}

        if "provider" in settings:
            dotenv.save_dotenv_value("TUNNEL_PROVIDER", settings.get("provider", "cloudflared"))
        if "watchdog_interval" in settings:
            interval = max(15, int(settings.get("watchdog_interval", 60)))
            dotenv.save_dotenv_value("TUNNEL_WATCHDOG_INTERVAL", str(interval))

        return {"success": True}
