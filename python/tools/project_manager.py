from python.helpers.tool import Tool, Response
from python.helpers.project_manager import ProjectManager as ProjectManagerHelper
from python.helpers.print_style import PrintStyle
from typing import Dict, Any


class ProjectManager(Tool):
    """
    Tool for managing Agent Zero projects.

    Allows agents to create, activate, deactivate, list, and edit projects.
    Only agent #0 can create new projects for security reasons.
    """

    def __init__(self, agent, **kwargs):
        super().__init__(agent, **kwargs)
        self.project_helper = ProjectManagerHelper()

    async def execute(self, action: str = "list", **kwargs) -> Response:
        """
        Execute project management action
        
        Args:
            action: Action to perform (create, activate, deactivate, list, edit, refresh)
            **kwargs: Additional arguments based on action

        Returns:
            Response with operation result
        """
        action = action.lower().strip()

        try:
            if action == "create":
                return await self._create_project(**kwargs)
            elif action == "activate":
                return await self._activate_project(**kwargs)
            elif action == "deactivate":
                return await self._deactivate_project()
            elif action == "list":
                return await self._list_projects()
            elif action == "edit":
                return await self._edit_project(**kwargs)
            elif action == "refresh":
                return await self._refresh_current_context()
            else:
                return Response(
                    message=f"Unknown action '{action}'. Available actions: create, activate, deactivate, list, edit, refresh",
                    break_loop=False
                )
                
        except Exception as e:
            error_msg = f"Project manager error: {str(e)}"
            PrintStyle(font_color="red", padding=True).print(error_msg)
            return Response(message=error_msg, break_loop=False)

    async def _create_project(self, name: str = "", description: str = "", instructions: str = "", **kwargs) -> Response:
        """Create a new project"""
        
        # Only allow agent #0 to create projects
        if self.agent.number != 0:
            return Response(
                message="Only the main agent (A0) can create new projects for security reasons.",
                break_loop=False
            )
        
        if not name.strip():
            return Response(
                message="Project name is required to create a project.",
                break_loop=False
            )
        
        try:
            result = self.project_helper.create_project(
                name=name.strip(),
                path=f"/tmp/agent-zero-projects/{name.strip().lower().replace(' ', '-')}",
                description=description.strip() if description else "",
                instructions=instructions.strip() if instructions else ""
            )

            if not result.get("success"):
                return Response(
                    message=f"Failed to create project: {result.get('error', 'Unknown error')}",
                    break_loop=False
                )

            project_data = result.get("project", {})
            message = f"Project '{project_data.get('name', 'Unknown')}' created successfully!\n\n"
            message += f"Description: {project_data.get('description') or 'No description'}\n"
            message += f"Project path: {project_data.get('path', 'Unknown')}\n\n"
            message += "Use 'activate' action to start working in this project context."

            return Response(message=message, break_loop=False)
        except Exception as e:
            return Response(
                message=f"Failed to create project: {str(e)}",
                break_loop=False
            )

    async def _activate_project(self, project_name: str = "", **kwargs) -> Response:
        """Activate a project for the current agent context"""
        
        if not project_name.strip():
            return Response(
                message="Project name is required to activate a project.",
                break_loop=False
            )
        
        try:
            # Get project by name
            project = self.project_helper.get_project_by_name(project_name.strip())
            if not project:
                return Response(
                    message=f"Project '{project_name}' not found.",
                    break_loop=False
                )

            # Activate project
            result = self.project_helper.activate_project(self.agent, project.id)

            if not result.get("success"):
                return Response(
                    message=f"Failed to activate project: {result.get('error', 'Unknown error')}",
                    break_loop=False
                )

            activated_project = result["project"]

            message = f"Project '{activated_project['name']}' is now active!\n\n"
            message += f"Description: {activated_project.get('description') or 'No description'}\n"
            message += f"Working directory: {activated_project['path']}\n\n"
            message += "All subsequent operations will be performed within this project context."

            return Response(message=message, break_loop=False)
        except Exception as e:
            return Response(
                message=f"Failed to activate project: {str(e)}",
                break_loop=False
            )

    async def _deactivate_project(self, **kwargs) -> Response:
        """Deactivate the current project"""
        
        current_project = self.project_helper.get_active_project(self.agent)

        if not current_project:
            return Response(
                message="No project is currently active.",
                break_loop=False
            )

        try:
            self.project_helper.deactivate_project(self.agent)

            return Response(
                message=f"Project '{current_project.name}' has been deactivated. You are now working in the default context.",
                break_loop=False
            )
        except Exception as e:
            return Response(
                message=f"Failed to deactivate project: {str(e)}",
                break_loop=False
            )

    async def _list_projects(self, **kwargs) -> Response:
        """List all available projects"""
        
        try:
            projects = self.project_helper.get_all_projects()
            
            # Always read from files as source of truth, ignore agent data
            current_project = None
            for proj in projects:
                if proj.active:
                    current_project = proj
                    # Sync agent data to match reality
                    self.agent.set_data("active_project", proj.id)
                    self.agent.set_data("active_project_entity", proj.to_dict())
                    break
            
            # If no active project found, clear agent data
            if not current_project:
                self.agent.set_data("active_project", None)
                self.agent.set_data("active_project_entity", None)

            if not projects:
                return Response(
                    message="No projects found. Create a new project using the 'create' action.",
                    break_loop=False
                )

            message = f"Available projects ({len(projects)} found):\n\n"

            for project in projects:
                status = " [ACTIVE]" if (current_project and project.id == current_project.id) else ""
                message += f"• **{project.name}**{status}\n"
                message += f"  Description: {project.description or 'No description'}\n"
                message += f"  Path: {project.path}\n"
                if project.last_opened_at:
                    try:
                        # Parse ISO datetime string and format it
                        from datetime import datetime
                        dt = datetime.fromisoformat(project.last_opened_at.replace('Z', '+00:00'))
                        message += f"  Last opened: {dt.strftime('%Y-%m-%d %H:%M')}\n"
                    except (ValueError, AttributeError):
                        message += f"  Last opened: {project.last_opened_at}\n"
                message += "\n"

            if current_project:
                message += f"\nCurrently active project: **{current_project.name}**"
            else:
                message += "\nNo project is currently active. Use 'activate' to start working in a project context."

            return Response(message=message, break_loop=False)
        except Exception as e:
            return Response(
                message=f"Failed to list projects: {str(e)}",
                break_loop=False
            )

    async def _edit_project(self, project_name: str = "", description: str = "", instructions: str = "", **kwargs) -> Response:
        """Edit an existing project"""
        
        if not project_name.strip():
            return Response(
                message="Project name is required to edit a project.",
                break_loop=False
            )
        
        try:
            # Find project by name
            existing_project = self.project_helper.get_project_by_name(project_name.strip())
            if not existing_project:
                return Response(
                    message=f"Project '{project_name}' not found.",
                    break_loop=False
                )

            # Prepare update data
            update_data = {}
            if description is not None:
                update_data['description'] = description.strip()

            if not update_data:
                return Response(
                    message="No update data provided.",
                    break_loop=False
                )

            # Update project
            updated_project = self.project_helper.update_project(existing_project.id, **update_data)

            message = f"Project '{updated_project['name']}' updated successfully!\n\n"
            message += f"Description: {updated_project['description'] or 'No description'}\n"
            message += f"Path: {updated_project['path']}"

            return Response(message=message, break_loop=False)
        except Exception as e:
            return Response(
                message=f"Failed to update project: {str(e)}",
                break_loop=False
            )

    async def _refresh_current_context(self, **kwargs) -> Response:
        """Refresh and display the current project context for this agent"""
        try:
            # Get the current active project from this agent's context
            active_project_id = self.agent.get_data("active_project")

            if not active_project_id:
                return Response(
                    message="No project is currently active in this agent's context.",
                    break_loop=False
                )

            # Get fresh project data
            project = self.project_helper.get_project_by_id(active_project_id)
            if not project:
                # Project was deleted, clear the context
                self.agent.set_data("active_project", None)
                self.agent.set_data("active_project_entity", None)
                return Response(
                    message=f"Previously active project '{active_project_id}' no longer exists. Context cleared.",
                    break_loop=False
                )

            # Refresh the agent's cached project entity
            self.agent.set_data("active_project_entity", project.to_dict())

            # Get additional project info
            file_structure = self.project_helper.get_project_file_structure(active_project_id)

            message = f"Current active project context refreshed:\\n\\n"
            message += f"**{project.name}**\\n"
            message += f"Description: {project.description or 'No description'}\\n"
            message += f"Project directory: {project.path}\\n"

            if project.instructions:
                instructions_preview = project.instructions[:200]
                if len(project.instructions) > 200:
                    instructions_preview += "..."
                message += f"Instructions: {instructions_preview}\\n"

            message += f"Files: {len(file_structure)} items in project structure"

            return Response(message=message, break_loop=False)

        except Exception as e:
            return Response(
                message=f"Failed to refresh project context: {str(e)}",
                break_loop=False
            )

    def get_log_object(self):
        """Override to provide custom log heading"""
        return self.agent.context.log.log(
            type="tool",
            heading=f"icon://folder {self.agent.agent_name}: Managing Projects",
            content="",
            kvps=self.args
        )