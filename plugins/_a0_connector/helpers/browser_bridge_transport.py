"""Fixed internal identities for trusted Browser bridge transports.

Transport identity is not runtime admission. Only the production constant created
in this module is accepted by composed Core helpers; protocol documents,
environment values, and callers cannot construct another accepted profile.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from helpers.ws_principal import WsPrincipal


RUNTIME_REQUIRED_SCOPES = frozenset(
    {
        "bridge.connect",
        "context.list",
        "context.read",
        "context.message",
        "browser.operate",
        "browser.control",
        "browser.artifact",
        "browser.approval",
    }
)
RUNTIME_REQUIRED_INBOUND_EVENTS = frozenset(
    {
        "connector_hello",
        "connector_context_list",
        "connector_subscribe_context",
        "connector_unsubscribe_context",
        "connector_send_message",
        "connector_message_queue_add",
        "connector_message_queue_remove",
        "connector_message_queue_send",
        "connector_browser_op_result",
        "connector_browser_control_result",
        "connector_browser_event",
        "connector_browser_artifact_chunk",
        "connector_browser_artifact_ack",
        "connector_browser_approval_decision",
        "connector_bridge_credential_control",
    }
)
RUNTIME_REQUIRED_OUTBOUND_EVENTS = frozenset(
    {
        "connector_context_snapshot",
        "connector_context_event",
        "connector_message_queue_updated",
        "connector_context_complete",
        "connector_context_error",
        "connector_browser_op",
        "connector_browser_control",
        "connector_browser_event_ack",
        "connector_browser_artifact_ack",
        "connector_browser_artifact_chunk",
        "connector_bridge_credential_status",
        "connector_bridge_forced_disconnect",
    }
)


@dataclass(frozen=True, slots=True, eq=False)
class BrowserBridgeTransportProfile:
    """One process-owned transport identity; equality is object identity."""

    profile_id: str
    principal_type: str
    handler_path: str
    handler_id: str
    namespace: str


PRODUCTION_BROWSER_BRIDGE_TRANSPORT = BrowserBridgeTransportProfile(
    profile_id="production",
    principal_type="browser_bridge",
    handler_path="plugins/_a0_connector/ws_connector",
    handler_id="ws_connector.WsConnector",
    namespace="/ws",
)
def require_browser_bridge_transport_profile(
    value: Any,
) -> BrowserBridgeTransportProfile:
    """Accept only the exact module-owned production constant."""

    if value is not PRODUCTION_BROWSER_BRIDGE_TRANSPORT:
        raise ValueError("invalid Browser bridge transport profile")
    return PRODUCTION_BROWSER_BRIDGE_TRANSPORT


def runtime_transport_profile_for_principal(
    principal: Any,
) -> BrowserBridgeTransportProfile:
    """Recognize a full-runtime principal for one fixed transport identity."""

    if (
        not isinstance(principal, WsPrincipal)
        or principal.scopes != RUNTIME_REQUIRED_SCOPES
        or principal.inbound_events != RUNTIME_REQUIRED_INBOUND_EVENTS
        or principal.outbound_events != RUNTIME_REQUIRED_OUTBOUND_EVENTS
        or type(principal.key_generation) is not int
        or principal.key_generation < 1
    ):
        raise ValueError("invalid Browser bridge runtime principal")
    return transport_profile_for_principal_identity(principal)


def transport_profile_for_principal_identity(
    principal: Any,
) -> BrowserBridgeTransportProfile:
    """Recognize only the fixed principal/handler identity, not capabilities."""

    profile = PRODUCTION_BROWSER_BRIDGE_TRANSPORT
    if (
        not isinstance(principal, WsPrincipal)
        or principal.principal_type != profile.principal_type
        or principal.handler_path != profile.handler_path
        or principal.handler_id != profile.handler_id
    ):
        raise ValueError("invalid Browser bridge transport principal")
    return profile


def require_runtime_transport_principal(
    principal: Any,
    profile: BrowserBridgeTransportProfile,
) -> WsPrincipal:
    """Require one full-runtime principal for the server-selected profile."""

    selected = require_browser_bridge_transport_profile(profile)
    if runtime_transport_profile_for_principal(principal) is not selected:
        raise ValueError("Browser bridge transport profile mismatch")
    return principal


def require_transport_principal_identity(
    principal: Any,
    profile: BrowserBridgeTransportProfile,
) -> WsPrincipal:
    """Require the fixed identity selected by composition, without adding scopes."""

    selected = require_browser_bridge_transport_profile(profile)
    if transport_profile_for_principal_identity(principal) is not selected:
        raise ValueError("Browser bridge transport profile mismatch")
    return principal
