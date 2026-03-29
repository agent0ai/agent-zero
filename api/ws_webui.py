from helpers.ws import WsHandler
from helpers import extension


class WsWebui(WsHandler):
    """State synchronisation handler — the primary WebSocket endpoint for the UI."""

    async def on_connect(self, sid: str) -> None:
        await extension.call_extensions_async(
            "webui_ws_connect", agent=None, instance=self, sid=sid
        )

    async def on_disconnect(self, sid: str) -> None:
        await extension.call_extensions_async(
            "webui_ws_disconnect", agent=None, instance=self, sid=sid
        )

    async def process(self, event: str, data: dict, sid: str) -> dict | None:
        response_data: dict = {}

        await extension.call_extensions_async(
            "webui_ws_event",
            agent=None,
            instance=self,
            sid=sid,
            event_type=event,
            data=data,
            response_data=response_data,
        )

        # Return None (fire-and-forget) when no extension populated the response.
        return response_data if response_data else None
