from typing import Any
from python.helpers.extension import Extension


class StoreLastToolCall(Extension):
    async def execute(self, response_data: dict[str, Any] | None = None, tool_name: str = "", tool_args: dict[str, Any] | None = None, **kwargs):
        if not response_data:
            return

        response = response_data.get("response") if isinstance(response_data, dict) else None
        if response is None:
            return

        try:
            message = getattr(response, "message") if hasattr(response, "message") else str(response)
        except Exception:
            message = str(response)

        self.agent.set_data(
            "last_tool_call",
            {
                "tool_name": tool_name or "",
                "tool_args": tool_args or {},
                "last_tool_output": message or "",
            },
        )
