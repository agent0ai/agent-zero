from typing import Any

from python.helpers.api import ApiHandler, Request, Response
from python.helpers.mcp_handler import MCPConfig


class McpToolsReload(ApiHandler):
    async def process(self, input: dict[Any, Any], request: Request) -> dict[Any, Any] | Response:
        force_reconnect = bool(input.get("force_reconnect", False))

        try:
            mcp_config = MCPConfig.get_instance()
            cache_meta = await mcp_config.reload_tools(force_reconnect=force_reconnect)
            status = mcp_config.get_servers_status_lightweight()
            return {
                "success": cache_meta.get("error") is None,
                "status": status,
                "cache": cache_meta,
            }
        except Exception as e:
            return {
                "success": False,
                "status": MCPConfig.get_instance().get_servers_status_lightweight(),
                "cache": {
                    "rebuilt": False,
                    "cache_key": "",
                    "tool_count": 0,
                    "duration_ms": 0,
                    "error": str(e),
                },
            }
