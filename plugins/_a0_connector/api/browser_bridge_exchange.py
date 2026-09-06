"""POST /api/plugins/_a0_connector/browser_bridge_exchange."""

from __future__ import annotations

import json
from typing import Any

from helpers.api import Request, Response
import plugins._a0_connector.api.v1.base as connector_base
from plugins._a0_connector.helpers.browser_bridge_pairing import (
    MAX_REQUEST_BYTES,
    BrowserBridgePairingExchangeFailed,
    BrowserBridgePairingUnavailable,
    coarse_source_key,
    configured_extension_id,
    get_browser_bridge_pairing_store,
    parse_unique_json_object,
)
from plugins._browser.helpers.bridge_foundation import get_browser_bridge_gate


_EXCHANGE_KEYS = {
    "trust_version",
    "pairing_code",
    "server_base_url",
    "extension_id",
    "companion_instance_id",
    "public_key",
}


class BrowserBridgeExchange(connector_base.PublicConnectorApiHandler):
    """Consume one pairing code without ambient WebUI authority."""

    async def handle_request(self, request: Request) -> Response:
        document = _read_bounded_document(request)
        if document is None:
            return _failure()
        return await self._dispatch(document, request)

    async def process(self, input: dict, request: Request) -> Response:
        if (
            _unsupported_body(input, request)
            or set(input) != _EXCHANGE_KEYS
        ):
            return _failure()
        return await self._dispatch(input, request)

    async def _dispatch(self, input: dict, request: Request) -> Response:
        expected_extension_id = configured_extension_id()
        if (
            set(input) != _EXCHANGE_KEYS
            or get_browser_bridge_gate().state not in {"preview", "available"}
            or expected_extension_id is None
            or input.get("extension_id") != expected_extension_id
        ):
            return _failure()
        try:
            exchange = get_browser_bridge_pairing_store().exchange(
                input,
                source_key=coarse_source_key(getattr(request, "remote_addr", None)),
            )
        except BrowserBridgePairingExchangeFailed:
            return _failure()
        except BrowserBridgePairingUnavailable:
            return _failure(status=503)
        except Exception:
            return _failure(status=503)
        return _json_response(exchange.as_public_dict())


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
            "contract": "a0.browser-bridge.trust.v1",
            "trust_version": 1,
            "error": "pairing_exchange_failed",
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
