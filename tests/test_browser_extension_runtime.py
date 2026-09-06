import asyncio
from dataclasses import replace
from copy import deepcopy

import pytest

from helpers.ws_principal import WsPrincipal
from plugins._a0_connector.helpers.browser_bridge_operations import (
    BridgeAuthorization, BrowserBridgeOperationBroker, OperationBinding,
)
from plugins._a0_connector.helpers.browser_bridge_policy import BrowserBridgePolicyRepository
from plugins._browser.helpers.extension_runtime import (
    ExtensionBrowserError, ExtensionBrowserRuntime, encode_extension_call,
)


def _fixture():
    principal = WsPrincipal(
        principal_type="browser_bridge", principal_id="bridge-1", subject_id="single-user",
        scopes=frozenset({"browser.operate", "browser.control"}),
        handler_path="plugins/_a0_connector/ws_connector", handler_id="ws_connector.WsConnector",
        inbound_events=frozenset({"connector_browser_op_result", "connector_browser_control_result"}),
        outbound_events=frozenset({"connector_browser_op", "connector_browser_control"}), key_generation=1,
    )
    binding = OperationBinding(principal, "sid-1", "load-1", "context-1", "session-1", "turn-1", "action-1", "op-1")
    stored = [None]
    policy = BrowserBridgePolicyRepository(load=lambda: deepcopy(stored[0]), save=lambda value: stored.__setitem__(0, deepcopy(value)))
    return binding, policy


def _authorize(binding):
    return BridgeAuthorization(
        binding.principal, binding.connector_sid, binding.load_generation_id, 1,
        frozenset({"browser_extension_bridge_v1", "connector_browser_control"}),
        frozenset({"open", "list", "state", "content", "navigate", "scroll", "ensure", "status"}),
        frozenset({"tab_leases_v1", "tab_groups_v1", "semantic_dom_v1", "cursor_v1"}),
    )


def _allow(policy, origin="https://example.com"):
    return policy.allow(server_instance_id="server-1", bridge_id="bridge-1", subject_id="single-user", origin=origin)


def _runtime(binding, policy, sender, *, binding_factory=None):
    broker = BrowserBridgeOperationBroker(sender=sender, authorizer=_authorize)
    runtime = ExtensionBrowserRuntime(
        "context-1", "bridge-1", broker=broker,
        binding_factory=binding_factory or (lambda: binding), policy_repository=policy,
        server_instance_id="server-1", target_origin_resolver=lambda _binding, handle: "https://example.com" if handle == "a0t1.load.tab" else None,
    )
    return runtime, broker


def test_foreground_preference_is_server_owned_action_scoped_and_fail_quiet():
    binding, policy = _fixture()
    runtime, _ = _runtime(binding, policy, None)
    assert runtime._operation_display("open") == {"cursor": False, "foreground": False}
    enabled = [True]
    runtime._foreground_preference = lambda: enabled[0]
    for action in ("open", "hover", "click", "type", "scroll", "upload_file"):
        assert runtime._operation_display(action)["foreground"] is True
    for action in ("list", "state", "content", "navigate", "status", "ensure", "screenshot"):
        assert runtime._operation_display(action)["foreground"] is False
    for disabled in (False, None, 1, "true"):
        enabled[0] = disabled
        assert runtime._operation_display("scroll") == {"cursor": True, "foreground": False}
    def unavailable():
        raise RuntimeError("settings unavailable")
    runtime._foreground_preference = unavailable
    assert runtime._operation_display("open")["foreground"] is False
    with pytest.raises(ExtensionBrowserError):
        encode_extension_call("open", ("https://example.com",), {"foreground": True})


def test_authorized_open_dispatch_projects_latest_foreground_preference():
    from plugins._browser.helpers.extension_first_open import FirstOpenSiteAuthority
    async def scenario():
        binding, policy = _fixture()
        authority = FirstOpenSiteAuthority()
        sent = []
        enabled = [False]
        async def sender(sid, _event, payload, _correlation, principal):
            sent.append(payload)
            keys = ("contract_version", "bridge_id", "load_generation_id", "context_id", "browser_session_id", "turn_id", "op_id", "action_id")
            broker.settle_operation(principal=principal, connector_sid=sid, load_generation_id="load-1", payload={
                **{key: payload[key] for key in keys}, "ok": True,
                "result": {}, "receipts": [], "artifacts": [],
            })
        runtime, broker = _runtime(binding, policy, sender)
        runtime._foreground_preference = lambda: enabled[0]
        runtime._first_open_authority = authority
        runtime._binding_current = lambda _binding: True
        task = asyncio.create_task(runtime.call("open", "https://example.com"))
        await asyncio.sleep(0)
        pending = authority.list_pending(subject_id="single-user", context_id="context-1", bridge_id="bridge-1")
        assert len(pending) == 1 and sent == []
        # A user's preference change during the real approval wait is honored.
        enabled[0] = True
        authority.decide(subject_id="single-user", challenge_id=pending[0]["challenge_id"], decision="allow_once")
        await task
        assert sent[0]["display"] == {"cursor": False, "foreground": True}
        assert sent[0]["policy"]["origin_grant_id"] is not None
    asyncio.run(scenario())


