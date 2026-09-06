import asyncio
import base64
import hashlib
import json
import time
import pytest
from types import SimpleNamespace
from plugins._a0_connector.helpers.browser_bridge_application import BrowserBridgeApplication
from plugins._a0_connector.helpers.browser_bridge_context import (
    BrowserContextSourceSummary,
    BrowserContextSourcePage,
)
from plugins._a0_connector.helpers.browser_bridge_runtime import BrowserBridgeRuntimeDenied
from plugins._browser.helpers.extension_sessions import ExtensionSessionLifecycle, ExtensionSessionRegistry
from plugins._a0_connector.helpers.browser_bridge_operations import OperationBinding, SettlementStatus
from plugins._a0_connector.helpers.browser_bridge_artifact_controller import (
    BrowserBridgeArtifactControllerDenied,
)
from plugins._a0_connector.helpers.browser_bridge_artifacts import ArtifactBinding
from plugins._a0_connector.helpers.browser_bridge_queue import BrowserBridgeQueueError
from test_browser_bridge_runtime_foundation import (
    _principal,
    _active,
    _admission,
    _hello,
    _reconcile_registered,
)
from browser_bridge_test_support import MemoryPersistence as Memory
from browser_bridge_test_support import MemoryKeyValue


class Source:
    def list_contexts(self, **_kwargs):
        return [BrowserContextSourceSummary("context-A", "Task", "chat", "running", 1, 2)]

    def context_exists(self, *, context_id, **_kwargs):
        return context_id == "context-A"

    def read_context(self, *, history, history_before, **_kwargs):
        return BrowserContextSourcePage(entries=(), last_sequence=0, complete=False,
                                       history_before=0 if history == "tail" else None,
                                       has_more_history=False if history == "tail" else None)


