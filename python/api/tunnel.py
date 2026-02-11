from python.helpers import runtime
from python.helpers.api import ApiHandler, Request, Response
from python.helpers.tunnel_manager import TunnelManager


class Tunnel(ApiHandler):
    async def process(self, input: dict, request: Request) -> dict | Response:
        return await process(input)


async def process(input: dict) -> dict | Response:
    action = input.get("action", "get")

    tunnel_manager = TunnelManager.get_instance()

    if action == "health":
        return {"success": True}

    if action == "create":
        port = runtime.get_web_ui_port()
        provider = input.get("provider", "serveo")  # Default to serveo
        tunnel_url = tunnel_manager.start_tunnel(port, provider)
        error = tunnel_manager.get_last_error()
        if error:
            return {
                "success": False,
                "tunnel_url": None,
                "message": error,
                "notifications": tunnel_manager.get_notifications(),
            }

        return {
            "success": tunnel_url is not None,
            "tunnel_url": tunnel_url,
            "notifications": tunnel_manager.get_notifications(),
        }

    elif action == "stop":
        return stop()

    elif action == "get":
        tunnel_url = tunnel_manager.get_tunnel_url()
        return {
            "success": tunnel_url is not None,
            "tunnel_url": tunnel_url,
            "is_running": tunnel_manager.is_running,
        }

    elif action == "notifications":
        return {
            "success": True,
            "notifications": tunnel_manager.get_notifications(),
            "tunnel_url": tunnel_manager.get_tunnel_url(),
            "is_running": tunnel_manager.is_running,
        }

    return {
        "success": False,
        "error": "Invalid action. Use 'create', 'stop', 'get', or 'notifications'.",
    }


def stop():
    tunnel_manager = TunnelManager.get_instance()
    tunnel_manager.stop_tunnel()
    return {"success": True}
