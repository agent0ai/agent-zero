from python.helpers import telemetry
from python.helpers.api import ApiHandler, Request, Response


class TelemetryClear(ApiHandler):
    async def process(self, input: dict, request: Request) -> dict | Response:
        ctxid = input.get("context", "")
        try:
            context = self.use_context(ctxid, create_if_not_exists=False)
        except Exception:
            return {"events": [], "stats": {}}

        context.data[telemetry.TELEMETRY_KEY] = {"events": [], "stats": {}}
        return {"events": [], "stats": {}}