def test_application_composes_exact_context_message_artifact_and_route_teardown(tmp_path):
    async def scenario():
        emitted = []

        class Manager:
            async def emit_to(self, *args, **kwargs):
                emitted.append((args, kwargs))

        messages, events, sessions = MemoryKeyValue(), Memory(), Memory()
        queues = MemoryKeyValue()
        delivered = []
        principal = _principal()
        app = BrowserBridgeApplication(
            manager=Manager(), server_instance_id=lambda: "server-A",
            lifecycle=ExtensionSessionLifecycle(registry=ExtensionSessionRegistry(persistence=sessions)),
            active_principal_verifier=_active, admission_evaluator=_admission,
            context_authorizer=lambda _route, context: context == "context-A",
            context_data_source=Source(), message_load=messages.load, message_save=messages.save,
            message_deliver=lambda *args: delivered.append(args), event_load=events.load, event_save=events.save,
            artifact_spool_parent=tmp_path,
            queue_context_get=lambda context: SimpleNamespace(get_data=lambda key: None),
            queue_load=queues.load, queue_save=queues.save,
            queue_mark_dirty=lambda context: None,
            selection_current=lambda context, bridge: context == "context-A" and bridge == principal.principal_id,
        )
        with pytest.raises(BrowserBridgeRuntimeDenied):
            await app.dispatch(principal, "sid-A", "connector_context_list", {"contract_version": 1})
        hello = _hello(principal)
        hello["host_browser"]["capabilities"]["actions"].append("screenshot")
        route = app.registry.register_hello(principal=principal, connector_sid="sid-A", data=hello)
        await _reconcile_registered(app.registry, route)
        listing = await app.dispatch(principal, "sid-A", "connector_context_list", {"contract_version": 1})
        assert listing["contexts"][0]["context_id"] == "context-A"
        await app.dispatch(principal, "sid-A", "connector_subscribe_context", {
            "contract_version": 1, "context_id": "context-A", "history": "tail",
        })
        assert emitted[0][1]["expected_principal"] is principal
        assert app.contexts.stream_count == 1
        message = {"contract_version": 1, "context_id": "context-A", "client_message_id": "message-1", "text": "Hello"}
        await app.dispatch(principal, "sid-A", "connector_send_message", message)
        await app.dispatch(principal, "sid-A", "connector_send_message", message)
        assert delivered == [("context-A", "Hello", "message-1")]
        session, turn = app.browser.lifecycle.registry.begin_turn(
            context_id="context-A", browser_id="extension:bridge-A", bridge_id="bridge-A",
        )
        operation = OperationBinding(principal, "sid-A", "generation-A", "context-A",
                                     session.browser_session_id, turn.turn_id, "action-image", "op-image")
        app.browser.leases.observe_open(operation, {
            "lease_id": "lease-nav", "tab_handle": "tab-nav", "browser_id": "tab-nav",
            "origin": "https://source.example", "disposition": "ephemeral",
        }, "https://source.example")
        navigation_binding = OperationBinding(principal, "sid-A", "generation-A", "context-A",
                                              session.browser_session_id, turn.turn_id, "action-nav", "op-nav")
        navigation = await app.registry.broker.begin_operation(
            navigation_binding, action="navigate", target={"tab_handle": "tab-nav"}, args={"url": "https://next.example/"},
            timeout_ms=30_000, required_capabilities=["navigate"], policy={"origin_grant_id": "source-grant"},
            display={"cursor": False, "foreground": False},
        )
        fingerprint = {"action_class": "navigate", "browser_id_digest": hashlib.sha256(b"tab-nav").hexdigest(),
                       "lease_id_digest": hashlib.sha256(b"lease-nav").hexdigest(), "document_id": None,
                       "document_epoch": 0, "load_generation_id": "generation-A", "origin": "https://next.example"}
        now = time.time_ns() // 1_000_000
        event = {"contract_version": 1, "event_id": "event-site", "load_generation_id": "generation-A",
                 "event_sequence": 1, "delivery": "critical", "event_type": "challenge.required", "observed_at_ms": now,
                 "context_id": "context-A", "browser_session_id": session.browser_session_id, "turn_id": turn.turn_id,
                 "op_id": "op-nav", "action_id": "action-nav", "data": {
                     **{key: value for key, value in fingerprint.items() if key != "load_generation_id"},
                     "challenge_id": "challenge-nav", "kind": "site", "canonical_parameter_hash": navigation.canonical_parameter_hash,
                     "target_fingerprint": hashlib.sha256(json.dumps(fingerprint, sort_keys=True, separators=(",", ":")).encode()).hexdigest(),
                     "summary": "Allow Agent Zero to work on next.example?", "options": ["deny", "allow_once", "allow_turn"],
                     "expires_at_ms": now + 20_000,
                 }}
        await app.dispatch(principal, "sid-A", "connector_browser_event", event)
        assert app.sites.list_pending(subject_id=principal.subject_id)[0]["origin"] == "https://next.example"
        decision = await app.sites.decide(subject_id=principal.subject_id, challenge_id="challenge-nav", decision="allow_turn")
        assert await app.sites.decide(subject_id=principal.subject_id, challenge_id="challenge-nav", decision="allow_turn") is decision
        for _ in range(3):
            await asyncio.sleep(0)
        control = next(args[3] for args, _kwargs in emitted if args[2] == "connector_browser_control")
        assert control["canonical_parameter_hash"] == navigation.canonical_parameter_hash
        assert control["grant"]["scope"] == "turn"
        control_response = {key: control[key] for key in (
            "contract_version", "method", "bridge_id", "load_generation_id", "context_id", "browser_session_id",
            "turn_id", "control_id", "op_id", "action_id",
        )}
        control_response.update(ok=True, result={"contract_version": 1, "control_id": decision.control_id,
                                                "challenge_id": "challenge-nav", "status": "resolved", "decision": "allow_turn"})
        assert (await app.dispatch(principal, "sid-A", "connector_browser_control_result", control_response))["status"] == SettlementStatus.SETTLED
        for _ in range(8):
            if app.sites.turn_grant_for(navigation_binding, origin="https://next.example") is not None:
                break
            await asyncio.sleep(0)
        assert app.sites.turn_grant_for(navigation_binding, origin="https://next.example") is not None
        ticket = await app.registry.broker.begin_operation(
            operation, action="screenshot", target={"tab_handle": "tab-image"}, args={},
            timeout_ms=5_000, required_capabilities=["screenshot"], policy={"origin_grant_id": "site-grant"},
            display={"cursor": False, "foreground": False},
        )
        artifact = ArtifactBinding(principal, "sid-A", "generation-A", "bridge-A", "context-A",
                                   session.browser_session_id, turn.turn_id, "action-image", "op-image",
                                   "artifact-image", "output", "screenshot")
        common = {name: getattr(artifact, name) for name in (
            "contract_version", "bridge_id", "load_generation_id", "context_id", "browser_session_id",
            "turn_id", "action_id", "op_id", "artifact_id", "direction", "purpose",
        )}
        data = b"synthetic artifact bytes"
        begin = {**common, "phase": "begin", "byte_count": len(data), "mime_type": "image/png", "sha256": "sha256:" + hashlib.sha256(data).hexdigest()}
        with pytest.raises(BrowserBridgeArtifactControllerDenied):
            await app.dispatch(principal, "sid-A", "connector_browser_artifact_chunk", {**begin, "action_id": "wrong-action"})
        await app.dispatch(principal, "sid-A", "connector_browser_artifact_chunk", begin)
        await app.dispatch(principal, "sid-A", "connector_browser_artifact_chunk", {
            **common, "phase": "chunk", "chunk_index": 0, "data_base64": base64.b64encode(data).decode(),
        })
        ended = await app.dispatch(principal, "sid-A", "connector_browser_artifact_chunk", {**common, "phase": "end"})
        assert ended["status"] == "complete"
        response = {name: getattr(operation, name) for name in (
            "bridge_id", "load_generation_id", "context_id", "browser_session_id", "turn_id", "action_id", "op_id",
        )}
        response.update(contract_version=1, ok=True, result={}, receipts=[], artifacts=[])
        assert (await app.dispatch(principal, "sid-A", "connector_browser_op_result", response))["status"] == SettlementStatus.SETTLED
        assert (await app.registry.broker.wait_operation(ticket)).ok
        # Verified output can be consumed once after the op settles, but only
        # while the independently retained exact turn and route remain active.
        assert app.artifact_receiver.consume(artifact, lambda stream, _descriptor: stream.read()) == data
        with pytest.raises(BrowserBridgeArtifactControllerDenied):
            await app.dispatch(principal, "sid-A", "connector_browser_artifact_chunk", {**begin, "artifact_id": "late-artifact"})
        with pytest.raises(BrowserBridgeQueueError):
            await app.dispatch(principal, "sid-A", "connector_message_queue_add", {"contract_version": 1})
        assert await app.disconnect(principal, "sid-A")
        assert app.contexts.stream_count == 0 and app.registry.session_count == 0
        assert not await app.disconnect(principal, "sid-A")
        await app.close()
        assert not list(tmp_path.iterdir())

    asyncio.run(scenario())


