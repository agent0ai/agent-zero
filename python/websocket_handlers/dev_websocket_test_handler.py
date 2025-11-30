from __future__ import annotations

import asyncio
from typing import Any, Dict

from python.helpers.print_style import PrintStyle
from python.helpers import runtime
from python.helpers.websocket import WebSocketHandler, WebSocketResult


class DevWebsocketTestHandler(WebSocketHandler):
    """Test harness handler powering the developer WebSocket validation component."""

    @classmethod
    def get_event_types(cls) -> list[str]:
        return [
            "ws_tester_emit",
            "ws_tester_request",
            "ws_tester_request_delayed",
            "ws_tester_trigger_persistence",
            "ws_tester_request_all",
            "ws_tester_broadcast_demo_trigger",
            "ws_event_console_subscribe",
            "ws_event_console_unsubscribe",
        ]

    async def process_event(
        self, event_type: str, data: Dict[str, Any], sid: str
    ) -> dict[str, Any] | WebSocketResult | None:
        if event_type == "ws_event_console_subscribe":
            if not runtime.is_development():
                return self.result_error(
                    code="NOT_AVAILABLE",
                    message="Event console is available only in development mode",
                )
            registered = self.manager.register_diagnostic_watcher(sid)
            if not registered:
                return self.result_error(
                    code="SUBSCRIBE_FAILED",
                    message="Unable to subscribe to diagnostics",
                )
            return self.result_ok(
                {"status": "subscribed", "timestamp": data.get("requestedAt")}
            )

        if event_type == "ws_event_console_unsubscribe":
            self.manager.unregister_diagnostic_watcher(sid)
            return self.result_ok({"status": "unsubscribed"})

        if event_type == "ws_tester_emit":
            message = data.get("message", "emit")
            payload = {
                "message": message,
                "echo": True,
                "timestamp": data.get("timestamp"),
            }
            await self.broadcast("ws_tester_broadcast", payload)
            PrintStyle.info(f"Harness emit broadcasted message='{message}'")
            return None

        if event_type == "ws_tester_request":
            value = data.get("value")
            response = {
                "echo": value,
                "handler": self.identifier,
                "status": "ok",
            }
            PrintStyle.debug("Harness request responded with echo %s", value)
            return self.result_ok(
                response,
                correlation_id=data.get("correlationId"),
            )

        if event_type == "ws_tester_request_delayed":
            delay_ms = int(data.get("delay_ms", 0))
            await asyncio.sleep(delay_ms / 1000)
            PrintStyle.warning(
                "Harness delayed request finished after %s ms", delay_ms
            )
            return self.result_ok(
                {
                    "status": "delayed",
                    "delay_ms": delay_ms,
                    "handler": self.identifier,
                },
                correlation_id=data.get("correlationId"),
            )

        if event_type == "ws_tester_trigger_persistence":
            phase = data.get("phase", "unknown")
            payload = {
                "phase": phase,
                "handler": self.identifier,
            }
            await self.emit_to(sid, "ws_tester_persistence", payload)
            PrintStyle.info(f"Harness persistence event phase='{phase}' -> {sid}")
            return None

        if event_type == "ws_tester_request_all":
            marker = data.get("marker")
            PrintStyle.debug(
                "Harness requestAll invoked by %s marker='%s'", sid, marker
            )
            exclude_handlers = data.get("excludeHandlers")
            aggregated = await self.request_all(
                "ws_tester_request",
                data,
                timeout_ms=2_000,
                exclude_handlers=exclude_handlers,
            )
            return self.result_ok(
                {"results": aggregated},
                correlation_id=data.get("correlationId"),
            )

        if event_type == "ws_tester_broadcast_demo_trigger":
            payload = {
                "demo": True,
                "requested_at": data.get("requested_at"),
            }
            await self.broadcast("ws_tester_broadcast_demo", payload)
            PrintStyle.info("Harness broadcast demo event dispatched")
            return None

        PrintStyle.warning(f"Harness received unknown event '{event_type}'")
        return self.result_error(
            code="HARNESS_UNKNOWN_EVENT",
            message="Unhandled event",
            details=event_type,
        )
