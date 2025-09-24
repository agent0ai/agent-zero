from python.helpers.extension import Extension
from python.helpers.project import ProjectHelper
from python.helpers.print_style import PrintStyle
from agent import LoopData


class ProjectListAwareness(Extension):
    """
    Extension to inject project list awareness into agent prompts.
    
    This extension runs after message loop prompts are built and adds
    information about all available projects to the agent's context,
    providing awareness of what projects exist and basic usage guidance.
    """

    async def execute(self, loop_data: LoopData = LoopData(), **kwargs):
        """
        Inject project list awareness into agent prompt
        
        Args:
            loop_data: The loop data containing prompt information
            **kwargs: Additional arguments
        """
        try:
            # Load all available projects
            projects = ProjectHelper.list_projects()
            
            if not projects:
                # No projects available, provide basic guidance
                project_awareness = self._build_no_projects_context()
            else:
                # Build project awareness information
                project_awareness = self._build_project_list_context(projects)
            
            # Add to temporary extras (will be included in this prompt only)
            loop_data.extras_temporary["project_list_awareness"] = project_awareness
            
            # Debug output (can be removed in production)
            PrintStyle(font_color="cyan", padding=True).print(
                f"Project list awareness injected: {len(projects)} projects available"
            )
            
        except Exception as e:
            PrintStyle(font_color="red", padding=True).print(
                f"Error injecting project list awareness: {str(e)}"
            )

    def _build_no_projects_context(self) -> str:
        """
        Build context message when no projects are available
        
        Returns:
            Formatted context string for no projects scenario
        """
        return """
## PROJECT MANAGEMENT AVAILABILITY

**Project System**: Agent Zero's project management system is available but no projects have been created yet.

**What are Projects?**
Projects provide organized workspaces with specific contexts, instructions, and goals. They help maintain focused work environments and provide clear guidelines for complex tasks.

**Project Management**:
- Use the `project_manager` tool to create, activate, list, or edit projects
- Only the main agent (A0) can create new projects for security reasons
- When a project is active, all work is performed within that project's context
- Project context is automatically passed to subordinate agents

**Getting Started**:
To create your first project, use:
```json
{"tool_name": "project_manager", "tool_args": {"action": "create", "name": "project_name", "description": "Brief description", "instructions": "Detailed instructions for agents"}}
```

**Available Actions**:
- `{"tool_name": "project_manager", "tool_args": {"action": "list"}}` - List all projects
- `{"tool_name": "project_manager", "tool_args": {"action": "create", "name": "name", "description": "desc", "instructions": "instructions"}}` - Create project (A0 only)
- `{"tool_name": "project_manager", "tool_args": {"action": "activate", "project_name": "name"}}` - Activate a project
- `{"tool_name": "project_manager", "tool_args": {"action": "deactivate"}}` - Deactivate current project

**Current Status**: No projects created yet. Consider creating a project to organize your work.
"""

    def _build_project_list_context(self, projects) -> str:
        """
        Build the project list awareness string for the agent
        
        Args:
            projects: List of ProjectData objects
            
        Returns:
            Formatted project awareness string
        """
        context = f"""
## AVAILABLE PROJECTS

**Project System Overview**: You have access to {len(projects)} project(s). Projects provide organized workspaces with specific contexts, instructions, and goals.

**Available Projects**:
"""
        
        for project in projects:
            context += f"""
• **{project.name}**
  - Description: {project.description}
  - Directory: {ProjectHelper.get_project_directory(project.name)}"""
            
            # Add preview of instructions if available
            if project.instructions:
                instructions_preview = project.instructions[:150]
                if len(project.instructions) > 150:
                    instructions_preview += "..."
                context += f"\n  - Instructions: {instructions_preview}"
        
        context += f"""

**Project Management**:
- Use the `project_manager` tool to create, activate, list, or edit projects
- Only the main agent (A0) can create new projects for security reasons
- When a project is active, all work is performed within that project's context
- Project context is automatically passed to subordinate agents
- Projects help maintain organized workspaces and provide specific guidelines

**Usage Examples**:
- `{{"tool_name": "project_manager", "tool_args": {{"action": "list"}}}}` - List all projects with details
- `{{"tool_name": "project_manager", "tool_args": {{"action": "activate", "project_name": "project_name"}}}}` - Activate a specific project
- `{{"tool_name": "project_manager", "tool_args": {{"action": "deactivate"}}}}` - Deactivate current project
- `{{"tool_name": "project_manager", "tool_args": {{"action": "create", "name": "new_project", "description": "Description", "instructions": "Instructions"}}}}` - Create new project (A0 only)
- `{{"tool_name": "project_manager", "tool_args": {{"action": "update", "project_name": "existing_name", "name": "new_name", "description": "New description", "instructions": "New instructions"}}}}` - Update existing project (A0 only)

**Project Benefits**:
- Organized workspace with dedicated directory structure
- Clear context and instructions for focused work
- Automatic context sharing with subordinate agents
- Consistent guidelines across agent interactions
- Better task organization and goal alignment
"""
        
        return context.strip()
    
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