from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]


def _extract_function_block(source: str, signature: str) -> str:
    start = source.index(signature)
    block_start = source.index("{", start)
    depth = 0

    for index in range(block_start, len(source)):
        char = source[index]
        if char == "{":
            depth += 1
        elif char == "}":
            depth -= 1
            if depth == 0:
                return source[start : index + 1]

    raise ValueError(f"Could not find closing brace for function: {signature}")


def test_update_chat_input_syncs_store_before_follow_up_send():
    index_js = (PROJECT_ROOT / "webui" / "index.js").read_text(encoding="utf-8")
    speech_store_js = (
        PROJECT_ROOT / "webui" / "components" / "chat" / "speech" / "speech-store.js"
    ).read_text(encoding="utf-8")
    update_chat_input_block = _extract_function_block(
        index_js, "export function updateChatInput(text)"
    )

    next_value_marker = "const nextValue ="
    value_assign_marker = "chatInputEl.value = nextValue;"
    sync_marker = "inputStore.message = nextValue;"
    adjust_marker = "adjustTextareaHeight();"
    dispatch_marker = "chatInputEl.dispatchEvent("
    update_call_marker = "updateChatInput(text);"
    send_marker = "await sendMessage();"

    assert next_value_marker in update_chat_input_block
    assert value_assign_marker in update_chat_input_block
    assert sync_marker in update_chat_input_block
    assert adjust_marker in update_chat_input_block
    assert dispatch_marker in update_chat_input_block
    assert update_chat_input_block.index(next_value_marker) < update_chat_input_block.index(value_assign_marker)
    assert update_chat_input_block.index(value_assign_marker) < update_chat_input_block.index(sync_marker)
    assert update_chat_input_block.index(sync_marker) < update_chat_input_block.index(adjust_marker)
    assert update_chat_input_block.index(sync_marker) < update_chat_input_block.index(dispatch_marker)

    assert update_call_marker in speech_store_js
    assert send_marker in speech_store_js
    assert speech_store_js.index(update_call_marker) < speech_store_js.index(send_marker)
