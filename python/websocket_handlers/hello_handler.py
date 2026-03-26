from __future__ import annotations

from helpers.print_style import PrintStyle
from helpers.websocket import WebSocketHandler


class HelloHandler(WebSocketHandler):
    """Sample handler used for foundational testing."""

    async def process_event(self, event_type: str, data: dict, sid: str):
        name = data.get("name") or "stranger"
        PrintStyle.info(f"hello_request from {sid} ({name})")
        return {"message": f"Hello, {name}!", "handler": self.identifier}


