"""Authenticated, CSRF-protected public browser setup guidance."""
import json

from helpers.api import ApiHandler, Request, Response
from plugins._a0_connector.api.v1.browser_companion_release import _has_unsupported_body
from plugins._a0_connector.helpers.browser_bridge_setup import browser_bridge_setup_status


class BrowserBridgeSetup(ApiHandler):
    async def process(self, input: dict, request: Request) -> Response:
        if not isinstance(input, dict) or input or _has_unsupported_body(request):
            return Response('{"error":"request_body_not_supported"}', status=400, mimetype="application/json")
        return Response(json.dumps(browser_bridge_setup_status(), separators=(",", ":")),
                        mimetype="application/json", headers={"Cache-Control": "no-store"})
