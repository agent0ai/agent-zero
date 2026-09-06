from __future__ import annotations

import asyncio
from copy import deepcopy
from dataclasses import replace
import hashlib
import json
from types import SimpleNamespace
from typing import Any

import pytest

from helpers.ws_principal import WsPrincipal
from plugins._a0_connector.helpers.browser_bridge_action_authority import (
    ACTION_AUTHORITY_CONTRACT,
    ActionDocumentBinding,
    BrowserBridgeActionAuthority,
    BrowserBridgeActionAuthorityUnavailable,
)
from plugins._a0_connector.helpers.browser_bridge_approval import (
    BrowserActionDataClassification,
    BrowserBridgeApprovalRepository,
    NO_ACTION_DATA_CLASSIFICATION,
)
from plugins._a0_connector.helpers.browser_bridge_context import (
    BrowserBridgeContextRoute,
)
from plugins._a0_connector.helpers.browser_bridge_events import (
    BROWSER_EVENT,
    BROWSER_EVENT_ACK,
    RESTRICTED_HANDLER_ID,
    ActionChallengeNotice,
    BrowserBridgeCriticalEventReceiver,
    TYPE_CHALLENGE_SUMMARY,
    UPLOAD_CHALLENGE_SUMMARY,
)
from plugins._a0_connector.helpers.browser_bridge_operations import (
    CONTROL_EVENT,
    BridgeAuthorization,
    BrokerCompletion,
    BrowserBridgeBrokerError,
    BrowserBridgeOperationBroker,
    ControlBinding,
    ControlTicket,
    OperationBinding,
    OperationTicket,
)


NOW_MS = 1_788_492_400_000
ORIGIN = "https://example.com"
LEASE_ID = "lease-A"
TAB_HANDLE = "tab-A"
DOCUMENT_ID = "document-A"
REF = "a0t1.generation-A.tab-A.1"
TYPE_TEXT = "sensitive café text"
TYPE_TEXT_SHA256 = hashlib.sha256(TYPE_TEXT.encode("utf-8")).hexdigest()


def _principal() -> WsPrincipal:
    return WsPrincipal(
        principal_type="browser_bridge",
        principal_id="bridge-A",
        subject_id="single_user",
        scopes=frozenset(
            {"browser.operate", "browser.control", "browser.approval"}
        ),
        handler_path="plugins/_a0_connector/ws_connector",
        handler_id=RESTRICTED_HANDLER_ID,
        inbound_events=frozenset({BROWSER_EVENT}),
        outbound_events=frozenset(
            {BROWSER_EVENT_ACK, "connector_browser_op", CONTROL_EVENT}
        ),
        key_generation=3,
    )


def _operation(
    loop: asyncio.AbstractEventLoop,
    principal: WsPrincipal,
    *,
    action: str = "click",
) -> OperationTicket:
    binding = OperationBinding(
        principal=principal,
        connector_sid="sid-A",
        load_generation_id="generation-A",
        context_id="context-A",
        browser_session_id="browser-session-A",
        turn_id="turn-A",
        action_id="action-A",
        op_id="op-A",
    )
    expected_action_class = (
        "sensitive_input" if action == "type" else "unknown"
    )
    args = {
        "ref": REF,
        **(
            {"text": TYPE_TEXT, "text_sha256": TYPE_TEXT_SHA256}
            if action == "type"
            else {}
        ),
        "expected_action_class": expected_action_class,
    }
    display = {"cursor": True, "foreground": False}
    canonical = {
        "action": action,
        "target": {"tabHandle": TAB_HANDLE},
        "context_id": binding.context_id,
        "browser_session_id": binding.browser_session_id,
        "turn_id": binding.turn_id,
        "args": args,
        "display": display,
    }
    parameter_hash = hashlib.sha256(
        json.dumps(
            canonical,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
        ).encode()
    ).hexdigest()
    return OperationTicket(
        binding=binding,
        deadline_ms=NOW_MS + 90_000,
        effect="mutating",
        _future=loop.create_future(),
        action=action,
        target_tab_handle=TAB_HANDLE,
        target_ref=REF,
        expected_action_class=expected_action_class,
        text_sha256=TYPE_TEXT_SHA256 if action == "type" else None,
        canonical_parameter_hash=parameter_hash,
    )


