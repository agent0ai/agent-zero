from __future__ import annotations

import asyncio
from collections import deque
from copy import deepcopy
from typing import Any, Sequence

import pytest

from helpers.ws_principal import WsPrincipal
from plugins._a0_connector.helpers.browser_bridge_context import (
    BrowserBridgeContextAccess,
    BrowserBridgeContextRoute,
    BrowserContextSourcePage,
    BrowserContextSourceSummary,
)
from plugins._a0_connector.helpers.browser_bridge_context_controller import (
    CONTEXT_COMPLETE_EVENT,
    CONTEXT_EVENT,
    CONTEXT_LIST_EVENT,
    CONTEXT_SEND_MESSAGE_EVENT,
    CONTEXT_SNAPSHOT_EVENT,
    CONTEXT_SUBSCRIBE_EVENT,
    CONTEXT_UNSUBSCRIBE_EVENT,
    RESTRICTED_HANDLER_ID,
    WS_NAMESPACE,
    BrowserBridgeContextController,
    BrowserBridgeContextControllerDenied,
    BrowserBridgeContextControllerError,
)
from plugins._a0_connector.helpers.browser_bridge_messages import (
    BrowserBridgeMessageDispatcher,
)


def _principal(name: str = "A") -> WsPrincipal:
    return WsPrincipal(
        principal_type="browser_bridge",
        principal_id=f"bridge-{name}",
        subject_id="single_user",
        scopes=frozenset({"context.list", "context.read", "context.message"}),
        handler_path="plugins/_a0_connector/ws_connector",
        handler_id=RESTRICTED_HANDLER_ID,
        inbound_events=frozenset(
            {
                CONTEXT_LIST_EVENT,
                CONTEXT_SUBSCRIBE_EVENT,
                CONTEXT_UNSUBSCRIBE_EVENT,
                CONTEXT_SEND_MESSAGE_EVENT,
            }
        ),
        outbound_events=frozenset(
            {CONTEXT_SNAPSHOT_EVENT, CONTEXT_EVENT, CONTEXT_COMPLETE_EVENT}
        ),
        key_generation=1,
    )


def _route(name: str = "A") -> BrowserBridgeContextRoute:
    return BrowserBridgeContextRoute(
        principal=_principal(name),
        connector_sid=f"sid-{name}",
        load_generation_id=f"generation-{name}",
    )


def _summary(context_id: str) -> BrowserContextSourceSummary:
    return BrowserContextSourceSummary(
        context_id=context_id,
        label=f"Task {context_id}",
        kind="task",
        status="running",
        created_at_ms=1,
        updated_at_ms=2,
    )


class _Source:
    def __init__(self) -> None:
        self.summaries = [_summary("context-A"), _summary("context-B")]
        self.pages: deque[BrowserContextSourcePage] = deque(
            [BrowserContextSourcePage(entries=(), last_sequence=0, complete=False)]
        )
        self.reads: list[tuple[int, str | None, int | None, int]] = []

    def list_contexts(
        self, *, subject_id: str, limit: int
    ) -> Sequence[BrowserContextSourceSummary]:
        assert subject_id == "single_user"
        return tuple(self.summaries[:limit])

    def context_exists(self, *, subject_id: str, context_id: str) -> bool:
        return subject_id == "single_user" and any(
            item.context_id == context_id for item in self.summaries
        )

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
        assert context_id in {item.context_id for item in self.summaries}
        self.reads.append((from_sequence, history, history_before, limit))
        if len(self.pages) > 1:
            return self.pages.popleft()
        return self.pages[0]


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
        await asyncio.sleep(0)


def _build(
    source: _Source,
    current: dict[int, bool],
    *,
    max_streams: int = 32,
) -> tuple[BrowserBridgeContextController, _Manager, list[tuple[str, str, str]]]:
    authorizer = lambda route: current.get(id(route.principal), False)
    access = BrowserBridgeContextAccess(
        data_source=source,
        route_authorizer=authorizer,
    )
    from browser_bridge_test_support import MemoryKeyValue
    stored = MemoryKeyValue()
    delivered: list[tuple[str, str, str]] = []
    messages = BrowserBridgeMessageDispatcher(
        access=access,
        server_instance_id=lambda: "server-1",
        load=stored.load,
        save=stored.save,
        deliver=lambda context_id, text, message_id: delivered.append(
            (context_id, text, message_id)
        ),
    )
    manager = _Manager()
    return (
        BrowserBridgeContextController(
            access=access,
            messages=messages,
            manager=manager,
            route_authorizer=authorizer,
            max_streams=max_streams,
            poll_interval_seconds=0.01,
            cancel_wait_seconds=0.1,
        ),
        manager,
        delivered,
    )


