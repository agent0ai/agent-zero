from __future__ import annotations

import asyncio
from copy import deepcopy
from dataclasses import replace
import hashlib
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
    WS_NAMESPACE,
    BrowserBridgeCriticalEventReceiver,
    BrowserBridgeEventDenied,
    BrowserBridgeEventError,
    LeaseInvalidation,
    TurnFinalizedNotice,
)


def _route(generation: str = "generation-A") -> BrowserBridgeContextRoute:
    principal = WsPrincipal(
        principal_type="browser_bridge",
        principal_id="bridge-A",
        subject_id="single_user",
        scopes=frozenset({"browser.operate"}),
        handler_path="plugins/_a0_connector/ws_connector",
        handler_id=RESTRICTED_HANDLER_ID,
        inbound_events=frozenset({BROWSER_EVENT}),
        outbound_events=frozenset({BROWSER_EVENT_ACK}),
        key_generation=3,
    )
    return BrowserBridgeContextRoute(principal, "sid-A", generation)


def _lease_event(
    sequence: int,
    *,
    event_id: str | None = None,
    generation: str = "generation-A",
    change: str = "tab_closed",
    state: str = "closed",
    reason_code: str | None = "TAB_CLOSED",
) -> dict[str, Any]:
    return {
        "contract_version": 1,
        "event_id": event_id or f"event-{sequence}",
        "load_generation_id": generation,
        "event_sequence": sequence,
        "delivery": "critical",
        "event_type": "lease.changed",
        "observed_at_ms": 1_000 + sequence,
        "context_id": "context-A",
        "browser_session_id": "browser-session-A",
        "turn_id": "turn-A",
        "op_id": None,
        "action_id": None,
        "data": {
            "lease_id_digest": hashlib.sha256(b"lease-A").hexdigest(),
            "browser_id_digest": hashlib.sha256(b"browser-A").hexdigest(),
            "state": state,
            "ownership": "created",
            "disposition": "ephemeral",
            "change": change,
            "reason_code": reason_code,
        },
    }


def _finalized_event(sequence: int) -> dict[str, Any]:
    return {
        "contract_version": 1,
        "event_id": f"final-event-{sequence}",
        "load_generation_id": "generation-A",
        "event_sequence": sequence,
        "delivery": "critical",
        "event_type": "turn.finalized",
        "observed_at_ms": 2_000 + sequence,
        "context_id": "context-A",
        "browser_session_id": "browser-session-A",
        "turn_id": "turn-A",
        "op_id": None,
        "action_id": None,
        "data": {
            "control_id": "finalize-control-A",
            "status": "completed",
            "closed_count": 2,
            "released_count": 1,
            "retained_count": 1,
            "already_finalized_count": 0,
            "error_count": 0,
        },
    }


class _Manager:
    def __init__(self) -> None:
        self.calls: list[tuple[str, str, str, dict[str, Any], dict[str, Any]]] = []

    async def emit_to(
        self,
        namespace: str,
        sid: str,
        event: str,
        data: dict[str, Any],
        **kwargs: Any,
    ) -> None:
        self.calls.append((namespace, sid, event, deepcopy(data), dict(kwargs)))


def _receiver(
    *,
    route: BrowserBridgeContextRoute,
    stored: list[Any],
    manager: _Manager,
    leases: list[LeaseInvalidation] | None = None,
    finalizations: list[TurnFinalizedNotice] | None = None,
    current: list[BrowserBridgeContextRoute] | None = None,
    save=None,
) -> BrowserBridgeCriticalEventReceiver:
    leases = leases if leases is not None else []
    finalizations = finalizations if finalizations is not None else []
    current = current if current is not None else [route]

    def is_current(candidate: BrowserBridgeContextRoute) -> bool:
        expected = current[0]
        return (
            candidate.principal is expected.principal
            and candidate.connector_sid == expected.connector_sid
            and candidate.load_generation_id == expected.load_generation_id
        )

    return BrowserBridgeCriticalEventReceiver(
        manager=manager,
        server_instance_id=lambda: "server-A",
        current_route_verifier=is_current,
        invalidate_lease=lambda value: leases.append(value),
        observe_finalization=lambda value: finalizations.append(value),
        load=lambda: deepcopy(stored[0]),
        save=save
        or (lambda value: stored.__setitem__(0, deepcopy(value))),
        ack_emit_seconds=0.1,
    )


