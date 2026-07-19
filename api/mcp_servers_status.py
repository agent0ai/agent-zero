from helpers.api import ApiHandler, Request, Response

from typing import Any

from helpers.mcp_handler import MCPConfig


class McpServersStatuss(ApiHandler):
    async def process(self, input: dict[Any, Any], request: Request) -> dict[Any, Any] | Response:
        
        # try:
            project_name = (input or {}).get("project_name") if isinstance(input, dict) else None
            config = MCPConfig.get_project_instance(project_name) if project_name else MCPConfig.get_instance()
            status = config.get_servers_status()
            return {"success": True, "status": status}
        # except Exception as e:
        #     return {"success": False, "error": str(e)}
