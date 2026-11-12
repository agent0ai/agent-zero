"""POST /api/plugins/_a0_connector/browser_bridge_policy."""

from __future__ import annotations

import json
from typing import Any

from helpers import runtime
from helpers.api import ApiHandler, Request, Response
from plugins._a0_connector.helpers.browser_bridge_pairing import (
    BrowserBridgePairingError,
    get_browser_bridge_pairing_store,
    parse_unique_json_object,
    validate_identifier,
)
from plugins._a0_connector.helpers.browser_bridge_policy import (
    BROWSER_BRIDGE_POLICY_CONTRACT,
    BROWSER_BRIDGE_POLICY_VERSION,
    MAX_POLICY_REQUEST_BYTES,
    BrowserBridgePolicyError,
    BrowserBridgePolicyUnavailable,
    get_browser_bridge_policy_repository,
)


class BrowserBridgePolicy(ApiHandler):
    """Manage saved exact sites or explicit production all-websites access."""

    async def handle_request(self, request: Request) -> Response:
        document = _read_bounded_document(request)
        if document is None:
            return _invalid()
        return await self._dispatch(document)

    async def process(self, input: dict, request: Request) -> Response:
        if _unsupported_body(input, request):
            return _invalid()
        return await self._dispatch(input)

    async def _dispatch(self, input: dict[str, Any]) -> Response:
        action = input.get("action")
        expected = (
            {"action", "bridge_id"}
            if action == "list"
            else {"action", "bridge_id", "site_mode"} if action == "set_mode"
            else {"action", "bridge_id", "origin"}
        )
        if not isinstance(action, str) or action not in {"list", "allow", "revoke", "set_mode"} or set(input) != expected:
            return _invalid()
        try:
            bridge_id = validate_identifier(input.get("bridge_id"), field_name="bridge_id")
        except BrowserBridgePairingError:
            return _invalid()
        server_instance_id = runtime.get_persistent_id()
        try:
            record = get_browser_bridge_pairing_store().active_bridge_record(
                bridge_id=bridge_id,
                server_instance_id=server_instance_id,
            )
        except Exception:
            return _unavailable(status=503)
        if record is None:
            return _unavailable(status=409)

        repository = get_browser_bridge_policy_repository()
        try:
            subject_id = validate_identifier(
                record.get("subject_id") if isinstance(record, dict) else None,
                field_name="subject_id",
            )
            identity = {
                "server_instance_id": server_instance_id,
                "bridge_id": bridge_id,
                "subject_id": subject_id,
            }
            if action == "allow":
                repository.allow(**identity, origin=input.get("origin"))
            elif action == "revoke":
                revoked = repository.revoke(**identity, origin=input.get("origin"))
            elif action == "set_mode":
                repository.set_site_mode(**identity, site_mode=input.get("site_mode"))
            grants = repository.list_grants(**identity)
            site_mode = repository.site_mode(**identity)
        except BrowserBridgePolicyUnavailable:
            return _unavailable(status=503)
        except BrowserBridgePolicyError:
            return _invalid()
        except Exception:
            return _unavailable(status=503)
        return _json_response(
            {
                "contract": BROWSER_BRIDGE_POLICY_CONTRACT,
                "policy_version": BROWSER_BRIDGE_POLICY_VERSION,
                "site_mode": site_mode,
                "bridge_id": bridge_id,
                "grants": [grant.as_public_dict() for grant in grants],
                **({"revoked": revoked} if action == "revoke" else {}),
                "operation_grants_enabled": False,
                "browser_control_ready": False,
            }
        )


def _unsupported_body(input: Any, request: Request | None) -> bool:
    if not isinstance(input, dict):
        return True
    if request is None:
        return False
    raw_data = bytes(getattr(request, "data", b"") or b"")
    content_length = getattr(request, "content_length", None)
    if isinstance(content_length, int) and content_length > MAX_POLICY_REQUEST_BYTES:
        return True
    if not raw_data:
        return False
    return (
        len(raw_data) > MAX_POLICY_REQUEST_BYTES
        or not bool(getattr(request, "is_json", False))
        or parse_unique_json_object(raw_data) is None
    )


def _read_bounded_document(request: Request) -> dict[str, Any] | None:
    content_length = getattr(request, "content_length", None)
    if isinstance(content_length, int) and not 1 <= content_length <= MAX_POLICY_REQUEST_BYTES:
        return None
    if not bool(getattr(request, "is_json", False)):
        return None
    stream = getattr(request, "stream", None)
    if stream is None or not hasattr(stream, "read"):
        return None
    try:
        raw_data = stream.read(MAX_POLICY_REQUEST_BYTES + 1)
    except Exception:
        return None
    if (
        not isinstance(raw_data, bytes)
        or not raw_data
        or len(raw_data) > MAX_POLICY_REQUEST_BYTES
    ):
        return None
    return parse_unique_json_object(raw_data)


def _invalid() -> Response:
    return _json_response({"error": "invalid_policy_request"}, status=400)


def _unavailable(*, status: int) -> Response:
    return _json_response(
        {
            "contract": BROWSER_BRIDGE_POLICY_CONTRACT,
            "policy_version": BROWSER_BRIDGE_POLICY_VERSION,
            "error": "browser_bridge_policy_unavailable",
        },
        status=status,
    )


def _json_response(payload: dict[str, Any], *, status: int = 200) -> Response:
    return Response(
        response=json.dumps(payload, separators=(",", ":")),
        status=status,
        mimetype="application/json",
        headers={"Cache-Control": "no-store"},
    )
