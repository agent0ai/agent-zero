"""Hello-only scoped session foundation; no browser/context runtime activation."""

from helpers.ws_principal import WsPrincipal
from plugins._a0_connector.helpers.browser_bridge_auth import (
    BRIDGE_CONNECTOR_HANDLER,
    get_browser_bridge_challenge_store,
)
from plugins._a0_connector.helpers.browser_bridge_pairing import (
    configured_extension_id,
    get_browser_bridge_pairing_store,
    server_base_url_for_request,
)
from plugins._browser.helpers.bridge_foundation import get_browser_bridge_gate


def authenticate(auth: dict, *, handler_id: str) -> WsPrincipal | None:
    # The shared namespace has already validated Origin before invoking us.
    from flask import request
    from helpers import runtime

    if (
        set(auth) != {"handlers", "principal"}
        or auth.get("handlers") != [BRIDGE_CONNECTOR_HANDLER]
        or not isinstance(auth.get("principal"), dict)
        or set(auth["principal"]) != {"type", "proof", "signature"}
        or auth["principal"].get("type") != "browser_bridge"
        or get_browser_bridge_gate().state not in {"preview", "available"}
    ):
        return None
    envelope = auth["principal"]
    verified = get_browser_bridge_challenge_store().verify(
        proof=envelope["proof"], signature=envelope["signature"],
    )
    if (
        verified.server_instance_id != runtime.get_persistent_id()
        or envelope["proof"]["server_base_url"] != server_base_url_for_request(request)
        or verified.extension_id != configured_extension_id()
        or "bridge.connect" not in verified.scopes
    ):
        return None
    from plugins._a0_connector.helpers.browser_bridge_bootstrap import (
        browser_bridge_principal_events,
    )

    inbound_events, outbound_events = browser_bridge_principal_events()
    return WsPrincipal(
        principal_type="browser_bridge", principal_id=verified.bridge_id,
        subject_id=verified.subject_id, scopes=frozenset(verified.scopes),
        handler_path=BRIDGE_CONNECTOR_HANDLER, handler_id=handler_id,
        # Operational event authority exists only for an explicitly installed
        # server application and never routes through legacy CLI code.
        inbound_events=inbound_events,
        outbound_events=outbound_events,
        key_generation=verified.key_generation,
    )


def is_active(principal: WsPrincipal) -> bool:
    from helpers import runtime

    try:
        if get_browser_bridge_gate().state not in {"preview", "available"}:
            return False
        record = get_browser_bridge_pairing_store().active_bridge_record(
            bridge_id=principal.principal_id,
            server_instance_id=runtime.get_persistent_id(),
        )
        return bool(
            record
            and record["key_generation"] == principal.key_generation
            and record["subject_id"] == principal.subject_id
            and record["extension_id"] == configured_extension_id()
            and frozenset(record["scopes"]) == principal.scopes
        )
    except Exception:
        return False


def hello(data: dict) -> dict:
    """Return no exec configuration, contexts, host metadata, or runtime feature."""
    return {
        "protocol": "a0-connector.v1",
        "features": [],
        "principal_type": "browser_bridge",
        "connector_session_ready": False,
        "browser_control_ready": False,
        "reason_code": "scoped_runtime_not_available",
    }