def test_contiguous_event_is_hash_only_durable_before_exact_ack_and_replay() -> None:
    async def scenario() -> None:
        route = _route()
        stored: list[Any] = [None]
        manager = _Manager()
        invalidations: list[LeaseInvalidation] = []
        receiver = _receiver(
            route=route,
            stored=stored,
            manager=manager,
            leases=invalidations,
        )
        event = _lease_event(1)
        assert await receiver.receive(route, event) == {
            "contract_version": 1,
            "event_id": "event-1",
            "status": "accepted",
        }
        assert len(invalidations) == 1
        invalidation = invalidations[0]
        assert invalidation.principal is route.principal
        assert invalidation.connector_sid == "sid-A"
        assert invalidation.change == "tab_closed"
        assert invalidation.state == "closed"
        assert manager.calls[0][0:3] == (
            WS_NAMESPACE,
            "sid-A",
            BROWSER_EVENT_ACK,
        )
        assert manager.calls[0][3] == {
            "contract_version": 1,
            "bridge_id": "bridge-A",
            "load_generation_id": "generation-A",
            "highest_contiguous_event_sequence": 1,
        }
        assert manager.calls[0][4]["handler_id"] == RESTRICTED_HANDLER_ID
        assert manager.calls[0][4]["expected_principal"] is route.principal
        persisted = repr(stored[0])
        for raw in (
            "server-A",
            "bridge-A",
            "single_user",
            "generation-A",
            "event-1",
            "context-A",
            "browser-session-A",
            event["data"]["lease_id_digest"],
        ):
            assert raw not in persisted

        await receiver.receive(route, event)
        assert len(invalidations) == 1
        assert len(manager.calls) == 2
        assert manager.calls[-1][3]["highest_contiguous_event_sequence"] == 1
        with pytest.raises(BrowserBridgeEventError) as conflict:
            await receiver.receive(route, _lease_event(1, event_id="changed-event"))
        assert conflict.value.code == "EVENT_SEQUENCE_CONFLICT"

    asyncio.run(scenario())


def test_gap_never_acks_forward_and_callback_failure_never_moves_cursor() -> None:
    async def scenario() -> None:
        route = _route()
        stored: list[Any] = [None]
        manager = _Manager()
        invalidations: list[LeaseInvalidation] = []
        receiver = _receiver(
            route=route,
            stored=stored,
            manager=manager,
            leases=invalidations,
        )
        await receiver.receive(route, _lease_event(2, event_id="event-two"))
        assert manager.calls == []
        assert next(iter(stored[0]["routes"].values()))["cursor"] == 0
        await receiver.receive(route, _lease_event(1, event_id="event-one"))
        assert manager.calls[-1][3]["highest_contiguous_event_sequence"] == 2
        assert len(invalidations) == 2

        receiver._invalidate_lease = lambda _value: (_ for _ in ()).throw(
            RuntimeError("raw private callback error")
        )
        with pytest.raises(BrowserBridgeEventError) as callback_error:
            await receiver.receive(route, _lease_event(3, event_id="event-three"))
        assert callback_error.value.code == "EVENT_CALLBACK_FAILED"
        assert "private" not in str(callback_error.value)
        assert next(iter(stored[0]["routes"].values()))["cursor"] == 2
        assert manager.calls[-1][3]["highest_contiguous_event_sequence"] == 2

        replayed: list[LeaseInvalidation] = []
        recovered = _receiver(
            route=route,
            stored=stored,
            manager=manager,
            leases=replayed,
        )
        await recovered.receive(route, _lease_event(3, event_id="event-three"))
        assert len(replayed) == 1
        assert next(iter(stored[0]["routes"].values()))["cursor"] == 3
        assert manager.calls[-1][3]["highest_contiguous_event_sequence"] == 3

    asyncio.run(scenario())


