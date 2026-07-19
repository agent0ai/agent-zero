from __future__ import annotations

import time
from typing import Any
from urllib.parse import parse_qs, urlparse

from plugins._oauth.helpers import state as state_store


def parse_manual_callback(raw: Any) -> dict[str, str | None] | None:
    text = "" if raw is None else str(raw).strip()
    if not text:
        return None

    if text.startswith("http://") or text.startswith("https://"):
        query = urlparse(text).query
    elif text.startswith("?"):
        query = text[1:]
    elif "=" in text or "&" in text:
        query = text
    else:
        return {
            "code": text,
            "state": None,
            "error": None,
            "error_description": None,
        }

    parsed = parse_qs(query, keep_blank_values=True)
    return {
        "code": first_query_value(parsed, "code"),
        "state": first_query_value(parsed, "state"),
        "error": first_query_value(parsed, "error"),
        "error_description": first_query_value(parsed, "error_description"),
    }


def latest_attempt(provider_id: str):
    state_store.cleanup_expired()
    with state_store._lock:
        attempts = [
            attempt
            for attempt in state_store._attempts.values()
            if attempt.provider_id == provider_id and not attempt.expired()
        ]
    if not attempts:
        return None
    return max(attempts, key=lambda attempt: attempt.created_at)


def models_from_payload(payload: Any) -> list[str]:
    values: list[Any]
    if isinstance(payload, dict) and isinstance(payload.get("data"), list):
        values = payload["data"]
    elif isinstance(payload, dict) and isinstance(payload.get("models"), list):
        values = payload["models"]
    elif isinstance(payload, list):
        values = payload
    else:
        return []

    models: list[str] = []
    seen: set[str] = set()
    for value in values:
        model_id = ""
        if isinstance(value, str):
            model_id = value
        elif isinstance(value, dict):
            model_id = str(value.get("id") or value.get("name") or "")
        model_id = model_id.strip()
        if model_id.startswith("models/"):
            model_id = model_id.split("/", 1)[1]
        if model_id and model_id not in seen:
            seen.add(model_id)
            models.append(model_id)
    return models


def json_payload(response: Any) -> dict[str, Any]:
    try:
        payload = response.json()
    except Exception:
        payload = {}
    if not isinstance(payload, dict):
        return {}
    return payload


def error_message(payload: dict[str, Any], fallback: str) -> str:
    error = payload.get("error")
    if isinstance(error, dict):
        return str(error.get("message") or error.get("status") or fallback)
    return str(payload.get("error_description") or payload.get("error") or fallback)


def first_query_value(parsed: dict[str, list[str]], key: str) -> str | None:
    values = parsed.get(key) or []
    if not values:
        return None
    return values[0]


def as_optional_string(value: Any) -> str | None:
    if isinstance(value, list):
        value = value[0] if value else None
    text = "" if value is None else str(value).strip()
    return text or None


def expires_ms(payload: dict[str, Any]) -> int:
    if payload.get("expires_at") is not None:
        try:
            value = float(payload["expires_at"])
            if value < 1_000_000_000_000:
                value *= 1000
            return int(value)
        except (TypeError, ValueError):
            pass
    try:
        return int((time.time() + float(payload.get("expires_in") or 0)) * 1000)
    except (TypeError, ValueError):
        return 0


def as_int(value: Any, default: int) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return default
