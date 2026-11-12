from __future__ import annotations

import asyncio
from copy import deepcopy
from dataclasses import replace
import hashlib
import io
import json
from types import SimpleNamespace
from typing import Any

import pytest

from helpers.ws_principal import WsPrincipal
from plugins._a0_connector.helpers.browser_bridge_context import (
    BrowserBridgeContextRoute,
)
from plugins._a0_connector.helpers.browser_bridge_events import (
    BROWSER_EVENT,
    BROWSER_EVENT_ACK,
    RESTRICTED_HANDLER_ID,
    BrowserBridgeCriticalEventReceiver,
    BrowserBridgeEventError,
    SiteChallengeNotice,
)
from plugins._a0_connector.helpers.browser_bridge_operations import (
    BrokerCompletion,
    ControlBinding,
    ControlTicket,
    OperationBinding,
    OperationTicket,
)
from plugins._a0_connector.helpers.browser_bridge_site_authority import (
    MAX_TURN_GRANT_TTL_MS,
    SITE_AUTHORITY_CONTRACT,
    BrowserBridgeSiteAuthorityRepository,
    BrowserBridgeSiteAuthorityUnavailable,
)


NOW_MS = 1_000_000
ORIGIN = "https://example.com"
PARAMETER_HASH = "a" * 64
LEASE_ID = "lease-A"
TAB_HANDLE = "browser-A"


def _principal(subject: str = "single_user") -> WsPrincipal:
    return WsPrincipal(
        principal_type="browser_bridge",
        principal_id="bridge-A",
        subject_id=subject,
        scopes=frozenset(
            {"browser.operate", "browser.control", "browser.approval"}
        ),
        handler_path="plugins/_a0_connector/ws_connector",
        handler_id=RESTRICTED_HANDLER_ID,
        inbound_events=frozenset({BROWSER_EVENT}),
        outbound_events=frozenset({BROWSER_EVENT_ACK}),
        key_generation=3,
    )


def _operation(
    loop: asyncio.AbstractEventLoop,
    principal: WsPrincipal,
    *,
    op_id: str = "op-A",
    action_id: str = "action-A",
    turn_id: str = "turn-A",
    origin: str = ORIGIN,
) -> OperationTicket:
    binding = OperationBinding(
        principal=principal,
        connector_sid="sid-A",
        load_generation_id="generation-A",
        context_id="context-A",
        browser_session_id="browser-session-A",
        turn_id=turn_id,
        action_id=action_id,
        op_id=op_id,
    )
    return OperationTicket(
        binding=binding,
        deadline_ms=NOW_MS + 90_000,
        effect="mutating",
        _future=loop.create_future(),
        action="navigate",
        target_tab_handle=TAB_HANDLE,
        canonical_parameter_hash=PARAMETER_HASH,
        destination_origin=origin,
    )


def _fingerprint(
    *,
    origin: str = ORIGIN,
    generation: str = "generation-A",
    document_id: str | None = None,
    document_epoch: int = 0,
) -> str:
    value = {
        "action_class": "navigate",
        "browser_id_digest": hashlib.sha256(TAB_HANDLE.encode()).hexdigest(),
        "document_epoch": document_epoch,
        "document_id": document_id,
        "lease_id_digest": hashlib.sha256(LEASE_ID.encode()).hexdigest(),
        "load_generation_id": generation,
        "origin": origin,
    }
    encoded = json.dumps(
        value, ensure_ascii=False, sort_keys=True, separators=(",", ":")
    ).encode()
    return hashlib.sha256(encoded).hexdigest()


def _notice(
    principal: WsPrincipal,
    *,
    challenge_id: str = "challenge-A",
    op_id: str = "op-A",
    action_id: str = "action-A",
    turn_id: str = "turn-A",
    origin: str = ORIGIN,
    target_fingerprint: str | None = None,
) -> SiteChallengeNotice:
    return SiteChallengeNotice(
        principal=principal,
        connector_sid="sid-A",
        load_generation_id="generation-A",
        context_id="context-A",
        browser_session_id="browser-session-A",
        turn_id=turn_id,
        action_id=action_id,
        op_id=op_id,
        challenge_id=challenge_id,
        origin=origin,
        canonical_parameter_hash=PARAMETER_HASH,
        target_fingerprint=target_fingerprint or _fingerprint(origin=origin),
        lease_id_digest=hashlib.sha256(LEASE_ID.encode()).hexdigest(),
        browser_id_digest=hashlib.sha256(TAB_HANDLE.encode()).hexdigest(),
        document_id=None,
        document_epoch=0,
        summary="Untrusted extension wording must not be shown or retained.",
        expires_at_ms=NOW_MS + 60_000,
    )


