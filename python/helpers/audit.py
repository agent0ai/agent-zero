import hashlib
import json
from typing import Any


def _canonical_json(payload: dict[str, Any]) -> str:
    return json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=True)


def hash_event(event_type: str, payload: dict[str, Any]) -> str:
    canonical = _canonical_json({"type": event_type, "payload": payload})
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def verify_event_hash(event_type: str, payload: dict[str, Any], event_hash: str) -> bool:
    return hash_event(event_type, payload) == event_hash
