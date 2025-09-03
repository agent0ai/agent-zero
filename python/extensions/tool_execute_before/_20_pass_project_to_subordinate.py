from python.helpers.extension import Extension
from python.helpers.project import ProjectHelper
from python.helpers.print_style import PrintStyle
from agent import Agent


class PassProjectToSubordinate(Extension):
    """
    Extension to pass active project context to subordinate agents when call_subordinate is executed.
    
    This extension runs before tool execution and specifically targets the call_subordinate tool,
    ensuring that subordinate agents inherit the same active project context as their superior.
    """

    async def execute(self, tool_args: dict = None, tool_name: str = "", **kwargs):
        """
        Pass active project information to subordinate agent when call_subordinate is executed
        
        Args:
            tool_args: Arguments being passed to the tool
            tool_name: Name of the tool being executed
            **kwargs: Additional arguments from tool execution
        """
        try:
            # Only act when call_subordinate tool is being executed
            if tool_name != "call_subordinate":
                return
            
            # Get the current active project of the superior agent
            active_project = ProjectHelper.get_active_project(self.agent)
            
            if not active_project:
                # No active project on superior, nothing to pass
                PrintStyle(font_color="cyan", padding=True).print(
                    f"No active project to pass to subordinate agent"
                )
                return
            
            # Get or create the subordinate agent
            subordinate = self.agent.get_data(Agent.DATA_NAME_SUBORDINATE)
            
            # If subordinate doesn't exist yet, it will be created by the call_subordinate tool
            # We'll set the project after tool execution or rely on the existing message_loop_start extension
            # For now, just log that we detected a call_subordinate with an active project
            PrintStyle(font_color="cyan", padding=True).print(
                f"Preparing to pass active project '{active_project}' to subordinate agent"
            )
            
            # Store the active project in the agent's temporary data so it can be picked up 
            # by the message_loop_start extension after subordinate creation
            self.agent.set_data("pending_project_for_subordinate", active_project)
                
        except Exception as e:
            PrintStyle(font_color="red", padding=True).print(
                f"Error preparing project context for subordinate: {str(e)}"
            )