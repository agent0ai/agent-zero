from python.helpers.extension import Extension
from python.helpers.project import ProjectHelper
from python.helpers.print_style import PrintStyle
from agent import Agent, LoopData


class PassProjectToSubordinate(Extension):
    """
    Extension to pass active project information from superior to subordinate agents.
    
    This extension runs at the start of message loops and ensures that when
    a subordinate agent is created via call_subordinate, it inherits the same
    active project context as its superior agent.
    """

    async def execute(self, loop_data: LoopData = LoopData(), **kwargs):
        """
        Pass active project information to subordinate agent if one exists
        
        Args:
            loop_data: The loop data for the current message loop
            **kwargs: Additional arguments
        """
        try:
            # Check if this agent has a subordinate
            subordinate = self.agent.get_data(Agent.DATA_NAME_SUBORDINATE)
            
            if not subordinate:
                # No subordinate agent, nothing to do
                return
            
            # Get the current active project of this agent
            active_project = ProjectHelper.get_active_project(self.agent)
            
            if not active_project:
                # No active project, ensure subordinate also has no active project
                subordinate_project = ProjectHelper.get_active_project(subordinate)
                if subordinate_project:
                    PrintStyle(font_color="yellow", padding=True).print(
                        f"Deactivating project '{subordinate_project}' in subordinate agent"
                    )
                    ProjectHelper.set_active_project(subordinate, None)
                return
            
            # Check if subordinate already has the same active project
            subordinate_project = ProjectHelper.get_active_project(subordinate)
            
            if subordinate_project == active_project:
                # Subordinate already has the correct project active
                return
            
            # Set the active project in the subordinate agent
            success = ProjectHelper.set_active_project(subordinate, active_project)
            
            if success:
                PrintStyle(font_color="cyan", padding=True).print(
                    f"Project '{active_project}' passed to subordinate agent {subordinate.agent_name}"
                )
            else:
                PrintStyle(font_color="red", padding=True).print(
                    f"Failed to pass project '{active_project}' to subordinate agent"
                )
                
        except Exception as e:
            PrintStyle(font_color="red", padding=True).print(
                f"Error passing project to subordinate: {str(e)}"
            )

    def _should_pass_project(self) -> bool:
        """
        Determine if project context should be passed to subordinate
        
        This can be extended with additional logic if needed, such as
        checking for specific project settings or agent configurations.
        
        Returns:
            True if project should be passed, False otherwise
        """
        # For now, always pass project context to subordinates
        # This ensures consistent project awareness across the agent hierarchy
        return True