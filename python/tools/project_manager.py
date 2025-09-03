from python.helpers.tool import Tool, Response
from python.helpers.project import ProjectHelper, ProjectData
from python.helpers.print_style import PrintStyle
from typing import Dict, Any


class ProjectManager(Tool):
    """
    Tool for managing Agent Zero projects.
    
    Allows agents to create, activate, deactivate, list, and edit projects.
    Only agent #0 can create new projects for security reasons.
    """

    async def execute(self, action: str = "list", **kwargs) -> Response:
        """
        Execute project management action
        
        Args:
            action: Action to perform (create, activate, deactivate, list, edit)
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
            else:
                return Response(
                    message=f"Unknown action '{action}'. Available actions: create, activate, deactivate, list, edit",
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
        
        result = ProjectHelper.create_project(
            name=name.strip(),
            description=description.strip(),
            instructions=instructions.strip()
        )
        
        if result["success"]:
            project_data = result["project"]
            message = f"Project '{project_data['name']}' created successfully!\n\n"
            message += f"Description: {project_data['description']}\n"
            message += f"Project directory: {ProjectHelper.get_project_directory(project_data['name'])}\n\n"
            message += "Use 'activate' action to start working in this project context."
            
            return Response(message=message, break_loop=False)
        else:
            return Response(
                message=f"Failed to create project: {result['error']}",
                break_loop=False
            )

    async def _activate_project(self, project_name: str = "", **kwargs) -> Response:
        """Activate a project for the current agent context"""
        
        if not project_name.strip():
            return Response(
                message="Project name is required to activate a project.",
                break_loop=False
            )
        
        success = ProjectHelper.set_active_project(self.agent, project_name.strip())
        
        if success:
            project_data = ProjectHelper.load_project(project_name.strip())
            if project_data:
                message = f"Project '{project_data.name}' is now active!\n\n"
                message += f"Description: {project_data.description}\n\n"
                message += f"Instructions:\n{project_data.instructions}\n\n"
                message += f"Working directory: {ProjectHelper.get_project_directory(project_data.name)}\n\n"
                message += "All subsequent operations will be performed within this project context."
                
                return Response(message=message, break_loop=False)
            else:
                return Response(
                    message=f"Project activated but could not load details.",
                    break_loop=False
                )
        else:
            return Response(
                message=f"Failed to activate project '{project_name}'. Make sure the project exists.",
                break_loop=False
            )

    async def _deactivate_project(self, **kwargs) -> Response:
        """Deactivate the current project"""
        
        current_project = ProjectHelper.get_active_project(self.agent)
        
        if not current_project:
            return Response(
                message="No project is currently active.",
                break_loop=False
            )
        
        ProjectHelper.set_active_project(self.agent, None)
        
        return Response(
            message=f"Project '{current_project}' has been deactivated. You are now working in the default context.",
            break_loop=False
        )

    async def _list_projects(self, **kwargs) -> Response:
        """List all available projects"""
        
        projects = ProjectHelper.list_projects()
        current_project = ProjectHelper.get_active_project(self.agent)
        
        if not projects:
            return Response(
                message="No projects found. Create a new project using the 'create' action.",
                break_loop=False
            )
        
        message = f"Available projects ({len(projects)} found):\n\n"
        
        for project in projects:
            status = " [ACTIVE]" if project.name == current_project else ""
            message += f"• **{project.name}**{status}\n"
            message += f"  Description: {project.description}\n"
            if project.instructions:
                # Show first 100 chars of instructions
                instructions_preview = project.instructions[:100]
                if len(project.instructions) > 100:
                    instructions_preview += "..."
                message += f"  Instructions: {instructions_preview}\n"
            message += f"  Directory: {ProjectHelper.get_project_directory(project.name)}\n\n"
        
        if current_project:
            message += f"\nCurrently active project: **{current_project}**"
        else:
            message += "\nNo project is currently active. Use 'activate' to start working in a project context."
        
        return Response(message=message, break_loop=False)

    async def _edit_project(self, project_name: str = "", description: str = None, instructions: str = None, **kwargs) -> Response:
        """Edit an existing project"""
        
        if not project_name.strip():
            return Response(
                message="Project name is required to edit a project.",
                break_loop=False
            )
        
        # Check if project exists
        existing_project = ProjectHelper.load_project(project_name.strip())
        if not existing_project:
            return Response(
                message=f"Project '{project_name}' not found.",
                break_loop=False
            )
        
        # Update project
        result = ProjectHelper.update_project(
            project_name=project_name.strip(),
            description=description.strip() if description is not None else None,
            instructions=instructions.strip() if instructions is not None else None
        )
        
        if result["success"]:
            project_data = result["project"]
            message = f"Project '{project_data['name']}' updated successfully!\n\n"
            message += f"Description: {project_data['description']}\n\n"
            message += f"Instructions:\n{project_data['instructions']}"
            
            return Response(message=message, break_loop=False)
        else:
            return Response(
                message=f"Failed to update project: {result['error']}",
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