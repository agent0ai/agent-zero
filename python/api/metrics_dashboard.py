from python.helpers.api import ApiHandler, Request, Response
from python.helpers.metrics_collector import collector


class MetricsDashboard(ApiHandler):

    async def process(self, input: dict, request: Request) -> dict | Response:
        action = input.get("action", "snapshot")

        if action == "snapshot":
            return {"success": True, **collector.snapshot()}
        elif action == "clear":
            collector.clear()
            return {"success": True, "message": "Metrics cleared"}
        else:
            return {"success": False, "error": f"Unknown action: {action}"}
