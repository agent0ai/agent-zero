from python.helpers.api import ApiHandler, Request, Response
from python.helpers.tunnel_watchdog import TunnelWatchdog


class TunnelWatchdogApi(ApiHandler):
    async def process(self, input: dict, request: Request) -> dict | Response:
        action = input.get("action", "status")
        watchdog = TunnelWatchdog.get_instance()

        if action == "start":
            interval = int(input.get("interval", 60))
            provider = input.get("provider", "cloudflared")
            watchdog.start(interval=interval, provider=provider)
        elif action == "stop":
            watchdog.stop()

        return {"status": watchdog.status()}
