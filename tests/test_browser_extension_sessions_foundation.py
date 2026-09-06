from __future__ import annotations

import asyncio
from concurrent.futures import ThreadPoolExecutor
import copy
from dataclasses import replace
import itertools
import json
from pathlib import Path
from types import SimpleNamespace
import threading

import pytest

from helpers.ws_principal import WsPrincipal
from plugins._browser.helpers.extension_sessions import (
    ExtensionSessionLifecycle,
    ExtensionSessionRegistry,
    ExtensionSessionStateError,
    ProcessFinalizationDispatcher,
    TURN_FINALIZATION_PENDING,
    TURN_FINALIZED,
    TURN_OUTCOME_UNKNOWN,
    ValidatedExtensionRoute,
)


PROJECT_ROOT = Path(__file__).resolve().parents[1]
BRIDGE_ID = "Bridge-Session-1"
BROWSER_ID = f"extension:{BRIDGE_ID}"


class MemoryPersistence:
    def __init__(self, value=None):
        self.value = copy.deepcopy(value)
        self.writes = 0

    def load(self):
        return copy.deepcopy(self.value)

    def save(self, value):
        self.value = copy.deepcopy(value)
        self.writes += 1


def _registry(*, persistence=None, max_turns=64):
    counter = itertools.count(1)
    return ExtensionSessionRegistry(
        persistence=persistence or MemoryPersistence(),
        clock_ms=lambda: 1_700_000_000_000 + next(counter),
        id_factory=lambda: f"id_{next(counter)}",
        max_turns_per_session=max_turns,
    )


def _principal(bridge_id=BRIDGE_ID):
    return WsPrincipal(
        principal_type="browser_bridge",
        principal_id=bridge_id,
        subject_id="single_user",
        scopes=frozenset({"bridge.connect", "browser.control"}),
        handler_path="plugins/_a0_connector/ws_connector",
        handler_id="ws_connector.WsConnector",
        inbound_events=frozenset({"connector_browser_control_result"}),
        outbound_events=frozenset({"connector_browser_control"}),
        key_generation=4,
    )


def _route(bridge_id=BRIDGE_ID):
    return ValidatedExtensionRoute(
        bridge_id=bridge_id,
        browser_id=f"extension:{bridge_id}",
        principal=_principal(bridge_id),
        connector_sid="sid-current",
        load_generation_id="generation.current-1",
    )


def _agent(context_id="context-1"):
    context = SimpleNamespace(id=context_id)
    agent = SimpleNamespace(context=context)
    context.agent0 = agent
    context.streaming_agent = None
    return agent


def _extension_config(_agent):
    return {
        "runtime_backend": "host_required",
        "host_browser_selection": BROWSER_ID,
    }


def test_registry_keeps_one_pinned_session_and_allocates_fresh_turns():
    registry = _registry()

    first_session, first_turn = registry.begin_turn(
        context_id="context-1", browser_id=BROWSER_ID, bridge_id=BRIDGE_ID
    )
    second_session, second_turn = registry.begin_turn(
        context_id="context-1", browser_id=BROWSER_ID, bridge_id=BRIDGE_ID
    )

    assert second_session.browser_session_id == first_session.browser_session_id
    assert second_turn.turn_id != first_turn.turn_id
    assert [turn.turn_id for turn in second_session.turns] == [
        first_turn.turn_id,
        second_turn.turn_id,
    ]
    with pytest.raises(ExtensionSessionStateError) as exc:
        registry.begin_turn(
            context_id="context-1",
            browser_id="extension:another-bridge",
            bridge_id="another-bridge",
        )
    assert exc.value.code == "BRIDGE_PIN_CONFLICT"


def test_durable_projection_is_bounded_sanitized_and_contains_only_dispositions():
    persistence = MemoryPersistence()
    registry = _registry(persistence=persistence)
    session, turn = registry.begin_turn(
        context_id="context-safe", browser_id=BROWSER_ID, bridge_id=BRIDGE_ID
    )
    registry.record_disposition(
        context_id=session.context_id,
        browser_session_id=session.browser_session_id,
        turn_id=turn.turn_id,
        lease_id="lease_opaque_1",
        disposition="ephemeral",
    )
    route = _route()

    encoded = json.dumps(persistence.value, sort_keys=True)
    assert persistence.value["contract"] == "a0.browser-bridge.extension-sessions.v1"
    assert persistence.value["schema_version"] == 1
    assert '"lease_opaque_1": "ephemeral"' in encoded
    for forbidden in (
        route.connector_sid,
        route.load_generation_id,
        route.principal.subject_id,
        "principal",
        "public_key",
        "tab_id",
        "group_id",
        "tab_handle",
        "https://",
        "page_content",
        "selector",
        "script",
    ):
        assert forbidden not in encoded


