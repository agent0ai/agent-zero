from __future__ import annotations

from dataclasses import replace
from datetime import UTC, datetime
import json
from types import SimpleNamespace
from typing import Any, Sequence

import pytest

from helpers.ws_principal import WsPrincipal
from plugins._a0_connector.helpers.browser_bridge_context import (
    MAX_CONTEXT_TEXT_BYTES,
    AgentContextDataSource,
    BrowserBridgeContextAccess,
    BrowserBridgeContextDenied,
    BrowserBridgeContextRoute,
    BrowserBridgeContextUnavailable,
    BrowserContextSourcePage,
    BrowserContextSourceSummary,
)


CONTEXT_A = "context-A"
CONTEXT_B = "context-B"


def _principal(
    *,
    bridge_id: str = "bridge-A",
    scopes: frozenset[str] | None = None,
) -> WsPrincipal:
    return WsPrincipal(
        principal_type="browser_bridge",
        principal_id=bridge_id,
        subject_id="single_user",
        scopes=scopes
        or frozenset({"context.list", "context.read", "context.message"}),
        handler_path="plugins/_a0_connector/ws_connector",
        handler_id="ws_connector.WsConnector",
        inbound_events=frozenset({"connector_context_list"}),
        outbound_events=frozenset({"connector_context_snapshot"}),
        key_generation=1,
    )


def _route(
    *,
    principal: WsPrincipal | None = None,
    sid: str = "sid-A",
    generation: str = "generation-A",
) -> BrowserBridgeContextRoute:
    return BrowserBridgeContextRoute(
        principal=principal or _principal(),
        connector_sid=sid,
        load_generation_id=generation,
    )


def _summary(context_id: str) -> BrowserContextSourceSummary:
    return BrowserContextSourceSummary(
        context_id=context_id,
        label=f"Task {context_id}",
        kind="chat",
        status="idle",
        created_at_ms=1_000,
        updated_at_ms=2_000,
    )


class _Source:
    def __init__(self) -> None:
        self.summaries: list[BrowserContextSourceSummary] = [
            _summary(CONTEXT_A),
            _summary(CONTEXT_B),
        ]
        self.existing = {CONTEXT_A, CONTEXT_B}
        self.page = BrowserContextSourcePage(
            entries=(),
            last_sequence=0,
            complete=True,
        )
        self.on_list = None
        self.on_exists = None
        self.on_read = None

    def list_contexts(
        self,
        *,
        subject_id: str,
        limit: int,
    ) -> Sequence[BrowserContextSourceSummary]:
        assert subject_id == "single_user"
        if self.on_list:
            self.on_list()
        return tuple(self.summaries[:limit])

    def context_exists(self, *, subject_id: str, context_id: str) -> bool:
        assert subject_id == "single_user"
        if self.on_exists:
            self.on_exists()
        return context_id in self.existing

    def read_context(
        self,
        *,
        subject_id: str,
        context_id: str,
        from_sequence: int,
        history: str | None,
        history_before: int | None,
        limit: int,
    ) -> BrowserContextSourcePage | None:
        assert subject_id == "single_user"
        assert context_id in self.existing
        if self.on_read:
            self.on_read()
        return self.page


def _access(
    source: _Source,
    *,
    current: list[bool] | None = None,
) -> BrowserBridgeContextAccess:
    state = current or [True]
    return BrowserBridgeContextAccess(
        data_source=source,
        route_authorizer=lambda _route: state[0],
    )


def test_context_ids_must_be_advertised_before_subscribe_or_message() -> None:
    source = _Source()
    access = _access(source)
    route = _route()
    with pytest.raises(BrowserBridgeContextDenied) as subscribe_error:
        access.subscribe(route, context_id=CONTEXT_A)
    assert subscribe_error.value.code == "CONTEXTS_NOT_ADVERTISED"
    with pytest.raises(BrowserBridgeContextDenied):
        access.authorize_message_target(route, context_id=CONTEXT_A)

    summaries = access.advertise_contexts(route)
    assert [item["context_id"] for item in summaries] == [CONTEXT_A, CONTEXT_B]
    assert set(summaries[0]) == {
        "context_id",
        "label",
        "kind",
        "status",
        "created_at_ms",
        "updated_at_ms",
    }
    access.subscribe(route, context_id=CONTEXT_A)
    access.authorize_message_target(route, context_id=CONTEXT_A)
    with pytest.raises(BrowserBridgeContextDenied) as unknown_error:
        access.subscribe(route, context_id="context-unadvertised")
    assert unknown_error.value.code == "CONTEXT_NOT_ADVERTISED"


@pytest.mark.parametrize("changed", ["principal", "connector_sid", "load_generation_id"])
def test_context_authority_is_isolated_to_exact_route(changed: str) -> None:
    source = _Source()
    access = _access(source)
    route = _route()
    access.advertise_contexts(route)
    replacement: Any = _principal() if changed == "principal" else f"other-{changed}"
    isolated = replace(route, **{changed: replacement})
    with pytest.raises(BrowserBridgeContextDenied) as error:
        access.subscribe(isolated, context_id=CONTEXT_A)
    assert error.value.code == "CONTEXTS_NOT_ADVERTISED"
    access.subscribe(route, context_id=CONTEXT_A)


