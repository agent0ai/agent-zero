from helpers.extension import Extension
from helpers.mcp_sampling import SamplingManager
from helpers.print_style import PrintStyle


class McpSamplingWsHandler(Extension):
    """Handle sampling response events from the frontend."""

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

        if event_type == "mcp_sampling_response":
            await self._handle_sampling_response(data, response_data)
        elif event_type == "mcp_sampling_list_pending":
            await self._handle_list_pending(response_data)

    async def _handle_sampling_response(
        self,
        data: dict,
        response_data: dict | None,
    ):
        request_id = data.get("request_id", "")
        action = data.get("action", "")

        if not request_id:
            PrintStyle(font_color="orange", padding=True).print(
                "MCP Sampling WS: Received response with no request_id"
            )
            if response_data is not None:
                response_data["ok"] = False
                response_data["error"] = "Missing request_id"
            return

        if not action:
            PrintStyle(font_color="orange", padding=True).print(
                f"MCP Sampling WS: Received response with no action for request '{request_id}'"
            )
            if response_data is not None:
                response_data["ok"] = False
                response_data["error"] = "Missing action"
            return

        manager = SamplingManager.get_instance()
        resolved = manager.resolve(request_id, action)

        if response_data is not None:
            response_data["ok"] = resolved
            if not resolved:
                response_data["error"] = f"Request '{request_id}' not found or already resolved"

    async def _handle_list_pending(self, response_data: dict | None):
        manager = SamplingManager.get_instance()
        pending = manager.get_all_pending()

        if response_data is not None:
            response_data["ok"] = True
            response_data["pending"] = pending
