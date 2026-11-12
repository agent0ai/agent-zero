"""Protected explicit prototype retirement; never a v1 activation endpoint."""
from helpers.api import ApiHandler, Request, Response
from plugins._a0_connector.api.browser_bridge_pairing import _read_bounded_document, _json_response
from plugins._a0_connector.helpers.browser_bridge_legacy_retirement import get_legacy_retirement


class BrowserBridgeLegacyRetirement(ApiHandler):
    async def handle_request(self, request: Request) -> Response:
        document = _read_bounded_document(request)
        if document is None:
            return _json_response({"error": "invalid_retirement_request"}, status=400)
        return await self.process(document, request)

    async def process(self, input: dict, request: Request) -> Response:
        if type(input) is not dict:
            return _json_response({"error": "invalid_retirement_request"}, status=400)
        owner = get_legacy_retirement()
        if input == {"action": "status"}:
            return _json_response(owner.status())
        if set(input) == {"action", "confirmed_all_legacy_scopes", "offset"} and input.get("action") == "quarantine" and input.get("confirmed_all_legacy_scopes") is True:
            from plugins._a0_connector.helpers.browser_bridge_legacy_quarantine import sweep_loaded
            try:
                return _json_response(sweep_loaded(input["offset"]))
            except Exception:
                return _json_response({"error": "legacy_quarantine_incomplete"}, status=409)
        if input != {"action": "retire", "confirmed_all_legacy_scopes": True} or type(input.get("confirmed_all_legacy_scopes")) is not bool:
            return _json_response({"error": "invalid_retirement_request"}, status=400)
        try:
            result = await owner.retire()
            return _json_response(result, status=200 if result["state"] == "legacy_disabled" else 409)
        except Exception:
            return _json_response({"error": "migration_incomplete", "status": owner.status()}, status=409)