def _notice(operation: OperationTicket, **changes: Any) -> ActionChallengeNotice:
    values = {
        "principal": operation.binding.principal,
        "connector_sid": operation.binding.connector_sid,
        "load_generation_id": operation.binding.load_generation_id,
        "context_id": operation.binding.context_id,
        "browser_session_id": operation.binding.browser_session_id,
        "turn_id": operation.binding.turn_id,
        "action_id": operation.binding.action_id,
        "op_id": operation.binding.op_id,
        "challenge_id": "challenge-A",
        "origin": ORIGIN,
        "action_class": operation.expected_action_class,
        "canonical_parameter_hash": operation.canonical_parameter_hash,
        "target_fingerprint": "b" * 64,
        "lease_id_digest": hashlib.sha256(LEASE_ID.encode()).hexdigest(),
        "browser_id_digest": hashlib.sha256(TAB_HANDLE.encode()).hexdigest(),
        "document_id": DOCUMENT_ID,
        "document_epoch": 1,
        "summary": (
            TYPE_CHALLENGE_SUMMARY
            if operation.action == "type"
            else "Untrusted extension wording is never shown."
        ),
        "data_classification": (
            BrowserActionDataClassification(
                "text", "sensitive", operation.text_sha256
            )
            if operation.action == "type"
            else NO_ACTION_DATA_CLASSIFICATION
        ),
        "expires_at_ms": NOW_MS + 60_000,
    }
    values.update(changes)
    return ActionChallengeNotice(**values)


class _Harness:
    def __init__(self, operation: OperationTicket) -> None:
        self.operation = operation
        self.selection_allowed = True
        self.operations = {operation.binding.op_id: operation}
        self.lease = SimpleNamespace(
            binding=operation.binding,
            lease_id=LEASE_ID,
            tab_handle=TAB_HANDLE,
            origin=ORIGIN,
        )
        self.document = ActionDocumentBinding(DOCUMENT_ID, 1, frozenset({REF}))
        self.current_route = BrowserBridgeContextRoute(
            operation.binding.principal,
            operation.binding.connector_sid,
            operation.binding.load_generation_id,
        )
        self.resolutions: list[dict[str, Any]] = []
        self.control_ids = iter(("control-A", "control-B"))
        self.grant_ids = iter(("grant-A", "grant-B"))
        self.approvals = BrowserBridgeApprovalRepository(
            route_authorizer=lambda route: self.authority.approval_route_current(
                route
            ),
            active_record_loader=self.active_record,
            server_instance_id_loader=lambda: "server-A",
            clock_ms=lambda: NOW_MS,
            receipt_id_factory=lambda: "receipt-A",
        )
        self.authority = BrowserBridgeActionAuthority(
            current_operation=self.current_operation,
            remaining_operation_ms=lambda _operation: 90_000,
            lease_for=self.lease_for,
            document_for=self.document_for,
            route_verifier=self.route_verifier,
            turn_current=lambda binding: self.current_operation(
                principal=binding.principal,
                connector_sid=binding.connector_sid,
                load_generation_id=binding.load_generation_id,
                op_id=binding.op_id,
            )
            is operation,
            selection_current=self.selection_current,
            begin_resolution=self.begin_resolution,
            wait_control=self.wait_control,
            server_instance_id=lambda: "server-A",
            approval_repository=self.approvals,
            clock_ms=lambda: NOW_MS,
            control_id_factory=lambda: next(self.control_ids),
            grant_id_factory=lambda: next(self.grant_ids),
        )

    def selection_current(self, context_id: str, bridge_id: str) -> bool:
        return bool(
            self.selection_allowed
            and context_id == self.operation.binding.context_id
            and bridge_id == self.operation.binding.bridge_id
        )

    def active_record(self, server_id: str, bridge_id: str) -> dict[str, Any] | None:
        principal = self.operation.binding.principal
        if server_id != "server-A" or bridge_id != principal.principal_id:
            return None
        return {
            "state": "active",
            "server_instance_id": server_id,
            "bridge_id": bridge_id,
            "subject_id": principal.subject_id,
            "key_generation": principal.key_generation,
            "scopes": sorted(principal.scopes),
        }

    def current_operation(self, **kwargs: Any) -> OperationTicket | None:
        operation = self.operations.get(kwargs["op_id"])
        if operation is None:
            return None
        binding = operation.binding
        return operation if (
            binding.principal is kwargs["principal"]
            and binding.connector_sid == kwargs["connector_sid"]
            and binding.load_generation_id == kwargs["load_generation_id"]
        ) else None

    def lease_for(self, binding: OperationBinding, handle: str) -> Any | None:
        return self.lease if (
            binding is self.operation.binding and handle == TAB_HANDLE
        ) else None

    def document_for(
        self, binding: OperationBinding, handle: str
    ) -> ActionDocumentBinding | None:
        return self.document if (
            binding is self.operation.binding and handle == TAB_HANDLE
        ) else None

    def route_verifier(self, route: BrowserBridgeContextRoute) -> bool:
        return (
            route.principal is self.current_route.principal
            and route.connector_sid == self.current_route.connector_sid
            and route.load_generation_id == self.current_route.load_generation_id
        )

    async def begin_resolution(
        self, operation: OperationTicket, **kwargs: Any
    ) -> ControlTicket:
        assert operation is self.operation
        assert self.approvals.pending_receipt_count == 0
        assert kwargs["authorization_current"]() is True
        self.resolutions.append(deepcopy(kwargs))
        binding = operation.binding
        return ControlTicket(
            binding=ControlBinding(
                binding.principal,
                binding.connector_sid,
                binding.load_generation_id,
                binding.context_id,
                binding.browser_session_id,
                binding.turn_id,
                kwargs["control_id"],
                "browser.resolve_challenge",
                binding.op_id,
                binding.action_id,
            ),
            deadline_ms=NOW_MS + kwargs["timeout_ms"],
            _future=asyncio.get_running_loop().create_future(),
        )

    async def wait_control(self, ticket: ControlTicket) -> BrokerCompletion:
        resolution = self.resolutions[-1]["resolution"]
        return BrokerCompletion(
            ok=True,
            result={
                "contract_version": 1,
                "control_id": ticket.binding.control_id,
                "challenge_id": resolution["challenge_id"],
                "status": "resolved",
                "decision": resolution["decision"],
            },
        )