def test_finalization_is_idempotent_exact_and_first_terminal_wins():
    registry = _registry()
    _session, turn = registry.begin_turn(
        context_id="context-1", browser_id=BROWSER_ID, bridge_id=BRIDGE_ID
    )

    first = registry.stage_finalize(
        context_id="context-1", turn_id=turn.turn_id, reason="completed"
    )
    repeated = registry.stage_finalize(
        context_id="context-1", turn_id=turn.turn_id, reason="different-repeat"
    )

    assert first == repeated
    assert first[0].dispositions == ()
    assert registry.settle_finalization(
        replace(first[0], browser_session_id="wrong-session"), TURN_FINALIZED
    ) == "mismatch"
    assert registry.settle_finalization(first[0], TURN_FINALIZED) == "settled"
    assert registry.settle_finalization(first[0], TURN_OUTCOME_UNKNOWN) == "duplicate"
    settled = registry.session("context-1")
    assert settled is not None
    assert settled.turns[0].state == TURN_FINALIZED
    assert "tabs_closed" not in repr(settled)


def test_retirement_deletes_only_proven_finalized_state_and_retains_uncertainty():
    finalized_registry = _registry()
    _, turn = finalized_registry.begin_turn(
        context_id="finalized-context", browser_id=BROWSER_ID, bridge_id=BRIDGE_ID
    )
    intent = finalized_registry.stage_finalize(
        context_id="finalized-context",
        turn_id=turn.turn_id,
        reason="reset",
        retire=True,
    )[0]
    assert finalized_registry.settle_finalization(intent, TURN_FINALIZED) == "settled"
    assert finalized_registry.session("finalized-context") is None

    unknown_registry = _registry()
    _, turn = unknown_registry.begin_turn(
        context_id="unknown-context", browser_id=BROWSER_ID, bridge_id=BRIDGE_ID
    )
    intent = unknown_registry.stage_finalize(
        context_id="unknown-context",
        turn_id=turn.turn_id,
        reason="removed",
        retire=True,
        remove=True,
    )[0]
    assert unknown_registry.settle_finalization(intent, TURN_OUTCOME_UNKNOWN) == "settled"
    retained = unknown_registry.session("unknown-context")
    assert retained is not None
    assert retained.remove_requested is True
    assert retained.turns[0].state == TURN_OUTCOME_UNKNOWN


def test_corrupt_or_over_capacity_state_fails_closed_without_rewrite():
    corrupt = MemoryPersistence(
        {
            "contract": "a0.browser-bridge.extension-sessions.v1",
            "schema_version": 1,
            "sessions": [],
            "page_content": "must-not-be-tolerated",
        }
    )
    registry = _registry(persistence=corrupt)

    with pytest.raises(ExtensionSessionStateError) as exc:
        registry.begin_turn(
            context_id="context-1", browser_id=BROWSER_ID, bridge_id=BRIDGE_ID
        )
    assert exc.value.code == "CORRUPT_STORE"
    assert corrupt.writes == 0

    bounded = _registry(max_turns=1)
    bounded.begin_turn(
        context_id="context-1", browser_id=BROWSER_ID, bridge_id=BRIDGE_ID
    )
    with pytest.raises(ExtensionSessionStateError) as exc:
        bounded.begin_turn(
            context_id="context-1", browser_id=BROWSER_ID, bridge_id=BRIDGE_ID
        )
    assert exc.value.code == "TURN_REGISTRY_FULL"


