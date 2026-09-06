"""First-open decisions are server-owned and never native challenge receipts."""
import asyncio
from dataclasses import replace
import json

import pytest

from plugins._browser.helpers.extension_first_open import FirstOpenSiteAuthority, FirstOpenDenied
from plugins._browser.helpers.extension_leases import ExtensionLeaseIndex
from plugins._browser.helpers.extension_runtime import ExtensionBrowserRuntime, ExtensionBrowserError
from plugins._a0_connector.helpers.browser_bridge_operations import BrowserBridgeOperationBroker
from test_browser_extension_runtime import _fixture, _authorize


def test_first_open_waits_for_explicit_choice_then_once_covers_only_resulting_lease():
    async def scenario():
        binding, policy = _fixture()
        authority = FirstOpenSiteAuthority()
        live = [True]
        current = lambda _binding: live[0]
        leases = ExtensionLeaseIndex(authorizer=current)
        sent = []
        active = [binding]

        async def sender(sid, event, payload, correlation, principal):
            sent.append(payload)
            keys = ("contract_version", "bridge_id", "load_generation_id", "context_id", "browser_session_id", "turn_id", "op_id", "action_id")
            result = {"browser_id": "tab-1", "tab_handle": "tab-1", "lease_id": "lease-1",
                      "origin": "https://example.com", "disposition": "ephemeral"} if payload["action"] == "open" else {}
            broker.settle_operation(principal=principal, connector_sid=sid, load_generation_id="load-1",
                payload={**{key: payload[key] for key in keys}, "ok": True, "result": result, "receipts": [], "artifacts": []})

        def observe(bound, call, result):
            if call.action == "open":
                leases.observe_open(bound, result, call.origin)
                authority.observe_open(bound, call.origin, result)

        broker = BrowserBridgeOperationBroker(sender=sender, authorizer=_authorize)
        runtime = ExtensionBrowserRuntime("context-1", "bridge-1", broker=broker,
            binding_factory=lambda: active[0], policy_repository=policy, server_instance_id="server-1",
            target_origin_resolver=leases.origin_for, binding_current=current, result_observer=observe,
            first_open_authority=authority)
        task = asyncio.create_task(runtime.call("open", "https://example.com/private?secret=canary"))
        await asyncio.sleep(0)
        pending = authority.list_pending(subject_id="single-user", context_id="context-1", bridge_id="bridge-1")
        assert len(pending) == 1 and pending[0]["action_class"] == "open" and sent == []
        assert "secret" not in json.dumps(pending)
        authority.decide(subject_id="single-user", challenge_id=pending[0]["challenge_id"], decision="allow_once")
        assert (await task)["tab_handle"] == "tab-1"
        assert sent[0]["policy"]["origin_grant_id"].startswith("open-grant-")
        assert policy.active_grant(server_instance_id="server-1", bridge_id="bridge-1", subject_id="single-user", origin="https://example.com") is None
        active[0] = replace(binding, op_id="op-2", action_id="action-2")
        assert await runtime.call("state", "tab-1") == {}
        assert authority.grant_for(active[0], "https://example.com") is None
        assert authority.grant_for(active[0], "https://example.com", "foreign-tab") is None
        assert authority.grant_for(replace(active[0], turn_id="another-turn"), "https://example.com", "tab-1") is None
        with pytest.raises(ExtensionBrowserError, match="TAB_NOT_OWNED"):
            await runtime.call("state", "foreign-tab")
        second = asyncio.create_task(runtime.call("open", "https://example.com/second"))
        await asyncio.sleep(0)
        assert len(sent) == 2
        authority.retire()
        with pytest.raises(ExtensionBrowserError, match="APPROVAL_DENIED"):
            await second
    asyncio.run(scenario())