def test_relisting_replaces_advertisement_and_subscription_sets() -> None:
    source = _Source()
    access = _access(source)
    route = _route()
    access.advertise_contexts(route)
    access.subscribe(route, context_id=CONTEXT_A)
    source.summaries = [_summary(CONTEXT_B)]
    access.advertise_contexts(route)
    with pytest.raises(BrowserBridgeContextDenied):
        access.authorize_message_target(route, context_id=CONTEXT_A)
    with pytest.raises(BrowserBridgeContextDenied):
        access.project_completion(route, context_id=CONTEXT_A, status="completed")


def test_scope_and_current_route_are_rechecked_after_source_reads() -> None:
    source = _Source()
    current = [True]
    access = _access(source, current=current)
    route = _route()
    source.on_list = lambda: current.__setitem__(0, False)
    with pytest.raises(BrowserBridgeContextDenied) as list_error:
        access.advertise_contexts(route)
    assert list_error.value.code == "STALE_BRIDGE_ROUTE"

    current[0] = True
    source.on_list = None
    access.advertise_contexts(route)
    source.on_exists = lambda: current.__setitem__(0, False)
    with pytest.raises(BrowserBridgeContextDenied) as subscribe_error:
        access.subscribe(route, context_id=CONTEXT_A)
    assert subscribe_error.value.code == "STALE_BRIDGE_ROUTE"

    current[0] = True
    source.on_exists = None
    no_read = _route(principal=_principal(scopes=frozenset({"context.list"})))
    access.advertise_contexts(no_read)
    with pytest.raises(BrowserBridgeContextDenied) as scope_error:
        access.subscribe(no_read, context_id=CONTEXT_A)
    assert scope_error.value.code == "SCOPE_DENIED"


def test_projection_keeps_only_actual_message_types_and_safe_activity() -> None:
    secret = "raw-browser-secret"
    source = _Source()
    source.page = BrowserContextSourcePage(
        entries=(
            {
                "no": 0,
                "type": "user",
                "content": "Please continue",
                "heading": "/private/user/path",
                "kvps": {"attachments": ["/private/file.txt"]},
                "id": "message-A",
                "timestamp": 1_700_000_000.25,
            },
            {
                "no": 1,
                "type": "response",
                "content": "Done",
                "kvps": {"selector": "#password"},
            },
            {
                "no": 2,
                "type": "tool",
                "content": secret,
                "heading": "evaluate javascript",
                "kvps": {"script": "document.cookie", "url": "https://x.test/a?q=1"},
            },
            {
                "no": 3,
                "type": "error",
                "content": "Traceback /secret/path",
                "kvps": {"exception": secret},
            },
            {"no": 4, "type": "ai_response", "content": secret},
            {"no": 5, "role": "assistant", "content": secret},
            {"no": 6, "type": "page_snapshot", "content": secret},
        ),
        last_sequence=7,
        complete=False,
        history_before=2,
        has_more_history=True,
    )
    access = _access(source)
    route = _route()
    access.advertise_contexts(route)
    access.subscribe(route, context_id=CONTEXT_A)
    snapshot = access.project_snapshot(
        route,
        context_id=CONTEXT_A,
        history="tail",
    )
    assert snapshot["last_sequence"] == 7
    assert snapshot["history_before"] == 2
    assert snapshot["has_more_history"] is True
    assert snapshot["complete"] is False
    assert snapshot["events"] == [
        {
            "context_id": CONTEXT_A,
            "sequence": 1,
            "event": "message",
            "data": {"role": "user", "text": "Please continue"},
            "timestamp_ms": 1_700_000_000_250,
            "correlation_id": "message-A",
        },
        {
            "context_id": CONTEXT_A,
            "sequence": 2,
            "event": "message",
            "data": {"role": "assistant", "text": "Done"},
        },
        {
            "context_id": CONTEXT_A,
            "sequence": 3,
            "event": "activity",
            "data": {"activity": "tool", "status": "updated"},
        },
        {
            "context_id": CONTEXT_A,
            "sequence": 4,
            "event": "activity",
            "data": {"activity": "status", "status": "failed"},
        },
    ]
    serialized = json.dumps(snapshot)
    for forbidden in (
        secret,
        "heading",
        "kvps",
        "attachments",
        "selector",
        "script",
        "url",
        "Traceback",
        "page_snapshot",
    ):
        assert forbidden not in serialized


