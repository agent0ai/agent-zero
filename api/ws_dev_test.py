import asyncio
from typing import Any

from helpers.ws import WsHandler
from helpers.ws_manager import WsResult
from helpers.print_style import PrintStyle
from helpers import runtime


class WsDevTest(WsHandler):
    """Developer-only WebSocket test harness handler."""

    async def process(self, event: str, data: dict, sid: str) -> dict[str, Any] | WsResult | None:
        if event == "ws_event_console_subscribe":
            if not runtime.is_development():
                return WsResult.error(
                    code="NOT_AVAILABLE",
                    message="Event console is available only in development mode",
                )
            registered = self.manager.register_diagnostic_watcher(self.namespace, sid)
            if not registered:
                return WsResult.error(
                    code="SUBSCRIBE_FAILED",
                    message="Unable to subscribe to diagnostics",
                )
            return {"status": "subscribed", "timestamp": data.get("requestedAt")}

        if event == "ws_event_console_unsubscribe":
            self.manager.unregister_diagnostic_watcher(self.namespace, sid)
            return {"status": "unsubscribed"}

        if event == "ws_tester_emit":
            message = data.get("message", "emit")
            payload = {"message": message, "echo": True, "timestamp": data.get("timestamp")}
            await self.broadcast("ws_tester_broadcast", payload)
            PrintStyle.info(f"Harness emit broadcasted message='{message}'")
            return None

        if event == "ws_tester_request":
            value = data.get("value")
            PrintStyle.debug("Harness request responded with echo %s", value)
            return {"echo": value, "handler": self.identifier, "status": "ok"}

        if event == "ws_tester_request_delayed":
            delay_ms = int(data.get("delay_ms", 0))
            await asyncio.sleep(delay_ms / 1000)
            PrintStyle.warning("Harness delayed request finished after %s ms", delay_ms)
            return {"status": "delayed", "delay_ms": delay_ms, "handler": self.identifier}

        if event == "ws_tester_trigger_persistence":
            phase = data.get("phase", "unknown")
            payload = {"phase": phase, "handler": self.identifier}
            await self.emit_to(sid, "ws_tester_persistence", payload)
            PrintStyle.info(f"Harness persistence event phase='{phase}' -> {sid}")
            return None

        if event == "ws_tester_broadcast_demo_trigger":
            payload = {"demo": True, "requested_at": data.get("requested_at")}
            await self.broadcast("ws_tester_broadcast_demo", payload)
            PrintStyle.info("Harness broadcast demo event dispatched")
            return None

        if event == "ws_tester_request_all":
            correlation_id = data.get("correlationId")
            aggregated = await self.dispatch_to_all_sids(
                "ws_tester_request",
                {"value": data.get("marker", "aggregate")},
                correlation_id=correlation_id,
            )
            return {"results": aggregated}

        # Ignore events not targeted at this handler (other activated handlers
        # may process them).  Only warn for events that look like dev-harness
        # traffic so we don't spam logs with unrelated events.
        if event.startswith("ws_tester_"):
            PrintStyle.warning(f"Harness received unknown event '{event}'")
        return None
