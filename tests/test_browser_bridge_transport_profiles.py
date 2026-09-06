"""Production transport identity and retired-channel rejection."""
from dataclasses import replace

import pytest

from helpers.ws_principal import WsPrincipal
from plugins._a0_connector.helpers.browser_bridge_transport import (
    PRODUCTION_BROWSER_BRIDGE_TRANSPORT as PROFILE,
    RUNTIME_REQUIRED_SCOPES,
    RUNTIME_REQUIRED_INBOUND_EVENTS,
    RUNTIME_REQUIRED_OUTBOUND_EVENTS,
    require_browser_bridge_transport_profile,
    runtime_transport_profile_for_principal,
    transport_profile_for_principal_identity,
)


def principal():
    return WsPrincipal(
        principal_type=PROFILE.principal_type, principal_id="bridge-1",
        subject_id="user-1", scopes=RUNTIME_REQUIRED_SCOPES,
        handler_path=PROFILE.handler_path, handler_id=PROFILE.handler_id,
        inbound_events=RUNTIME_REQUIRED_INBOUND_EVENTS,
        outbound_events=RUNTIME_REQUIRED_OUTBOUND_EVENTS, key_generation=1,
    )


def test_only_server_owned_production_profile_is_accepted():
    assert require_browser_bridge_transport_profile(PROFILE) is PROFILE
    assert runtime_transport_profile_for_principal(principal()) is PROFILE
    for forged in (replace(PROFILE), "production", None,
                   replace(PROFILE, profile_id="local-development")):
        with pytest.raises(ValueError):
            require_browser_bridge_transport_profile(forged)


def test_retired_development_identity_is_rejected_even_with_full_scopes():
    retired = replace(principal(), principal_type="browser_bridge_development",
        handler_path="plugins/_a0_connector/ws_browser_development",
        handler_id="ws_browser_development.WsBrowserDevelopment")
    for validate in (transport_profile_for_principal_identity,
                     runtime_transport_profile_for_principal):
        with pytest.raises(ValueError):
            validate(retired)


def test_identity_alone_does_not_grant_runtime_capabilities():
    incomplete = replace(principal(), scopes=frozenset({"bridge.connect"}),
                         inbound_events=frozenset({"connector_hello"}),
                         outbound_events=frozenset())
    assert transport_profile_for_principal_identity(incomplete) is PROFILE
    with pytest.raises(ValueError):
        runtime_transport_profile_for_principal(incomplete)
