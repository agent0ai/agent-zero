from helpers.websocket import WebSocketHandler, WebSocketResult
from helpers import extension


class WebuiHandler(WebSocketHandler):
    async def on_connect(self, sid: str) -> None:
        await extension.call_extensions_async(
            "webui_ws_connect", agent=None, instance=self, sid=sid
        )

    async def on_disconnect(self, sid: str) -> None:
        await extension.call_extensions_async(
            "webui_ws_disconnect", agent=None, instance=self, sid=sid
        )

    async def process_event(
        self, event_type: str, data: dict, sid: str
    ) -> dict | WebSocketResult | None:
        response_data: dict = {}

        await extension.call_extensions_async(
            "webui_ws_event",
            agent=None,
            instance=self,
            sid=sid,
            event_type=event_type,
            data=data,
            response_data=response_data,
        )

        return self.result_ok(
            response_data,
            correlation_id=data.get("correlationId"),
        )