def test_list_subscribe_and_unsubscribe_use_exact_native_ack_and_emit_shapes() -> None:
    async def scenario() -> None:
        route = _route()
        source = _Source()
        source.pages = deque(
            [
                BrowserContextSourcePage(
                    entries=(
                        {"no": 4, "type": "response", "content": "safe text"},
                    ),
                    last_sequence=5,
                    complete=True,
                    history_before=4,
                    has_more_history=True,
                )
            ]
        )
        controller, manager, _delivered = _build(
            source, {id(route.principal): True}
        )
        listed = await controller.dispatch(
            CONTEXT_LIST_EVENT,
            route,
            {"contract_version": 1, "limit": 1, "correlationId": "transport"},
        )
        assert set(listed) == {"contract_version", "contexts"}
        assert [item["context_id"] for item in listed["contexts"]] == ["context-A"]

        subscribed = await controller.dispatch(
            CONTEXT_SUBSCRIBE_EVENT,
            route,
            {
                "contract_version": 1,
                "context_id": "context-A",
                "from": 2,
                "history": "tail",
                "history_before": 5,
            },
        )
        assert subscribed == {
            "contract_version": 1,
            "context_id": "context-A",
            "subscribed": True,
            "last_sequence": 5,
            "history_before": 4,
            "has_more_history": True,
        }
        assert source.reads[0] == (2, "tail", 5, 50)
        assert [call[2] for call in manager.calls] == [
            CONTEXT_SNAPSHOT_EVENT,
            CONTEXT_COMPLETE_EVENT,
        ]
        snapshot = manager.calls[0]
        assert snapshot[0:3] == (WS_NAMESPACE, "sid-A", CONTEXT_SNAPSHOT_EVENT)
        assert snapshot[3] == {
            "contract_version": 1,
            "context_id": "context-A",
            "events": [
                {
                    "context_id": "context-A",
                    "sequence": 5,
                    "event": "message",
                    "data": {"role": "assistant", "text": "safe text"},
                }
            ],
            "last_sequence": 5,
            "complete": True,
            "history_before": 4,
            "has_more_history": True,
        }
        assert snapshot[4]["handler_id"] == RESTRICTED_HANDLER_ID
        assert snapshot[4]["expected_principal"] is route.principal

        assert await controller.dispatch(
            CONTEXT_UNSUBSCRIBE_EVENT,
            route,
            {"contract_version": 1, "context_id": "context-A"},
        ) == {
            "contract_version": 1,
            "context_id": "context-A",
            "unsubscribed": True,
        }
        assert controller.stream_count == 0

    asyncio.run(scenario())


def test_live_projection_is_paged_bounded_and_completion_emits_once() -> None:
    async def scenario() -> None:
        route = _route()
        source = _Source()
        source.pages = deque(
            [
                BrowserContextSourcePage(
                    entries=({"no": 0, "type": "tool", "content": "secret"},),
                    last_sequence=1,
                    complete=False,
                ),
                BrowserContextSourcePage(
                    entries=(
                        {"no": 1, "type": "input", "content": "visible"},
                        {"no": 2, "type": "response", "content": "also visible"},
                        {"no": 3, "type": "unknown", "content": "drop me"},
                    ),
                    last_sequence=4,
                    complete=True,
                ),
                BrowserContextSourcePage(
                    entries=(),
                    last_sequence=4,
                    complete=True,
                ),
            ]
        )
        controller, manager, _delivered = _build(
            source,
            {id(route.principal): True},
        )
        await controller.dispatch(
            CONTEXT_LIST_EVENT, route, {"contract_version": 1}
        )
        await controller.dispatch(
            CONTEXT_SUBSCRIBE_EVENT,
            route,
            {"contract_version": 1, "context_id": "context-A"},
        )
        for _ in range(20):
            if any(call[2] == CONTEXT_COMPLETE_EVENT for call in manager.calls):
                break
            await asyncio.sleep(0.01)
        assert controller.stream_count == 1
        assert source.reads[:2] == [
            (0, None, None, 50),
            (1, None, None, 50),
        ]
        assert [call[2] for call in manager.calls] == [
            CONTEXT_SNAPSHOT_EVENT,
            CONTEXT_EVENT,
            CONTEXT_EVENT,
            CONTEXT_COMPLETE_EVENT,
        ]
        assert manager.calls[0][3]["events"][0]["data"] == {
            "activity": "tool",
            "status": "updated",
        }
        assert manager.calls[1][3] == {
            "contract_version": 1,
            "context_id": "context-A",
            "sequence": 2,
            "last_sequence": 1,
            "event": "message",
            "data": {"role": "user", "text": "visible"},
        }
        assert manager.calls[2][3] == {
            "contract_version": 1,
            "context_id": "context-A",
            "sequence": 3,
            "last_sequence": 4,
            "event": "message",
            "data": {"role": "assistant", "text": "also visible"},
        }
        assert manager.calls[3][3]["status"] == "completed"
        assert all("secret" not in repr(call[3]) for call in manager.calls)
        await controller.dispatch(
            CONTEXT_UNSUBSCRIBE_EVENT,
            route,
            {"contract_version": 1, "context_id": "context-A"},
        )
        assert controller.stream_count == 0

    asyncio.run(scenario())


