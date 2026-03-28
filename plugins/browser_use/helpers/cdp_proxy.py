"""CDP WebSocket proxy with method whitelisting.

Relays screencast frames from browser to viewer and input events from
viewer to browser. Only whitelisted CDP methods are allowed.
"""

from __future__ import annotations

import asyncio
import json
from typing import Any, Optional

from python.helpers.print_style import PrintStyle

# CDP methods allowed through the proxy
ALLOWED_METHODS = frozenset({
    # Screencast (viewer receives frames)
    "Page.startScreencast",
    "Page.stopScreencast",
    "Page.screencastFrameAck",
    # Input (viewer sends mouse/keyboard)
    "Input.dispatchMouseEvent",
    "Input.dispatchKeyEvent",
    "Input.dispatchTouchEvent",
    # Navigation
    "Page.navigate",
    "Page.reload",
    # Page info
    "Page.getFrameTree",
})

# CDP events forwarded from browser to viewer
ALLOWED_EVENTS = frozenset({
    "Page.screencastFrame",
    "Page.frameNavigated",
    "Page.loadEventFired",
    "Page.domContentEventFired",
})


class CDPProxy:
    """Proxies CDP messages between a WebUI viewer and the browser.

    Uses Playwright's CDPSession rather than raw WebSocket to avoid
    needing to know the browser's CDP port.
    """

    def __init__(self):
        self._cdp_session = None
        self._send_to_viewer = None
        self._active = False
        self._msg_id = 1000

    async def connect(self, session_manager, send_callback):
        """Connect to the browser's CDP session."""
        self._send_to_viewer = send_callback

        page = await session_manager.get_page()
        if not page:
            raise RuntimeError("No browser page available for CDP proxy")

        context = session_manager.browser_session.browser_context
        if not context:
            raise RuntimeError("No browser context available")

        self._cdp_session = await context.new_cdp_session(page)
        self._active = True

        for event in ALLOWED_EVENTS:
            self._cdp_session.on(event, lambda params, e=event: asyncio.ensure_future(
                self._on_browser_event(e, params)
            ))

        PrintStyle().print("CDP proxy connected")

    async def _on_browser_event(self, event: str, params: dict):
        """Forward browser CDP events to the viewer."""
        if not self._active or not self._send_to_viewer:
            return
        try:
            await self._send_to_viewer({
                "type": "event",
                "method": event,
                "params": params,
            })
        except Exception as e:
            PrintStyle().warning(f"CDP proxy: Failed to forward event {event}: {e}")

    async def handle_viewer_message(self, data: dict) -> Optional[dict]:
        """Handle a message from the WebUI viewer."""
        if not self._active or not self._cdp_session:
            return {"error": "CDP proxy not connected"}

        method = data.get("method", "")
        params = data.get("params", {})

        if method not in ALLOWED_METHODS:
            return {"error": f"Method '{method}' is not allowed"}

        try:
            result = await self._cdp_session.send(method, params)
            return {"id": data.get("id"), "result": result}
        except Exception as e:
            return {"id": data.get("id"), "error": str(e)}

    async def disconnect(self):
        """Disconnect the CDP proxy."""
        self._active = False
        if self._cdp_session:
            try:
                await self._cdp_session.detach()
            except Exception:
                pass
            self._cdp_session = None
        self._send_to_viewer = None
        PrintStyle().print("CDP proxy disconnected")
