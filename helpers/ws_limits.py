"""Shared WebSocket payload limits for Agent Zero transports."""

from __future__ import annotations

import os
from typing import Any


DEFAULT_WS_MAX_PAYLOAD_BYTES = 50 * 1024 * 1024
LEGACY_WS_MAX_PAYLOAD_BYTES = 4 * 1024 * 1024


def _positive_int_env(name: str, default: int) -> int:
    try:
        value = int(os.getenv(name, str(default)))
    except (TypeError, ValueError):
        return default
    return value if value > 0 else default


A0_WS_MAX_PAYLOAD_BYTES = _positive_int_env(
    "A0_WS_MAX_PAYLOAD_BYTES",
    DEFAULT_WS_MAX_PAYLOAD_BYTES,
)


def peer_ws_max_payload_bytes(value: Any) -> int:
    """Return a safe outbound limit for a peer capability value."""
    try:
        limit = int(value)
    except (TypeError, ValueError):
        return min(LEGACY_WS_MAX_PAYLOAD_BYTES, A0_WS_MAX_PAYLOAD_BYTES)
    if limit <= 0:
        return min(LEGACY_WS_MAX_PAYLOAD_BYTES, A0_WS_MAX_PAYLOAD_BYTES)
    return min(limit, A0_WS_MAX_PAYLOAD_BYTES)