def test_all_websites_bypasses_only_site_prompt_not_action_approval():
    async def scenario():
        binding, policy = _fixture()
        policy.set_site_mode(server_instance_id="server-1", bridge_id="bridge-1",
            subject_id="single-user", site_mode="allow_all_websites")
        authority = FirstOpenSiteAuthority()
        sent = []
        active = [binding]
        async def sender(sid, event, payload, correlation, principal):
            sent.append(payload)
            keys = ("contract_version", "bridge_id", "load_generation_id", "context_id", "browser_session_id", "turn_id", "op_id", "action_id")
            broker.settle_operation(principal=principal, connector_sid=sid, load_generation_id="load-1",
                payload={**{key: payload[key] for key in keys}, "ok": True, "result": {}, "receipts": [], "artifacts": []})
        broker = BrowserBridgeOperationBroker(sender=sender, authorizer=_authorize)
        runtime = ExtensionBrowserRuntime("context-1", "bridge-1", broker=broker,
            binding_factory=lambda: active[0], policy_repository=policy, server_instance_id="server-1",
            target_origin_resolver=lambda binding, handle: "https://one.example",
            binding_current=lambda binding: True, first_open_authority=authority)
        await runtime.call("open", "https://one.example/private")
        active[0] = replace(binding, op_id="second", action_id="second", turn_id="second-turn")
        await runtime.call("open", "https://two.example/private")
        assert len(sent) == 2 and authority.list_pending(subject_id="single-user", context_id="context-1", bridge_id="bridge-1") == ()
        assert sent[0]["policy"]["origin_grant_id"] != sent[1]["policy"]["origin_grant_id"]
        with pytest.raises(ExtensionBrowserError, match="APPROVAL_REQUIRED"):
            await runtime.call("click", "tab-1", "ref-1")
        assert len(sent) == 2
    asyncio.run(scenario())


def test_first_open_turn_scope_denial_staleness_expiry_and_cancellation():
    async def scenario():
        binding, _ = _fixture()
        now = [1000]
        current = [True]
        authority = FirstOpenSiteAuthority(clock_ms=lambda: now[0])
        def pending():
            return authority.list_pending(subject_id="single-user", context_id="context-1", bridge_id="bridge-1")
        async def begin():
            task = asyncio.create_task(authority.request(binding, "https://example.com", current=lambda b: current[0]))
            await asyncio.sleep(0)
            return task, pending()[0]["challenge_id"]
        task, challenge = await begin()
        with pytest.raises(FirstOpenDenied):
            authority.decide(subject_id="other-subject", challenge_id=challenge, decision="allow_turn")
        authority.decide(subject_id="single-user", challenge_id=challenge, decision="allow_turn")
        grant = await task
        assert authority.grant_for(replace(binding, op_id="next-op"), "https://example.com") == grant
        for field in ("connector_sid", "load_generation_id", "context_id", "browser_session_id", "turn_id"):
            assert authority.grant_for(replace(binding, **{field: "different"}), "https://example.com") is None
        assert authority.grant_for(replace(binding, principal=replace(binding.principal)), "https://example.com") is None
        assert authority.grant_for(binding, "https://elsewhere.example") is None
        current[0] = False
        assert authority.grant_for(binding, "https://example.com") is None
        current[0] = True
        task, challenge = await begin()
        authority.decide(subject_id="single-user", challenge_id=challenge, decision="deny")
        with pytest.raises(FirstOpenDenied):
            await task
        task, challenge = await begin()
        now[0] += 120_000
        assert pending() == ()
        with pytest.raises(FirstOpenDenied):
            await task
        task, challenge = await begin()
        task.cancel()
        with pytest.raises(asyncio.CancelledError):
            await task
        assert pending() == ()
    asyncio.run(scenario())