def test_exact_action_challenge_and_receipt_are_bound_once() -> None:
    async def scenario() -> None:
        operation = _operation(asyncio.get_running_loop(), _principal())
        harness = _Harness(operation)
        assert harness.authority.ready_for(operation.binding) is True
        challenge = harness.authority.register_challenge(_notice(operation))
        assert challenge.as_public_dict() == {
            "challenge_id": "challenge-A",
            "action": "click",
            "origin": ORIGIN,
            "action_class": "unknown",
            "options": ["decline", "approve_once"],
            "expires_at_ms": NOW_MS + 60_000,
        }
        assert harness.authority.list_pending(
            subject_id="single_user",
            context_id="context-A",
            bridge_id="bridge-A",
        ) == (challenge.as_public_dict(),)
        assert harness.authority.list_pending(
            subject_id="single_user",
            context_id="context-B",
            bridge_id="bridge-A",
        ) == ()
        decision = await harness.authority.decide(
            subject_id="single_user",
            challenge_id="challenge-A",
            choice="approve_once",
        )
        assert decision.as_public_dict() == {
            "challenge_id": "challenge-A",
            "decision": "approved",
            "control_id": "control-A",
            "status": "accepted",
        }
        assert harness.approvals.pending_receipt_count == 1
        replay = await harness.authority.decide(
            subject_id="single_user",
            challenge_id="challenge-A",
            choice="approve_once",
        )
        assert replay is decision
        with pytest.raises(BrowserBridgeActionAuthorityUnavailable):
            await harness.authority.decide(
                subject_id="single_user",
                challenge_id="challenge-A",
                choice="decline",
            )
        await asyncio.sleep(0)
        await asyncio.sleep(0)
        assert harness.approvals.pending_receipt_count == 0
        resolution = harness.resolutions[0]["resolution"]
        assert resolution == {
            "challenge_id": "challenge-A",
            "tab_handle": TAB_HANDLE,
            "document_id": DOCUMENT_ID,
            "document_epoch": 1,
            "canonical_parameter_hash": operation.canonical_parameter_hash,
            "target_fingerprint": "b" * 64,
            "origin": ORIGIN,
            "action_class": "unknown",
            "data_classification": "none",
            "decision": "approve_once",
            "grant": {
                "action_grant_id": "grant-A",
                "scope": "operation",
                "origin": ORIGIN,
                "action_class": "unknown",
                "canonical_parameter_hash": operation.canonical_parameter_hash,
                "target_fingerprint": "b" * 64,
                "data_classification": "none",
                "expires_at_ms": NOW_MS + 60_000,
            },
        }
        await harness.authority.close()

    asyncio.run(scenario())