class _Harness:
    def __init__(
        self,
        operation: OperationTicket,
        *,
        completion_gate: asyncio.Future[BrokerCompletion] | None = None,
    ) -> None:
        self.operations = {operation.binding.op_id: operation}
        self.operation = operation
        self.selection_allowed = True
        self.lease = SimpleNamespace(
            binding=operation.binding,
            lease_id=LEASE_ID,
            tab_handle=TAB_HANDLE,
            origin=ORIGIN,
        )
        self.completion_gate = completion_gate
        self.resolutions: list[dict[str, Any]] = []
        self.control_index = 0
        self.grant_index = 0
        self.current_route = BrowserBridgeContextRoute(
            operation.binding.principal,
            operation.binding.connector_sid,
            operation.binding.load_generation_id,
        )

    def current_operation(self, **kwargs: Any) -> OperationTicket | None:
        operation = self.operations.get(kwargs["op_id"])
        if operation is None:
            return None
        binding = operation.binding
        if (
            binding.principal is kwargs["principal"]
            and binding.connector_sid == kwargs["connector_sid"]
            and binding.load_generation_id == kwargs["load_generation_id"]
        ):
            return operation
        return None

    @staticmethod
    def remaining_operation_ms(_operation: OperationTicket) -> int:
        return 90_000

    def lease_for(self, binding: OperationBinding, handle: str) -> Any | None:
        if (
            binding.principal is self.lease.binding.principal
            and binding.connector_sid == self.lease.binding.connector_sid
            and binding.load_generation_id == self.lease.binding.load_generation_id
            and binding.context_id == self.lease.binding.context_id
            and binding.browser_session_id
            == self.lease.binding.browser_session_id
            and binding.turn_id == self.lease.binding.turn_id
            and handle == self.lease.tab_handle
        ):
            return self.lease
        return None

    def route_verifier(self, route: BrowserBridgeContextRoute) -> bool:
        current = self.current_route
        return (
            route.principal is current.principal
            and route.connector_sid == current.connector_sid
            and route.load_generation_id == current.load_generation_id
        )

    def turn_current(self, binding: OperationBinding) -> bool:
        return any(
            candidate.binding.principal is binding.principal
            and candidate.binding.connector_sid == binding.connector_sid
            and candidate.binding.load_generation_id == binding.load_generation_id
            and candidate.binding.context_id == binding.context_id
            and candidate.binding.browser_session_id == binding.browser_session_id
            and candidate.binding.turn_id == binding.turn_id
            for candidate in self.operations.values()
        )

    def selection_current(self, context_id: str, bridge_id: str) -> bool:
        return bool(
            self.selection_allowed
            and context_id == self.operation.binding.context_id
            and bridge_id == self.operation.binding.bridge_id
        )

    def control_id(self) -> str:
        self.control_index += 1
        return f"control-{chr(64 + self.control_index)}"

    def grant_id(self) -> str:
        self.grant_index += 1
        return f"grant-{chr(64 + self.grant_index)}"

    async def begin_resolution(
        self,
        operation: OperationTicket,
        **kwargs: Any,
    ) -> ControlTicket:
        assert operation in self.operations.values()
        assert kwargs["authorization_current"]() is True
        self.resolutions.append(deepcopy(kwargs))
        binding = operation.binding
        return ControlTicket(
            ControlBinding(
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
            NOW_MS + kwargs["timeout_ms"],
            asyncio.get_running_loop().create_future(),
        )

    async def wait_control(self, ticket: ControlTicket) -> BrokerCompletion:
        if self.completion_gate is not None:
            return await self.completion_gate
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

    def repository(self, **kwargs: Any) -> BrowserBridgeSiteAuthorityRepository:
        return BrowserBridgeSiteAuthorityRepository(
            current_operation=self.current_operation,
            remaining_operation_ms=self.remaining_operation_ms,
            lease_for=self.lease_for,
            route_verifier=self.route_verifier,
            turn_current=self.turn_current,
            selection_current=self.selection_current,
            begin_resolution=self.begin_resolution,
            wait_control=self.wait_control,
            server_instance_id=lambda: "server-A",
            clock_ms=lambda: NOW_MS,
            control_id_factory=self.control_id,
            grant_id_factory=self.grant_id,
            **kwargs,
        )


def test_challenge_registration_requires_exact_retained_intent_lease_and_fingerprint() -> None:
    async def scenario() -> None:
        principal = _principal()
        operation = _operation(asyncio.get_running_loop(), principal)
        harness = _Harness(operation)
        repository = harness.repository()
        challenge = repository.register_event(_notice(principal))
        assert challenge is None
        assert repository.list_pending(subject_id="single_user") == (
            {
                "challenge_id": "challenge-A",
                "origin": ORIGIN,
                "action_class": "navigate",
                "summary": f"Allow navigation to {ORIGIN}?",
                "options": ["deny", "allow_once", "allow_turn"],
                "expires_at_ms": NOW_MS + 60_000,
            },
        )
        assert repository.list_pending(
            subject_id="single_user",
            context_id="context-A",
            bridge_id="bridge-A",
        ) == repository.list_pending(subject_id="single_user")
        assert repository.list_pending(
            subject_id="single_user",
            context_id="context-B",
            bridge_id="bridge-A",
        ) == ()
        assert "Untrusted extension wording" not in repr(
            repository.list_pending(subject_id="single_user")
        )
        assert repository.list_pending(subject_id="another_user") == ()

        other = _operation(
            asyncio.get_running_loop(),
            principal,
            op_id="op-B",
            action_id="action-B",
        )
        harness.operations["op-B"] = other
        for invalid in (
            _notice(
                principal,
                challenge_id="challenge-B",
                op_id="op-B",
                action_id="action-B",
                target_fingerprint="b" * 64,
            ),
            replace(
                _notice(
                    principal,
                    challenge_id="challenge-C",
                    op_id="op-B",
                    action_id="action-B",
                ),
                lease_id_digest="c" * 64,
            ),
            replace(
                _notice(
                    principal,
                    challenge_id="challenge-D",
                    op_id="op-B",
                    action_id="action-B",
                ),
                canonical_parameter_hash="d" * 64,
            ),
        ):
            with pytest.raises(BrowserBridgeSiteAuthorityUnavailable):
                repository.register_event(invalid)
        await repository.close()

    asyncio.run(scenario())


def test_allow_once_is_idempotent_and_grants_only_after_matching_control_result() -> None:
    async def scenario() -> None:
        principal = _principal()
        operation = _operation(asyncio.get_running_loop(), principal)
        gate: asyncio.Future[BrokerCompletion] = (
            asyncio.get_running_loop().create_future()
        )
        harness = _Harness(operation, completion_gate=gate)
        repository = harness.repository()
        repository.register_event(_notice(principal))
        first = await repository.decide(
            subject_id="single_user",
            challenge_id="challenge-A",
            decision="allow_once",
        )
        second = await repository.decide(
            subject_id="single_user",
            challenge_id="challenge-A",
            decision="allow_once",
        )
        assert first is second
        assert first.as_public_dict() == second.as_public_dict()
        await asyncio.sleep(0)
        assert repository.resolution_task_count == 1
        assert repository.grant_for_operation(operation, origin=ORIGIN) is None
        resolution = harness.resolutions[0]["resolution"]
        assert set(resolution) == {
            "challenge_id",
            "tab_handle",
            "document_id",
            "document_epoch",
            "canonical_parameter_hash",
            "target_fingerprint",
            "origin",
            "action_class",
            "decision",
            "grant",
        }
        assert resolution["grant"] == {
            "origin_grant_id": "grant-A",
            "scope": "operation",
            "origin": ORIGIN,
            "expires_at_ms": NOW_MS + 60_000,
        }
        gate.set_result(
            BrokerCompletion(
                ok=True,
                result={
                    "contract_version": 1,
                    "control_id": "control-A",
                    "challenge_id": "challenge-A",
                    "status": "resolved",
                    "decision": "allow_once",
                },
            )
        )
        await asyncio.sleep(0)
        await asyncio.sleep(0)
        grant = repository.grant_for_operation(operation, origin=ORIGIN)
        assert grant is not None and grant.scope == "operation"
        assert repository.grant_for_operation(
            replace(operation, destination_origin="https://evil.example"),
            origin=ORIGIN,
        ) is None
        repository.cancel_operation(operation)
        assert repository.grant_for_operation(operation, origin=ORIGIN) is None
        await repository.close()

    asyncio.run(scenario())


def test_site_decision_is_withdrawn_when_server_selection_changes() -> None:
    async def scenario() -> None:
        principal = _principal()
        operation = _operation(asyncio.get_running_loop(), principal)
        harness = _Harness(operation)
        repository = harness.repository()
        repository.register_event(_notice(principal))
        harness.selection_allowed = False
        with pytest.raises(BrowserBridgeSiteAuthorityUnavailable):
            await repository.decide(
                subject_id="single_user",
                challenge_id="challenge-A",
                decision="allow_once",
            )
        assert harness.resolutions == []
        await repository.close()

        queued_operation = _operation(
            asyncio.get_running_loop(), _principal()
        )
        queued = _Harness(queued_operation)
        queued_repository = queued.repository()
        queued_repository.register_event(_notice(queued_operation.binding.principal))
        await queued_repository.decide(
            subject_id="single_user",
            challenge_id="challenge-A",
            decision="allow_once",
        )
        queued.selection_allowed = False
        await asyncio.sleep(0)
        assert queued.resolutions == []
        with pytest.raises(BrowserBridgeSiteAuthorityUnavailable):
            await queued_repository.decide(
                subject_id="single_user",
                challenge_id="challenge-A",
                decision="allow_once",
            )
        await queued_repository.close()

    asyncio.run(scenario())


def test_allow_turn_is_exact_route_and_turn_bound_then_lifecycle_revoked() -> None:
    async def scenario() -> None:
        principal = _principal()
        operation = _operation(asyncio.get_running_loop(), principal)
        harness = _Harness(operation)
        repository = harness.repository()
        repository.register_event(_notice(principal))
        await repository.decide(
            subject_id="single_user",
            challenge_id="challenge-A",
            decision="allow_turn",
        )
        await asyncio.sleep(0)
        await asyncio.sleep(0)
        next_operation = _operation(
            asyncio.get_running_loop(),
            principal,
            op_id="op-next",
            action_id="action-next",
        )
        harness.operations[next_operation.binding.op_id] = next_operation
        turn_grant = repository.turn_grant_for(
            next_operation.binding,
            origin=ORIGIN,
        )
        assert turn_grant is not None and turn_grant.scope == "turn"
        grant = repository.grant_for_operation(next_operation, origin=ORIGIN)
        assert grant is not None and grant.scope == "turn"
        assert grant.expires_at_ms == NOW_MS + MAX_TURN_GRANT_TTL_MS
        assert repository.grant_for_operation(
            replace(next_operation, destination_origin="https://other.example"),
            origin=ORIGIN,
        ) is None
        repository.register_event(
            _notice(
                principal,
                challenge_id="challenge-B",
                op_id="op-next",
                action_id="action-next",
            )
        )
        assert repository.list_pending(subject_id="single_user") == ()
        await asyncio.sleep(0)
        await asyncio.sleep(0)
        assert len(harness.resolutions) == 2
        assert harness.resolutions[-1]["resolution"]["decision"] == "allow_turn"
        assert harness.resolutions[-1]["resolution"]["grant"]["origin_grant_id"] == (
            turn_grant.origin_grant_id
        )
        summary = repository.finalize_turn(
            principal=principal,
            connector_sid="sid-A",
            load_generation_id="generation-A",
            context_id="context-A",
            browser_session_id="browser-session-A",
            turn_id="turn-A",
        )
        assert summary.grants == 1
        assert repository.grant_for_operation(next_operation, origin=ORIGIN) is None
        await repository.close()

    asyncio.run(scenario())


class _Manager:
    def __init__(self) -> None:
        self.calls: list[tuple[Any, ...]] = []

    async def emit_to(self, *args: Any, **kwargs: Any) -> None:
        self.calls.append((*args, kwargs))


def _challenge_event(notice: SiteChallengeNotice) -> dict[str, Any]:
    return {
        "contract_version": 1,
        "event_id": "event-challenge-A",
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
            "kind": "site",
            "origin": notice.origin,
            "action_class": "navigate",
            "canonical_parameter_hash": notice.canonical_parameter_hash,
            "target_fingerprint": notice.target_fingerprint,
            "lease_id_digest": notice.lease_id_digest,
            "browser_id_digest": notice.browser_id_digest,
            "document_id": notice.document_id,
            "document_epoch": notice.document_epoch,
            "summary": notice.summary,
            "options": ["deny", "allow_once", "allow_turn"],
            "expires_at_ms": notice.expires_at_ms,
        },
    }


