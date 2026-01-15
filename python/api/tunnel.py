from python.helpers.api import ApiHandler, Request, Response
from python.helpers import runtime


class Tunnel(ApiHandler):
    async def process(self, input: dict, request: Request) -> dict | Response:
        return await process(input)

async def process(input: dict) -> dict | Response:
    # Lazy import - tunnel_manager requires flaredantic which may not be installed
    try:
        from python.helpers.tunnel_manager import TunnelManager
    except ImportError as e:
        return {"success": False, "error": f"Tunnel not available: {e}"}

    action = input.get("action", "get")

    tunnel_manager = TunnelManager.get_instance()

    if action == "health":
        return {"success": True}
    
    if action == "create":
        port = runtime.get_web_ui_port()
        provider = input.get("provider", "serveo")  # Default to serveo
        tunnel_url = tunnel_manager.start_tunnel(port, provider)
        if tunnel_url is None:
            # Add a little delay and check again - tunnel might be starting
            import time
            time.sleep(2)
            tunnel_url = tunnel_manager.get_tunnel_url()
        
        return {
            "success": tunnel_url is not None,
            "tunnel_url": tunnel_url,
            "message": "Tunnel creation in progress" if tunnel_url is None else "Tunnel created successfully"
        }
    
    elif action == "stop":
        return stop()
    
    elif action == "get":
        tunnel_url = tunnel_manager.get_tunnel_url()
        return {
            "success": tunnel_url is not None,
            "tunnel_url": tunnel_url,
            "is_running": tunnel_manager.is_running
        }
    
    return {
        "success": False,
        "error": "Invalid action. Use 'create', 'stop', or 'get'."
    } 

def stop():
    tunnel_manager = TunnelManager.get_instance()
    tunnel_manager.stop_tunnel()
    return {
        "success": True
    }
