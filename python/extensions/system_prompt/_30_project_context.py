from python.helpers.extension import Extension
from python.helpers.project_manager import ProjectManager
from python.helpers.print_style import PrintStyle
from agent import Agent, LoopData
from typing import Any


class ProjectContextPrompt(Extension):
    """Extension to inject project context directly into the system prompt."""

    async def execute(self, system_prompt: list[str] = [], loop_data: LoopData = LoopData(), **kwargs: Any):
        """Add project context to the system prompt."""
        try:
            # Load project manager
            project_manager = ProjectManager()
            
            # Always read from files as source of truth
            active_project = None
            all_projects = project_manager.get_all_projects()
            for proj in all_projects:
                if proj.active:
                    active_project = proj.id
                    self.agent.set_data("active_project", proj.id)
                    self.agent.set_data("active_project_entity", proj.to_dict())
                    self.agent.set_data("project_context_refresh", True)
                    PrintStyle(font_color="magenta", padding=False).print(
                        f"[System Prompt] Active project: {proj.name}"
                    )
                    break
            
            # If no active project, clear agent data
            if not active_project:
                self.agent.set_data("active_project", None)
                self.agent.set_data("active_project_entity", None)
                PrintStyle(font_color="magenta", padding=False).print(
                    "[System Prompt] No active project"
                )

            # Add project list context
            projects = project_manager.get_all_projects()
            project_list_context = self._render_project_list_context(projects)
            if project_list_context:
                system_prompt.append(project_list_context)

            # Add active project context if there is one
            if active_project:
                project_entity = project_manager.get_project_by_id(active_project)
                if project_entity:
                    active_project_context = self._render_active_project_context(
                        project_entity, project_manager, active_project
                    )
                    if active_project_context:
                        system_prompt.append(active_project_context)
                        
                        # Clear the refresh flag after applying context
                        if self.agent.get_data("project_context_refresh"):
                            self.agent.set_data("project_context_refresh", False)
                else:
                    # Project not found, clear the context
                    self.agent.set_data("active_project", None)
                    self.agent.set_data("active_project_entity", None)

        except Exception as e:
            PrintStyle(font_color="red", padding=True).print(
                f"Error adding project context to system prompt: {str(e)}"
            )

    def _render_project_list_context(self, projects) -> str:
        """Render the project list context."""
        try:
            # Prepare template variables
            project_list = []
            if projects:
                for project in projects:
                    project_data = {
                        "name": project.name,
                        "description": project.description or "No description"
                    }
                    # Add instructions preview if available
                    if hasattr(project, 'instructions') and project.instructions:
                        preview = project.instructions[:100]
                        if len(project.instructions) > 100:
                            preview += "..."
                        project_data["instructions_preview"] = preview
                    project_list.append(project_data)

            # Render the project list context template
            return self.agent.read_prompt(
                "agent.context.project_list.md",
                has_projects=len(projects) > 0,
                projects=project_list
            )
        except Exception as e:
            PrintStyle(font_color="red", padding=True).print(
                f"Error rendering project list context: {str(e)}"
            )
            return ""

    def _render_active_project_context(self, project_entity, project_manager, active_project) -> str:
        """Render the active project context."""
        try:
            # Get file structure
            file_structure = project_manager.get_project_file_structure(active_project)

            # Render the active project context template
            return self.agent.read_prompt(
                "agent.context.active_project.md",
                project_name=project_entity.name,
                project_description=project_entity.description or "No description",
                project_instructions=getattr(project_entity, 'instructions', None),
                project_directory=project_entity.path,
                has_files=len(file_structure) > 0,
                file_structure=file_structure[:20],  # Limit to 20 items
                has_more_files=len(file_structure) > 20,
                additional_files_count=len(file_structure) - 20 if len(file_structure) > 20 else 0
            )
        except Exception as e:
            PrintStyle(font_color="red", padding=True).print(
                f"Error rendering active project context: {str(e)}"
            )
            return ""
