import asyncio
from types import SimpleNamespace

import pytest

from plugins._sidebar_folders.api import search
from plugins._sidebar_folders.helpers.search import search_contexts


def context(id, name, *messages, kind=search.AgentContextType.USER):
    return SimpleNamespace(id=id, name=name, type=kind,
                           log=SimpleNamespace(logs=[SimpleNamespace(content=text) for text in messages]))


def excerpt(match):
    return "".join(part["text"] for part in match["parts"])


def test_search_uses_titles_recent_messages_and_literal_unicode_snippets():
    contexts = [context("title", "Release plan"), context("logs", "Notes", "old release", "latest RELEASE notes"),
                context("unicode", "Straße"), context("offset", "Notes", "ß" * 300 + "needle" + "tail" * 80),
                context("html", "Notes", None, "<script>alert(1)</script>")]
    matches = search_contexts(contexts, "release", {})
    assert [item["id"] for item in matches] == ["title", "logs"]
    assert matches[0]["title"] is True
    assert matches[1]["title"] is False
    assert excerpt(matches[1]) == "latest RELEASE notes"
    assert [part["text"] for part in matches[1]["parts"] if part["match"]] == ["RELEASE"]
    assert search_contexts(contexts, "STRASSE", {})[0]["id"] == "unicode"
    snippet = excerpt(search_contexts(contexts, "needle", {})[0])
    assert "needle" in snippet and len(snippet) < 250
    assert excerpt(search_contexts(contexts, "<script>", {})[0]) == "<script>alert(1)</script>"


@pytest.mark.parametrize("text, query, preview, hits", [
    ("## Results\nThe **test** and `TEST` passed.", "test", "Results The test and TEST passed.", ["test", "TEST"]),
    ("See [test notes](https://example.test).", "test", "See test notes.", ["test"]),
    ("See [notes](https://example.test).", "example.test", "See [notes](https://example.test).", ["example.test"]),
    ("Use **bold** here.", "**", "Use **bold** here.", ["**", "**"]),
    ("🚀 Straße STRASSE", "strasse", "🚀 Straße STRASSE", ["Straße", "STRASSE"]),
    ("ß s", "s", "ß s", ["ß", "s"]),
    ("İstanbul", "İST", "İstanbul", ["İst"]),
    ("first  test\nnext", "first  test", "first test next", ["first test"]),
])
def test_excerpt_highlights_safe_readable_text_without_losing_literal_matches(text, query, preview, hits):
    match = search_contexts([context("chat", "", text)], query, {})[0]
    assert excerpt(match) == preview
    assert [part["text"] for part in match["parts"] if part["match"]] == hits


def test_excerpt_keeps_the_hit_near_the_start_and_marks_truncation():
    text = "earlier context " * 80 + "needle" + " later context" * 80
    match = search_contexts([context("chat", "Notes", text)], "needle", {})[0]
    preview = excerpt(match)
    assert preview.startswith("… ") and preview.endswith(" …")
    assert preview.index("needle") <= 34
    assert len(preview) <= 182


def test_search_api_shares_chat_and_task_results_but_excludes_background_contexts(monkeypatch):
    contexts = [context("chat", "Daily notes"), context("task", "Generated title", "daily output", kind=search.AgentContextType.TASK),
                context("background", "Daily hidden", kind=search.AgentContextType.BACKGROUND)]
    task = SimpleNamespace(uuid="task", name="Daily report", is_dedicated=lambda: True)
    monkeypatch.setattr(search.AgentContext, "all", lambda: contexts)
    monkeypatch.setattr(search.TaskScheduler, "get", lambda: SimpleNamespace(get_tasks=lambda: [task]))
    handler = search.Search(None, None)
    result = asyncio.run(handler.process({"query": " daily "}, None))
    assert [(match["id"], match["title"], excerpt(match)) for match in result["matches"]] == [
        ("chat", True, "Daily notes"), ("task", True, "Daily report")]
    assert asyncio.run(handler.process({"query": "output"}, None))["matches"][0]["id"] == "task"
    assert handler.requires_auth()
    assert handler.requires_csrf()


@pytest.mark.parametrize("query", [None, [], {}, 42, "x" * 201])
def test_search_api_rejects_invalid_queries(query):
    response = asyncio.run(search.Search(None, None).process({"query": query}, None))
    assert response.status_code == 400


@pytest.mark.parametrize("body", [None, [], "query"])
def test_search_api_rejects_non_object_requests(body):
    assert asyncio.run(search.Search(None, None).process(body, None)).status_code == 400


def test_empty_search_does_not_scan_contexts(monkeypatch):
    def unexpected_scan():
        pytest.fail("Empty search must not load conversations")
    monkeypatch.setattr(search.AgentContext, "all", unexpected_scan)
    assert asyncio.run(search.Search(None, None).process({"query": "  "}, None)) == {"matches": []}
