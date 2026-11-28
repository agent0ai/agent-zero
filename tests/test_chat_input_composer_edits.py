from pathlib import Path

import pytest


PROJECT_ROOT = Path(__file__).resolve().parents[1]
INPUT_STORE = "webui/components/chat/input/input-store.js"
CHAT_BAR = "webui/components/chat/input/chat-bar-input.html"


def test_composer_is_a_native_textarea_without_input_interception() -> None:
    chat_bar = (PROJECT_ROOT / CHAT_BAR).read_text(encoding="utf-8")
    store = (PROJECT_ROOT / INPUT_STORE).read_text(encoding="utf-8")

    assert '<textarea id="chat-input"' in chat_bar
    assert "contenteditable" not in chat_bar
    assert "handlePaste" not in chat_bar
    assert "composer-code" not in chat_bar
    assert "is-code-context" not in chat_bar

    assert 'this._message = editor.value ?? ""' in store
    assert "if (editor.value !== text) editor.value = text;" in store
    for gone in (
        "execCommand",
        "handlePaste",
        "_insertPlainText",
        "_plainText",
        "BLOCK_TAGS",
        "_tryCreateCodeBlock",
        "FENCE_LINE_RE",
        "data-code-block",
        "_isCaretInsideFence",
        "_setEditorEmptyState",
        "is-empty",
    ):
        assert gone not in store
