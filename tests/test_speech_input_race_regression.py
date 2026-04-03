from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]


def test_update_chat_input_syncs_store_before_follow_up_send():
    index_js = (PROJECT_ROOT / "webui" / "index.js").read_text(encoding="utf-8")
    speech_store_js = (
        PROJECT_ROOT / "webui" / "components" / "chat" / "speech" / "speech-store.js"
    ).read_text(encoding="utf-8")
    update_chat_input_start = index_js.index("export function updateChatInput(text) {")
    update_chat_input_end = index_js.index("async function updateUserTime()")
    update_chat_input_block = index_js[
        update_chat_input_start:update_chat_input_end
    ]

    next_value_marker = "const nextValue = currentValue + (needsSpace ? \" \" : \"\") + text + \" \";"
    sync_marker = "inputStore.message = nextValue;"
    adjust_marker = "adjustTextareaHeight();"
    dispatch_marker = 'chatInputEl.dispatchEvent(new Event("input"));'

    assert next_value_marker in update_chat_input_block
    assert sync_marker in update_chat_input_block
    assert adjust_marker in update_chat_input_block
    assert dispatch_marker in update_chat_input_block
    assert update_chat_input_block.index(sync_marker) < update_chat_input_block.index(adjust_marker)
    assert update_chat_input_block.index(sync_marker) < update_chat_input_block.index(dispatch_marker)

    assert "updateChatInput(text);" in speech_store_js
    assert "await sendMessage();" in speech_store_js
