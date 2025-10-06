from python.helpers.extension import Extension
from python.helpers.project_manager import ProjectManager
from python.helpers.print_style import PrintStyle
from agent import LoopData


class LoadActiveProject(Extension):
    """
    Extension to load the active project when Agent Zero initializes.

    This extension runs during agent initialization and checks if there's
    an active project in the database that should be loaded into the agent context.
    """

    async def execute(self, loop_data: LoopData | None = None, **kwargs):
        """
        Load active project into agent context on initialization

        Args:
            loop_data: The loop data containing initialization information
            **kwargs: Additional arguments
        """
        try:
            loop_data = loop_data or LoopData()

            # Only run this for the main agent (A0) to avoid duplicate loading
            if self.agent.agent_name != "A0":
                return

            # Check if agent already has an active project set
            current_active = self.agent.get_data("active_project")
            
            if current_active:
                # Agent already has an active project, don't override
                return

            # Load project manager and check for active projects
            project_manager = ProjectManager()
            projects = project_manager.get_all_projects()

            # Find the active project
            active_project = None
            for project in projects:
                if project.active:
                    active_project = project
                    break

            if active_project:
                # Set the active project in agent data
                self.agent.set_data("active_project", active_project.id)
                self.agent.set_data("active_project_entity", active_project.to_dict())

        except Exception as e:
            PrintStyle(font_color="red", padding=True).print(
                f"Error loading active project on initialization: {str(e)}"
            )