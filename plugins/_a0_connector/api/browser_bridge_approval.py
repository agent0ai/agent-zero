"""POST /api/plugins/_a0_connector/browser_bridge_approval."""

from __future__ import annotations

import json
from typing import Any

from helpers.api import ApiHandler, Request, Response
from plugins._a0_connector.helpers.browser_bridge_approval import (
    APPROVAL_CHOICES,
    BROWSER_BRIDGE_APPROVAL_CONTRACT,
    BROWSER_BRIDGE_APPROVAL_VERSION,
    MAX_APPROVAL_REQUEST_BYTES,
    BrowserBridgeApprovalError,
    validate_approval_identifier,
)
from plugins._a0_connector.helpers.browser_bridge_action_authority import (
    BrowserBridgeActionAuthorityError,
    BrowserBridgeActionAuthorityUnavailable,
    get_browser_bridge_action_authority,
)
from plugins._a0_connector.helpers.browser_bridge_pairing import (
    SUBJECT_ID,
    parse_unique_json_object,
)
from plugins._a0_connector.helpers.browser_bridge_selection import selected_bridge


class BrowserBridgeApproval(ApiHandler):
    """Record one protected user decision for an existing exact challenge."""

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
        if input.get("action") == "list":
            if set(input) != {"action", "context_id"}:
                return _invalid()
            try:
                context_id = validate_approval_identifier(
                    input.get("context_id"), field_name="context_id"
                )
            except BrowserBridgeApprovalError:
                return _invalid()
            bridge_id = selected_bridge(context_id)
            if bridge_id is None:
                return _json_response({**_base_response(), "challenges": []})
            try:
                challenges = get_browser_bridge_action_authority().list_pending(
                    subject_id=SUBJECT_ID,
                    context_id=context_id,
                    bridge_id=bridge_id,
                )
            except BrowserBridgeActionAuthorityUnavailable:
                return _unavailable(status=503)
            except Exception:
                return _unavailable(status=503)
            return _json_response(
                {
                    **_base_response(),
                    "challenges": [dict(challenge) for challenge in challenges],
                }
            )
        if set(input) != {"challenge_id", "choice"}:
            return _invalid()
        try:
            challenge_id = validate_approval_identifier(
                input.get("challenge_id"),
                field_name="challenge_id",
            )
        except BrowserBridgeApprovalError:
            return _invalid()
        choice = input.get("choice")
        if not isinstance(choice, str) or choice not in APPROVAL_CHOICES:
            return _invalid()
        try:
            decision = await get_browser_bridge_action_authority().decide(
                subject_id=SUBJECT_ID,
                challenge_id=challenge_id,
                choice=choice,
            )
        except (BrowserBridgeApprovalError, BrowserBridgeActionAuthorityError):
            return _invalid()
        except BrowserBridgeActionAuthorityUnavailable:
            return _unavailable(status=409)
        except Exception:
            return _unavailable(status=503)
        return _json_response({**_base_response(), **decision.as_public_dict()})


def _base_response() -> dict[str, Any]:
    return {
        "contract": BROWSER_BRIDGE_APPROVAL_CONTRACT,
        "approval_version": BROWSER_BRIDGE_APPROVAL_VERSION,
        "browser_control_ready": False,
    }


def _unsupported_body(input: Any, request: Request | None) -> bool:
    if not isinstance(input, dict):
        return True
    if request is None:
        return False
    raw_data = bytes(getattr(request, "data", b"") or b"")
    content_length = getattr(request, "content_length", None)
    if isinstance(content_length, int) and content_length > MAX_APPROVAL_REQUEST_BYTES:
        return True
    if not raw_data:
        return False
    return (
        len(raw_data) > MAX_APPROVAL_REQUEST_BYTES
        or not bool(getattr(request, "is_json", False))
        or parse_unique_json_object(raw_data) is None
    )


def _read_bounded_document(request: Request) -> dict[str, Any] | None:
    content_length = getattr(request, "content_length", None)
    if (
        isinstance(content_length, int)
        and not 1 <= content_length <= MAX_APPROVAL_REQUEST_BYTES
    ):
        return None
    if not bool(getattr(request, "is_json", False)):
        return None
    stream = getattr(request, "stream", None)
    if stream is None or not hasattr(stream, "read"):
        return None
    try:
        raw_data = stream.read(MAX_APPROVAL_REQUEST_BYTES + 1)
    except Exception:
        return None
    if (
        not isinstance(raw_data, bytes)
        or not raw_data
        or len(raw_data) > MAX_APPROVAL_REQUEST_BYTES
    ):
        return None
    return parse_unique_json_object(raw_data)


def _invalid() -> Response:
    return _json_response({"error": "invalid_approval_request"}, status=400)


def _unavailable(*, status: int) -> Response:
    return _json_response(
        {
            **_base_response(),
            "error": "browser_bridge_approval_unavailable",
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