def test_finalization_notice_is_informational_and_unsupported_events_fail_closed() -> None:
    async def scenario() -> None:
        route = _route()
        stored: list[Any] = [None]
        manager = _Manager()
        notices: list[TurnFinalizedNotice] = []
        receiver = _receiver(
            route=route,
            stored=stored,
            manager=manager,
            finalizations=notices,
        )
        event = _finalized_event(1)
        await receiver.receive(route, event)
        assert len(notices) == 1
        notice = notices[0]
        assert notice.status == "completed" and notice.closed_count == 2
        assert not hasattr(notice, "control_id")
        assert notice.control_id_digest == hashlib.sha256(
            b"finalize-control-A"
        ).hexdigest()
        assert "finalize-control-A" not in repr(stored[0])

        for invalid in (
            {**_lease_event(2), "delivery": "best_effort"},
            {**_lease_event(2), "event_type": "challenge.required"},
            {**_lease_event(2), "event_type": {"untrusted": True}},
            {
                **_lease_event(2),
                "data": {**_lease_event(2)["data"], "origin": "https://secret.example"},
            },
            {
                **_lease_event(2),
                "data": {**_lease_event(2)["data"], "state": ["closed"]},
            },
            {
                **_lease_event(2),
                "data": {
                    **_lease_event(2)["data"],
                    "change": "finalized",
                    "state": "closed",
                    "reason_code": "TAB_CLOSED",
                },
            },
            {
                **_finalized_event(2),
                "data": {**_finalized_event(2)["data"], "error_count": 257},
            },
        ):
            with pytest.raises(BrowserBridgeEventError):
                await receiver.receive(route, invalid)
        assert len(notices) == 1

        unavailable = BrowserBridgeCriticalEventReceiver(
            manager=manager,
            server_instance_id=lambda: "server-A",
            current_route_verifier=lambda _route: True,
            load=lambda: None,
            save=lambda _value: None,
        )
        # Passive creation neither grants nor withdraws Core authority and does
        # not require an invalidation callback.
        await unavailable.receive(
            route,
            _lease_event(
                1,
                event_id="passive-created",
                change="created",
                state="active",
                reason_code=None,
            ),
        )
        with pytest.raises(BrowserBridgeEventError) as missing_callback:
            await unavailable.receive(route, _lease_event(2))
        assert missing_callback.value.code == "EVENT_CALLBACK_FAILED"

    asyncio.run(scenario())


def test_verified_generation_replacement_cannot_be_reset_by_old_replay() -> None:
    async def scenario() -> None:
        old_route = _route("generation-old")
        new_route = replace(old_route, load_generation_id="generation-new")
        current = [old_route]
        stored: list[Any] = [None]
        manager = _Manager()
        receiver = _receiver(
            route=old_route,
            stored=stored,
            manager=manager,
            current=current,
        )
        await receiver.receive(
            old_route, _lease_event(1, generation="generation-old")
        )
        current[0] = new_route
        await receiver.receive(
            new_route, _lease_event(1, event_id="new-event", generation="generation-new")
        )
        assert len(stored[0]["routes"]) == 1
        assert next(iter(stored[0]["routes"].values()))["cursor"] == 1
        calls_before = len(manager.calls)
        with pytest.raises(BrowserBridgeEventDenied):
            await receiver.receive(
                old_route,
                _lease_event(2, event_id="old-replay", generation="generation-old"),
            )
        assert len(manager.calls) == calls_before
        assert len(stored[0]["routes"]) == 1
        assert next(iter(stored[0]["routes"].values()))["cursor"] == 1

    asyncio.run(scenario())
