"""Base classes for multi-channel messaging gateway.

Provides abstract interfaces that each channel adapter implements.
Generalised from the Telegram bridge/client pattern.
"""

from __future__ import annotations

import json
import os
import re
import time
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

# ---------------------------------------------------------------------------
# Data models
# ---------------------------------------------------------------------------

MAX_MESSAGE_LENGTH = 8_000  # characters — reject messages exceeding this
MAX_ATTACHMENT_BYTES = 10 * 1024 * 1024  # 10 MiB per attachment


@dataclass
class NormalizedMessage:
    """Platform-agnostic inbound message."""

    channel: str  # e.g. "telegram", "slack", "discord", "whatsapp"
    conversation_id: str  # channel-specific conversation/chat identifier
    sender_id: str  # channel-specific user identifier
    text: str
    attachments: list[str] = field(default_factory=list)  # file paths / URLs
    metadata: dict[str, Any] = field(default_factory=dict)
    timestamp: float = field(default_factory=time.time)

    def validate(self) -> list[str]:
        """Return a list of validation errors (empty means valid)."""
        errors: list[str] = []
        if not self.channel:
            errors.append("channel is required")
        if not self.conversation_id:
            errors.append("conversation_id is required")
        if not self.sender_id:
            errors.append("sender_id is required")
        if not self.text or not self.text.strip():
            errors.append("text must not be empty")
        if len(self.text) > MAX_MESSAGE_LENGTH:
            errors.append(f"text exceeds {MAX_MESSAGE_LENGTH} characters " f"({len(self.text)})")
        return errors


@dataclass
class ChannelStatus:
    """Health snapshot for a single channel."""

    channel: str
    connected: bool = False
    enabled: bool = False
    error: str | None = None
    last_activity: float | None = None
    message_count: int = 0


# ---------------------------------------------------------------------------
# Tag extraction (shared across channels)
# ---------------------------------------------------------------------------

TAG_KEYWORDS: dict[str, list[str]] = {
    "idea": ["idea", "brainstorm"],
    "risk": ["risk", "concern", "issue"],
    "decision": ["decision", "decide", "decided"],
    "action": ["action", "todo", "to-do", "task"],
    "followup": ["follow up", "follow-up", "followup"],
    "update": ["update", "status"],
    "link": ["http://", "https://"],
}


def extract_tags(text: str, channel_tag: str | None = None) -> list[str]:
    """Extract semantic tags from message text."""
    tags: set[str] = set()
    if not text:
        return []

    for tag in re.findall(r"#([a-zA-Z0-9_-]+)", text):
        tags.add(tag.lower())

    lower = text.lower()
    for tag, keywords in TAG_KEYWORDS.items():
        if any(kw in lower for kw in keywords):
            tags.add(tag)

    if channel_tag:
        tags.add(channel_tag)
    return sorted(tags)


def build_title(text: str, prefix: str = "Message", max_words: int = 8) -> str:
    """Create a short title from message text."""
    words = [w for w in re.split(r"\s+", text.strip()) if w]
    if not words:
        return f"{prefix} Update"
    snippet = " ".join(words[:max_words])
    if len(words) > max_words:
        snippet += "..."
    return f"{prefix}: {snippet}"


# ---------------------------------------------------------------------------
# Abstract channel bridge (state + routing)
# ---------------------------------------------------------------------------


class ChannelBridge(ABC):
    """Manages conversation-to-context mapping and deduplication for a channel."""

    def __init__(self, channel_name: str, state_dir: str = "data"):
        self.channel_name = channel_name
        self._state_path = Path(state_dir) / f"{channel_name}_state.json"

    # -- State persistence ---------------------------------------------------

    def load_state(self) -> dict[str, Any]:
        if not self._state_path.exists():
            return {"chat_contexts": {}, "last_update": {}}
        return json.loads(self._state_path.read_text(encoding="utf-8"))

    def save_state(self, state: dict[str, Any]) -> None:
        self._state_path.parent.mkdir(parents=True, exist_ok=True)
        self._state_path.write_text(json.dumps(state, indent=2) + "\n", encoding="utf-8")

    # -- Context routing -----------------------------------------------------

    def get_context_for_conversation(self, conversation_id: str) -> str | None:
        state = self.load_state()
        return state.get("chat_contexts", {}).get(conversation_id)

    def set_context_for_conversation(self, conversation_id: str, ctxid: str) -> None:
        state = self.load_state()
        state.setdefault("chat_contexts", {})[conversation_id] = ctxid
        self.save_state(state)

    def clear_context_for_conversation(self, conversation_id: str) -> None:
        state = self.load_state()
        state.get("chat_contexts", {}).pop(conversation_id, None)
        self.save_state(state)

    # -- Deduplication -------------------------------------------------------

    def should_ignore_update(self, conversation_id: str, update_id: int | str) -> bool:
        state = self.load_state()
        last = state.setdefault("last_update", {}).get(conversation_id, -1)
        update_val = int(update_id) if isinstance(update_id, str) else update_id
        if update_val <= int(last):
            return True
        state["last_update"][conversation_id] = update_val
        self.save_state(state)
        return False

    # -- Channel configuration -----------------------------------------------

    def is_configured(self) -> bool:
        """Return True if this channel has the required env vars set."""
        return all(os.getenv(v) for v in self.required_env_vars())

    @abstractmethod
    def required_env_vars(self) -> list[str]:
        """Return list of required environment variable names."""
        ...

    # -- Status ---------------------------------------------------------------

    def get_status(self) -> ChannelStatus:
        configured = self.is_configured()
        state = self.load_state()
        msg_count = sum(1 for _ in state.get("last_update", {}).values())
        return ChannelStatus(
            channel=self.channel_name,
            connected=configured,
            enabled=configured,
            last_activity=None,
            message_count=msg_count,
        )


# ---------------------------------------------------------------------------
# Abstract channel client (send messages to external platform)
# ---------------------------------------------------------------------------


class ChannelClient(ABC):
    """Sends messages to a specific external platform."""

    @abstractmethod
    async def send_message(self, recipient_id: str, text: str, **kwargs: Any) -> dict[str, Any]:
        """Send a text message to the platform. Returns platform response."""
        ...

    @abstractmethod
    async def verify_webhook_signature(
        self,
        payload: bytes,
        signature: str,
        **kwargs: Any,
    ) -> bool:
        """Verify that an incoming webhook is authentic."""
        ...
