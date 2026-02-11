from __future__ import annotations

from python.helpers import runtime
from python.helpers.print_style import PrintStyle
from python.helpers.state_monitor import _ws_debug_enabled, get_state_monitor
from python.helpers.state_snapshot import (
    StateRequestValidationError,
    parse_state_request_payload,
)
from python.helpers.websocket import WebSocketHandler, WebSocketResult


class StateSyncHandler(WebSocketHandler):
    @classmethod
    def get_event_types(cls) -> list[str]:
        return ["state_request"]

    async def on_connect(self, sid: str) -> None:
        monitor = get_state_monitor()
        monitor.bind_manager(self.manager, handler_id=self.identifier)
        monitor.register_sid(self.namespace, sid)
        if _ws_debug_enabled():
            PrintStyle.debug(f"[StateSyncHandler] connect sid={sid}")

    async def on_disconnect(self, sid: str) -> None:
        get_state_monitor().unregister_sid(self.namespace, sid)
        if _ws_debug_enabled():
            PrintStyle.debug(f"[StateSyncHandler] disconnect sid={sid}")

    async def process_event(
        self, event_type: str, data: dict, sid: str
    ) -> dict | WebSocketResult | None:
        correlation_id = data.get("correlationId")
        try:
            request = parse_state_request_payload(data)
        except StateRequestValidationError as exc:
            PrintStyle.warning(
                f"[StateSyncHandler] INVALID_REQUEST sid={sid} reason={exc.reason} details={exc.details!r}"
            )
            return self.result_error(
                code="INVALID_REQUEST",
                message=str(exc),
                correlation_id=correlation_id,
            )

        if _ws_debug_enabled():
            PrintStyle.debug(
                f"[StateSyncHandler] state_request sid={sid} context={request.context!r} "
                f"log_from={request.log_from} notifications_from={request.notifications_from} timezone={request.timezone!r} "
                f"correlation_id={correlation_id}"
            )

        # Baseline sequence must be reset on every state_request (new sync period).
        # V1 policy: seq_base starts >0 to allow simple gating checks.
        seq_base = 1
        monitor = get_state_monitor()
        monitor.update_projection(
            self.namespace,
            sid,
            request=request,
            seq_base=seq_base,
        )
        # INVARIANT.STATE.INITIAL_SNAPSHOT: schedule a full snapshot quickly after handshake.
        monitor.mark_dirty(
            self.namespace,
            sid,
            reason="state_sync_handler.StateSyncHandler.state_request",
        )
        if _ws_debug_enabled():
            PrintStyle.debug(
                f"[StateSyncHandler] state_request accepted sid={sid} seq_base={seq_base}"
            )

        return self.result_ok(
            {
                "runtime_epoch": runtime.get_runtime_id(),
                "seq_base": seq_base,
            },
            correlation_id=correlation_id,
        )