def test_critical_challenge_registration_precedes_cursor_and_persists_hashes_only() -> None:
    async def scenario() -> None:
        principal = _principal()
        operation = _operation(asyncio.get_running_loop(), principal)
        harness = _Harness(operation)
        repository = harness.repository()
        route = harness.current_route
        state: list[Any] = [None]
        manager = _Manager()
        receiver = BrowserBridgeCriticalEventReceiver(
            manager=manager,
            server_instance_id=lambda: "server-A",
            current_route_verifier=harness.route_verifier,
            register_site_challenge=repository.register_event,
            load=lambda: deepcopy(state[0]),
            save=lambda value: state.__setitem__(0, deepcopy(value)),
            ack_emit_seconds=0.1,
        )
        notice = _notice(principal)
        await receiver.receive(route, _challenge_event(notice))
        assert repository.pending_count == 1
        assert next(iter(state[0]["routes"].values()))["cursor"] == 1
        persisted = repr(state[0])
        for raw in (ORIGIN, notice.summary, notice.target_fingerprint):
            assert raw not in persisted
        assert manager.calls[-1][2] == BROWSER_EVENT_ACK

        rejected_state: list[Any] = [None]
        rejected = BrowserBridgeCriticalEventReceiver(
            manager=manager,
            server_instance_id=lambda: "server-A",
            current_route_verifier=harness.route_verifier,
            register_site_challenge=repository.register_event,
            load=lambda: deepcopy(rejected_state[0]),
            save=lambda value: rejected_state.__setitem__(0, deepcopy(value)),
            ack_emit_seconds=0.1,
        )
        invalid = replace(
            _notice(
                principal,
                challenge_id="challenge-B",
                op_id="op-A",
                action_id="action-A",
            ),
            target_fingerprint="b" * 64,
        )
        invalid_event = _challenge_event(invalid)
        invalid_event["event_id"] = "event-challenge-B"
        with pytest.raises(BrowserBridgeEventError) as failure:
            await rejected.receive(route, invalid_event)
        assert failure.value.code == "EVENT_CALLBACK_FAILED"
        assert next(iter(rejected_state[0]["routes"].values()))["cursor"] == 0
        await repository.close()

    asyncio.run(scenario())


