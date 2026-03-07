"""Base class for messaging channel adapters.

Defines the ChannelBridge abstract base, NormalizedMessage data class,
and ChannelStatus enum used across all channel adapters.
"""

from __future__ import annotations

import time
import uuid
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class ChannelStatus(Enum):
    """Lifecycle status for a channel adapter."""

    DISCONNECTED = "disconnected"
    CONNECTING = "connecting"
    CONNECTED = "connected"
    ERROR = "error"


@dataclass
class NormalizedMessage:
    """Platform-agnostic message representation.

    Every adapter converts its native payload into this form so that
    downstream processing (queue, store, gateway) never depends on
    platform-specific fields.
    """

    id: str = field(default_factory=lambda: uuid.uuid4().hex)
    channel: str = ""
    sender_id: str = ""
    sender_name: str = ""
    text: str = ""
    timestamp: float = field(default_factory=time.time)
    metadata: dict[str, Any] = field(default_factory=dict)
    raw: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "channel": self.channel,
            "sender_id": self.sender_id,
            "sender_name": self.sender_name,
            "text": self.text,
            "timestamp": self.timestamp,
            "metadata": self.metadata,
        }


class ChannelBridge(ABC):
    """Abstract base for all messaging channel adapters.

    Subclasses must implement ``normalize``, ``send``, ``verify_webhook``,
    and ``connect``/``disconnect`` for lifecycle management.
    """

    def __init__(self, config: dict[str, Any]) -> None:
        self.config = config
        self.status: ChannelStatus = ChannelStatus.DISCONNECTED

    # --- abstract interface ---------------------------------------------------

    @abstractmethod
    async def normalize(self, raw_payload: dict[str, Any]) -> NormalizedMessage:
        """Convert a platform-specific payload into a NormalizedMessage."""
        ...

    @abstractmethod
    async def send(self, target_id: str, text: str, **kwargs: Any) -> dict[str, Any]:
        """Send a message to the platform. Return platform response dict."""
        ...

    @abstractmethod
    async def verify_webhook(self, headers: dict[str, str], body: bytes) -> bool:
        """Validate that an incoming webhook request is authentic."""
        ...

    @abstractmethod
    async def connect(self) -> None:
        """Establish connection / register with the platform."""
        ...

    @abstractmethod
    async def disconnect(self) -> None:
        """Tear down connection / cleanup resources."""
        ...

    # --- helpers --------------------------------------------------------------

    @property
    def name(self) -> str:
        """Return the adapter name (lowercase class name sans 'Adapter')."""
        cls_name = type(self).__name__
        return cls_name.replace("Adapter", "").lower()