def test_dispatcher_leaves_missing_route_pending_and_marks_send_uncertain():
    registry = _registry()
    _, turn = registry.begin_turn(
        context_id="context-1", browser_id=BROWSER_ID, bridge_id=BRIDGE_ID
    )
    intent = registry.stage_finalize(
        context_id="context-1", turn_id=turn.turn_id, reason="canceled"
    )[0]

    with ThreadPoolExecutor(max_workers=1) as executor:
        dispatcher = ProcessFinalizationDispatcher(
            registry=registry,
            route_resolver=lambda _context_id, _bridge_id: None,
            sender=lambda _intent, _route: pytest.fail("sender must not run"),
            submitter=lambda coroutine: executor.submit(asyncio.run, coroutine),
        )
        assert dispatcher.replay_pending() == ()
        assert registry.session("context-1").turns[0].state == TURN_FINALIZATION_PENDING

        async def uncertain_sender(_intent, _route):
            raise ConnectionError("raw remote detail must not persist")

        dispatcher = ProcessFinalizationDispatcher(
            registry=registry,
            route_resolver=lambda _context_id, _bridge_id: _route(),
            sender=uncertain_sender,
            submitter=lambda coroutine: executor.submit(asyncio.run, coroutine),
        )
        assert dispatcher.replay_pending() == (intent.control_id,)
        for _ in range(100):
            state = registry.session("context-1").turns[0].state
            if state == TURN_OUTCOME_UNKNOWN:
                break
            threading.Event().wait(0.005)
        assert state == TURN_OUTCOME_UNKNOWN

    assert "raw remote detail" not in json.dumps(registry.sessions(), default=str)


def test_process_owned_dispatch_survives_the_callers_scope():
    registry = _registry()
    _, turn = registry.begin_turn(
        context_id="context-1", browser_id=BROWSER_ID, bridge_id=BRIDGE_ID
    )
    intent = registry.stage_finalize(
        context_id="context-1", turn_id=turn.turn_id, reason="completed"
    )[0]
    release = threading.Event()
    delivered = threading.Event()

    async def sender(_intent, _route):
        await asyncio.to_thread(release.wait)
        delivered.set()
        return TURN_FINALIZED

    with ThreadPoolExecutor(max_workers=1) as executor:
        dispatcher = ProcessFinalizationDispatcher(
            registry=registry,
            route_resolver=lambda _context_id, _bridge_id: _route(),
            sender=sender,
            submitter=lambda coroutine: executor.submit(asyncio.run, coroutine),
        )
        assert dispatcher.schedule((intent,)) == (intent.control_id,)
        assert dispatcher.inflight_count == 1
        release.set()
        assert delivered.wait(1)
        for _ in range(100):
            if registry.session("context-1").turns[0].state == TURN_FINALIZED:
                break
            threading.Event().wait(0.005)
        assert registry.session("context-1").turns[0].state == TURN_FINALIZED


def test_dispatch_re_resolves_route_after_background_handoff():
    registry = _registry()
    _, turn = registry.begin_turn(
        context_id="context-1", browser_id=BROWSER_ID, bridge_id=BRIDGE_ID
    )
    intent = registry.stage_finalize(
        context_id="context-1", turn_id=turn.turn_id, reason="completed"
    )[0]
    old_route = _route()
    new_route = replace(old_route, connector_sid="sid-reconnected")
    resolutions = iter((old_route, new_route))
    used_routes = []

    async def sender(_intent, route):
        used_routes.append(route)
        return TURN_FINALIZED

    with ThreadPoolExecutor(max_workers=1) as executor:
        dispatcher = ProcessFinalizationDispatcher(
            registry=registry,
            route_resolver=lambda _context_id, _bridge_id: next(resolutions),
            sender=sender,
            submitter=lambda coroutine: executor.submit(asyncio.run, coroutine),
        )
        assert dispatcher.schedule((intent,)) == (intent.control_id,)
        for _ in range(100):
            if used_routes:
                break
            threading.Event().wait(0.005)

    assert used_routes == [new_route]