def test_upload_challenge_requires_fixed_warning_and_exact_artifact_parameter_hash() -> None:
    from plugins._a0_connector.helpers.browser_bridge_operations import _operation_parameter_hash

    async def scenario() -> None:
        operation = replace(_operation(asyncio.get_running_loop(), _principal()),
                            action="upload_file", expected_action_class="external_side_effect")
        args = {"ref": REF, "expected_action_class": "external_side_effect", "artifact_id": "input-A",
                "mime_type": "text/plain", "byte_count": 3, "sha256": "sha256:" + "a" * 64}
        digest = _operation_parameter_hash(operation.binding, "upload_file", {"tab_handle": TAB_HANDLE}, args,
                                           {"cursor": True, "foreground": False})
        assert digest is not None
        assert _operation_parameter_hash(operation.binding, "upload_file", {"tab_handle": TAB_HANDLE},
                                         {**args, "path": "/private/secret"}, {}) is None
        changed = _operation_parameter_hash(operation.binding, "upload_file", {"tab_handle": TAB_HANDLE},
                                             {**args, "sha256": "sha256:" + "b" * 64}, {"cursor": True, "foreground": False})
        assert changed != digest
        operation = replace(operation, canonical_parameter_hash=digest)
        harness = _Harness(operation)
        with pytest.raises(BrowserBridgeActionAuthorityUnavailable):
            harness.authority.register_challenge(_notice(operation))
        challenge = harness.authority.register_challenge(_notice(operation, summary=UPLOAD_CHALLENGE_SUMMARY))
        assert challenge.as_public_dict()["action"] == "upload_file"
        assert challenge.data_classification == NO_ACTION_DATA_CLASSIFICATION
        await harness.authority.decide(subject_id="single_user", challenge_id="challenge-A", choice="approve_once")
        await asyncio.sleep(0)
        await asyncio.sleep(0)
        resolution = harness.resolutions[0]["resolution"]
        assert resolution["action_class"] == "external_side_effect"
        assert resolution["data_classification"] == "none"
        assert resolution["canonical_parameter_hash"] == digest
        await harness.authority.close()

    asyncio.run(scenario())


def test_type_challenge_binds_tagged_digest_without_retaining_text() -> None:
    async def scenario() -> None:
        operation = _operation(
            asyncio.get_running_loop(), _principal(), action="type"
        )
        harness = _Harness(operation)
        wrong = BrowserActionDataClassification(
            "text", "sensitive", "c" * 64
        )
        with pytest.raises(BrowserBridgeActionAuthorityUnavailable):
            harness.authority.register_challenge(
                _notice(operation, data_classification=wrong)
            )
        challenge = harness.authority.register_challenge(_notice(operation))
        assert challenge.as_public_dict() == {
            "challenge_id": "challenge-A",
            "action": "type",
            "origin": ORIGIN,
            "action_class": "sensitive_input",
            "options": ["decline", "approve_once"],
            "expires_at_ms": NOW_MS + 60_000,
        }
        assert challenge.data_classification.as_wire_value() == {
            "kind": "text",
            "sensitivity": "sensitive",
            "text_sha256": TYPE_TEXT_SHA256,
        }
        assert TYPE_TEXT not in repr(operation)
        assert TYPE_TEXT not in repr(challenge)
        await harness.authority.decide(
            subject_id="single_user",
            challenge_id="challenge-A",
            choice="approve_once",
        )
        await asyncio.sleep(0)
        await asyncio.sleep(0)
        resolution = harness.resolutions[0]["resolution"]
        assert resolution["data_classification"] == {
            "kind": "text",
            "sensitivity": "sensitive",
            "text_sha256": TYPE_TEXT_SHA256,
        }
        assert resolution["grant"]["data_classification"] == (
            resolution["data_classification"]
        )
        assert TYPE_TEXT not in json.dumps(resolution, sort_keys=True)
        await harness.authority.close()

    asyncio.run(scenario())


