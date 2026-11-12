"""POST /api/plugins/_a0_connector/browser_bridge_site_authority."""

from __future__ import annotations

import json
from typing import Any

from helpers.api import ApiHandler, Request, Response
from plugins._browser.helpers.extension_first_open import current_first_open_authority, FirstOpenDenied
from plugins._a0_connector.helpers.browser_bridge_approval import (
    BrowserBridgeApprovalError,
    validate_approval_identifier,
)
from plugins._a0_connector.helpers.browser_bridge_pairing import (
    SUBJECT_ID,
    parse_unique_json_object,
)
from plugins._a0_connector.helpers.browser_bridge_selection import selected_bridge
from plugins._a0_connector.helpers.browser_bridge_site_authority import (
    MAX_SITE_AUTHORITY_REQUEST_BYTES,
    SITE_AUTHORITY_CONTRACT,
    SITE_AUTHORITY_VERSION,
    SITE_DECISIONS,
    BrowserBridgeSiteAuthorityError,
    BrowserBridgeSiteAuthorityUnavailable,
    get_browser_bridge_site_authority_repository,
)


class BrowserBridgeSiteAuthority(ApiHandler):
    """List safe site prompts or relay one explicit protected decision."""

    async def handle_request(self, request: Request) -> Response:
        document = _read_bounded_document(request)
        if document is None:
            return _invalid()
        return await self._dispatch(document)

    async def process(self, input: dict, request: Request) -> Response:
        if _unsupported_body(input, request):
            return _invalid()
        return await self._dispatch(input)

    async def _dispatch(self, value: dict[str, Any]) -> Response:
        action = value.get("action")
        if action == "list":
            if set(value) != {"action", "context_id"}:
                return _invalid()
            try:
                context_id = validate_approval_identifier(
                    value.get("context_id"), field_name="context_id"
                )
            except BrowserBridgeApprovalError:
                return _invalid()
            bridge_id = selected_bridge(context_id)
            if bridge_id is None:
                return _json_response({**_base_response(), "challenges": []})
            try:
                challenges = get_browser_bridge_site_authority_repository().list_pending(
                    subject_id=SUBJECT_ID,
                    context_id=context_id,
                    bridge_id=bridge_id,
                )
                first_open = current_first_open_authority()
                if first_open is not None:
                    challenges = tuple(challenges) + first_open.list_pending(
                        subject_id=SUBJECT_ID, context_id=context_id, bridge_id=bridge_id)
                challenges = sorted(challenges, key=lambda item: item["expires_at_ms"])[:128]
            except BrowserBridgeSiteAuthorityError:
                return _invalid()
            except BrowserBridgeSiteAuthorityUnavailable:
                return _unavailable(status=503)
            except Exception:
                return _unavailable(status=503)
            return _json_response(
                {
                    **_base_response(),
                    "challenges": [dict(challenge) for challenge in challenges],
                }
            )

        if action != "decide" or set(value) != {
            "action",
            "challenge_id",
            "decision",
        }:
            return _invalid()
        decision = value.get("decision")
        is_first_open = isinstance(value.get("challenge_id"), str) and value["challenge_id"].startswith("open-site-")
        if not isinstance(decision, str) or decision not in (SITE_DECISIONS | {"allow_site"} if is_first_open else SITE_DECISIONS):
            return _invalid()
        if is_first_open:
            try:
                challenge_id = validate_approval_identifier(value["challenge_id"], field_name="challenge_id")
                first_open = current_first_open_authority()
                if first_open is None:
                    return _unavailable(status=409)
                result = first_open.decide(subject_id=SUBJECT_ID, challenge_id=challenge_id, decision=decision)
                return _json_response({**_base_response(), **result})
            except (BrowserBridgeApprovalError, FirstOpenDenied):
                return _invalid()
            except Exception:
                return _unavailable(status=503)
        try:
            result = await get_browser_bridge_site_authority_repository().decide(
                subject_id=SUBJECT_ID,
                challenge_id=value.get("challenge_id"),
                decision=decision,
            )
        except BrowserBridgeSiteAuthorityError:
            return _invalid()
        except BrowserBridgeSiteAuthorityUnavailable:
            return _unavailable(status=409)
        except Exception:
            return _unavailable(status=503)
        return _json_response({**_base_response(), **result.as_public_dict()})


def _base_response() -> dict[str, Any]:
    return {
        "contract": SITE_AUTHORITY_CONTRACT,
        "authority_version": SITE_AUTHORITY_VERSION,
        "browser_control_ready": False,
    }


def _unsupported_body(input: Any, request: Request | None) -> bool:
    if not isinstance(input, dict):
        return True
    if request is None:
        return False
    raw_data = bytes(getattr(request, "data", b"") or b"")
    content_length = getattr(request, "content_length", None)
    if (
        isinstance(content_length, int)
        and content_length > MAX_SITE_AUTHORITY_REQUEST_BYTES
    ):
        return True
    if not raw_data:
        return False
    return (
        len(raw_data) > MAX_SITE_AUTHORITY_REQUEST_BYTES
        or not bool(getattr(request, "is_json", False))
        or parse_unique_json_object(raw_data) is None
    )


def _read_bounded_document(request: Request) -> dict[str, Any] | None:
    content_length = getattr(request, "content_length", None)
    if (
        isinstance(content_length, int)
        and not 1 <= content_length <= MAX_SITE_AUTHORITY_REQUEST_BYTES
    ):
        return None
    if not bool(getattr(request, "is_json", False)):
        return None
    stream = getattr(request, "stream", None)
    if stream is None or not hasattr(stream, "read"):
        return None
    try:
        raw_data = stream.read(MAX_SITE_AUTHORITY_REQUEST_BYTES + 1)
    except Exception:
        return None
    if (
        not isinstance(raw_data, bytes)
        or not raw_data
        or len(raw_data) > MAX_SITE_AUTHORITY_REQUEST_BYTES
    ):
        return None
    return parse_unique_json_object(raw_data)


def _invalid() -> Response:
    return _json_response(
        {"error": "invalid_site_authority_request"}, status=400
    )


def _unavailable(*, status: int) -> Response:
    return _json_response(
        {
            **_base_response(),
            "error": "browser_bridge_site_authority_unavailable",
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