def test_lifecycle_creates_no_intent_without_exact_explicit_validated_route():
    persistence = MemoryPersistence()
    registry = _registry(persistence=persistence)
    agent = _agent()
    lifecycle = ExtensionSessionLifecycle(
        registry=registry, config_loader=_extension_config
    )

    assert lifecycle.begin_agent_turn(agent) is None
    assert persistence.writes == 0

    with ThreadPoolExecutor(max_workers=1) as executor:
        lifecycle.configure(
            route_resolver=lambda _context_id, _bridge_id: None,
            sender=lambda _intent, _route: pytest.fail("sender must not run"),
            submitter=lambda coroutine: executor.submit(asyncio.run, coroutine),
        )
        assert lifecycle.begin_agent_turn(agent) is None
        assert persistence.writes == 0

        container = ExtensionSessionLifecycle(
            registry=registry,
            config_loader=lambda _agent: {
                "runtime_backend": "container",
                "host_browser_selection": BROWSER_ID,
            },
        )
        container.configure(
            route_resolver=lambda _context_id, _bridge_id: _route(),
            sender=lambda _intent, _route: TURN_FINALIZED,
            submitter=lambda coroutine: executor.submit(asyncio.run, coroutine),
        )
        assert container.begin_agent_turn(agent) is None
        assert persistence.writes == 0

        lifecycle = ExtensionSessionLifecycle(
            registry=registry, config_loader=_extension_config
        )
        lifecycle.configure(
            route_resolver=lambda _context_id, _bridge_id: _route(),
            sender=lambda _intent, _route: TURN_FINALIZED,
            submitter=lambda coroutine: executor.submit(asyncio.run, coroutine),
        )
        turn = lifecycle.begin_agent_turn(agent)
        assert turn is not None
        session = registry.session("context-1")
        assert session is not None
        assert session.browser_id == BROWSER_ID
        binding = lifecycle.active_agent_turn(agent)
        assert binding is not None
        assert lifecycle.is_current_turn(agent, binding) is True
        assert (
            binding.context_id,
            binding.browser_session_id,
            binding.browser_id,
            binding.bridge_id,
            binding.turn_id,
        ) == (
            "context-1",
            session.browser_session_id,
            BROWSER_ID,
            BRIDGE_ID,
            turn.turn_id,
        )

        with pytest.raises(ExtensionSessionStateError) as exc:
            lifecycle.configure(
                route_resolver=lambda _context_id, _bridge_id: _route(),
                sender=lambda _intent, _route: TURN_FINALIZED,
                submitter=lambda coroutine: executor.submit(asyncio.run, coroutine),
            )
        assert exc.value.code == "ALREADY_CONFIGURED"


def test_exact_owner_unconfigure_is_reversible_and_preserves_offline_cleanup():
    registry = _registry()
    lifecycle = ExtensionSessionLifecycle(
        registry=registry, config_loader=_extension_config
    )
    owner = object()
    replacement_owner = object()
    current_route = [_route()]
    delivered = []

    async def sender(intent, _route):
        delivered.append(intent)
        return TURN_FINALIZED

    lifecycle.configure(
        owner=owner,
        route_resolver=lambda _context_id, _bridge_id: current_route[0],
        sender=sender,
    )
    agent = _agent()
    turn = lifecycle.begin_agent_turn(agent)
    assert turn is not None
    with pytest.raises(ExtensionSessionStateError) as exc:
        lifecycle.unconfigure(owner=replacement_owner)
    assert exc.value.code == "OWNER_MISMATCH"
    assert lifecycle.configured_for(owner)

    # Losing the route during owner retirement cannot turn a pending cleanup
    # into a false not-applied or finalized result.
    current_route[0] = None
    assert lifecycle.unconfigure(owner=owner) == ()
    pending = registry.session("context-1").turns[-1]
    assert pending.state == TURN_FINALIZATION_PENDING
    assert pending.reason == "restarted"
    assert "runtime_owner_retired" not in repr(registry.sessions())
    assert not lifecycle.configured

    current_route[0] = _route()
    replayed = lifecycle.configure(
        owner=replacement_owner,
        route_resolver=lambda _context_id, _bridge_id: current_route[0],
        sender=sender,
    )
    assert replayed == (pending.control_id,)
    for _ in range(100):
        if registry.session("context-1").turns[-1].state == TURN_FINALIZED:
            break
        threading.Event().wait(0.005)
    assert registry.session("context-1").turns[-1].state == TURN_FINALIZED
    assert delivered[0].reason == "restarted"
    assert lifecycle.unconfigure(owner=replacement_owner) == ()


def test_offline_cleanup_stages_existing_intent_after_selection_changes():
    persistence = MemoryPersistence()
    registry = _registry(persistence=persistence)
    agent = _agent("offline-context")
    config = {
        "runtime_backend": "host_required",
        "host_browser_selection": BROWSER_ID,
    }
    current_route = [_route()]

    with ThreadPoolExecutor(max_workers=1) as executor:
        lifecycle = ExtensionSessionLifecycle(
            registry=registry, config_loader=lambda _agent: dict(config)
        )
        lifecycle.configure(
            route_resolver=lambda _context_id, _bridge_id: current_route[0],
            sender=lambda _intent, _route: pytest.fail("offline sender must not run"),
            submitter=lambda coroutine: executor.submit(asyncio.run, coroutine),
        )
        turn = lifecycle.begin_agent_turn(agent)
        assert turn is not None

        config["runtime_backend"] = "container"
        config["host_browser_selection"] = ""
        current_route[0] = None
        assert lifecycle.finalize_context(
            agent.context, reason="reset", retire=True
        ) == ()

    session = registry.session("offline-context")
    assert session is not None
    assert session.retire_requested is True
    assert session.turns[0].turn_id == turn.turn_id
    assert session.turns[0].state == TURN_FINALIZATION_PENDING