def test_action_registration_rechecks_document_ref_lease_and_hash() -> None:
    async def scenario() -> None:
        operation = _operation(asyncio.get_running_loop(), _principal())
        harness = _Harness(operation)
        harness.document = ActionDocumentBinding(
            DOCUMENT_ID, 1, frozenset({"different-ref"})
        )
        with pytest.raises(BrowserBridgeActionAuthorityUnavailable):
            harness.authority.register_challenge(_notice(operation))
        harness.document = ActionDocumentBinding(DOCUMENT_ID, 1, frozenset({REF}))
        with pytest.raises(BrowserBridgeActionAuthorityUnavailable):
            harness.authority.register_challenge(
                _notice(operation, canonical_parameter_hash="c" * 64)
            )
        harness.lease.origin = "https://different.example"
        with pytest.raises(BrowserBridgeActionAuthorityUnavailable):
            harness.authority.register_challenge(_notice(operation))
        await harness.authority.close()

    asyncio.run(scenario())


def test_action_decision_is_withdrawn_when_server_selection_changes() -> None:
    async def scenario() -> None:
        operation = _operation(asyncio.get_running_loop(), _principal())
        harness = _Harness(operation)
        harness.authority.register_challenge(_notice(operation))
        harness.selection_allowed = False
        with pytest.raises(BrowserBridgeActionAuthorityUnavailable):
            await harness.authority.decide(
                subject_id="single_user",
                challenge_id="challenge-A",
                choice="approve_once",
            )
        assert harness.resolutions == []
        await harness.authority.close()

        queued = _Harness(
            _operation(asyncio.get_running_loop(), _principal())
        )
        queued.authority.register_challenge(_notice(queued.operation))
        await queued.authority.decide(
            subject_id="single_user",
            challenge_id="challenge-A",
            choice="approve_once",
        )
        queued.selection_allowed = False
        await asyncio.sleep(0)
        assert queued.resolutions == []
        with pytest.raises(BrowserBridgeActionAuthorityUnavailable):
            await queued.authority.decide(
                subject_id="single_user",
                challenge_id="challenge-A",
                choice="approve_once",
            )
        await queued.authority.close()

    asyncio.run(scenario())


class _Manager:
    def __init__(self) -> None:
        self.emits: list[tuple[Any, ...]] = []

    async def emit_to(self, *args: Any, **kwargs: Any) -> None:
        self.emits.append((*args, kwargs))


def _event(notice: ActionChallengeNotice) -> dict[str, Any]:
    return {
        "contract_version": 1,
        "event_id": "event-A",
        "load_generation_id": notice.load_generation_id,
        "event_sequence": 1,
        "delivery": "critical",
        "event_type": "challenge.required",
        "observed_at_ms": NOW_MS,
        "context_id": notice.context_id,
        "browser_session_id": notice.browser_session_id,
        "turn_id": notice.turn_id,
        "op_id": notice.op_id,
        "action_id": notice.action_id,
        "data": {
            "challenge_id": notice.challenge_id,
            "kind": "action",
            "origin": notice.origin,
            "action_class": notice.action_class,
            "canonical_parameter_hash": notice.canonical_parameter_hash,
            "target_fingerprint": notice.target_fingerprint,
            "lease_id_digest": notice.lease_id_digest,
            "browser_id_digest": notice.browser_id_digest,
            "document_id": notice.document_id,
            "document_epoch": notice.document_epoch,
            "summary": notice.summary,
            "options": ["decline", "approve_once"],
            "data_classification": notice.data_classification.as_wire_value(),
            "expires_at_ms": notice.expires_at_ms,
        },
    }


