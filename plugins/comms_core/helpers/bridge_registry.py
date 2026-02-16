"""
Singleton registry for active communication bridges.

Each platform bridge registers itself on startup via register().
The generic channel_send tool and other consumers look up bridges here.
This enables platform-agnostic outbound messaging.
"""

import threading
from typing import Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from plugins.comms_core.helpers.bridge_base import CommunicationBridge

_lock = threading.RLock()
_bridges: dict[str, "CommunicationBridge"] = {}


def register(bridge: "CommunicationBridge") -> None:
    """Register a bridge instance. Called by platform plugins on startup."""
    with _lock:
        _bridges[bridge.platform_name] = bridge


def unregister(platform: str) -> None:
    """Unregister a bridge. Called on platform plugin shutdown."""
    with _lock:
        _bridges.pop(platform, None)


def get_bridge(platform: str) -> Optional["CommunicationBridge"]:
    """Look up a running bridge by platform name."""
    with _lock:
        return _bridges.get(platform)


def list_platforms() -> list[str]:
    """Return names of all registered platforms."""
    with _lock:
        return list(_bridges.keys())


def get_all() -> dict[str, "CommunicationBridge"]:
    """Return a snapshot of all registered bridges."""
    with _lock:
        return dict(_bridges)
