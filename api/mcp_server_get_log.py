from helpers.api import ApiHandler, Request, Response
from typing import Any

from helpers.mcp_handler import MCPConfig


class McpServerGetLog(ApiHandler):
    async def process(self, input: dict[Any, Any], request: Request) -> dict[Any, Any] | Response:
        
        # try:
            server_name = input.get("server_name")
            project_name = str(input.get("project_name", "") or "").strip()
            if not server_name:
                return {"success": False, "error": "Missing server_name"}
            config = MCPConfig.get_project_instance(project_name) if project_name else MCPConfig.get_instance()
            log = config.get_server_log(server_name)
            return {"success": True, "log": log}
        # except Exception as e:
        #     return {"success": False, "error": str(e)}