@pytest.mark.parametrize("action", ["click", "type"])
def test_application_binds_action_approval_to_inspected_document_and_once_control(tmp_path, action):
    async def scenario():
        emitted = []
        class Manager:
            async def emit_to(self, *args, **kwargs):
                emitted.append((args, kwargs))
        principal = _principal()
        messages, events, sessions = MemoryKeyValue(), Memory(), Memory()
        app = BrowserBridgeApplication(
            manager=Manager(), server_instance_id=lambda: "server-A",
            lifecycle=ExtensionSessionLifecycle(registry=ExtensionSessionRegistry(persistence=sessions)),
            active_principal_verifier=_active, admission_evaluator=_admission,
            context_authorizer=lambda _route, context: context == "context-A", context_data_source=Source(),
            message_load=messages.load, message_save=messages.save, message_deliver=lambda *_args: None,
            event_load=events.load, event_save=events.save, artifact_spool_parent=tmp_path,
            selection_current=lambda context, bridge: context == "context-A" and bridge == principal.principal_id,
            approval_record_loader=lambda server, bridge: {
                "state": "active", "server_instance_id": server, "bridge_id": bridge,
                "subject_id": principal.subject_id, "key_generation": principal.key_generation,
                "scopes": sorted(principal.scopes),
            },
        )
        hello = _hello(principal)
        hello["host_browser"]["capabilities"]["actions"].append(action)
        route = app.registry.register_hello(principal=principal, connector_sid="sid-A", data=hello)
        await _reconcile_registered(app.registry, route)
        session, turn = app.browser.lifecycle.registry.begin_turn(
            context_id="context-A", browser_id="extension:bridge-A", bridge_id="bridge-A",
        )
        binding = OperationBinding(principal, "sid-A", "generation-A", "context-A",
                                   session.browser_session_id, turn.turn_id, "action-click", "op-click")
        app.browser.leases.observe_open(binding, {
            "lease_id": "lease-click", "browser_id": "tab-click", "tab_handle": "tab-click",
            "origin": "https://example.com", "disposition": "ephemeral",
        }, "https://example.com")
        app.browser.leases.observe_content(binding, "tab-click", {
            "lease_id": "lease-click", "browser_id": "tab-click", "tab_handle": "tab-click",
            "document_id": "document-click", "document_epoch": "1", "title": "Synthetic", "text": "",
            "nodes": [{"ref": "doc:1:click", "role": "button", "name": "Synthetic control"}], "truncated": False,
        })
        action_class = "sensitive_input" if action == "type" else "unknown"
        params = {"ref": "doc:1:click", "expected_action_class": action_class}
        classification = "none"
        if action == "type":
            digest = hashlib.sha256(b"synthetic private input").hexdigest()
            params.update(text="synthetic private input", text_sha256=digest)
            classification = {"kind": "text", "sensitivity": "sensitive", "text_sha256": digest}
        ticket = await app.registry.broker.begin_operation(
            binding, action=action, target={"tab_handle": "tab-click"},
            args=params, timeout_ms=30_000,
            required_capabilities=[action], policy={"origin_grant_id": "origin-grant", "action_grant_id": None},
            display={"cursor": True, "foreground": False},
        )
        now = time.time_ns() // 1_000_000
        event = {"contract_version": 1, "event_id": "event-action", "load_generation_id": "generation-A",
                 "event_sequence": 1, "delivery": "critical", "event_type": "challenge.required", "observed_at_ms": now,
                 "context_id": "context-A", "browser_session_id": session.browser_session_id, "turn_id": turn.turn_id,
                 "op_id": "op-click", "action_id": "action-click", "data": {
                     "challenge_id": "challenge-click", "kind": "action", "origin": "https://example.com",
                     "action_class": action_class, "canonical_parameter_hash": ticket.canonical_parameter_hash,
                     "target_fingerprint": hashlib.sha256(b"synthetic exact target").hexdigest(),
                     "lease_id_digest": hashlib.sha256(b"lease-click").hexdigest(),
                     "browser_id_digest": hashlib.sha256(b"tab-click").hexdigest(),
                     "document_id": "document-click", "document_epoch": 1,
                     "summary": "Allow Agent Zero to type into the highlighted field?" if action == "type" else "Confirm this browser action",
                     "options": ["decline", "approve_once"], "data_classification": classification, "expires_at_ms": now + 20_000,
                 }}
        await app.dispatch(principal, "sid-A", "connector_browser_event", event)
        listing = app.actions.list_pending(subject_id=principal.subject_id)
        assert listing[0]["challenge_id"] == "challenge-click" and listing[0]["origin"] == "https://example.com"
        assert listing[0]["action"] == action
        assert "synthetic private input" not in json.dumps(listing) + json.dumps(events.value)
        decision = await app.actions.decide(subject_id=principal.subject_id, challenge_id="challenge-click", choice="approve_once")
        assert await app.actions.decide(subject_id=principal.subject_id, challenge_id="challenge-click", choice="approve_once") is decision
        for _ in range(8):
            await asyncio.sleep(0)
            if any(args[2] == "connector_browser_control" for args, _kwargs in emitted):
                break
        controls = [args[3] for args, _kwargs in emitted if args[2] == "connector_browser_control"]
        assert len(controls) == 1
        control = controls[0]
        assert control["grant"]["scope"] == "operation" and control["grant"]["canonical_parameter_hash"] == ticket.canonical_parameter_hash
        assert control["document_id"] == "document-click" and control["grant"]["expires_at_ms"] <= event["data"]["expires_at_ms"]
        assert control["data_classification"] == classification == control["grant"]["data_classification"]
        response = {key: control[key] for key in (
            "contract_version", "method", "bridge_id", "load_generation_id", "context_id", "browser_session_id",
            "turn_id", "control_id", "op_id", "action_id",
        )}
        response.update(ok=True, result={"contract_version": 1, "control_id": decision.control_id,
                                        "challenge_id": "challenge-click", "status": "resolved", "decision": "approve_once"})
        assert (await app.dispatch(principal, "sid-A", "connector_browser_control_result", response))["status"] == SettlementStatus.SETTLED
        await app.disconnect(principal, "sid-A")
        assert not app.actions.list_pending(subject_id=principal.subject_id)
        await app.close()
        assert not list(tmp_path.iterdir())

    asyncio.run(scenario())