def test_send_accepts_only_empty_native_placeholders_and_durable_text_shape() -> None:
    async def scenario() -> None:
        route = _route()
        source = _Source()
        controller, _manager, delivered = _build(
            source, {id(route.principal): True}
        )
        await controller.dispatch(
            CONTEXT_LIST_EVENT, route, {"contract_version": 1}
        )
        result = await controller.dispatch(
            CONTEXT_SEND_MESSAGE_EVENT,
            route,
            {
                "contract_version": 1,
                "context_id": "context-A",
                "client_message_id": "message-1",
                "text": "hello",
                "artifact_ids": [],
                "tab_candidates": [],
            },
        )
        assert result == {
            "contract_version": 1,
            "context_id": "context-A",
            "client_message_id": "message-1",
            "status": "accepted",
        }
        assert delivered == [("context-A", "hello", "message-1")]
        for field in ("artifact_ids", "tab_candidates"):
            with pytest.raises(BrowserBridgeContextControllerDenied) as error:
                await controller.dispatch(
                    CONTEXT_SEND_MESSAGE_EVENT,
                    route,
                    {
                        "contract_version": 1,
                        "context_id": "context-A",
                        "client_message_id": f"message-{field}",
                        "text": "hello",
                        field: ["untrusted"],
                    },
                )
            assert error.value.code == "ATTACHMENT_AUTHORITY_UNAVAILABLE"
        with pytest.raises(BrowserBridgeContextControllerError):
            await controller.dispatch(
                CONTEXT_SEND_MESSAGE_EVENT,
                route,
                {
                    "contract_version": 1,
                    "context_id": "context-A",
                    "client_message_id": "message-extra",
                    "text": "hello",
                    "path": "/private/file",
                },
            )

    asyncio.run(scenario())


def test_capacity_stale_route_and_exact_disconnect_only_cancel_presentations() -> None:
    async def scenario() -> None:
        route_a = _route("A")
        route_b = _route("B")
        current = {id(route_a.principal): True, id(route_b.principal): True}
        source = _Source()
        controller, manager, _delivered = _build(
            source, current, max_streams=2
        )
        await controller.dispatch(CONTEXT_LIST_EVENT, route_a, {"contract_version": 1})
        await controller.dispatch(CONTEXT_LIST_EVENT, route_b, {"contract_version": 1})
        await controller.dispatch(
            CONTEXT_SUBSCRIBE_EVENT,
            route_a,
            {"contract_version": 1, "context_id": "context-A"},
        )
        await controller.dispatch(
            CONTEXT_SUBSCRIBE_EVENT,
            route_b,
            {"contract_version": 1, "context_id": "context-B"},
        )
        with pytest.raises(BrowserBridgeContextControllerDenied) as full:
            await controller.dispatch(
                CONTEXT_SUBSCRIBE_EVENT,
                route_a,
                {"contract_version": 1, "context_id": "context-B"},
            )
        assert full.value.code == "CONTEXT_STREAM_LIMIT"

        unrelated_agent_task = asyncio.create_task(asyncio.sleep(10))
        assert await controller.disconnect(
            principal=route_a.principal,
            connector_sid=route_a.connector_sid,
            load_generation_id=route_a.load_generation_id,
        )
        assert controller.stream_count == 1
        assert not unrelated_agent_task.cancelled()

        calls_before = len(manager.calls)
        current[id(route_b.principal)] = False
        for _ in range(20):
            if controller.stream_count == 0:
                break
            await asyncio.sleep(0.01)
        assert controller.stream_count == 0
        assert len(manager.calls) == calls_before
        unrelated_agent_task.cancel()
        with pytest.raises(asyncio.CancelledError):
            await unrelated_agent_task

    asyncio.run(scenario())
