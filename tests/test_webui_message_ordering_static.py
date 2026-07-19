from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]


def read(*parts: str) -> str:
    return (PROJECT_ROOT / Path(*parts)).read_text(encoding="utf-8")


def test_full_log_replays_replace_existing_message_dom():
    index_js = read("webui", "index.js")
    messages_js = read("webui", "js", "messages.js")

    assert "snapshot.logs?.[0]?.no === 0" in index_js
    assert 'chatHistoryEl.innerHTML = "";' in index_js
    assert "messages.sort((a, b)" in messages_js


def test_message_ordering_fix_does_not_add_renderer_cache_state():
    messages_js = read("webui", "js", "messages.js")

    assert "_messageCacheByNo" not in messages_js
    assert "resetMessageRenderState" not in messages_js
