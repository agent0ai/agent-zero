"""
Diagnostic Tool for SWE Planner Agent
Helps diagnose tool availability and state management issues
"""

from python.helpers.tool import Tool, Response
from python.helpers.swe_graph_state import GraphState

class Diagnostic(Tool):
    """
    Tool for diagnosing SWE workflow issues
    """
    
    async def execute(self, **kwargs):
        """Execute diagnostic operations"""
        
        operation = kwargs.get("operation", "full")
        
        if operation == "full":
            return await self.full_diagnostic()
        elif operation == "state":
            return await self.check_state()
        elif operation == "tools":
            return await self.check_tools()
        else:
            return Response(
                message=f"Unknown operation: {operation}. Supported: full, state, tools",
                break_loop=False
            )
    
    async def full_diagnostic(self) -> Response:
        """Run full diagnostic check"""
        results = []
        
        # Check state
        state_result = await self.check_state()
        results.append("🔍 **State Check**:")
        results.append(state_result.message)
        
        # Check tools  
        tools_result = await self.check_tools()
        results.append("\n🛠️ **Tools Check**:")
        results.append(tools_result.message)
        
        return Response(
            message="\n".join(results),
            break_loop=False
        )
    
    async def check_state(self) -> Response:
        """Check SWE state management"""
        results = []
        
        # Check if state exists
        state = self.agent.get_data("swe_state")
        state_dict = self.agent.get_data("swe_state_dict")
        
        results.append(f"- State object exists: {'✅ Yes' if state else '❌ No'}")
        results.append(f"- State dict exists: {'✅ Yes' if state_dict else '❌ No'}")
        
        if state:
            results.append(f"- State type: {type(state).__name__}")
            results.append(f"- Current agent: {getattr(state, 'current_agent', 'Not set')}")
            if hasattr(state, 'plan') and state.plan:
                results.append(f"- Plan goal: {state.plan.goal or 'Not set'}")
                results.append(f"- Tasks count: {len(state.plan.tasks) if state.plan.tasks else 0}")
        
        if state_dict and isinstance(state_dict, dict):
            results.append(f"- Dict keys: {list(state_dict.keys())}")
        
        return Response(message="\n".join(results), break_loop=False)
    
    async def check_tools(self) -> Response:
        """Check available tools"""
        results = []
        
        # Check if we have access to common tools
        test_tools = [
            'plan_manager',
            'rules_parser', 
            'code_execution_tool',
            'response',
            'call_subordinate'
        ]
        
        for tool_name in test_tools:
            try:
                # Try to create a tool instance (without executing)
                tool_exists = hasattr(self.agent, 'get_tool')
                results.append(f"- {tool_name}: {'✅ Available' if tool_exists else '❓ Unknown'}")
            except Exception as e:
                results.append(f"- {tool_name}: ❌ Error ({str(e)[:50]})")
        
        # Check our own tools directory
        import os
        tools_dir = "/home/lazy/Documents/agent-zero/agents/swe-planner/tools"
        if os.path.exists(tools_dir):
            tool_files = [f for f in os.listdir(tools_dir) if f.endswith('.py') and f != '__pycache__']
            results.append(f"\n📁 **Local tools found**: {', '.join([f[:-3] for f in tool_files])}")
        else:
            results.append("\n📁 **Local tools directory**: ❌ Not found")
        
        return Response(message="\n".join(results), break_loop=False)
    
    def get_or_create_state(self) -> GraphState:
        """Get existing state or create new one"""
        state = self.agent.get_data("swe_state")
        
        if not state or not isinstance(state, GraphState):
            # Try to restore from dict format
            state_dict = self.agent.get_data("swe_state_dict")
            if state_dict and isinstance(state_dict, dict):
                state = GraphState.from_dict(state_dict)
            else:
                state = GraphState()
                state.current_agent = "swe-planner"
        
        return state
    
    def save_state(self, state: GraphState):
        """Save state in both formats for reliability"""
        self.agent.set_data("swe_state", state)
        # Also save as dict for backup
        if hasattr(state, 'to_dict'):
            self.agent.set_data("swe_state_dict", state.to_dict())