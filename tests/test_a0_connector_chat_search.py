import asyncio
from types import SimpleNamespace

import pytest

from agent import AgentContext
from plugins._a0_connector.api.v1.chats_list import ChatsList


def context(id, name, *messages):
    return SimpleNamespace(
        id=id, name=name, no=1, agent0=None,
        log=SimpleNamespace(logs=[SimpleNamespace(content=text) for text in messages]),
        output=lambda: {"name": name, "no": 1, "created_at": 100, "last_message": 200},
        get_data=lambda key: "", get_output_data=lambda key: None,
    )


def call(payload):
    return asyncio.run(ChatsList(None, None).process(payload, None))


def test_connector_search_uses_shared_literal_excerpts_without_changing_the_list(monkeypatch):
    monkeypatch.setattr(AgentContext, "all", lambda: [
        context("title", "Release plan"), context("message", "Notes", "older release", "Latest RELEASE [/path]"),
        context("unicode", "Other", "Straße"),
    ])
    original = call({})
    assert original["chats"] == original["contexts"]
    assert len(original["contexts"]) == 3
    assert "matches" not in original
    result = call({"query": " release "})["matches"]
    assert [match["id"] for match in result] == ["title", "message"]
    assert result[0]["title"] is True
    assert result[1]["parts"] == [
        {"text": "Latest ", "match": False}, {"text": "RELEASE", "match": True},
        {"text": " [/path]", "match": False},
    ]
    assert call({"query": "STRASSE"})["matches"][0]["parts"] == [{"text": "Straße", "match": True}]
    assert call({}) == original
    assert ChatsList.requires_auth() is True


@pytest.mark.parametrize("payload", [None, [], "release", {"query": None}, {"query": []}, {"query": 1}, {"query": "x" * 201}])
def test_connector_search_rejects_invalid_queries_before_scanning(monkeypatch, payload):
    monkeypatch.setattr(AgentContext, "all", lambda: pytest.fail("Invalid requests must not scan chats"))
    assert call(payload).status_code == 400


def test_connector_empty_query_does_not_scan_chats(monkeypatch):
    monkeypatch.setattr(AgentContext, "all", lambda: pytest.fail("Empty queries must not scan chats"))
    assert call({"query": "  "}) == {"matches": []}
