import asyncio
import hashlib
import json
from dataclasses import replace

import pytest

from helpers.ws_principal import WsPrincipal
from plugins._a0_connector.helpers.browser_bridge_operations import (
    BridgeAuthorization,
    BrowserBridgeBrokerError,
    BrowserBridgeOperationBroker,
    CONTROL_EVENT,
    OPERATION_EVENT,
    OperationBinding,
    SettlementStatus,
    TurnBinding,
)


def _principal(**changes):
    values = {
        "principal_type": "browser_bridge",
        "principal_id": "bridge-1",
        "subject_id": "single-user",
        "scopes": frozenset({"bridge.connect", "browser.operate", "browser.control"}),
        "handler_path": "plugins/_a0_connector/ws_connector",
        "handler_id": "ws_connector.WsConnector",
        "inbound_events": frozenset(
            {"connector_browser_op_result", "connector_browser_control_result"}
        ),
        "outbound_events": frozenset({OPERATION_EVENT, CONTROL_EVENT}),
        "key_generation": 3,
    }
    values.update(changes)
    return WsPrincipal(**values)


def _binding(principal=None, **changes):
    values = {
        "principal": principal or _principal(),
        "connector_sid": "sid-1",
        "load_generation_id": "load-1",
        "context_id": "context-1",
        "browser_session_id": "session-1",
        "turn_id": "turn-1",
        "action_id": "action-1",
        "op_id": "op-1",
    }
    values.update(changes)
    return OperationBinding(**values)


def _authorization(binding, *, actions=("click", "state"), features=("cursor_v1",)):
    return BridgeAuthorization(
        principal=binding.principal,
        connector_sid=binding.connector_sid,
        load_generation_id=binding.load_generation_id,
        contract_version=1,
        outer_features=frozenset(
            {"browser_extension_bridge_v1", "connector_browser_control"}
        ),
        actions=frozenset(actions),
        features=frozenset(features),
    )


async def _start(broker, binding, *, action="click", timeout_ms=5_000):
    args = {"ref": "frame0:node24"}
    if action == "click":
        args["expected_action_class"] = "unknown"
    return await broker.begin_operation(
        binding,
        action=action,
        target={"tab_handle": "a0t1.generation.lease"},
        args=args,
        timeout_ms=timeout_ms,
        required_capabilities=[action, "cursor_v1"],
        policy={"origin_grant_id": "grant-1"},
        display={"cursor": True, "foreground": False},
    )


def test_dispatch_barrier_waits_for_sender_and_survives_waiter_cancellation():
    async def scenario():
        binding = _binding()
        entered, release = asyncio.Event(), asyncio.Event()

        async def sender(*_args):
            entered.set()
            await release.wait()

        broker = BrowserBridgeOperationBroker(authorizer=lambda *_args, **_kwargs: _authorization(binding), sender=sender)
        ticket = await _start(broker, binding)
        await entered.wait()
        waiter = asyncio.create_task(broker.wait_dispatched(ticket))
        await asyncio.sleep(0)
        assert not waiter.done()
        waiter.cancel()
        with pytest.raises(asyncio.CancelledError):
            await waiter
        release.set()
        await broker.wait_dispatched(ticket)
        broker.disconnect(principal=binding.principal, connector_sid=binding.connector_sid, load_generation_id=binding.load_generation_id)
        with pytest.raises(BrowserBridgeBrokerError):
            await broker.wait_dispatched(ticket)

    asyncio.run(scenario())


def _success(payload):
    keys = (
        "contract_version", "bridge_id", "load_generation_id", "context_id",
        "browser_session_id", "turn_id", "op_id", "action_id",
    )
    result = {key: payload[key] for key in keys}
    result.update(ok=True, result={"value": 7}, receipts=[], artifacts=[])
    return result


