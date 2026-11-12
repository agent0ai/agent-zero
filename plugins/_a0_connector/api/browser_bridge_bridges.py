"""POST /api/plugins/_a0_connector/browser_bridge_bridges."""

from __future__ import annotations

import json
from typing import Any

from helpers import runtime
from helpers.api import ApiHandler, Request, Response
from plugins._a0_connector.helpers.browser_bridge_pairing import (
    BROWSER_BRIDGE_INVENTORY_CONTRACT,
    BROWSER_BRIDGE_TRUST_VERSION,
    MAX_REQUEST_BYTES,
    SUBJECT_ID,
    BrowserBridgePairingError,
    BrowserBridgePairingUnavailable,
    BrowserBridgePublicRecord,
    get_browser_bridge_pairing_store,
    parse_unique_json_object,
    validate_identifier,
)


class BrowserBridgeBridges(ApiHandler):
    """List, inspect, or durably revoke current-subject bridge records."""

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
        expected = {"action"} if action == "list" else {"action", "bridge_id"}
        if not isinstance(action, str) or action not in {"list", "detail", "revoke"} or set(input) != expected:
            return _invalid()
        bridge_id: str | None = None
        if action != "list":
            try:
                bridge_id = validate_identifier(
                    input.get("bridge_id"),
                    field_name="bridge_id",
                )
            except BrowserBridgePairingError:
                return _invalid()

        try:
            store = get_browser_bridge_pairing_store()
            server_instance_id = runtime.get_persistent_id()
            if action == "list":
                records = store.list_bridge_records(
                    server_instance_id=server_instance_id,
                    subject_id=SUBJECT_ID,
                )
                return _json_response(
                    {
                        **_base_response(),
                        "bridges": [record.as_public_dict() for record in records],
                    }
                )
            if action == "detail":
                record = store.bridge_record(
                    bridge_id=bridge_id,
                    server_instance_id=server_instance_id,
                    subject_id=SUBJECT_ID,
                )
                if record is None:
                    return _not_found()
                return _json_response(
                    {**_base_response(), "bridge": record.as_public_dict()}
                )

            revocation = store.revoke_bridge(
                bridge_id=bridge_id,
                server_instance_id=server_instance_id,
                subject_id=SUBJECT_ID,
            )
        except (BrowserBridgePairingError, BrowserBridgePairingUnavailable):
            return _unavailable()
        except Exception:
            return _unavailable()
        if revocation is None:
            return _not_found()

        # Authorization is already durably denied. Transport cleanup is best
        # effort and cannot roll that state back or turn the response into a
        # claim about native credentials, Chrome tabs, actions, or leases.
        cleanup = await _disconnect_restricted_sessions(revocation.bridge)
        return _json_response(
            {
                **_base_response(),
                "revoked": True,
                "already_revoked": revocation.already_revoked,
                "bridge": revocation.bridge.as_public_dict(),
                "server_session_cleanup": cleanup,
            }
        )


async def _disconnect_restricted_sessions(
    record: BrowserBridgePublicRecord,
) -> str:
    """Request exact matching restricted Socket.IO sessions to disconnect."""
    try:
        from helpers.ws_manager import get_shared_ws_manager

        manager = get_shared_ws_manager()
        with manager.lock:
            targets = [
                identity
                for identity, info in manager.connections.items()
                if info.principal is not None
                and info.principal.principal_type == "browser_bridge"
                and info.principal.principal_id == record.bridge_id
                and info.principal.subject_id == SUBJECT_ID
            ]
    except Exception:
        return "pending"

    complete = True
    for namespace, sid in targets:
        try:
            # The Socket.IO disconnect callback owns normal manager/handler
            # cleanup. Do not edit the manager registry behind its back.
            await manager.socketio.disconnect(sid, namespace=namespace)
        except Exception:
            complete = False
    return "completed" if complete else "pending"


def _base_response() -> dict[str, Any]:
    return {
        "contract": BROWSER_BRIDGE_INVENTORY_CONTRACT,
        "trust_version": BROWSER_BRIDGE_TRUST_VERSION,
        "browser_control_ready": False,
    }


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
    return (
        len(raw_data) > MAX_REQUEST_BYTES
        or not bool(getattr(request, "is_json", False))
        or parse_unique_json_object(raw_data) is None
    )


def _read_bounded_document(request: Request) -> dict[str, Any] | None:
    content_length = getattr(request, "content_length", None)
    if (
        isinstance(content_length, int)
        and not 1 <= content_length <= MAX_REQUEST_BYTES
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
    if (
        not isinstance(raw_data, bytes)
        or not raw_data
        or len(raw_data) > MAX_REQUEST_BYTES
    ):
        return None
    return parse_unique_json_object(raw_data)


def _invalid() -> Response:
    return _json_response({"error": "invalid_bridge_inventory_request"}, status=400)


def _not_found() -> Response:
    return _json_response(
        {**_base_response(), "error": "browser_bridge_not_found"},
        status=404,
    )


def _unavailable() -> Response:
    return _json_response(
        {**_base_response(), "error": "browser_bridge_inventory_unavailable"},
        status=503,
    )


def _json_response(payload: dict[str, Any], *, status: int = 200) -> Response:
    return Response(
        response=json.dumps(payload, separators=(",", ":")),
        status=status,
        mimetype="application/json",
        headers={"Cache-Control": "no-store"},
    )
