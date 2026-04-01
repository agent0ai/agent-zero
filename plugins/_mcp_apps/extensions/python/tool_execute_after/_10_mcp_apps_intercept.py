"""
Extension that runs after MCP tool execution. If the tool has _meta.ui metadata,
fetches the UI resource and registers an app instance, then broadcasts an
mcp_app message to the frontend via the agent context log.
"""

from helpers.extension import Extension
from helpers.print_style import PrintStyle


class McpAppsToolIntercept(Extension):
    async def execute(self, **kwargs):
        tool_name = kwargs.get("tool_name", "")
        response = kwargs.get("response", None)

        PrintStyle(font_color="yellow", padding=True).print(
            f"DEBUG McpAppsToolIntercept: called with tool_name='{tool_name}'"
        )

        if not tool_name or "." not in tool_name:
            PrintStyle(font_color="yellow", padding=True).print(
                f"DEBUG McpAppsToolIntercept: skipping (no dot in tool_name)"
            )
            return

        try:
            import helpers.mcp_handler as mcp_handler

            mcp_config = mcp_handler.MCPConfig.get_instance()
            ui_meta = mcp_config.get_tool_ui_meta(tool_name)
            PrintStyle(font_color="yellow", padding=True).print(
                f"DEBUG McpAppsToolIntercept: ui_meta for '{tool_name}' = {ui_meta}"
            )
            if not ui_meta:
                return

            resource_uri = ui_meta.get("resourceUri")
            if not resource_uri:
                return

            server_name = tool_name.split(".", 1)[0]

            PrintStyle(font_color="cyan", padding=True).print(
                f"MCP Apps: Tool '{tool_name}' has UI resource '{resource_uri}', fetching..."
            )

            from usr.plugins.mcp_apps.helpers.mcp_apps_manager import MCPAppsManager

            manager = MCPAppsManager.get_instance()
            html_content = await manager.fetch_ui_resource(server_name, resource_uri)

            tool_result_text = response.message if response else ""
            tool_args = kwargs.get("tool_args", {})

            # Look up tool description and input schema from MCP tool cache
            short_tool_name = tool_name.split(".", 1)[1]
            tool_description = ""
            tool_input_schema = None
            for srv in mcp_config.servers:
                if srv.name == server_name:
                    for t in srv.get_tools():
                        if t.get("name") == short_tool_name:
                            tool_description = t.get("description", "")
                            tool_input_schema = t.get("input_schema")
                            break
                    break

            app_id = manager.register_app(
                server_name=server_name,
                tool_name=short_tool_name,
                resource_uri=resource_uri,
                html_content=html_content,
                tool_args=tool_args,
                tool_result={"content": [{"type": "text", "text": tool_result_text}]},
                ui_meta=ui_meta,
                tool_description=tool_description,
                tool_input_schema=tool_input_schema,
            )

            if self.agent and self.agent.context:
                csp = ui_meta.get("csp", {})
                permissions = ui_meta.get("permissions", {})
                prefers_border = ui_meta.get("prefersBorder", True)

                self.agent.context.log.log(
                    type="mcp_app",
                    heading=f"icon://widgets MCP App: {tool_name}",
                    content="",
                    kvps={
                        "app_id": app_id,
                        "server_name": server_name,
                        "tool_name": tool_name,
                        "resource_uri": resource_uri,
                        "csp": csp,
                        "permissions": permissions,
                        "prefers_border": prefers_border,
                    },
                )

            PrintStyle(font_color="green", padding=True).print(
                f"MCP Apps: App '{app_id}' ready for '{tool_name}' "
                f"({len(html_content)} bytes HTML)"
            )

        except Exception as e:
            PrintStyle(font_color="red", padding=True).print(
                f"MCP Apps: Failed to set up app for tool '{tool_name}': {e}"
            )