def test_protected_api_is_strict_no_store_and_decision_only(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from plugins._a0_connector.api import browser_bridge_site_authority as endpoint

    public = {
        "challenge_id": "challenge-A",
        "origin": ORIGIN,
        "action_class": "navigate",
        "summary": f"Allow navigation to {ORIGIN}?",
        "options": ["deny", "allow_once", "allow_turn"],
        "expires_at_ms": NOW_MS + 60_000,
    }

    class Repository:
        def list_pending(
            self,
            *,
            subject_id: str,
            context_id: str,
            bridge_id: str,
        ) -> tuple[dict[str, Any], ...]:
            assert subject_id == "single_user"
            assert context_id == "context-A"
            assert bridge_id == "bridge-A"
            return (public,)

        async def decide(self, **kwargs: Any) -> Any:
            assert kwargs == {
                "subject_id": "single_user",
                "challenge_id": "challenge-A",
                "decision": "deny",
            }
            return SimpleNamespace(
                as_public_dict=lambda: {
                    "challenge_id": "challenge-A",
                    "decision": "deny",
                    "control_id": "control-A",
                    "status": "accepted",
                    "expires_at_ms": NOW_MS + 60_000,
                }
            )

    monkeypatch.setattr(endpoint, "selected_bridge", lambda _context: None)
    monkeypatch.setattr(
        endpoint,
        "get_browser_bridge_site_authority_repository",
        lambda: pytest.fail("unselected context resolved site authority"),
    )
    empty = asyncio.run(
        endpoint.BrowserBridgeSiteAuthority(None, None).process(
            {"action": "list", "context_id": "context-missing"},
            request=None,
        )
    )
    assert json.loads(empty.get_data(as_text=True))["challenges"] == []
    monkeypatch.setattr(
        endpoint,
        "get_browser_bridge_site_authority_repository",
        lambda: Repository(),
    )
    monkeypatch.setattr(
        endpoint,
        "selected_bridge",
        lambda context: "bridge-A" if context == "context-A" else None,
    )
    handler = endpoint.BrowserBridgeSiteAuthority(None, None)
    listed = asyncio.run(
        handler.process(
            {"action": "list", "context_id": "context-A"}, request=None
        )
    )
    listed_payload = json.loads(listed.get_data(as_text=True))
    assert handler.requires_auth() is True and handler.requires_csrf() is True
    assert listed.status_code == 200
    assert listed.headers["Cache-Control"] == "no-store"
    assert listed_payload == {
        "contract": SITE_AUTHORITY_CONTRACT,
        "authority_version": 1,
        "browser_control_ready": False,
        "challenges": [public],
    }
    decided = asyncio.run(
        handler.process(
            {
                "action": "decide",
                "challenge_id": "challenge-A",
                "decision": "deny",
            },
            request=None,
        )
    )
    assert json.loads(decided.get_data(as_text=True)) == {
        "contract": SITE_AUTHORITY_CONTRACT,
        "authority_version": 1,
        "browser_control_ready": False,
        "challenge_id": "challenge-A",
        "decision": "deny",
        "control_id": "control-A",
        "status": "accepted",
        "expires_at_ms": NOW_MS + 60_000,
    }
    extra = asyncio.run(
        handler.process(
            {
                "action": "decide",
                "challenge_id": "challenge-A",
                "decision": "deny",
                "origin": "https://attacker.example",
            },
            request=None,
        )
    )
    assert extra.status_code == 400

    raw = b'{"action":"list","action":"decide"}'
    request = SimpleNamespace(
        content_length=len(raw),
        is_json=True,
        stream=io.BytesIO(raw),
    )
    duplicate = asyncio.run(handler.handle_request(request))
    assert duplicate.status_code == 400


def test_saved_site_policy_auto_resolves_only_exact_live_navigation_and_rechecks_withdrawal():
    async def scenario():
        principal = _principal()
        operation = _operation(asyncio.get_running_loop(), principal)
        harness = _Harness(operation)
        allowed = ["all-sites-policy-generation"]
        repo = harness.repository(saved_origin_grant=lambda binding, origin: allowed[0])
        repo.register_challenge(_notice(principal))
        assert repo.list_pending(subject_id=principal.subject_id) == ()
        await asyncio.sleep(0)
        assert harness.resolutions[0]["resolution"]["decision"] == "allow_once"
        assert harness.resolutions[0]["resolution"]["grant"]["origin"] == ORIGIN
        assert harness.resolutions[0]["resolution"]["grant"]["scope"] == "operation"
        await repo.close()

        harness = _Harness(operation)
        repo = harness.repository(saved_origin_grant=lambda binding, origin: allowed[0])
        repo.register_challenge(_notice(principal))
        allowed[0] = None  # Withdraw before the scheduled control dispatch.
        await asyncio.sleep(0)
        assert harness.resolutions == []
        await repo.close()
    asyncio.run(scenario())


def test_default_repository_is_unavailable() -> None:
    repository = BrowserBridgeSiteAuthorityRepository()
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
    assert repository.turn_grant_for(binding, origin=ORIGIN) is None