def test_critical_action_event_registers_before_hash_only_receipt() -> None:
    async def scenario() -> None:
        operation = _operation(
            asyncio.get_running_loop(), _principal(), action="type"
        )
        harness = _Harness(operation)
        stores: list[dict[str, Any]] = []
        manager = _Manager()
        receiver = BrowserBridgeCriticalEventReceiver(
            manager=manager,
            server_instance_id=lambda: "server-A",
            current_route_verifier=harness.route_verifier,
            register_action_challenge=harness.authority.register_event,
            load=lambda: stores[-1] if stores else None,
            save=lambda state: stores.append(deepcopy(state)),
        )
        result = await receiver.receive(harness.current_route, _event(_notice(operation)))
        assert result == {
            "contract_version": 1,
            "event_id": "event-A",
            "status": "accepted",
        }
        assert harness.authority.pending_count == 1
        serialized = json.dumps(stores[-1], sort_keys=True)
        for secret in (
            ORIGIN,
            "challenge-A",
            DOCUMENT_ID,
            TYPE_TEXT,
            TYPE_TEXT_SHA256,
        ):
            assert secret not in serialized
        assert manager.emits[-1][2] == BROWSER_EVENT_ACK
        await harness.authority.close()

    asyncio.run(scenario())


def test_action_broker_hash_and_exact_resolution_schema() -> None:
    async def scenario() -> None:
        sent: list[tuple[Any, ...]] = []
        principal = _principal()
        binding = OperationBinding(
            principal,
            "sid-A",
            "generation-A",
            "context-A",
            "browser-session-A",
            "turn-A",
            "action-A",
            "op-A",
        )

        async def sender(*args: Any) -> None:
            sent.append(args)

        def authorize(candidate: Any) -> BridgeAuthorization:
            return BridgeAuthorization(
                candidate.principal,
                candidate.connector_sid,
                candidate.load_generation_id,
                1,
                frozenset(
                    {"browser_extension_bridge_v1", "connector_browser_control"}
                ),
                frozenset(
                    {
                        "click",
                        "type",
                        "semantic_dom_v1",
                        "cursor_v1",
                        "trusted_input_v1",
                    }
                ),
                frozenset(),
            )

        broker = BrowserBridgeOperationBroker(sender=sender, authorizer=authorize)
        ticket = await broker.begin_operation(
            binding,
            action="click",
            target={"tab_handle": TAB_HANDLE},
            args={"ref": REF, "expected_action_class": "unknown"},
            timeout_ms=30_000,
            required_capabilities=[
                "click",
                "semantic_dom_v1",
                "cursor_v1",
                "trusted_input_v1",
            ],
            policy={"origin_grant_id": "origin-grant", "action_grant_id": None},
            display={"cursor": True, "foreground": False},
        )
        assert ticket.target_ref == REF
        resolution = {
            "challenge_id": "challenge-A",
            "tab_handle": TAB_HANDLE,
            "document_id": DOCUMENT_ID,
            "document_epoch": 1,
            "canonical_parameter_hash": ticket.canonical_parameter_hash,
            "target_fingerprint": "b" * 64,
            "origin": ORIGIN,
            "action_class": "unknown",
            "data_classification": "none",
            "decision": "decline",
            "grant": None,
        }
        await broker.begin_action_resolution(
            ticket,
            control_id="control-A",
            resolution=resolution,
            authorization_current=lambda: True,
        )
        await asyncio.sleep(0)
        control = next(item[2] for item in sent if item[1] == CONTROL_EVENT)
        assert set(control) == {
            "method",
            "contract_version",
            "bridge_id",
            "load_generation_id",
            "control_id",
            "context_id",
            "browser_session_id",
            "turn_id",
            "op_id",
            "action_id",
            *resolution,
        }
        type_binding = OperationBinding(
            principal,
            "sid-A",
            "generation-A",
            "context-A",
            "browser-session-A",
            "turn-A",
            "action-B",
            "op-B",
        )
        type_args = {
            "ref": REF,
            "text": TYPE_TEXT,
            "text_sha256": TYPE_TEXT_SHA256,
            "expected_action_class": "sensitive_input",
        }
        with pytest.raises(BrowserBridgeBrokerError):
            await broker.begin_operation(
                type_binding,
                action="type",
                target={"tab_handle": TAB_HANDLE},
                args={**type_args, "text_sha256": "c" * 64},
                timeout_ms=30_000,
                required_capabilities=["type", "trusted_input_v1"],
                display={"cursor": True, "foreground": False},
            )
        type_ticket = await broker.begin_operation(
            type_binding,
            action="type",
            target={"tab_handle": TAB_HANDLE},
            args=type_args,
            timeout_ms=30_000,
            required_capabilities=["type", "trusted_input_v1"],
            display={"cursor": True, "foreground": False},
        )
        assert type_ticket.target_ref == REF
        assert type_ticket.expected_action_class == "sensitive_input"
        assert type_ticket.text_sha256 == TYPE_TEXT_SHA256
        assert TYPE_TEXT not in repr(type_ticket)
        type_classification = {
            "kind": "text",
            "sensitivity": "sensitive",
            "text_sha256": TYPE_TEXT_SHA256,
        }
        await broker.begin_action_resolution(
            type_ticket,
            control_id="control-B",
            resolution={
                "challenge_id": "challenge-B",
                "tab_handle": TAB_HANDLE,
                "document_id": DOCUMENT_ID,
                "document_epoch": 1,
                "canonical_parameter_hash": type_ticket.canonical_parameter_hash,
                "target_fingerprint": "c" * 64,
                "origin": ORIGIN,
                "action_class": "sensitive_input",
                "data_classification": type_classification,
                "decision": "decline",
                "grant": None,
            },
            authorization_current=lambda: True,
        )
        await asyncio.sleep(0)
        type_control = next(
            item[2]
            for item in sent
            if item[1] == CONTROL_EVENT and item[2]["control_id"] == "control-B"
        )
        assert type_control["data_classification"] == type_classification
        broker.disconnect(
            principal=principal,
            connector_sid="sid-A",
            load_generation_id="generation-A",
        )

    asyncio.run(scenario())


