from python.helpers.tool import Tool, Response
from python.helpers.tunnel_manager import TunnelManager
import asyncio

class BrowserControl(Tool):
    """
    A tool to control the browser used by the browser_agent.
    """

    async def execute(self, action: str = "start", port: int = 9224, **kwargs):
        """
        Start, stop, or release a tunnel to the browser's remote debugging port.

        Args:
            action (str): "start", "stop", or "release"
            port (int): The port to tunnel to.
        """
        tunnel_manager = TunnelManager.get_instance()
        browser_agent_state = self.agent.get_data("_browser_agent_state")

        if action == "start":
            if browser_agent_state:
                browser_agent_state.pause()
            tunnel_url = tunnel_manager.start_tunnel(port=port, provider="serveo")
            if tunnel_url:
                return Response(
                    message=f"Browser control tunnel started at: {tunnel_url}",
                    break_loop=False,
                    open_window=tunnel_url
                )
            else:
                return Response(message="Failed to start browser control tunnel.", break_loop=False)

        elif action == "release":
            if browser_agent_state:
                browser_agent_state.resume()
            tunnel_manager.stop_tunnel()
            return Response(message="Browser control released.", break_loop=False)

        elif action == "stop":
            if tunnel_manager.stop_tunnel():
                return Response(message="Browser control tunnel stopped.", break_loop=False)
            else:
                return Response(message="Failed to stop browser control tunnel.", break_loop=False)

        else:
            return Response(message=f"Invalid action: {action}", break_loop=False)