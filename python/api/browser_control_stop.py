from flask import Request, jsonify
from agent import AgentContext
from python.helpers.api import ApiHandler, Input, Output
from python.services.browser_session_manager import get_browser_session_manager
from python.helpers.print_style import PrintStyle

ps = PrintStyle()

class BrowserControlStop(ApiHandler):
    """Stop browser control session."""
    
    async def process(self, input: Input, request: Request) -> Output:
        try:
            # Get session context
            ctxid = input.get("context", "")
            context = self.get_context(ctxid)
            if not context:
                return {"error": "Invalid context"}
            
            # Stop browser session
            browser_manager = get_browser_session_manager()
            if browser_manager.is_running:
                browser_manager.stop_browser_session()
            
            # Prepare response
            result = {
                "status": "stopped",
                "message": "Browser control session stopped successfully"
            }
            
            ps.success(f"Browser control stopped for session {context.id}")
            
        except Exception as e:
            ps.error(f"Failed to stop browser control: {e}")
            return {"error": str(e)}
        
        return result
        