def test_canonical_codec_rejects_legacy_fields_and_unimplemented_actions():
    call = encode_extension_call("open", ("HTTPS://EXAMPLE.COM:443/path?q=1",), {})
    assert call.args == {"url": "https://example.com/path?q=1", "disposition": "ephemeral"}
    assert call.target is None and call.origin == "https://example.com"
    assert "tab_groups_v1" in call.required_capabilities
    for method, args, kwargs in (
        ("type_submit", ("tab", "ref", "text"), {}),
        ("content", ("tab", {"selector": "input"}), {}),
        ("state", (123,), {}),
        ("list", (), {"include_content": True}),
        ("open", ("https://user:secret@example.com/",), {}),
        ("open", ("http://127.1/",), {}),
        ("open", ("https://example.com/",), {"policy": {"origin_grant_id": "forged"}}),
    ):
        with pytest.raises(ExtensionBrowserError):
            encode_extension_call(method, args, kwargs)


def test_hover_accepts_browser_tool_ref_form_but_never_coordinates():
    call = encode_extension_call("hover", ("a0t1.load.tab",), {
        "ref": "ref-1", "x": 0.0, "y": 0.0, "offset_x": 0.0, "offset_y": 0.0,
    })
    assert call.action == "hover" and call.args == {"ref": "ref-1"}
    assert "trusted_input_v1" in call.required_capabilities
    for kwargs in ({"ref": "ref-1", "x": 1}, {"ref": "ref-1", "y": False},
                   {"ref": "ref-1", "selector": "button"}, {"ref": None}):
        with pytest.raises(ExtensionBrowserError):
            encode_extension_call("hover", ("a0t1.load.tab",), kwargs)


def test_click_requires_current_action_authority_and_never_accepts_a_risk_downgrade():
    call = encode_extension_call("click", ("a0t1.load.tab", "ref-1"), {})
    assert call.args == {"ref": "ref-1", "expected_action_class": "unknown"}
    with pytest.raises(ExtensionBrowserError):
        encode_extension_call("click", ("a0t1.load.tab", "ref-1"), {"expected_action_class": "reversible_input"})

    async def scenario():
        binding, policy = _fixture()
        _allow(policy)
        sent = []
        async def sender(*args):
            sent.append(args)
        runtime, _ = _runtime(binding, policy, sender)
        with pytest.raises(ExtensionBrowserError, match="APPROVAL_REQUIRED"):
            await runtime.call("click", "a0t1.load.tab", "ref-1")
        assert sent == []
    asyncio.run(scenario())


def test_type_codec_binds_exact_utf8_and_requires_action_authority():
    import hashlib

    text = "Private \U0001f511\nsecond line"
    call = encode_extension_call("type", ("a0t1.load.tab", "ref-1", text), {})
    assert call.args == {"ref": "ref-1", "text": text, "text_sha256": hashlib.sha256(text.encode()).hexdigest(),
                         "expected_action_class": "sensitive_input"}
    assert "trusted_input_v1" in call.required_capabilities
    for invalid in ("", "\x00", "\r", "\ud800", "\U0001f511" * 8193, None):
        with pytest.raises(ExtensionBrowserError, match="INVALID_STATE"):
            encode_extension_call("type", ("a0t1.load.tab", "ref-1", invalid), {})
    with pytest.raises(ExtensionBrowserError):
        encode_extension_call("type", ("a0t1.load.tab", "ref-1", text), {"submit": True})

    async def scenario():
        binding, policy = _fixture()
        sent = []
        async def sender(*args):
            sent.append(args)
        runtime, _ = _runtime(binding, policy, sender)
        with pytest.raises(ExtensionBrowserError, match="APPROVAL_REQUIRED"):
            await runtime.call("type", "a0t1.load.tab", "ref-1", text)
        assert sent == []
    asyncio.run(scenario())


