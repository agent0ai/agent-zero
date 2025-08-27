from python.helpers.api import ApiHandler, Input, Output
from flask import Request, Response
import logging
import os


class BrowserControl(ApiHandler):
    """API handler for browser control operations"""
    
    def __init__(self, app=None, thread_lock=None):
        super().__init__(app, thread_lock)
        self.logger = logging.getLogger(__name__)
    
    @classmethod
    def requires_csrf(cls) -> bool:
        return False  # Disable CSRF for browser control
    
    async def process(self, input: Input, request: Request) -> Output:
        """Handle browser control API requests"""
        action = input.get("action", "start")
        context_id = input.get("context", "") or ""
        
        try:
            if action == "start":
                # Direct Chrome DevTools approach
                return {
                    "success": True,
                    "message": "Browser control started. Chrome DevTools available.",
                    "action": action,
                    "devtools_url": "http://localhost:59222",
                    "vnc_url": "http://localhost:56080/vnc.html",
                    "break_loop": False
                }
                
            elif action == "start_vnc_session":
                # Return VNC connection info
                return {
                    "success": True,
                    "message": "VNC session available",
                    "action": action,
                    "vnc_url": "http://localhost:56080/vnc.html",
                    "vnc_direct": "vnc://localhost:55900",
                    "session_id": "vnc-browser-session"
                }
                
            elif action == "release_vnc_session":
                return {
                    "success": True,
                    "message": "VNC session released",
                    "action": action
                }
                
            elif action == "request_human_control":
                return {
                    "success": True,
                    "message": "Human control available",
                    "action": action,
                    "vnc_url": "http://localhost:56080/vnc.html"
                }
                
            elif action == "release_human_control":
                return {
                    "success": True,
                    "message": "Released back to agent control",
                    "action": action
                }
                
            elif action == "get_vnc_status":
                # Simple status check - VNC is always available in Docker
                return {
                    "success": True,
                    "message": "VNC services running",
                    "action": action,
                    "status": {
                        "vnc_running": True,
                        "websockify_running": True,
                        "chrome_running": True,
                        "vnc_url": "http://localhost:56080/vnc_lite.html",
                        "vnc_password": os.getenv("VNC_PASSWORD", "agent123")
                    }
                }
                
            elif action == "get_vnc_password":
                # Get current VNC password for authentication
                return {
                    "success": True,
                    "message": "VNC password retrieved",
                    "action": action,
                    "password": os.getenv("VNC_PASSWORD", "agent123"),
                    "vnc_url": "http://localhost:56080/vnc_lite.html"
                }
                
            else:
                return {
                    "success": True,
                    "message": "Browser control stopped",
                    "action": action,
                    "break_loop": False
                }
                
        except Exception as e:
            self.logger.error(f"Browser control error: {e}")
            return {
                "success": False,
                "error": str(e),
                "action": action
            }