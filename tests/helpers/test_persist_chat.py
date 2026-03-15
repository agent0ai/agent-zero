from __future__ import annotations


def test_deserialize_log_preserves_item_id() -> None:
    from python.helpers.log import Log
    from python.helpers.persist_chat import _deserialize_log, _serialize_log

    log = Log()
    log.log(type="user", heading="User message", content="hello", id="msg-123")
    log.log(type="assistant", heading="Assistant", content="hi")

    serialized = _serialize_log(log)
    restored = _deserialize_log(serialized)

    assert restored.logs[0].type == "user"
    assert restored.logs[0].id == "msg-123"
    assert restored.logs[1].type == "assistant"
    assert restored.logs[1].id is None
