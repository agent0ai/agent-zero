from flask import Request
from python.helpers.api import ApiHandler, Input, Output
from python.services.browser_session_manager import get_browser_session_manager
from python.helpers.print_style import PrintStyle

ps = PrintStyle()

class BrowserControlStart(ApiHandler):
    """Start browser control session with VNC access."""
    
    async def process(self, input: Input, request: Request) -> Output:
        try:
            # Get session context
            ctxid = input.get("context", "")
            context = self.get_context(ctxid)

            # Get browser control mode from request
            mode = input.get("mode", "devtools")  # devtools or cdp
            headless = input.get("headless", False)

            # Start browser session
            browser_manager = get_browser_session_manager()
            browser_info = browser_manager.start_browser_session(headless=headless)

            # Prepare response
            result = {
                "status": "started",
                "browser": browser_info,
                "mode": mode
            }

            ps.success(f"Browser control started for session {context.id}")
            return result

        except Exception as e:
            ps.error(f"Failed to start browser control: {e}")
            return {"error": str(e)}