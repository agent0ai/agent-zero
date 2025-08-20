from flask import Request, jsonify
from agent import AgentContext
from python.helpers.api import ApiHandler, Input, Output
from python.services.browser_session_manager import get_browser_session_manager
from python.helpers.print_style import PrintStyle

ps = PrintStyle()

class BrowserControlStatus(ApiHandler):
    """Get browser control session status."""
    
    async def process(self, input: Input, request: Request) -> Output:
        try:
            # Get session context
            ctxid = input.get("context", "")
            context = self.get_context(ctxid)
            if not context:
                return {"error": "Invalid context"}
            
            # Get browser status
            browser_manager = get_browser_session_manager()
            browser_info = browser_manager.get_connection_info()
            
            # Check if browser is being used by agent
            browser_in_use = False
            agent = context.agent0
            if agent:
                browser_state = agent.get_data("_browser_agent_state")
                if browser_state and browser_state.browser_session:
                    browser_in_use = True
            
            # Prepare response
            result = {
                "browser": browser_info,
                "browser_in_use": browser_in_use,
                "status": "running" if browser_info.get("is_running") else "stopped"
            }
            
        except Exception as e:
            ps.error(f"Failed to get browser control status: {e}")
            return {"error": str(e)}
        
        return result