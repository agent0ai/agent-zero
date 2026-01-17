from python.helpers.audit import hash_event, verify_event_hash


def test_hash_event_is_deterministic():
    payload = {"b": 2, "a": 1}
    first = hash_event("calendar.event_created", payload)
    second = hash_event("calendar.event_created", payload)
    assert first == second


def test_verify_event_hash():
    payload = {"id": 42, "title": "Sync"}
    event_hash = hash_event("finance.txn_ingested", payload)
    assert verify_event_hash("finance.txn_ingested", payload, event_hash) is True
