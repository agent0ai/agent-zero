"""Immutable, server-derived restrictions for non-session WebSocket clients."""

from dataclasses import dataclass
import re


class WsScopeDeniedError(PermissionError):
    """An internal emit attempted to cross a restricted socket boundary."""


@dataclass(frozen=True, slots=True)
class WsPrincipal:
    principal_type: str
    principal_id: str
    subject_id: str
    scopes: frozenset[str]
    handler_path: str
    handler_id: str
    inbound_events: frozenset[str]
    outbound_events: frozenset[str]
    key_generation: int
    diagnostic_mode: str = "bridge_redacted"

    def __post_init__(self) -> None:
        # Copy even server-supplied collections; frozen dataclasses alone do not
        # protect mutable collection fields.
        for name in ("scopes", "inbound_events", "outbound_events"):
            object.__setattr__(self, name, frozenset(getattr(self, name)))
        if self.diagnostic_mode != "bridge_redacted":
            raise ValueError("Restricted principals require redacted diagnostics")

    def permits_inbound(self, event: str, handler_id: str) -> bool:
        return handler_id == self.handler_id and event in self.inbound_events

    def permits_outbound(self, event: str, handler_id: str | None) -> bool:
        return handler_id == self.handler_id and event in self.outbound_events


def restricted_correlation_id(value: object) -> str:
    """Never reflect arbitrary client payloads as correlation metadata."""
    import uuid

    if isinstance(value, str) and re.fullmatch(r"[A-Za-z0-9_-]{1,128}", value):
        return value
    return uuid.uuid4().hex
