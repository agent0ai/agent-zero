import time
from python.helpers.api import ApiHandler, Request, Response
from typing import Any

from python.helpers import projects, dirty_json
from python.helpers.settings import get_settings
from python.helpers.mcp_handler import MCPConfig


class ProjectMcpServers(ApiHandler):
    async def process(
        self, input: dict[Any, Any], request: Request
    ) -> dict[Any, Any] | Response:
        action = input.get("action", "")
        project_name = input.get("project_name")

        if action == "list_global":
            return self._list_global_servers()

        if not project_name:
            return {"success": False, "error": "Missing project_name"}

        if action == "load":
            return self._load_config(project_name)
        elif action == "save":
            config = input.get("config", "")
            return self._save_config(project_name, config)
        elif action == "apply":
            config = input.get("config", "")
            return self._apply_config(project_name, config)
        elif action == "status":
            return self._get_status(project_name)
        else:
            return {"success": False, "error": "Invalid action"}

    def _load_config(self, project_name: str) -> dict[str, Any]:
        config = projects.load_project_mcp_servers(project_name)
        return {"success": True, "config": config}

    def _save_config(self, project_name: str, config: str) -> dict[str, Any]:
        projects.save_project_mcp_servers(project_name, config)
        return {"success": True}

    def _apply_config(self, project_name: str, config: str) -> dict[str, Any]:
        projects.save_project_mcp_servers(project_name, config)
        return {"success": True, "status": []}

    def _get_status(self, project_name: str) -> dict[str, Any]:
        status = self._get_server_status(project_name)
        return {"success": True, "status": status}

    def _get_server_status(self, project_name: str) -> list[dict[str, Any]]:
        mcp = MCPConfig.get_instance()
        servers = mcp.get_project_servers(project_name)
        result = []
        for server in servers:
            tool_count = len(server.get_tools())
            error = server.get_error()
            result.append(
                {
                    "name": server.name,
                    "description": server.description,
                    "connected": tool_count > 0 and not error,
                    "error": error,
                    "tool_count": tool_count,
                }
            )
        return result

    def _list_global_servers(self) -> dict[str, Any]:
        global_config_str = get_settings().get("mcp_servers", '{"mcpServers": {}}')
        global_config = dirty_json.parse(global_config_str) or {"mcpServers": {}}
        servers = global_config.get("mcpServers", {})
        return {"success": True, "servers": servers}
