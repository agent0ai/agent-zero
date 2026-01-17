from python.helpers import dotenv
from python.helpers.api import ApiHandler, Request, Response
from python.helpers.tunnel_watchdog import TunnelWatchdog


class TunnelSettingsGet(ApiHandler):
    async def process(self, input: dict, request: Request) -> dict | Response:
        watchdog = TunnelWatchdog.get_instance().status()
        return {
            "settings": {
                "provider": dotenv.get_dotenv_value("TUNNEL_PROVIDER", "cloudflared"),
                "watchdog_interval": int(dotenv.get_dotenv_value("TUNNEL_WATCHDOG_INTERVAL", 60)),
            },
            "watchdog": watchdog,
        }