def _control_success(payload):
    keys = (
        "contract_version", "method", "bridge_id", "load_generation_id",
        "context_id", "browser_session_id", "turn_id", "control_id",
    )
    result = {key: payload[key] for key in keys}
    if payload["method"] == "browser.cancel":
        result.update(op_id=payload["op_id"], action_id=payload["action_id"])
    result.update(ok=True, result={"contract_version": 1, "status": "canceled"})
    return result


def test_site_control_matches_pending_navigation_hash_and_rechecks_decision():
    async def scenario():
        sent = []
        allowed = True

        async def sender(*args):
            sent.append(args)

        binding = _binding()
        broker = BrowserBridgeOperationBroker(
            sender=sender, authorizer=lambda candidate: _authorization(candidate, actions=("navigate",)),
        )
        ticket = await broker.begin_operation(
            binding, action="navigate", target={"tab_handle": "tab-1"}, args={"url": "https://next.example/path?q=private"},
            timeout_ms=5_000, required_capabilities=["navigate"], policy={"origin_grant_id": "source-grant"},
            display={"cursor": True, "foreground": False},
        )
        expected = {"action": "navigate", "target": {"tabHandle": "tab-1"}, "context_id": binding.context_id,
                    "browser_session_id": binding.browser_session_id, "turn_id": binding.turn_id,
                    "args": {"url": "https://next.example/path?q=private"}, "display": {"cursor": True, "foreground": False}}
        assert ticket.canonical_parameter_hash == hashlib.sha256(json.dumps(expected, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()).hexdigest()
        assert ticket.destination_origin == "https://next.example"
        resolution = {"challenge_id": "challenge-1", "tab_handle": "tab-1", "document_id": None, "document_epoch": 0,
                      "canonical_parameter_hash": ticket.canonical_parameter_hash, "target_fingerprint": "a" * 64,
                      "origin": ticket.destination_origin, "action_class": "navigate", "decision": "deny", "grant": None}
        control = await broker.begin_site_resolution(ticket, control_id="control-1", resolution=resolution,
                                                     authorization_current=lambda: allowed)
        await asyncio.sleep(0)
        payload = next(item[2] for item in sent if item[1] == CONTROL_EVENT)
        response = _control_success(payload)
        response.update(op_id=binding.op_id, action_id=binding.action_id,
                        result={"contract_version": 1, "control_id": "control-1", "challenge_id": "challenge-1", "status": "resolved", "decision": "deny"})
        assert broker.settle_control(principal=binding.principal, connector_sid=binding.connector_sid,
                                     load_generation_id=binding.load_generation_id, payload=response) == SettlementStatus.SETTLED
        assert (await broker.wait_control(control)).result == response["result"]
        second = await broker.begin_site_resolution(ticket, control_id="control-2", resolution=resolution,
                                                    authorization_current=lambda: allowed)
        allowed = False
        await asyncio.sleep(0)
        assert not (await broker.wait_control(second)).ok
        assert not any(item[2].get("control_id") == "control-2" for item in sent)
        broker.disconnect(principal=binding.principal, connector_sid=binding.connector_sid,
                          load_generation_id=binding.load_generation_id)

    asyncio.run(scenario())


def test_operation_dispatch_is_canonical_bound_and_exactly_settled():
    async def scenario():
        sent = []

        async def sender(sid, event, data, correlation, principal):
            sent.append((sid, event, data, correlation, principal))

        binding = _binding()
        broker = BrowserBridgeOperationBroker(
            sender=sender, authorizer=lambda candidate: _authorization(candidate)
        )
        ticket = await _start(broker, binding)
        await asyncio.sleep(0)

        assert len(sent) == 1
        sid, event, data, correlation, principal = sent[0]
        assert (sid, event, correlation, principal) == (
            "sid-1", OPERATION_EVENT, "op-1", binding.principal
        )
        assert data == {
            "contract_version": 1,
            "bridge_id": "bridge-1",
            "load_generation_id": "load-1",
            "op_id": "op-1",
            "action_id": "action-1",
            "context_id": "context-1",
            "browser_session_id": "session-1",
            "turn_id": "turn-1",
            "action": "click",
            "target": {"tab_handle": "a0t1.generation.lease"},
            "args": {
                "ref": "frame0:node24",
                "expected_action_class": "unknown",
            },
            "timeout_ms": 5_000,
            "required_capabilities": ["click", "cursor_v1"],
            "policy": {"origin_grant_id": "grant-1", "action_grant_id": None},
            "display": {"cursor": True, "foreground": False},
        }
        assert "connector_sid" not in data
        assert "key_generation" not in data

        assert broker.settle_operation(
            principal=principal,
            connector_sid=sid,
            load_generation_id="load-1",
            payload=_success(data),
        ) == SettlementStatus.SETTLED
        completion = await broker.wait_operation(ticket)
        assert completion.ok is True
        assert completion.result == {"value": 7}
        assert broker.settle_operation(
            principal=principal,
            connector_sid=sid,
            load_generation_id="load-1",
            payload=_success(data),
        ) == SettlementStatus.DUPLICATE

    asyncio.run(scenario())


def test_authority_and_capabilities_fail_before_send_or_registry_insertion():
    async def scenario():
        sent = []

        async def sender(*args):
            sent.append(args)

        binding = _binding()
        broker = BrowserBridgeOperationBroker(
            sender=sender,
            authorizer=lambda candidate: replace(
                _authorization(candidate), features=frozenset()
            ),
        )
        with pytest.raises(BrowserBridgeBrokerError) as exc:
            await _start(broker, binding)
        assert exc.value.code == "UNSUPPORTED_CAPABILITY"
        assert exc.value.outcome == "not_applied"
        assert broker.pending_operation_count == 0

        stale = BrowserBridgeOperationBroker(
            sender=sender,
            authorizer=lambda candidate: replace(
                _authorization(candidate), load_generation_id="stale-load"
            ),
        )
        with pytest.raises(BrowserBridgeBrokerError) as exc:
            await _start(stale, binding)
        assert exc.value.code == "SCOPE_DENIED"
        await asyncio.sleep(0)
        assert sent == []

    asyncio.run(scenario())


def test_every_operation_identity_dimension_is_exact_and_mismatch_stays_pending():
    async def scenario():
        sent = []

        async def sender(_sid, _event, data, _correlation, _principal):
            sent.append(data)

        binding = _binding()
        broker = BrowserBridgeOperationBroker(
            sender=sender, authorizer=lambda candidate: _authorization(candidate)
        )
        ticket = await _start(broker, binding)
        await asyncio.sleep(0)
        valid = _success(sent[0])

        mutations = {
            "bridge_id": "other-bridge",
            "load_generation_id": "other-load",
            "context_id": "other-context",
            "browser_session_id": "other-session",
            "turn_id": "other-turn",
            "action_id": "other-action",
        }
        for key, value in mutations.items():
            candidate = dict(valid)
            candidate[key] = value
            assert broker.settle_operation(
                principal=binding.principal,
                connector_sid=binding.connector_sid,
                load_generation_id=binding.load_generation_id,
                payload=candidate,
            ) == SettlementStatus.MISMATCH
            assert broker.pending_operation_count == 1

        equal_but_unbound_principal = replace(binding.principal)
        assert broker.settle_operation(
            principal=equal_but_unbound_principal,
            connector_sid=binding.connector_sid,
            load_generation_id=binding.load_generation_id,
            payload=valid,
        ) == SettlementStatus.MISMATCH
        assert broker.settle_operation(
            principal=binding.principal,
            connector_sid="another-sid",
            load_generation_id=binding.load_generation_id,
            payload=valid,
        ) == SettlementStatus.MISMATCH

        invalid = dict(valid)
        invalid["unexpected"] = "data"
        assert broker.settle_operation(
            principal=binding.principal,
            connector_sid=binding.connector_sid,
            load_generation_id=binding.load_generation_id,
            payload=invalid,
        ) == SettlementStatus.MISMATCH
        assert not ticket._future.done()
        assert broker.settle_operation(
            principal=binding.principal,
            connector_sid=binding.connector_sid,
            load_generation_id=binding.load_generation_id,
            payload=valid,
        ) == SettlementStatus.SETTLED
        assert (await broker.wait_operation(ticket)).ok

    asyncio.run(scenario())


def test_disconnect_is_generation_bound_and_mutations_become_unknown():
    async def scenario():
        async def sender(*_args):
            return None

        principal = _principal()
        broker = BrowserBridgeOperationBroker(
            sender=sender,
            authorizer=lambda candidate: _authorization(
                candidate, actions=("click", "state")
            ),
        )
        mutation = await _start(broker, _binding(principal, op_id="op-m", action_id="action-m"))
        read = await _start(
            broker,
            _binding(principal, op_id="op-r", action_id="action-r"),
            action="state",
        )
        assert broker.disconnect(
            principal=principal, connector_sid="sid-1", load_generation_id="stale"
        ).operations == 0
        assert broker.pending_operation_count == 2

        summary = broker.disconnect(
            principal=principal, connector_sid="sid-1", load_generation_id="load-1"
        )
        assert summary.operations == 2
        mutation_result, read_result = await asyncio.gather(
            broker.wait_operation(mutation), broker.wait_operation(read)
        )
        assert (mutation_result.code, mutation_result.outcome, mutation_result.retryable) == (
            "OUTCOME_UNKNOWN", "unknown", False
        )
        assert (read_result.code, read_result.outcome, read_result.retryable) == (
            "CONNECTION_LOST", "not_applied", True
        )

    asyncio.run(scenario())


def test_expiry_is_deterministic_and_conservative_by_effect_class():
    async def scenario():
        now = [10_000]

        async def sender(*_args):
            return None

        broker = BrowserBridgeOperationBroker(
            sender=sender,
            authorizer=lambda candidate: _authorization(
                candidate, actions=("click", "state")
            ),
            clock_ms=lambda: now[0],
        )
        mutation = await _start(
            broker, _binding(op_id="op-m", action_id="action-m"), timeout_ms=30
        )
        read = await _start(
            broker,
            _binding(op_id="op-r", action_id="action-r"),
            action="state",
            timeout_ms=30,
        )
        assert broker.expire(10_029).operations == 0
        assert broker.expire(10_030).operations == 2
        mutation_result, read_result = await asyncio.gather(
            broker.wait_operation(mutation), broker.wait_operation(read)
        )
        assert mutation_result.code == "OUTCOME_UNKNOWN"
        assert read_result.code == "DEADLINE_EXCEEDED"
        assert read_result.retryable is True

    asyncio.run(scenario())


def test_waiter_cancellation_does_not_cancel_operation_or_its_receipt():
    async def scenario():
        sent = []

        async def sender(_sid, _event, data, _correlation, _principal):
            sent.append(data)

        binding = _binding()
        broker = BrowserBridgeOperationBroker(
            sender=sender, authorizer=lambda candidate: _authorization(candidate)
        )
        ticket = await _start(broker, binding)
        waiter = asyncio.create_task(broker.wait_operation(ticket))
        waiter.cancel()
        with pytest.raises(asyncio.CancelledError):
            await waiter
        await asyncio.sleep(0)
        assert broker.pending_operation_count == 1
        assert ticket._future.cancelled() is False
        assert broker.settle_operation(
            principal=binding.principal,
            connector_sid=binding.connector_sid,
            load_generation_id=binding.load_generation_id,
            payload=_success(sent[0]),
        ) == SettlementStatus.SETTLED
        assert (await broker.wait_operation(ticket)).ok

    asyncio.run(scenario())


def test_cancel_and_finalize_use_exact_control_bindings_and_correlation():
    async def scenario():
        sent = []

        async def sender(sid, event, data, correlation, principal):
            sent.append((sid, event, data, correlation, principal))

        principal = _principal()
        broker = BrowserBridgeOperationBroker(
            sender=sender, authorizer=lambda candidate: _authorization(candidate)
        )
        operation = await _start(broker, _binding(principal))
        cancel = await broker.begin_cancel(
            operation, control_id="control-cancel", reason="turn stopped", timeout_ms=1_000
        )
        turn = TurnBinding(
            principal=principal,
            connector_sid="sid-1",
            load_generation_id="load-1",
            context_id="context-1",
            browser_session_id="session-1",
            turn_id="turn-1",
        )
        finalize = await broker.begin_finalize(
            turn,
            control_id="control-finalize",
            dispositions={"lease-created": "ephemeral", "lease-user": "handoff"},
            reason="stopped",
            timeout_ms=1_000,
        )
        await asyncio.sleep(0)
        controls = {entry[2]["method"]: entry for entry in sent if entry[1] == CONTROL_EVENT}
        cancel_wire = controls["browser.cancel"][2]
        finalize_wire = controls["browser.finalize_turn"][2]
        assert controls["browser.cancel"][3] == "control-cancel"
        assert cancel_wire["load_generation_id"] == "load-1"
        assert cancel_wire["browser_session_id"] == "session-1"
        assert cancel_wire["op_id"] == "op-1"
        assert cancel_wire["action_id"] == "action-1"
        assert controls["browser.finalize_turn"][3] == "control-finalize"
        assert finalize_wire["bridge_id"] == "bridge-1"
        assert finalize_wire["load_generation_id"] == "load-1"
        assert finalize_wire["dispositions"] == {
            "lease-created": "ephemeral", "lease-user": "handoff"
        }

        bad = _control_success(cancel_wire)
        bad["browser_session_id"] = "another-session"
        assert broker.settle_control(
            principal=principal,
            connector_sid="sid-1",
            load_generation_id="load-1",
            payload=bad,
        ) == SettlementStatus.MISMATCH
        for ticket, wire in ((cancel, cancel_wire), (finalize, finalize_wire)):
            assert broker.settle_control(
                principal=principal,
                connector_sid="sid-1",
                load_generation_id="load-1",
                payload=_control_success(wire),
            ) == SettlementStatus.SETTLED
            assert (await broker.wait_control(ticket)).ok

    asyncio.run(scenario())


def test_sender_failure_and_pending_bounds_never_claim_mutation_not_applied():
    async def scenario():
        async def failing_sender(*_args):
            raise RuntimeError("raw transport secret")

        broker = BrowserBridgeOperationBroker(
            sender=failing_sender,
            authorizer=lambda candidate: _authorization(candidate),
            max_pending_operations=1,
        )
        mutation = await _start(broker, _binding())
        await asyncio.sleep(0)
        result = await broker.wait_operation(mutation)
        assert (result.code, result.outcome) == ("OUTCOME_UNKNOWN", "unknown")
        assert "secret" not in (result.error or "")

        async def sender(*_args):
            return None

        bounded = BrowserBridgeOperationBroker(
            sender=sender,
            authorizer=lambda candidate: _authorization(candidate),
            max_pending_operations=1,
        )
        await _start(bounded, _binding(op_id="first", action_id="first-action"))
        with pytest.raises(BrowserBridgeBrokerError) as exc:
            await _start(bounded, _binding(op_id="second", action_id="second-action"))
        assert exc.value.code == "INVALID_STATE"
        assert bounded.pending_operation_count == 1

    asyncio.run(scenario())


def test_noncanonical_or_oversize_payloads_are_rejected_before_send():
    async def scenario():
        sent = []

        async def sender(*args):
            sent.append(args)

        broker = BrowserBridgeOperationBroker(
            sender=sender, authorizer=lambda candidate: _authorization(candidate)
        )
        with pytest.raises(BrowserBridgeBrokerError) as exc:
            await broker.begin_operation(
                _binding(),
                action="click",
                target=None,
                args={"not-json": object()},
                timeout_ms=1_000,
                required_capabilities=["click"],
            )
        assert exc.value.code == "INVALID_STATE"
        with pytest.raises(BrowserBridgeBrokerError):
            await broker.begin_operation(
                _binding(op_id="op-large", action_id="action-large"),
                action="click",
                target=None,
                args={"large": "x" * (512 * 1024)},
                timeout_ms=1_000,
                required_capabilities=["click"],
            )
        # The native RPC grammar is broader, but Core uses op/control IDs as
        # restricted Socket.IO correlation IDs and must honor its 128-byte,
        # alphanumeric/underscore/hyphen-only boundary before dispatch.
        with pytest.raises(BrowserBridgeBrokerError):
            await broker.begin_operation(
                _binding(op_id="native.allowed.but-core-forbidden"),
                action="click",
                target=None,
                args={},
                timeout_ms=1_000,
                required_capabilities=["click"],
            )
        assert sent == []
        assert broker.pending_operation_count == 0

    asyncio.run(scenario())


def test_queued_dispatch_rechecks_revocation_and_pending_identity():
    async def scenario():
        sent = []
        current = True

        async def sender(*args):
            sent.append(args)

        binding = _binding()
        broker = BrowserBridgeOperationBroker(
            sender=sender,
            authorizer=lambda candidate: _authorization(candidate) if current else None,
        )
        revoked = await _start(broker, binding)
        current = False
        result = await broker.wait_operation(revoked)
        assert (result.code, result.outcome) == ("SCOPE_DENIED", "not_applied")
        current = True
        disconnected = await _start(broker, replace(binding, op_id="disconnected"))
        broker.disconnect(principal=binding.principal, connector_sid="sid-1", load_generation_id="load-1")
        assert (await broker.wait_operation(disconnected)).outcome == "unknown"
        assert sent == []

    asyncio.run(scenario())


def test_completed_replies_do_not_release_running_transport_capacity():
    async def scenario():
        sent = []
        release = asyncio.Event()

        async def sender(_sid, _event, payload, _correlation, _principal):
            sent.append(payload)
            await release.wait()

        broker = BrowserBridgeOperationBroker(
            sender=sender, authorizer=_authorization,
            max_pending_operations=1, max_pending_controls=1,
        )
        for index in range(2):
            binding = _binding(op_id=f"op-{index}", action_id=f"action-{index}")
            ticket = await _start(broker, binding)
            await asyncio.sleep(0)
            assert broker.settle_operation(
                principal=binding.principal, connector_sid="sid-1", load_generation_id="load-1",
                payload=_success(sent[-1]),
            ) == SettlementStatus.SETTLED
            assert (await broker.wait_operation(ticket)).ok
        with pytest.raises(BrowserBridgeBrokerError, match="transport queue is full"):
            await _start(broker, _binding(op_id="overflow", action_id="overflow"))
        release.set()

    asyncio.run(scenario())


def test_late_valid_result_cannot_bypass_deadline_without_expiry_tick():
    async def scenario():
        now = [100]
        sent = []

        async def sender(_sid, _event, payload, _correlation, _principal):
            sent.append(payload)

        broker = BrowserBridgeOperationBroker(sender=sender, authorizer=_authorization, clock_ms=lambda: now[0])
        binding = _binding()
        ticket = await _start(broker, binding, timeout_ms=100)
        await asyncio.sleep(0)
        now[0] = 200
        assert broker.settle_operation(
            principal=binding.principal, connector_sid="sid-1", load_generation_id="load-1",
            payload=_success(sent[0]),
        ) == SettlementStatus.SETTLED
        assert (await broker.wait_operation(ticket)).outcome == "unknown"

    asyncio.run(scenario())
