from __future__ import annotations

import asyncio
from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest

from helpers.ws_manager import WsResult
from plugins._a0_connector.api import ws_connector as ws_module
from plugins._a0_connector.api.ws_connector import (
    WsConnector,
    _attachment_log_metadata,
)
from plugins._a0_connector.helpers.event_bridge import log_entry_to_connector_event


def test_attachment_log_metadata_keeps_only_safe_basenames() -> None:
    assert _attachment_log_metadata(
        [
            "/a0/usr/uploads/scan.png",
            r"C:\\Users\\person\\result.jpg",
            "https://agent.test/api/image_get?path=/a0/usr/uploads/chart.webp&token=secret#view",
            "/a0/usr/uploads/",
            "",
        ]
    ) == {
        "attachments": ["scan.png", "result.jpg", "image_get"]
    }


def test_attachment_log_metadata_omits_empty_metadata() -> None:
    assert _attachment_log_metadata([]) == {}
    assert _attachment_log_metadata(["", "/"]) == {}


def test_attachment_log_metadata_decodes_encoded_separators() -> None:
    assert _attachment_log_metadata(
        [
            "https://host/%2Fhome%2Falice%2Fsecret.png",
            "https://host/C:%5CUsers%5CAlice%5Csecret.png",
        ]
    ) == {"attachments": ["secret.png", "secret.png"]}


def test_attachment_log_metadata_strips_encoded_query_and_fragment_suffixes() -> None:
    assert _attachment_log_metadata(
        [
            "https://host/report%3Ftoken%3Dsecret.png",
            "https://host/image%23private-fragment.png",
        ]
    ) == {"attachments": ["report", "image"]}


class RecordingLog:
    def __init__(self) -> None:
        self.calls: list[dict[str, object]] = []

    def log(self, **kwargs: object) -> None:
        self.calls.append(dict(kwargs))


@pytest.mark.asyncio
async def test_websocket_attachment_names_reach_replayed_user_event(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    log = RecordingLog()
    context = SimpleNamespace(log=log)
    handler = WsConnector(None, None)
    monkeypatch.setattr(
        handler,
        "_resolve_context",
        AsyncMock(return_value=(context, "ctx-1")),
    )
    monkeypatch.setattr(
        ws_module,
        "subscribed_contexts_for_sid",
        lambda sid: {"ctx-1"} if sid == "sid-cli" else set(),
    )

    scheduled: list[bool] = []

    def close_scheduled(coroutine: object) -> SimpleNamespace:
        close = getattr(coroutine, "close")
        close()
        scheduled.append(True)
        return SimpleNamespace()

    monkeypatch.setattr(asyncio, "create_task", close_scheduled)

    result = await handler._handle_send_message(
        {
            "context_id": "ctx-1",
            "message": "Review these",
            "attachments": [
                "/a0/usr/uploads/scan.png",
                "/a0/usr/uploads/result.jpg",
            ],
            "client_message_id": "client-1",
        },
        "sid-cli",
    )

    assert result == {
        "context_id": "ctx-1",
        "status": "accepted",
        "client_message_id": "client-1",
    }
    assert scheduled == [True]
    assert log.calls == [
        {
            "type": "user",
            "heading": "",
            "content": "Review these",
            "kvps": {"attachments": ["scan.png", "result.jpg"]},
            "id": "client-1",
        }
    ]

    replayed = log_entry_to_connector_event(
        {"no": 0, **log.calls[0]},
        "ctx-1",
    )
    assert replayed["event"] == "user_message"
    assert replayed["data"]["meta"] == {
        "attachments": ["scan.png", "result.jpg"]
    }


@pytest.mark.asyncio
async def test_websocket_text_only_message_keeps_empty_kvps(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    log = RecordingLog()
    context = SimpleNamespace(log=log)
    handler = WsConnector(None, None)
    monkeypatch.setattr(
        handler,
        "_resolve_context",
        AsyncMock(return_value=(context, "ctx-1")),
    )
    monkeypatch.setattr(
        ws_module,
        "subscribed_contexts_for_sid",
        lambda sid: {"ctx-1"} if sid == "sid-cli" else set(),
    )

    def close_scheduled(coroutine: object) -> SimpleNamespace:
        getattr(coroutine, "close")()
        return SimpleNamespace()

    monkeypatch.setattr(asyncio, "create_task", close_scheduled)
    await handler._handle_send_message(
        {"context_id": "ctx-1", "message": "Text only"},
        "sid-cli",
    )
    assert log.calls[0]["kvps"] == {}


@pytest.mark.asyncio
async def test_websocket_malformed_attachment_url_keeps_message_delivery(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    log = RecordingLog()
    context = SimpleNamespace(log=log)
    handler = WsConnector(None, None)
    monkeypatch.setattr(
        handler,
        "_resolve_context",
        AsyncMock(return_value=(context, "ctx-1")),
    )
    monkeypatch.setattr(
        ws_module,
        "subscribed_contexts_for_sid",
        lambda sid: {"ctx-1"} if sid == "sid-cli" else set(),
    )

    scheduled: list[bool] = []

    def close_scheduled(coroutine: object) -> SimpleNamespace:
        getattr(coroutine, "close")()
        scheduled.append(True)
        return SimpleNamespace()

    monkeypatch.setattr(asyncio, "create_task", close_scheduled)

    result = await handler._handle_send_message(
        {
            "context_id": "ctx-1",
            "message": "Review this",
            "attachments": ["http://["],
            "client_message_id": "client-malformed",
        },
        "sid-cli",
    )

    assert result == {
        "context_id": "ctx-1",
        "status": "accepted",
        "client_message_id": "client-malformed",
    }
    assert scheduled == [True]
    assert log.calls[0]["kvps"] == {}


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("payload", "code"),
    [
        (
            {
                "message": "image",
                "attachments": [{"path": "data:image/png;base64,AAAA"}],
            },
            "INVALID_ATTACHMENTS",
        ),
        ({"message": "", "attachments": []}, "MISSING_MESSAGE"),
    ],
)
async def test_websocket_rejected_attachments_do_not_reach_context(
    payload: dict[str, object],
    code: str,
) -> None:
    handler = WsConnector(None, None)
    result = await handler.process("connector_send_message", payload, "sid-cli")
    assert isinstance(result, WsResult)
    rendered = result.as_result(handler_id="test", fallback_correlation_id=None)
    assert rendered["ok"] is False
    assert rendered["error"]["code"] == code
