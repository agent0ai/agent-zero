import os
from python.helpers.extension import Extension
from python.helpers.project import ProjectHelper
from agent import LoopData
from python.helpers.print_style import PrintStyle


class ActiveProjectContext(Extension):
    """
    Extension to inject active project context into agent prompts.
    
    This extension runs after message loop prompts are built and adds
    active project information to the agent's context, including:
    - Project name, description, and instructions
    - Current working directory set to project root
    - Project file structure overview
    - Project-specific guidelines
    """

    async def execute(self, loop_data: LoopData = LoopData(), **kwargs):
        """
        Inject active project context into agent prompt
        
        Args:
            loop_data: The loop data containing prompt information
            **kwargs: Additional arguments
        """
        try:
            # Get active project for this agent
            active_project = ProjectHelper.get_active_project(self.agent)
            
            if not active_project:
                # No active project, nothing to inject
                return
            
            # Load project data
            project_data = ProjectHelper.load_project(active_project)
            
            if not project_data:
                # Project data couldn't be loaded, remove from agent data
                PrintStyle(font_color="orange", padding=True).print(
                    f"Warning: Active project '{active_project}' could not be loaded. Deactivating."
                )
                ProjectHelper.set_active_project(self.agent, None)
                return
            
            # Get project directory and file structure
            project_directory = ProjectHelper.get_project_directory(active_project)
            file_structure = ProjectHelper.get_project_file_structure(active_project)
            
            # Build project context information
            project_context = self._build_project_context(
                project_data=project_data,
                project_directory=project_directory,
                file_structure=file_structure
            )
            
            # Add to temporary extras (will be included in this prompt only)
            loop_data.extras_temporary["active_project_context"] = project_context
            
            # Debug output (can be removed in production)
            PrintStyle(font_color="cyan", padding=True).print(
                f"Active project context injected: {project_data.name}"
            )
            
        except Exception as e:
            PrintStyle(font_color="red", padding=True).print(
                f"Error injecting project context: {str(e)}"
            )

    def _build_project_context(self, project_data, project_directory: str, file_structure: list) -> str:
        """
        Build the project context string to inject into the prompt
        
        Args:
            project_data: ProjectData object with project information
            project_directory: Full path to project directory
            file_structure: List of files/directories in project
            
        Returns:
            Formatted project context string
        """
        context = f"""
## ACTIVE PROJECT CONTEXT

**Project Name**: {project_data.name}

**Description**: {project_data.description}

**Project Instructions**: 
{project_data.instructions}

**Working Directory**: {project_directory}
You are currently working within this project context. All file operations, code execution, and development activities should be performed relative to this project directory unless explicitly instructed otherwise.

**Project Structure**:
"""
        
        if file_structure:
            context += "```\n"
            for item in file_structure[:20]:  # Limit to first 20 items to avoid overwhelming the context
                context += f"{item}\n"
            
            if len(file_structure) > 20:
                context += f"... and {len(file_structure) - 20} more items\n"
            context += "```\n"
        else:
            context += "```\n(Project directory is empty or newly created)\n```\n"
        
        context += f"""
**Project Guidelines**:
- Always work within the project context and follow the project instructions
- Create new files and directories relative to the project root: {project_directory}
- Consider the existing project structure when adding new components
- Maintain consistency with the project's goals and requirements
- Use the project_manager tool to modify project settings if needed

**Important**: This project context applies to all agents in this conversation chain, including any subordinate agents you may delegate work to.
"""
        
        return context.strip()
    
    def _format_file_structure(self, file_structure: list) -> str:
        """
        Format the file structure list for display
        
        Args:
            file_structure: List of file/directory paths
            
        Returns:
            Formatted file structure string
        """
        if not file_structure:
            return "(Empty project directory)"
        
        formatted = []
        for item in file_structure:
            if item.endswith('/'):
                # Directory
                formatted.append(f"📁 {item}")
            else:
                # File
                formatted.append(f"📄 {item}")
        
        return '\n'.join(formatted)