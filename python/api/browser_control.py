from python.helpers.api import ApiHandler, Request, Response
from flask import send_file, redirect
import os

class BrowserControl(ApiHandler):
    """
    API endpoint for accessing the browser control interface (noVNC).
    This allows users to manually interact with the browser when the agent pauses.
    """

    @classmethod
    def requires_auth(cls) -> bool:
        # Require authentication for browser control access
        return True

    @classmethod
    def requires_csrf(cls) -> bool:
        # CSRF not needed for GET requests
        return False

    @classmethod
    def get_methods(cls) -> list[str]:
        return ["GET"]

    async def process(self, input: dict, request: Request) -> dict | Response:
        """
        Returns information about the VNC server and provides access to noVNC client.

        Query parameters:
        - action: 'info' (default) | 'redirect'
        - info: Returns VNC connection details
        - redirect: Redirects to the noVNC web client
        """
        action = request.args.get('action', 'info')

        # Check if VNC is running by reading status file
        vnc_status_file = '/tmp/vnc/status'
        vnc_ready = False
        vnc_display = ':99'
        novnc_port = '6080'

        # Get external port mapping from environment variable (for Docker port mapping)
        # Default to 56080 which is the standard external mapping for noVNC port 6080
        external_novnc_port = os.environ.get('NOVNC_EXTERNAL_PORT', '56080')

        if os.path.exists(vnc_status_file):
            try:
                with open(vnc_status_file, 'r') as f:
                    status_lines = f.readlines()
                    status_dict = {}
                    for line in status_lines:
                        if '=' in line:
                            key, value = line.strip().split('=', 1)
                            status_dict[key] = value

                    vnc_ready = status_dict.get('READY', 'false') == 'true'
                    vnc_display = status_dict.get('DISPLAY', ':99')
                    novnc_port = status_dict.get('NOVNC_PORT', '6080')
            except Exception as e:
                pass

        if action == 'redirect':
            # Redirect to noVNC client using external port mapping with optimized parameters
            novnc_url = f"http://localhost:{external_novnc_port}/vnc.html?autoconnect=true&resize=scale&reconnect=true&reconnect_delay=1000&show_dot=true"
            return redirect(novnc_url, code=302)

        # Default: return info with optimized noVNC URL parameters
        # Parameters:
        # - autoconnect: Connect automatically on load
        # - resize=scale: Scale the remote session to fit the viewport
        # - reconnect: Automatically reconnect if connection is lost
        # - reconnect_delay: Wait 1 second before reconnecting
        # - show_dot: Show connection status indicator
        return {
            "vnc_ready": vnc_ready,
            "vnc_display": vnc_display,
            "novnc_port": novnc_port,
            "external_novnc_port": external_novnc_port,
            "novnc_url": f"http://localhost:{external_novnc_port}/vnc.html?autoconnect=true&resize=scale&reconnect=true&reconnect_delay=1000&show_dot=true",
            "instructions": "Click the noVNC URL to access the browser control interface" if vnc_ready else "VNC server is not running"
        }
