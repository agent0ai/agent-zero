from __future__ import annotations

import pytz

from python.helpers import runtime
from python.helpers.print_style import PrintStyle
from python.helpers.websocket import WebSocketHandler, WebSocketResult
from python.helpers.state_monitor import get_state_monitor


class StateSyncHandler(WebSocketHandler):
    @classmethod
    def get_event_types(cls) -> list[str]:
        return ["state_request"]

    async def on_connect(self, sid: str) -> None:
        monitor = get_state_monitor()
        monitor.bind_manager(self.manager, handler_id=self.identifier)
        monitor.register_sid(sid)
        PrintStyle.info(f"[StateSyncHandler] connect sid={sid}")

    async def on_disconnect(self, sid: str) -> None:
        get_state_monitor().unregister_sid(sid)
        PrintStyle.info(f"[StateSyncHandler] disconnect sid={sid}")

    async def process_event(self, event_type: str, data: dict, sid: str) -> dict | WebSocketResult | None:
        correlation_id = data.get("correlationId")

        context = data.get("context")
        log_from = data.get("log_from")
        notifications_from = data.get("notifications_from")
        timezone = data.get("timezone")

        PrintStyle.debug(
            f"[StateSyncHandler] state_request sid={sid} context={context!r} "
            f"log_from={log_from} notifications_from={notifications_from} timezone={timezone!r} "
            f"correlation_id={correlation_id}"
        )

        if context is not None and not isinstance(context, str):
            PrintStyle.warning(
                f"[StateSyncHandler] INVALID_REQUEST sid={sid} reason=context_type "
                f"context_type={type(context).__name__}"
            )
            return self.result_error(
                code="INVALID_REQUEST",
                message="context must be a string or null",
                correlation_id=correlation_id,
            )
        if not isinstance(log_from, int) or log_from < 0:
            PrintStyle.warning(
                f"[StateSyncHandler] INVALID_REQUEST sid={sid} reason=log_from "
                f"log_from={log_from!r}"
            )
            return self.result_error(
                code="INVALID_REQUEST",
                message="log_from must be an integer >= 0",
                correlation_id=correlation_id,
            )
        if not isinstance(notifications_from, int) or notifications_from < 0:
            PrintStyle.warning(
                f"[StateSyncHandler] INVALID_REQUEST sid={sid} reason=notifications_from "
                f"notifications_from={notifications_from!r}"
            )
            return self.result_error(
                code="INVALID_REQUEST",
                message="notifications_from must be an integer >= 0",
                correlation_id=correlation_id,
            )
        if not isinstance(timezone, str) or not timezone.strip():
            PrintStyle.warning(
                f"[StateSyncHandler] INVALID_REQUEST sid={sid} reason=timezone_empty "
                f"timezone={timezone!r}"
            )
            return self.result_error(
                code="INVALID_REQUEST",
                message="timezone must be a non-empty string",
                correlation_id=correlation_id,
            )

        tz = timezone.strip()
        try:
            pytz.timezone(tz)
        except pytz.exceptions.UnknownTimeZoneError:
            PrintStyle.warning(
                f"[StateSyncHandler] INVALID_REQUEST sid={sid} reason=timezone_invalid timezone={tz!r}"
            )
            return self.result_error(
                code="INVALID_REQUEST",
                message="timezone must be a valid IANA timezone name",
                correlation_id=correlation_id,
            )

        # Baseline sequence must be reset on every state_request (new sync period).
        # V1 policy: seq_base starts >0 to allow simple gating checks.
        seq_base = 1
        monitor = get_state_monitor()
        monitor.update_projection(
            sid,
            context=(context.strip() or None) if isinstance(context, str) else None,
            log_from=log_from,
            notifications_from=notifications_from,
            timezone=tz,
            seq_base=seq_base,
        )
        # INVARIANT.STATE.INITIAL_SNAPSHOT: schedule a full snapshot quickly after handshake.
        monitor.mark_dirty(sid, reason="state_sync_handler.StateSyncHandler.state_request")
        PrintStyle.debug(f"[StateSyncHandler] state_request accepted sid={sid} seq_base={seq_base}")

        return self.result_ok(
            {
                "runtime_epoch": runtime.get_runtime_id(),
                "seq_base": seq_base,
            },
            correlation_id=correlation_id,
        )