def test_task_done_fallback_stages_exact_tracked_turn_without_current_route():
    callbacks = []

    class FakeTask:
        def add_done_callback(self, callback):
            callbacks.append(callback)

    registry = _registry()
    agent = _agent("task-done-context")
    agent.context.task = FakeTask()
    current_route = [_route()]
    with ThreadPoolExecutor(max_workers=1) as executor:
        lifecycle = ExtensionSessionLifecycle(
            registry=registry, config_loader=_extension_config
        )
        lifecycle.configure(
            route_resolver=lambda _context_id, _bridge_id: current_route[0],
            sender=lambda _intent, _route: pytest.fail("offline sender must not run"),
            submitter=lambda coroutine: executor.submit(asyncio.run, coroutine),
        )
        turn = lifecycle.begin_agent_turn(agent)
        assert turn is not None
        assert len(callbacks) == 1
        current_route[0] = None
        callbacks[0](object())

    session = registry.session("task-done-context")
    assert session is not None
    assert session.turns[0].turn_id == turn.turn_id
    assert session.turns[0].state == TURN_FINALIZATION_PENDING
    assert session.turns[0].reason == "task_done"


def test_synthetic_scope_is_exact_bounded_and_never_overwrites_monologue_turn():
    registry = _registry()
    agent = _agent("synthetic-context")
    delivered = threading.Event()

    async def sender(_intent, _route):
        delivered.set()
        return TURN_FINALIZED

    with ThreadPoolExecutor(max_workers=1) as executor:
        lifecycle = ExtensionSessionLifecycle(
            registry=registry, config_loader=_extension_config
        )
        lifecycle.configure(
            route_resolver=lambda _context_id, _bridge_id: _route(),
            sender=sender,
            submitter=lambda coroutine: executor.submit(asyncio.run, coroutine),
        )
        synthetic = lifecycle.begin_synthetic_turn(agent)
        assert synthetic is not None
        assert lifecycle.active_agent_turn(agent) is None
        assert lifecycle.is_current_turn(agent, synthetic) is True
        assert lifecycle.begin_synthetic_turn(agent) is None
        assert lifecycle.finalize_synthetic_turn(
            agent, replace(synthetic, turn_id="wrong-turn")
        ) == ()
        scheduled = lifecycle.finalize_synthetic_turn(agent, synthetic)
        assert len(scheduled) == 1
        assert lifecycle.is_current_turn(agent, synthetic) is False
        assert delivered.wait(1)

        monologue_turn = lifecycle.begin_agent_turn(agent)
        assert monologue_turn is not None
        assert lifecycle.begin_synthetic_turn(agent) is None
        active = lifecycle.active_agent_turn(agent)
        assert active is not None
        assert active.turn_id == monologue_turn.turn_id


def test_lifecycle_hooks_are_wired_before_existing_reset_and_remove_cleanup():
    browser_extensions = PROJECT_ROOT / "plugins" / "_browser" / "extensions" / "python"
    expected = (
        "monologue_start/_15_extension_session.py",
        "monologue_end/_10_extension_session.py",
        "_functions/agent/AgentContext/kill_process/start/_05_finalize_extension_session.py",
        "_functions/agent/AgentContext/reset/start/_05_finalize_extension_session.py",
        "_functions/agent/AgentContext/remove/start/_05_finalize_extension_session.py",
        "_functions/agent/AgentContext/__init__/start/_05_finalize_replaced_extension_session.py",
        "_functions/agent/Agent/monologue/end/_05_finalize_extension_session.py",
    )
    for relative in expected:
        assert (browser_extensions / relative).is_file()

    reset_names = sorted(
        path.name
        for path in (
            browser_extensions / "_functions/agent/AgentContext/reset/start"
        ).glob("*.py")
    )
    remove_names = sorted(
        path.name
        for path in (
            browser_extensions / "_functions/agent/AgentContext/remove/start"
        ).glob("*.py")
    )
    assert reset_names.index("_05_finalize_extension_session.py") < reset_names.index(
        "_10_cleanup_browser_runtime.py"
    )
    assert remove_names.index("_05_finalize_extension_session.py") < remove_names.index(
        "_10_cleanup_browser_runtime.py"
    )
