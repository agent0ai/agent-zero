"""POST /api/plugins/_a0_connector/browser_bridge_challenge."""

from __future__ import annotations

import json
from typing import Any

from helpers import runtime
from helpers.api import Request, Response
import plugins._a0_connector.api.v1.base as connector_base
from plugins._a0_connector.helpers.browser_bridge_auth import (
    BrowserBridgeChallengeFailed,
    BrowserBridgeChallengeUnavailable,
    get_browser_bridge_challenge_store,
)
from plugins._a0_connector.helpers.browser_bridge_pairing import (
    BROWSER_BRIDGE_TRUST_CONTRACT,
    BROWSER_BRIDGE_TRUST_VERSION,
    MAX_REQUEST_BYTES,
    BrowserBridgePairingError,
    coarse_source_key,
    parse_unique_json_object,
    server_base_url_for_request,
)
from plugins._browser.helpers.bridge_foundation import get_browser_bridge_gate


_CHALLENGE_KEYS = {"trust_version", "bridge_id", "client_nonce"}


class BrowserBridgeChallenge(connector_base.PublicConnectorApiHandler):
    """Issue one memory-only challenge for an active bridge credential."""

    async def handle_request(self, request: Request) -> Response:
        document = _read_bounded_document(request)
        if document is None:
            return _failure()
        return await self._dispatch(document, request)

    async def process(self, input: dict, request: Request) -> Response:
        if _unsupported_body(input, request) or set(input) != _CHALLENGE_KEYS:
            return _failure()
        return await self._dispatch(input, request)

    async def _dispatch(self, input: dict, request: Request) -> Response:
        if (
            set(input) != _CHALLENGE_KEYS
            or get_browser_bridge_gate().state not in {"preview", "available"}
        ):
            return _failure()
        try:
            challenge = get_browser_bridge_challenge_store().issue(
                input,
                source_key=coarse_source_key(
                    getattr(request, "remote_addr", None)
                ),
                server_instance_id=runtime.get_persistent_id(),
                server_base_url=server_base_url_for_request(request),
            )
        except (BrowserBridgeChallengeFailed, BrowserBridgePairingError):
            return _failure()
        except BrowserBridgeChallengeUnavailable:
            return _failure(status=503)
        except Exception:
            return _failure(status=503)
        return _json_response(challenge.as_public_dict())


def _unsupported_body(input: Any, request: Request | None) -> bool:
    if not isinstance(input, dict):
        return True
    if request is None:
        return False
    raw_data = bytes(getattr(request, "data", b"") or b"")
    content_length = getattr(request, "content_length", None)
    if isinstance(content_length, int) and content_length > MAX_REQUEST_BYTES:
        return True
    if not raw_data or len(raw_data) > MAX_REQUEST_BYTES:
        return True
    if not bool(getattr(request, "is_json", False)):
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


def _failure(*, status: int = 400) -> Response:
    return _json_response(
        {
            "contract": BROWSER_BRIDGE_TRUST_CONTRACT,
            "trust_version": BROWSER_BRIDGE_TRUST_VERSION,
            "error": "bridge_challenge_failed",
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
