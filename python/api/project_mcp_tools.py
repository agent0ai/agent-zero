from python.helpers.api import ApiHandler, Request, Response
from typing import Any

from python.helpers import projects
from python.helpers.mcp_handler import MCPConfig


class ProjectMcpTools(ApiHandler):
    async def process(
        self, input: dict[Any, Any], request: Request
    ) -> dict[Any, Any] | Response:
        action = input.get("action", "")
        project_name = input.get("project_name")

        if not project_name:
            return {"success": False, "error": "Missing project_name"}

        if action == "list":
            return self._list_tools(project_name)
        elif action == "toggle":
            server_name = input.get("server_name")
            tool_name = input.get("tool_name")
            if not server_name or not tool_name:
                return {"success": False, "error": "Missing server_name or tool_name"}
            return self._toggle_tool(project_name, server_name, tool_name)
        elif action == "get_disabled":
            return self._get_disabled_tools(project_name)
        else:
            return {"success": False, "error": "Invalid action"}

    def _list_tools(self, project_name: str) -> dict[str, Any]:
        mcp_config = MCPConfig.get_instance()
        servers_status = mcp_config.get_servers_status()
        project_disabled = projects.load_project_mcp_tools(project_name)

        servers_with_tools = []
        for status in servers_status:
            if status["tool_count"] > 0:
                detail = mcp_config.get_server_detail(status["name"])
                servers_with_tools.append(
                    {
                        "name": status["name"],
                        "description": detail.get("description", ""),
                        "tools": detail.get("tools", []),
                        "global_disabled_tools": detail.get("disabled_tools", []),
                        "project_disabled_tools": project_disabled.get(
                            status["name"], []
                        ),
                    }
                )

        return {"success": True, "servers": servers_with_tools}

    def _toggle_tool(
        self, project_name: str, server_name: str, tool_name: str
    ) -> dict[str, Any]:
        updated = projects.toggle_project_mcp_tool(project_name, server_name, tool_name)
        return {"success": True, "disabled_tools": updated}

    def _get_disabled_tools(self, project_name: str) -> dict[str, Any]:
        disabled = projects.load_project_mcp_tools(project_name)
        return {"success": True, "disabled_tools": disabled}
