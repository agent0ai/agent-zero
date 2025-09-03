from python.helpers.extension import Extension
from python.helpers.project import ProjectHelper
from python.helpers.print_style import PrintStyle
from agent import LoopData


class LoadProjectsAwareness(Extension):
    """
    Extension to load project awareness during agent initialization.
    
    This extension runs when an agent is initialized and provides the agent
    with awareness of all available projects. This information is added to
    the agent's persistent extras so the agent knows what projects exist
    and can reference them in conversations.
    """

    async def execute(self, **kwargs):
        """
        Load project awareness for the agent
        
        Args:
            **kwargs: Additional arguments from agent initialization
        """
        try:
            # Load all available projects
            projects = ProjectHelper.list_projects()
            
            if not projects:
                # No projects available, add a note about this
                project_info = "No projects are currently available. You can create a new project using the project_manager tool."
            else:
                # Build project awareness information
                project_info = self._build_project_awareness(projects)
            
            # Add to persistent extras so it's always available to the agent
            # We'll store this in the agent's loop_data when it's first created
            if not hasattr(self.agent, 'loop_data') or not self.agent.loop_data:
                self.agent.loop_data = LoopData()
            
            # Add to persistent extras
            self.agent.loop_data.extras_persistent["available_projects"] = project_info
            
            # Debug output (can be removed in production)
            PrintStyle(font_color="cyan", padding=True).print(
                f"Project awareness loaded for {self.agent.agent_name}: {len(projects)} projects available"
            )
            
        except Exception as e:
            PrintStyle(font_color="red", padding=True).print(
                f"Error loading project awareness for {self.agent.agent_name}: {str(e)}"
            )

    def _build_project_awareness(self, projects) -> str:
        """
        Build the project awareness string for the agent
        
        Args:
            projects: List of ProjectData objects
            
        Returns:
            Formatted project awareness string
        """
        awareness = f"""
## AVAILABLE PROJECTS

You have access to {len(projects)} project(s). Projects provide organized workspaces with specific contexts, instructions, and goals.

**Project Overview**:
"""
        
        for project in projects:
            awareness += f"""
• **{project.name}**
  - Description: {project.description}
  - Directory: {ProjectHelper.get_project_directory(project.name)}"""
            
            # Add preview of instructions if available
            if project.instructions:
                instructions_preview = project.instructions[:150]
                if len(project.instructions) > 150:
                    instructions_preview += "..."
                awareness += f"\n  - Instructions: {instructions_preview}"
        
        awareness += f"""

**Project Management**:
- Use the `project_manager` tool to create, activate, list, or edit projects
- Only agent A0 can create new projects
- When a project is active, all work is performed within that project's context
- Project context is automatically passed to subordinate agents
- Projects help maintain organized workspaces and provide specific guidelines

**Usage Examples**:
- `{{"tool_name": "project_manager", "tool_args": {{"action": "list"}}}}` - List all projects
- `{{"tool_name": "project_manager", "tool_args": {{"action": "activate", "project_name": "project_name"}}}}` - Activate a project
- `{{"tool_name": "project_manager", "tool_args": {{"action": "create", "name": "new_project", "description": "Description", "instructions": "Instructions"}}}}` - Create a new project (A0 only)

**Current Status**: {'Active project will be shown in context when one is activated' if not ProjectHelper.get_active_project(self.agent) else f"Active project: {ProjectHelper.get_active_project(self.agent)}"}
"""
        
        return awareness.strip()
    
    def _format_project_summary(self, project) -> str:
        """
        Format a single project for the awareness summary
        
        Args:
            project: ProjectData object
            
        Returns:
            Formatted project summary string
        """
        summary = f"• **{project.name}**: {project.description}"
        
        if project.instructions:
            # Add brief instructions preview
            instructions_preview = project.instructions[:100]
            if len(project.instructions) > 100:
                instructions_preview += "..."
            summary += f" | Instructions: {instructions_preview}"
        
        return summary