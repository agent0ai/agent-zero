"""Normally authenticated and CSRF-protected production Browser selection."""

import json

from helpers.api import ApiHandler, Request, Response
from plugins._a0_connector.helpers.browser_bridge_pairing import MAX_REQUEST_BYTES, parse_unique_json_object
from plugins._a0_connector.helpers.browser_bridge_selection import (
    selected_bridge, select_bridge_for_context, default_selected_bridge, select_default_bridge,
)


class BrowserBridgeSelection(ApiHandler):
    async def handle_request(self, request: Request) -> Response:
        if not request.is_json:
            return _response({"error": "invalid_selection_request"}, 400)
        raw = request.stream.read(MAX_REQUEST_BYTES + 1)
        document = parse_unique_json_object(raw) if 0 < len(raw) <= MAX_REQUEST_BYTES else None
        return await self._dispatch(document)

    async def process(self, input: dict, request: Request) -> Response:
        # Raw HTTP requests always use the duplicate-key rejecting boundary.
        if request is not None:
            return await self.handle_request(request)
        return await self._dispatch(input)

    async def _dispatch(self, value) -> Response:
        if not isinstance(value, dict):
            return _response({"error": "invalid_selection_request"}, 400)
        action = value.get("action")
        if not isinstance(action, str):
            return _response({"error": "invalid_selection_request"}, 400)
        if action in {"default_status", "use_default", "clear_default"}:
            return self._default_dispatch(value)
        expected = (
            {"action", "context_id", "bridge_id"} if action == "use"
            else {"action", "context_id", "expected_bridge_id"} if action == "clear"
            else {"action", "context_id"}
        )
        if action not in {"use", "clear", "status"} or set(value) != expected:
            return _response({"error": "invalid_selection_request"}, 400)
        from plugins._a0_connector.helpers.browser_bridge_pairing import validate_identifier
        from plugins._a0_connector.helpers.browser_bridge_bootstrap import get_browser_bridge_application
        try:
            context_id = validate_identifier(value["context_id"], field_name="context_id")
            if action == "use":
                bridge_id = validate_identifier(value["bridge_id"], field_name="bridge_id")
                select_bridge_for_context(context_id, bridge_id)
            elif action == "clear":
                expected_bridge_id = validate_identifier(value["expected_bridge_id"], field_name="bridge_id")
                select_bridge_for_context(context_id, None, expected_bridge_id=expected_bridge_id)
            bridge_id = selected_bridge(context_id)
            application = get_browser_bridge_application()
            route = (
                application.registry.resolve_extension_route(context_id, bridge_id)
                if application is not None and bridge_id is not None else None
            )
        except ValueError:
            return _response({"error": "invalid_selection_request"}, 400)
        except Exception:
            return _response({"error": "browser_runtime_unavailable"}, 409)
        return _response({
            "contract": "a0.browser-bridge.selection.v1", "context_id": context_id,
            "bridge_id": bridge_id, "selected": bridge_id is not None,
            "browser_control_ready": route is not None,
            "reconnect_required": bridge_id is not None and route is None,
        })

    def _default_dispatch(self, value) -> Response:
        action = value["action"]
        keys = ({"action", "bridge_id", "expected_bridge_id"} if action == "use_default"
                else {"action", "expected_bridge_id"} if action == "clear_default" else {"action"})
        if set(value) != keys:
            return _response({"error": "invalid_selection_request"}, 400)
        from plugins._a0_connector.helpers.browser_bridge_pairing import validate_identifier
        from plugins._a0_connector.helpers.browser_bridge_bootstrap import get_browser_bridge_application
        try:
            if action != "default_status":
                previous = value["expected_bridge_id"]
                if previous is not None or action == "clear_default":
                    previous = validate_identifier(previous, field_name="bridge_id")
                bridge = (validate_identifier(value["bridge_id"], field_name="bridge_id")
                          if action == "use_default" else None)
                select_default_bridge(bridge, expected_bridge_id=previous)
            bridge = default_selected_bridge()
            application = get_browser_bridge_application()
            ready = bool(bridge is not None and application is not None
                         and application.registry.current_bridge_ready(bridge))
        except ValueError:
            return _response({"error": "invalid_selection_request"}, 400)
        except Exception:
            return _response({"error": "browser_runtime_unavailable"}, 409)
        return _response({
            "contract": "a0.browser-bridge.default-selection.v1", "bridge_id": bridge,
            "selected": bridge is not None, "browser_control_ready": ready,
            "reconnect_required": bridge is not None and not ready,
        })


def _response(payload: dict, status: int = 200) -> Response:
    return Response(json.dumps(payload, separators=(",", ":")), status=status,
                    mimetype="application/json", headers={"Cache-Control": "no-store"})
