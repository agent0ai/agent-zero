from helpers import runtime
from helpers.extension import Extension
from helpers.print_style import PrintStyle
from helpers.state_monitor import get_state_monitor, _ws_debug_enabled
from helpers.state_snapshot import (
    StateRequestValidationError,
    parse_state_request_payload,
)


class StateSync(Extension):
    async def execute(
        self,
        instance=None,
        sid: str = "",
        event_type: str = "",
        data: dict | None = None,
        response_data: dict | None = None,
        **kwargs,
    ):
        if instance is None or data is None:
            return

        if event_type != "state_request":
            return

        correlation_id = data.get("correlationId")
        try:
            request = parse_state_request_payload(data)
        except StateRequestValidationError as exc:
            PrintStyle.warning(
                f"[WebuiHandler] INVALID_REQUEST sid={sid} reason={exc.reason} details={exc.details!r}"
            )
            if response_data is not None:
                response_data["code"] = "INVALID_REQUEST"
                response_data["message"] = str(exc)
            return

        if _ws_debug_enabled():
            PrintStyle.debug(
                f"[WebuiHandler] state_request sid={sid} context={request.context!r} "
                f"log_from={request.log_from} notifications_from={request.notifications_from} timezone={request.timezone!r} "
                f"correlation_id={correlation_id}"
            )

        seq_base = 1
        monitor = get_state_monitor()
        monitor.update_projection(
            instance.namespace,
            sid,
            request=request,
            seq_base=seq_base,
        )
        monitor.mark_dirty(
            instance.namespace,
            sid,
            reason="webui_ws_event.StateSync.state_request",
        )
        if _ws_debug_enabled():
            PrintStyle.debug(
                f"[WebuiHandler] state_request accepted sid={sid} seq_base={seq_base}"
            )

        if response_data is not None:
            response_data["runtime_epoch"] = runtime.get_runtime_id()
            response_data["seq_base"] = seq_base
