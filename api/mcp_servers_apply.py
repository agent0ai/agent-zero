import time
from helpers.api import ApiHandler, Request, Response

from typing import Any

from helpers.mcp_handler import MCPConfig
from helpers.settings import set_settings_delta
from helpers import projects


class McpServersApply(ApiHandler):
    async def process(self, input: dict[Any, Any], request: Request) -> dict[Any, Any] | Response:
        mcp_servers = input["mcp_servers"]
        project_name = str(input.get("project_name", "") or "").strip()
        try:
            if project_name:
                projects.save_project_mcp_servers(project_name, mcp_servers)
                config = MCPConfig.refresh_project(project_name)
            else:
                # MCPConfig.update(mcp_servers) # done in settings automatically
                set_settings_delta({"mcp_servers": "[]"}) # to force reinitialization
                set_settings_delta({"mcp_servers": mcp_servers})

                time.sleep(1) # wait at least a second
                # MCPConfig.wait_for_lock() # wait until config lock is released
                config = MCPConfig.get_instance()
            status = config.get_servers_status()
            return {"success": True, "status": status, "mcp_servers": mcp_servers, "project_name": project_name}

        except Exception as e:
            return {"success": False, "error": str(e)}