def test_dropped_rows_advance_cursor_and_bounded_text_is_utf8_safe() -> None:
    source = _Source()
    source.page = BrowserContextSourcePage(
        entries=(
            {"no": 10, "type": "unknown", "content": "drop"},
            {"no": 11, "type": "response", "content": "é" * 10_000},
        ),
        last_sequence=12,
        complete=True,
    )
    access = _access(source)
    route = _route()
    access.advertise_contexts(route)
    access.subscribe(route, context_id=CONTEXT_A)
    snapshot = access.project_snapshot(
        route,
        context_id=CONTEXT_A,
        from_sequence=10,
    )
    assert snapshot["last_sequence"] == 12
    assert snapshot["complete"] is True
    text = snapshot["events"][0]["data"]["text"]
    assert len(text.encode("utf-8")) <= MAX_CONTEXT_TEXT_BYTES
    assert text.endswith("[Text truncated]")
    assert access.project_completion(
        route,
        context_id=CONTEXT_A,
        status="completed",
    ) == {"context_id": CONTEXT_A, "status": "completed"}


def test_snapshot_route_is_rechecked_after_source_read() -> None:
    source = _Source()
    current = [True]
    access = _access(source, current=current)
    route = _route()
    access.advertise_contexts(route)
    access.subscribe(route, context_id=CONTEXT_A)
    source.on_read = lambda: current.__setitem__(0, False)
    with pytest.raises(BrowserBridgeContextDenied) as error:
        access.project_snapshot(route, context_id=CONTEXT_A)
    assert error.value.code == "STALE_BRIDGE_ROUTE"


@pytest.mark.parametrize(
    ("page", "arguments"),
    [
        (
            BrowserContextSourcePage(
                entries=({"no": 0, "type": "response", "content": "again"},),
                last_sequence=0,
                complete=False,
            ),
            {"from_sequence": 0},
        ),
        (
            BrowserContextSourcePage(
                entries=(),
                last_sequence=0,
                complete=False,
            ),
            {"history": "tail"},
        ),
    ],
)
def test_snapshot_rejects_nonadvancing_or_unpageable_source_pages(
    page: BrowserContextSourcePage,
    arguments: dict[str, Any],
) -> None:
    source = _Source()
    source.page = page
    access = _access(source)
    route = _route()
    access.advertise_contexts(route)
    access.subscribe(route, context_id=CONTEXT_A)
    with pytest.raises(BrowserBridgeContextUnavailable):
        access.project_snapshot(route, context_id=CONTEXT_A, **arguments)


def test_disconnect_drops_only_exact_route_state() -> None:
    source = _Source()
    access = _access(source)
    route_a = _route()
    route_b = _route(principal=_principal(bridge_id="bridge-B"), sid="sid-B")
    access.advertise_contexts(route_a)
    access.advertise_contexts(route_b)
    assert access.disconnect(
        principal=route_a.principal,
        connector_sid=route_a.connector_sid,
        load_generation_id=route_a.load_generation_id,
    ) is True
    with pytest.raises(BrowserBridgeContextDenied):
        access.authorize_message_target(route_a, context_id=CONTEXT_A)
    access.authorize_message_target(route_b, context_id=CONTEXT_A)


def test_concrete_agent_context_source_reads_only_allowlisted_shape(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    class _Lock:
        def __enter__(self):
            return self

        def __exit__(self, *_args):
            return None

    class _Log:
        _lock = _Lock()
        updates = [0]

        def output(self, start=0, end=None):
            values = [{"no": 0, "type": "user", "content": "hello"}]
            selected = values[start:end]
            return SimpleNamespace(items=selected, end=len(values) if end is None else end)

    class _Context:
        def __init__(self, context_id: str, type_name: str) -> None:
            self.id = context_id
            self.name = "Visible task"
            self.type = SimpleNamespace(value=type_name)
            self.paused = False
            self.created_at = datetime(2026, 1, 1, tzinfo=UTC)
            self.last_message = datetime(2026, 1, 2, tzinfo=UTC)
            self.log = _Log()
            self.output_data = {"secret": "must not be read"}

        def is_running(self) -> bool:
            return False

        def output(self):
            raise AssertionError("broad AgentContext.output must not be used")

    visible = _Context(CONTEXT_A, "user")
    background = _Context("background-A", "background")

    class _AgentContext:
        @staticmethod
        def all():
            return [background, visible]

        @staticmethod
        def get(context_id: str):
            return {visible.id: visible, background.id: background}.get(context_id)

    monkeypatch.setitem(
        __import__("sys").modules,
        "agent",
        SimpleNamespace(AgentContext=_AgentContext),
    )
    source = AgentContextDataSource()
    summaries = source.list_contexts(subject_id="single_user", limit=10)
    assert [summary.context_id for summary in summaries] == [CONTEXT_A]
    assert summaries[0].label == "Visible task"
    assert source.context_exists(subject_id="single_user", context_id=CONTEXT_A)
    assert not source.context_exists(subject_id="single_user", context_id="background-A")
    page = source.read_context(
        subject_id="single_user",
        context_id=CONTEXT_A,
        from_sequence=0,
        history=None,
        history_before=None,
        limit=10,
    )
    assert page is not None
    assert page.entries == ({"no": 0, "type": "user", "content": "hello"},)
    assert source.list_contexts(subject_id="other-subject", limit=10) == ()
