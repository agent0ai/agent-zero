from __future__ import annotations

from typing import Any

from python.helpers.websocket import WebSocketHandler, WebSocketResult


class RootDefaultHandler(WebSocketHandler):
    """Reserved root (`/`) namespace diagnostics-only handler.

    Root is intentionally *not* used for application traffic. This handler exists to support
    optional low-risk diagnostics on `/` without making root behave like a global namespace.
    """

    @classmethod
    def requires_auth(cls) -> bool:
        return False

    @classmethod
    def requires_csrf(cls) -> bool:
        return False

    @classmethod
    def get_event_types(cls) -> list[str]:
        # Diagnostics-only noop endpoint.
        return ["ws_root_echo"]

    async def process_event(
        self, event_type: str, data: dict[str, Any], sid: str
    ) -> dict[str, Any] | WebSocketResult | None:
        return {"ok": True, "namespace": self.namespace, "sid": sid, "echo": data}
