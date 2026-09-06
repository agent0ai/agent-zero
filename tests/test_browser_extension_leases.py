from dataclasses import replace

import pytest

from helpers.ws_principal import WsPrincipal
from plugins._a0_connector.helpers.browser_bridge_operations import OperationBinding, TurnBinding
from plugins._browser.helpers.extension_leases import ExtensionLeaseIndex, ExtensionLeaseError


def test_correlated_open_index_is_current_route_session_scoped_and_bounded():
    principal = WsPrincipal(
        principal_type="browser_bridge", principal_id="bridge", subject_id="user",
        scopes=frozenset({"browser.operate"}), handler_path="plugins/_a0_connector/ws_connector",
        handler_id="ws_connector.WsConnector", inbound_events=frozenset(),
        outbound_events=frozenset(), key_generation=1,
    )
    binding = OperationBinding(principal, "sid", "generation", "context", "session", "turn", "action", "op")
    current = [True]
    index = ExtensionLeaseIndex(authorizer=lambda _: current[0], max_leases=1)
    result = {"lease_id": "lease", "tab_handle": "tab", "browser_id": "tab", "origin": "https://example.com", "disposition": "ephemeral", "title": "not retained"}
    lease = index.observe_open(binding, result, "https://example.com")
    assert not hasattr(lease, "title")
    assert index.origin_for(binding, "tab") == "https://example.com"
    for other in (
        replace(binding, principal=replace(principal)), replace(binding, connector_sid="new-sid"),
        replace(binding, load_generation_id="new-generation"), replace(binding, context_id="other"),
        replace(binding, browser_session_id="other"), replace(binding, turn_id="other"),
    ):
        assert index.origin_for(other, "tab") is None
    with pytest.raises(ExtensionLeaseError):
        index.observe_open(binding, {**result, "origin": "https://other.example"}, "https://example.com")
    with pytest.raises(ExtensionLeaseError):
        index.observe_open(binding, {**result, "lease_id": "second", "tab_handle": "second-tab", "browser_id": "second-tab"}, "https://example.com")
    navigation = {key: result[key] for key in ("lease_id", "tab_handle", "browser_id", "origin")}
    assert index.document_for(binding, "tab") is None
    content = {key: result[key] for key in ("lease_id", "tab_handle", "browser_id")}
    content.update(document_id="document-1", document_epoch="1", title="not authority", text="not retained",
                   nodes=[{"ref": "doc:1:opaque", "role": "button", "name": "not authority"}], truncated=False)
    index.observe_content(binding, "tab", content)
    document = index.document_for(binding, "tab")
    assert document.document_id == "document-1" and document.document_epoch == 1
    assert document.refs == frozenset({"doc:1:opaque"}) and not hasattr(document, "text")
    for changes in ({"document_id": "other-document"}, {"document_epoch": "0"},
                    {"nodes": content["nodes"] * 2}, {"document_epoch": "9007199254740992"}):
        with pytest.raises(ExtensionLeaseError):
            index.observe_content(binding, "tab", {**content, **changes})
    navigation["origin"] = "https://next.example"
    index.observe_navigation(binding, "tab", navigation, "https://next.example")
    assert index.origin_for(binding, "tab") == "https://next.example"
    assert index.document_for(binding, "tab") is None
    with pytest.raises(ExtensionLeaseError):
        index.observe_navigation(binding, "tab", {**navigation, "lease_id": "other"}, "https://next.example")
    current[0] = False
    assert index.origin_for(binding, "tab") is None
    current[0] = True
    index.retire_turn(TurnBinding(principal, "sid", "generation", "context", "session", "turn"))
    assert index.origin_for(binding, "tab") is None
    index.observe_open(binding, result, "https://example.com")
    index.invalidate(principal=principal, connector_sid="sid", load_generation_id="generation")
    assert index.origin_for(binding, "tab") is None