def test_cross_origin_request_requires_challenge_lane_and_uses_source_permission():
    async def scenario():
        binding, policy = _fixture()
        source_grant = _allow(policy)
        sent = []

        async def sender(sid, _event, payload, _correlation, principal):
            sent.append(payload)
            keys = ("contract_version", "bridge_id", "load_generation_id", "context_id", "browser_session_id", "turn_id", "op_id", "action_id")
            broker.settle_operation(principal=principal, connector_sid=sid, load_generation_id="load-1", payload={
                **{key: payload[key] for key in keys}, "ok": False, "code": "APPROVAL_DENIED", "error": "Site request denied",
                "error_data": {"outcome": "not_applied", "retryable": False, "details": {}},
            })

        broker = BrowserBridgeOperationBroker(sender=sender, authorizer=_authorize)
        runtime = ExtensionBrowserRuntime(
            "context-1", "bridge-1", broker=broker, binding_factory=lambda: binding,
            policy_repository=policy, server_instance_id="server-1",
            target_origin_resolver=lambda _binding, _handle: "https://example.com",
            site_challenge_ready=lambda _binding: True,
        )
        with pytest.raises(ExtensionBrowserError) as denied:
            await runtime.call("navigate", "a0t1.load.tab", "https://next.example/path")
        assert denied.value.code == "APPROVAL_DENIED"
        assert len(sent) == 1 and sent[0]["policy"]["origin_grant_id"] == source_grant.grant_id
        assert sent[0]["args"] == {"url": "https://next.example/path"}

    asyncio.run(scenario())


def test_browser_call_uses_exact_server_binding_and_saved_origin_grant():
    async def scenario():
        binding, policy = _fixture()
        grant = _allow(policy)
        sent = []

        async def sender(sid, event, payload, correlation, principal):
            sent.append(payload)
            keys = ("contract_version", "bridge_id", "load_generation_id", "context_id", "browser_session_id", "turn_id", "op_id", "action_id")
            broker.settle_operation(
                principal=principal, connector_sid=sid, load_generation_id="load-1",
                payload={**{key: payload[key] for key in keys}, "ok": True, "result": {"browser_id": "a0t1.load.tab"}, "receipts": [], "artifacts": []},
            )

        runtime, broker = _runtime(binding, policy, sender)
        assert await runtime.call("open", "https://example.com/page") == {"browser_id": "a0t1.load.tab"}
        assert sent[0]["policy"] == {"origin_grant_id": grant.grant_id, "action_grant_id": None}
        assert sent[0]["context_id"] == "context-1"
        assert sent[0]["display"] == {"cursor": False, "foreground": False}
        assert "profile_mode" not in sent[0] and "cdp_endpoint" not in sent[0]

    asyncio.run(scenario())


def test_policy_and_target_isolation_deny_without_dispatch():
    async def scenario():
        binding, policy = _fixture()
        sent = []

        async def sender(*args):
            sent.append(args)

        runtime, _ = _runtime(binding, policy, sender)
        with pytest.raises(ExtensionBrowserError, match="ORIGIN_BLOCKED"):
            await runtime.call("open", "https://example.com/")
        _allow(policy)
        _allow(policy, "https://another.example")
        with pytest.raises(ExtensionBrowserError, match="APPROVAL_REQUIRED"):
            await runtime.call("navigate", "a0t1.load.tab", "https://another.example/")
        with pytest.raises(ExtensionBrowserError, match="TAB_NOT_OWNED"):
            await runtime.call("content", "foreign-tab", None)
        mismatched, _ = _runtime(binding, policy, sender, binding_factory=lambda: replace(binding, context_id="other-context"))
        with pytest.raises(ExtensionBrowserError, match="SCOPE_DENIED"):
            await mismatched.call("list", include_content=False)
        assert sent == []

    asyncio.run(scenario())


def test_revoked_policy_between_enqueue_and_send_blocks_the_effect():
    async def scenario():
        binding, policy = _fixture()
        _allow(policy)
        sent = []

        async def sender(*args):
            sent.append(args)

        runtime, _ = _runtime(binding, policy, sender)
        task = asyncio.create_task(runtime.call("open", "https://example.com/"))
        await asyncio.sleep(0)
        policy.revoke(server_instance_id="server-1", bridge_id="bridge-1", subject_id="single-user", origin="https://example.com")
        with pytest.raises(ExtensionBrowserError, match="ORIGIN_BLOCKED"):
            await task
        assert sent == []

    asyncio.run(scenario())
