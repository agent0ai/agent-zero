"""
WebSocket extension handling MCP Apps events from the frontend iframe bridge.

Events handled:
- mcp_app_tool_call: Proxy a tools/call from iframe to MCP server
- mcp_app_resource_read: Proxy a resources/read from iframe to MCP server
- mcp_app_get_data: Retrieve app data (HTML, tool result, etc.) for an app_id
- mcp_app_teardown: Clean up an app instance
"""

from helpers.extension import Extension


class McpAppsWsExtension(Extension):
    async def execute(self, **kwargs):
        event_type = kwargs.get("event_type", "")
        data = kwargs.get("data", {})
        response_data = kwargs.get("response_data", {})

        if event_type == "mcp_app_tool_call":
            await self._handle_tool_call(data, response_data)
        elif event_type == "mcp_app_resource_read":
            await self._handle_resource_read(data, response_data)
        elif event_type == "mcp_app_get_data":
            await self._handle_get_data(data, response_data)
        elif event_type == "mcp_app_teardown":
            await self._handle_teardown(data, response_data)

    async def _handle_tool_call(self, data: dict, response_data: dict):
        import asyncio
        from helpers.print_style import PrintStyle
        from usr.plugins.mcp_apps.helpers.mcp_apps_manager import MCPAppsManager

        app_id = data.get("app_id", "")
        tool_name = data.get("tool_name", "")
        arguments = data.get("arguments", {})

        if not app_id or not tool_name:
            response_data["error"] = "Missing app_id or tool_name"
            return

        PrintStyle(font_color="cyan", padding=True).print(
            f"MCP Apps WS: tool_call app_id={app_id} tool={tool_name}"
        )

        manager = MCPAppsManager.get_instance()
        try:
            result = await asyncio.wait_for(
                manager.proxy_tool_call(app_id, tool_name, arguments),
                timeout=60,
            )
            response_data.update(result)
        except asyncio.TimeoutError:
            PrintStyle(font_color="red", padding=True).print(
                f"MCP Apps WS: tool_call TIMEOUT for {tool_name}"
            )
            response_data["error"] = {"code": -32000, "message": f"Tool call '{tool_name}' timed out"}
        except Exception as e:
            PrintStyle(font_color="red", padding=True).print(
                f"MCP Apps WS: tool_call ERROR for {tool_name}: {e}"
            )
            response_data["error"] = {"code": -32000, "message": str(e)}

    async def _handle_resource_read(self, data: dict, response_data: dict):
        from usr.plugins.mcp_apps.helpers.mcp_apps_manager import MCPAppsManager

        app_id = data.get("app_id", "")
        uri = data.get("uri", "")

        if not app_id or not uri:
            response_data["error"] = "Missing app_id or uri"
            return

        manager = MCPAppsManager.get_instance()
        result = await manager.proxy_resource_read(app_id, uri)
        response_data.update(result)

    async def _handle_get_data(self, data: dict, response_data: dict):
        from usr.plugins.mcp_apps.helpers.mcp_apps_manager import MCPAppsManager

        app_id = data.get("app_id", "")
        if not app_id:
            response_data["error"] = "Missing app_id"
            return

        manager = MCPAppsManager.get_instance()
        app_data = manager.get_app_data(app_id)
        if app_data:
            response_data.update(app_data)
        else:
            response_data["error"] = f"App '{app_id}' not found"

    async def _handle_teardown(self, data: dict, response_data: dict):
        from usr.plugins.mcp_apps.helpers.mcp_apps_manager import MCPAppsManager

        app_id = data.get("app_id", "")
        if not app_id:
            response_data["error"] = "Missing app_id"
            return

        manager = MCPAppsManager.get_instance()
        manager.remove_app(app_id)
        response_data["ok"] = True
