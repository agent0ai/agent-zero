from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def read(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def test_tool_args_preference_toggle_is_wired_in_webui() -> None:
    store = read("webui/components/sidebar/bottom/preferences/preferences-store.js")
    panel = read("webui/components/sidebar/bottom/preferences/preferences-panel.html")

    assert "get showToolArgs()" in store
    assert "set showToolArgs(value)" in store
    assert "_showToolArgs: false," in store
    assert 'localStorage.getItem("showToolArgs")' in store
    assert 'localStorage.setItem("showToolArgs", value)' in store
    assert "this._applyShowToolArgs(this._showToolArgs);" in store
    assert "_applyShowToolArgs(value)" in store

    assert "Show verbose tool calls" in panel
    assert 'x-model="$store.preferences.showToolArgs"' in panel


def test_message_stream_gates_tool_args_display_behind_preference() -> None:
    messages = read("webui/js/messages.js")

    assert "if (preferencesStore.showToolArgs && !isResponse) {" in messages
    assert "kvps?.tool_args ?? kvps?.args" in messages
    assert 'const isResponse = kvps?.tool_name === "response";' in messages
    assert "!reservedKeys.has(key)" in messages
    assert 'icon://build[Tool]' in messages