def test_protected_api_lists_and_decides_server_open_without_native_receipt(monkeypatch):
    from plugins._a0_connector.api import browser_bridge_site_authority as endpoint
    from types import SimpleNamespace
    async def scenario():
        binding, policy = _fixture()
        binding = replace(binding, principal=replace(binding.principal, subject_id=endpoint.SUBJECT_ID))
        authority = FirstOpenSiteAuthority(policy_repository=policy, server_instance_id="server-1")
        monkeypatch.setattr(endpoint, "selected_bridge", lambda context: "bridge-1")
        monkeypatch.setattr(endpoint, "current_first_open_authority", lambda: authority)
        monkeypatch.setattr(endpoint, "get_browser_bridge_site_authority_repository", lambda: SimpleNamespace(list_pending=lambda **kw: ()))
        task = asyncio.create_task(authority.request(binding, "https://example.com", current=lambda b: True))
        await asyncio.sleep(0)
        handler = object.__new__(endpoint.BrowserBridgeSiteAuthority)
        response = await handler._dispatch({"action": "list", "context_id": "context-1"})
        assert response.headers["Cache-Control"] == "no-store"
        listed = json.loads(response.get_data())
        challenge = listed["challenges"][0]
        assert challenge["action_class"] == "open" and listed["browser_control_ready"] is False
        rejected = await handler._dispatch({"action": "decide", "challenge_id": "native-challenge", "decision": "allow_site"})
        assert rejected.status_code == 400
        response = await handler._dispatch({"action": "decide", "challenge_id": challenge["challenge_id"], "decision": "allow_site"})
        assert response.status_code == 200
        assert json.loads(response.get_data())["control_id"].startswith("open-decision-")
        saved = policy.active_grant(server_instance_id="server-1", bridge_id="bridge-1", subject_id=endpoint.SUBJECT_ID, origin="https://example.com")
        assert await task == saved.grant_id
    asyncio.run(scenario())


def test_remember_persists_exact_origin_before_waking_and_survives_turn_retirement():
    async def scenario():
        binding, policy = _fixture()
        authority = FirstOpenSiteAuthority(policy_repository=policy, server_instance_id="server-1")
        task = asyncio.create_task(authority.request(binding, "https://example.com", current=lambda b: True))
        await asyncio.sleep(0)
        prompt = authority.list_pending(subject_id="single-user", context_id="context-1", bridge_id="bridge-1")[0]
        assert prompt["options"] == ["deny", "allow_once", "allow_turn", "allow_site"]
        original_save = policy._save
        def save(value):
            assert not task.done()
            original_save(value)
        policy._save = save
        authority.decide(subject_id="single-user", challenge_id=prompt["challenge_id"], decision="allow_site")
        saved = policy.active_grant(server_instance_id="server-1", bridge_id="bridge-1", subject_id="single-user", origin="https://example.com")
        assert saved is not None and await task == saved.grant_id
        authority.retire()
        # The next chat/turn reads the normal durable policy, not a stale request.
        assert policy.active_grant(server_instance_id="server-1", bridge_id="bridge-1", subject_id="single-user", origin="https://example.com") == saved
        for override in ({"origin": "https://sub.example.com"}, {"bridge_id": "other-bridge"}, {"subject_id": "other-subject"}, {"server_instance_id": "other-server"}):
            scope = dict(server_instance_id="server-1", bridge_id="bridge-1", subject_id="single-user", origin="https://example.com")
            assert policy.active_grant(**(scope | override)) is None
    asyncio.run(scenario())


def test_remember_save_failure_or_stale_selection_never_releases_grant():
    async def scenario():
        for fail_save in (True, False):
            binding, policy = _fixture()
            live = [True]
            authority = FirstOpenSiteAuthority(policy_repository=policy, server_instance_id="server-1")
            task = asyncio.create_task(authority.request(binding, "https://example.com", current=lambda b: live[0]))
            await asyncio.sleep(0)
            prompt = authority.list_pending(subject_id="single-user", context_id="context-1", bridge_id="bridge-1")[0]
            original_save = policy._save
            def save(value):
                if fail_save:
                    raise OSError("synthetic storage unavailable")
                original_save(value)
                live[0] = False
            policy._save = save
            with pytest.raises(Exception):
                authority.decide(subject_id="single-user", challenge_id=prompt["challenge_id"], decision="allow_site")
            assert authority.grant_for(binding, "https://example.com") is None
            authority.retire()
            with pytest.raises(FirstOpenDenied):
                await task
    asyncio.run(scenario())
