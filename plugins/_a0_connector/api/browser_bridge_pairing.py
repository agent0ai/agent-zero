"""POST /api/plugins/_a0_connector/browser_bridge_pairing."""

from __future__ import annotations

import json
from typing import Any

from helpers import runtime
from helpers.api import ApiHandler, Request, Response, session
from plugins._a0_connector.helpers.browser_bridge_pairing import (
    MAX_REQUEST_BYTES,
    BrowserBridgePairingError,
    BrowserBridgePairingUnavailable,
    build_browser_bridge_pairing_foundation_status,
    configured_extension_id,
    get_browser_bridge_pairing_store,
    pairing_owner_id,
    parse_unique_json_object,
    server_base_url_for_request,
    validate_display_name,
    validate_identifier,
)
from plugins._browser.helpers.bridge_foundation import get_browser_bridge_gate


class BrowserBridgePairing(ApiHandler):
    """Create, inspect, or cancel one WebUI-session pairing intent."""

    async def handle_request(self, request: Request) -> Response:
        document = _read_bounded_document(request)
        if document is None:
            return _json_response(
                {"error": "invalid_pairing_request"},
                status=400,
            )
        return await self._dispatch(document, request)

    async def process(self, input: dict, request: Request) -> Response:
        if _unsupported_body(input, request):
            return _json_response(
                {"error": "invalid_pairing_request"},
                status=400,
            )
        return await self._dispatch(input, request)

    async def _dispatch(self, input: dict, request: Request) -> Response:
        action = input.get("action")
        if action == "create":
            if set(input) != {"action", "display_name"}:
                return _json_response(
                    {"error": "invalid_pairing_request"},
                    status=400,
                )
            try:
                validate_display_name(input.get("display_name"))
            except BrowserBridgePairingError:
                return _json_response(
                    {"error": "invalid_pairing_request"},
                    status=400,
                )
            return self._create(input, request)
        if action == "status":
            if set(input) != {"action"}:
                return _json_response(
                    {"error": "invalid_pairing_request"},
                    status=400,
                )
            return self._status()
        if action == "cancel":
            if set(input) != {"action", "pairing_id"}:
                return _json_response(
                    {"error": "invalid_pairing_request"},
                    status=400,
                )
            try:
                validate_identifier(
                    input.get("pairing_id"),
                    field_name="pairing_id",
                )
            except BrowserBridgePairingError:
                return _json_response(
                    {"error": "invalid_pairing_request"},
                    status=400,
                )
            return self._cancel(input)
        return _json_response({"error": "invalid_pairing_request"}, status=400)

    def _create(self, input: dict[str, Any], request: Request) -> Response:
        gate = get_browser_bridge_gate()
        foundation = build_browser_bridge_pairing_foundation_status(gate)
        if not foundation["pairing_create_enabled"]:
            return _json_response(
                {
                    "error": "pairing_unavailable",
                    "status": foundation,
                },
                status=409,
            )
        extension_id = configured_extension_id()
        if extension_id is None:
            return _json_response(
                {"error": "pairing_unavailable", "status": foundation},
                status=409,
            )
        try:
            owner_id = pairing_owner_id(session, create=True)
            if owner_id is None:
                raise BrowserBridgePairingUnavailable("pairing owner unavailable")
            creation = get_browser_bridge_pairing_store().create(
                owner_id=owner_id,
                server_instance_id=runtime.get_persistent_id(),
                server_base_url=server_base_url_for_request(request),
                extension_id=extension_id,
                display_name=input.get("display_name"),
            )
        except BrowserBridgePairingError:
            return _json_response({"error": "pairing_unavailable"}, status=409)
        except Exception:
            return _json_response({"error": "pairing_unavailable"}, status=503)
        return _json_response(creation.as_public_dict(), status=201)

    def _status(self) -> Response:
        gate = get_browser_bridge_gate()
        foundation = build_browser_bridge_pairing_foundation_status(gate)
        try:
            status = get_browser_bridge_pairing_store().status(
                owner_id=pairing_owner_id(session, create=False),
                server_instance_id=runtime.get_persistent_id(),
            )
        except Exception:
            status = {
                "contract": foundation["contract"],
                "trust_version": foundation["trust_version"],
                "state": "repair_required",
                "reason_code": "pairing_status_unavailable",
                "pairing_code_present": False,
                "native_runtime_location": "user_browser_host",
                "docker_install_target": False,
                "connector_session_ready": False,
                "browser_control_ready": False,
            }
        status["server_pairing_enabled"] = foundation["pairing_create_enabled"]
        return _json_response(status)

    def _cancel(self, input: dict[str, Any]) -> Response:
        store = get_browser_bridge_pairing_store()
        try:
            canceled = store.cancel(
                owner_id=pairing_owner_id(session, create=False),
                pairing_id=input.get("pairing_id"),
            )
            status = store.status(
                owner_id=pairing_owner_id(session, create=False),
                server_instance_id=runtime.get_persistent_id(),
            )
        except Exception:
            return _json_response({"error": "pairing_unavailable"}, status=503)
        status["canceled"] = canceled
        status["server_pairing_enabled"] = build_browser_bridge_pairing_foundation_status(
            get_browser_bridge_gate()
        )["pairing_create_enabled"]
        return _json_response(status)


def _unsupported_body(input: Any, request: Request | None) -> bool:
    if not isinstance(input, dict):
        return True
    if request is None:
        return False
    raw_data = bytes(getattr(request, "data", b"") or b"")
    content_length = getattr(request, "content_length", None)
    if isinstance(content_length, int) and content_length > MAX_REQUEST_BYTES:
        return True
    if not raw_data:
        return False
    if len(raw_data) > MAX_REQUEST_BYTES or not bool(getattr(request, "is_json", False)):
        return True
    return parse_unique_json_object(raw_data) is None


def _read_bounded_document(request: Request) -> dict[str, Any] | None:
    content_length = getattr(request, "content_length", None)
    if (
        isinstance(content_length, int)
        and (content_length < 1 or content_length > MAX_REQUEST_BYTES)
    ):
        return None
    if not bool(getattr(request, "is_json", False)):
        return None
    stream = getattr(request, "stream", None)
    if stream is None or not hasattr(stream, "read"):
        return None
    try:
        raw_data = stream.read(MAX_REQUEST_BYTES + 1)
    except Exception:
        return None
    if not isinstance(raw_data, bytes) or not raw_data or len(raw_data) > MAX_REQUEST_BYTES:
        return None
    return parse_unique_json_object(raw_data)


def _json_response(payload: dict[str, Any], *, status: int = 200) -> Response:
    return Response(
        response=json.dumps(payload, separators=(",", ":")),
        status=status,
        mimetype="application/json",
        headers={"Cache-Control": "no-store"},
    )