def test_protected_action_api_is_decision_only_and_default_unavailable(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from plugins._a0_connector.api import browser_bridge_approval as endpoint

    async def scenario() -> None:
        operation = _operation(asyncio.get_running_loop(), _principal())
        harness = _Harness(operation)
        harness.authority.register_challenge(_notice(operation))
        monkeypatch.setattr(endpoint, "selected_bridge", lambda _context: None)
        monkeypatch.setattr(
            endpoint,
            "get_browser_bridge_action_authority",
            lambda: pytest.fail("unselected context resolved action authority"),
        )
        empty = await endpoint.BrowserBridgeApproval(None, None).process(
            {"action": "list", "context_id": "context-missing"},
            request=None,
        )
        assert json.loads(empty.get_data(as_text=True))["challenges"] == []
        monkeypatch.setattr(
            endpoint,
            "selected_bridge",
            lambda context: "bridge-A" if context == "context-A" else None,
        )
        monkeypatch.setattr(
            endpoint,
            "get_browser_bridge_action_authority",
            lambda: harness.authority,
        )
        handler = endpoint.BrowserBridgeApproval(None, None)
        listing = await handler.process(
            {"action": "list", "context_id": "context-A"}, request=None
        )
        listed = json.loads(listing.get_data(as_text=True))
        assert listing.headers["Cache-Control"] == "no-store"
        assert listed == {
            "contract": ACTION_AUTHORITY_CONTRACT,
            "approval_version": 1,
            "browser_control_ready": False,
            "challenges": [
                harness.authority.list_pending(
                    subject_id="single_user",
                    context_id="context-A",
                    bridge_id="bridge-A",
                )[0]
            ],
        }
        rejected = await handler.process(
            {
                "challenge_id": "challenge-A",
                "choice": "approve_once",
                "target_fingerprint": "c" * 64,
            },
            request=None,
        )
        assert rejected.status_code == 400
        response = await handler.process(
            {"challenge_id": "challenge-A", "choice": "decline"},
            request=None,
        )
        assert json.loads(response.get_data(as_text=True)) == {
            "contract": ACTION_AUTHORITY_CONTRACT,
            "approval_version": 1,
            "browser_control_ready": False,
            "challenge_id": "challenge-A",
            "decision": "declined",
            "control_id": "control-A",
            "status": "accepted",
        }
        await harness.authority.close()

    asyncio.run(scenario())
