import uuid
from typing import Any

from python.helpers.extension import Extension
from python.helpers.settings import get_settings
from python.helpers import telemetry, cowork, master_orchestrator, observability_adapters


class TelemetryToolStart(Extension):
    async def execute(self, tool_args: dict[str, Any] | None = None, tool_name: str = "", **kwargs):
        settings = get_settings()
        if not settings.get("telemetry_enabled"):
            return

        tool_args = tool_args or {}
        active = self.agent.get_data("_telemetry_active") or {}
        trace_id = str(uuid.uuid4())
        start_ms = telemetry.now_ms()

        active[tool_name] = {
            "trace_id": trace_id,
            "start_ms": start_ms,
            "tool_args": cowork.summarize_args(tool_args),
        }
        self.agent.set_data("_telemetry_active", active)

        event = telemetry.build_event(
            self.agent.context,
            trace_id=trace_id,
            agent_name=self.agent.agent_name,
            agent_number=self.agent.number,
            tool_name=tool_name,
            stage="tool_start",
            tool_args=cowork.summarize_args(tool_args),
            status="started",
        )
        telemetry.record_event(
            self.agent.context,
            event,
            max_events=int(settings.get("telemetry_max_events", 200)),
        )

        step_id = master_orchestrator.record_tool_start(
            self.agent.context,
            tool_name=tool_name,
            trace_id=trace_id,
            agent_name=self.agent.agent_name,
            agent_number=self.agent.number,
            tool_args=cowork.summarize_args(tool_args),
            auto_store=settings.get("observability_auto_store", True),
        )
        if step_id:
            active[tool_name]["step_id"] = step_id
            self.agent.set_data("_telemetry_active", active)

        observability_adapters.dispatch_event(self.agent.context, event)
