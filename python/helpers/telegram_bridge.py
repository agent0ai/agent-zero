"""Telegram webhook routing and state management."""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any
import re


STATE_PATH = Path(os.getenv("TELEGRAM_STATE_PATH", "data/telegram_state.json"))


def load_state() -> dict[str, Any]:
    if not STATE_PATH.exists():
        return {"chat_contexts": {}, "last_update": {}}
    return json.loads(STATE_PATH.read_text(encoding="utf-8"))


def save_state(state: dict[str, Any]) -> None:
    STATE_PATH.parent.mkdir(parents=True, exist_ok=True)
    STATE_PATH.write_text(json.dumps(state, indent=2) + "\n", encoding="utf-8")


def get_context_for_chat(chat_id: str) -> str | None:
    state = load_state()
    return state.get("chat_contexts", {}).get(chat_id)


def set_context_for_chat(chat_id: str, ctxid: str) -> None:
    state = load_state()
    state.setdefault("chat_contexts", {})[chat_id] = ctxid
    save_state(state)


def clear_context_for_chat(chat_id: str) -> None:
    state = load_state()
    if chat_id in state.get("chat_contexts", {}):
        state["chat_contexts"].pop(chat_id, None)
    save_state(state)


def should_ignore_update(chat_id: str, update_id: int) -> bool:
    state = load_state()
    last_update = state.setdefault("last_update", {}).get(chat_id, -1)
    if update_id <= int(last_update):
        return True
    state["last_update"][chat_id] = update_id
    save_state(state)
    return False


TAG_KEYWORDS = {
    "idea": ["idea", "brainstorm"],
    "risk": ["risk", "concern", "issue"],
    "decision": ["decision", "decide", "decided"],
    "action": ["action", "todo", "to-do", "task"],
    "followup": ["follow up", "follow-up", "followup"],
    "update": ["update", "status"],
    "link": ["http://", "https://"],
}


def extract_tags(text: str) -> list[str]:
    tags = set()
    if not text:
        return []

    for tag in re.findall(r"#([a-zA-Z0-9_-]+)", text):
        tags.add(tag.lower())

    lower = text.lower()
    for tag, keywords in TAG_KEYWORDS.items():
        if any(keyword in lower for keyword in keywords):
            tags.add(tag)

    tags.add("telegram")
    return sorted(tags)


def build_title(text: str, max_words: int = 8) -> str:
    words = [word for word in re.split(r"\s+", text.strip()) if word]
    if not words:
        return "Telegram Update"
    snippet = " ".join(words[:max_words])
    if len(words) > max_words:
        snippet += "..."
    return f"Telegram: {snippet}"
