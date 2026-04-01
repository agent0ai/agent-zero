from helpers.extension import Extension
from helpers.mcp_elicitation import ElicitationManager
from helpers.print_style import PrintStyle


class McpElicitationWsHandler(Extension):
    """Handle elicitation response events from the frontend."""

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

        if event_type == "mcp_elicitation_response":
            await self._handle_elicitation_response(data, response_data)
        elif event_type == "mcp_elicitation_list_pending":
            await self._handle_list_pending(response_data)

    async def _handle_elicitation_response(
        self,
        data: dict,
        response_data: dict | None,
    ):
        request_id = data.get("request_id", "")
        action = data.get("action", "")
        content = data.get("content", None)

        if not request_id:
            PrintStyle(font_color="orange", padding=True).print(
                "MCP Elicitation WS: Received response with no request_id"
            )
            if response_data is not None:
                response_data["ok"] = False
                response_data["error"] = "Missing request_id"
            return

        if not action:
            PrintStyle(font_color="orange", padding=True).print(
                f"MCP Elicitation WS: Received response with no action for request '{request_id}'"
            )
            if response_data is not None:
                response_data["ok"] = False
                response_data["error"] = "Missing action"
            return

        manager = ElicitationManager.get_instance()
        resolved = manager.resolve(request_id, action, content)

        if response_data is not None:
            response_data["ok"] = resolved
            if not resolved:
                response_data["error"] = f"Request '{request_id}' not found or already resolved"

    async def _handle_list_pending(self, response_data: dict | None):
        manager = ElicitationManager.get_instance()
        pending = manager.get_all_pending()

        if response_data is not None:
            response_data["ok"] = True
            response_data["pending"] = pending
