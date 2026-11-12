import asyncio
import hashlib
from typing import Any
import uuid

from helpers.ws import WsHandler
from helpers.ws_manager import WsResult
from helpers.print_style import PrintStyle
from helpers import runtime


_MAX_CONNECTOR_TRANSFER_TEST_BYTES = 32 * 1024 * 1024


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

        if event == "ws_tester_emit_to":
            payload = {
                "message": data.get("message", "emit"),
                "echo": True,
                "timestamp": data.get("timestamp"),
            }
            await self.emit_to(sid, "ws_tester_emit_to_result", payload)
            return {"status": "emitted"}

        if event == "ws_tester_connector_transfer":
            try:
                request_bytes = int(data.get("request_bytes", 0))
                result_bytes = int(data.get("result_bytes", 0))
            except (TypeError, ValueError):
                request_bytes = result_bytes = -1
            if not (
                0 <= request_bytes <= _MAX_CONNECTOR_TRANSFER_TEST_BYTES
                and 0 <= result_bytes <= _MAX_CONNECTOR_TRANSFER_TEST_BYTES
            ):
                return WsResult.error(
                    code="INVALID_SIZE",
                    message=(
                        "request_bytes and result_bytes must be between 0 and "
                        f"{_MAX_CONNECTOR_TRANSFER_TEST_BYTES}"
                    ),
                )

            from plugins._a0_connector.helpers.ws_runtime import (
                abort_transfers_for_context,
                clear_pending_browser_op,
                emit_connector_event,
                store_pending_browser_op,
            )

            op_id = uuid.uuid4().hex
            loop = asyncio.get_running_loop()
            future: asyncio.Future[dict[str, Any]] = loop.create_future()
            store_pending_browser_op(
                op_id,
                sid=sid,
                future=future,
                loop=loop,
                context_id="ws-dev-test",
            )
            cancel_task: asyncio.Task[int] | None = None
            cancelled_transfers = 0
            if bool(data.get("cancel")):
                async def cancel_after_start() -> int:
                    await asyncio.sleep(0)
                    return await abort_transfers_for_context(
                        "ws-dev-test",
                        reason="developer harness cancelled transfer",
                        manager=self.manager,
                    )

                cancel_task = asyncio.create_task(cancel_after_start())
            try:
                await emit_connector_event(
                    sid,
                    "connector_browser_op",
                    {
                        "op_id": op_id,
                        "context_id": "ws-dev-test",
                        "action": "transfer_stress",
                        "request_padding": "r" * request_bytes,
                        "result_bytes": result_bytes,
                    },
                    handler_id=self.identifier,
                    manager=self.manager,
                )
                result = await asyncio.wait_for(future, timeout=30)
            finally:
                clear_pending_browser_op(op_id)
                if cancel_task is not None:
                    cancelled_transfers = await cancel_task

            result_payload = result.get("result") if isinstance(result, dict) else None
            result_padding = (
                str(result_payload.get("result_padding") or "")
                if isinstance(result_payload, dict)
                else ""
            )
            response = {
                "status": "ok" if result.get("ok") is True else "error",
                "request_bytes": request_bytes,
                "result_bytes": len(result_padding.encode("utf-8")),
                "result_sha256": hashlib.sha256(result_padding.encode("utf-8")).hexdigest(),
            }
            if cancel_task is not None:
                response["status"] = "cancelled" if cancelled_transfers else "error"
                response["cancelled_transfers"] = cancelled_transfers
            return response

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
