from __future__ import annotations

from helpers.extension import Extension
from plugins._code_execution.helpers.destinations import ExecutionDestination


class IncludeConnectedHostDestination(Extension):
    def execute(self, destinations: list[ExecutionDestination], **kwargs) -> None:
        if self.agent is None:
            return
        context_id = str(getattr(getattr(self.agent, "context", None), "id", "") or "")
        if not context_id:
            return
        try:
            from plugins._a0_connector.helpers.remote_tool_prompts import (
                remote_tool_prompt_availability,
            )

            available = remote_tool_prompt_availability(context_id)
        except ImportError:
            return
        if available.get("code_execution_remote"):
            destinations.append(
                ExecutionDestination(
                    id="host",
                    kind="host",
                    label="Connected host",
                    description="The A0 CLI or Launcher host computer connected to this chat.",
                    status="connected",
                )
            )
