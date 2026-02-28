from typing import Any
from python.helpers import master_orchestrator, observability_adapters, telemetry
from python.helpers.extension import Extension
from python.helpers.settings import get_settings


class TelemetryToolEnd(Extension):
    async def execute(self, response=None, tool_name: str = "", **kwargs):
        settings = get_settings()
        if not settings.get("telemetry_enabled"):
            return

        active = self.agent.get_data("_telemetry_active") or {}
        tool_state = active.pop(tool_name, None)
        if tool_state:
            self.agent.set_data("_telemetry_active", active)

        trace_id = tool_state.get("trace_id") if tool_state else ""
        start_ms = tool_state.get("start_ms") if tool_state else None
        duration_ms = telemetry.now_ms() - start_ms if start_ms else None

        event = telemetry.build_event(
            self.agent.context,
            trace_id=trace_id or "",
            agent_name=self.agent.agent_name,
            agent_number=self.agent.number,
            tool_name=tool_name,
            stage="tool_end",
            duration_ms=duration_ms,
            status="success",
        )
        telemetry.record_event(
            self.agent.context,
            event,
            max_events=int(settings.get("telemetry_max_events", 200)),
        )
        telemetry.update_stats(self.agent.context, tool_name, duration_ms, "success")

        step_id = tool_state.get("step_id") if tool_state else None
        master_orchestrator.record_tool_end(
            self.agent.context,
            step_id=step_id,
            status="success",
            duration_ms=duration_ms,
            output=self._extract_output(response),
        )

        observability_adapters.dispatch_event(self.agent.context, event)

    @staticmethod
    def _extract_output(response: Any) -> dict[str, Any] | None:
        additional = getattr(response, "additional", None)
        if not isinstance(additional, dict):
            return None
        return additional
