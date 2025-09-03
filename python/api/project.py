from python.helpers.api import ApiHandler, Request, Response
from python.helpers.project import ProjectHelper, ProjectData
from python.helpers.print_style import PrintStyle
from flask import jsonify
from typing import Dict, Any


class Project(ApiHandler):
    """
    API handler for project management operations.
    
    Supports creating, listing, loading, activating, and deactivating projects
    through HTTP POST requests with JSON or form data.
    """

    async def process(self, input: dict, request: Request) -> dict | Response:
        """
        Process project management API requests
        
        Args:
            input: Input data from request (JSON or form data)
            request: Flask request object
            
        Returns:
            Response dict or Flask Response object
        """
        try:
            # Handle both JSON and multipart/form-data
            if request.content_type.startswith("multipart/form-data"):
                action = request.form.get("action", "").lower().strip()
                name = request.form.get("name", "").strip()
                description = request.form.get("description", "").strip()
                instructions = request.form.get("instructions", "").strip()
                ctxid = request.form.get("context", "")
            else:
                # Handle JSON request
                action = input.get("action", "").lower().strip()
                name = input.get("name", "").strip()
                description = input.get("description", "").strip()
                instructions = input.get("instructions", "").strip()
                ctxid = input.get("context", "")

            # Get agent context if needed for activate/deactivate operations
            context = None
            if action in ["activate", "deactivate", "get_active"]:
                context = self.get_context(ctxid)

            # Route to appropriate handler
            if action == "create":
                return await self._handle_create(name, description, instructions)
            elif action == "list":
                return await self._handle_list()
            elif action == "load":
                return await self._handle_load(name)
            elif action == "activate":
                return await self._handle_activate(context, name)
            elif action == "deactivate":
                return await self._handle_deactivate(context)
            elif action == "get_active":
                return await self._handle_get_active(context)
            elif action == "update":
                return await self._handle_update(name, description, instructions)
            else:
                return {
                    "success": False,
                    "error": f"Unknown action '{action}'. Available actions: create, list, load, activate, deactivate, get_active, update"
                }

        except Exception as e:
            error_msg = f"Project API error: {str(e)}"
            PrintStyle(font_color="red", padding=True).print(error_msg)
            return {
                "success": False,
                "error": error_msg
            }

    async def _handle_create(self, name: str, description: str, instructions: str) -> Dict[str, Any]:
        """Handle project creation"""
        if not name:
            return {
                "success": False,
                "error": "Project name is required"
            }

        result = ProjectHelper.create_project(
            name=name,
            description=description,
            instructions=instructions
        )

        return result

    async def _handle_list(self) -> Dict[str, Any]:
        """Handle listing all projects"""
        try:
            projects = ProjectHelper.list_projects()
            
            project_list = []
            for project in projects:
                project_list.append({
                    "name": project.name,
                    "description": project.description,
                    "instructions": project.instructions,
                    "directory": ProjectHelper.get_project_directory(project.name)
                })
            
            return {
                "success": True,
                "projects": project_list
            }

        except Exception as e:
            return {
                "success": False,
                "error": f"Failed to list projects: {str(e)}"
            }

    async def _handle_load(self, name: str) -> Dict[str, Any]:
        """Handle loading a specific project"""
        if not name:
            return {
                "success": False,
                "error": "Project name is required"
            }

        project = ProjectHelper.load_project(name)
        
        if not project:
            return {
                "success": False,
                "error": f"Project '{name}' not found"
            }

        return {
            "success": True,
            "project": {
                "name": project.name,
                "description": project.description,
                "instructions": project.instructions,
                "directory": ProjectHelper.get_project_directory(project.name),
                "file_structure": ProjectHelper.get_project_file_structure(project.name)
            }
        }

    async def _handle_activate(self, context, name: str) -> Dict[str, Any]:
        """Handle project activation"""
        if not context:
            return {
                "success": False,
                "error": "Agent context is required for project activation"
            }

        if not name:
            return {
                "success": False,
                "error": "Project name is required"
            }

        success = ProjectHelper.set_active_project(context.agent0, name)
        
        if success:
            project = ProjectHelper.load_project(name)
            return {
                "success": True,
                "message": f"Project '{name}' activated successfully",
                "project": {
                    "name": project.name if project else name,
                    "description": project.description if project else "",
                    "instructions": project.instructions if project else "",
                    "directory": ProjectHelper.get_project_directory(name)
                } if project else None
            }
        else:
            return {
                "success": False,
                "error": f"Failed to activate project '{name}'"
            }

    async def _handle_deactivate(self, context) -> Dict[str, Any]:
        """Handle project deactivation"""
        if not context:
            return {
                "success": False,
                "error": "Agent context is required for project deactivation"
            }

        current_project = ProjectHelper.get_active_project(context.agent0)
        
        if not current_project:
            return {
                "success": False,
                "error": "No project is currently active"
            }

        ProjectHelper.set_active_project(context.agent0, None)
        
        return {
            "success": True,
            "message": f"Project '{current_project}' deactivated successfully"
        }

    async def _handle_get_active(self, context) -> Dict[str, Any]:
        """Get currently active project"""
        if not context:
            return {
                "success": False,
                "error": "Agent context is required"
            }

        current_project = ProjectHelper.get_active_project(context.agent0)
        
        if not current_project:
            return {
                "success": True,
                "active_project": None,
                "message": "No project is currently active"
            }

        project = ProjectHelper.load_project(current_project)
        
        return {
            "success": True,
            "active_project": {
                "name": project.name if project else current_project,
                "description": project.description if project else "",
                "instructions": project.instructions if project else "",
                "directory": ProjectHelper.get_project_directory(current_project)
            } if project else {
                "name": current_project,
                "description": "",
                "instructions": "",
                "directory": ProjectHelper.get_project_directory(current_project)
            }
        }

    async def _handle_update(self, name: str, description: str, instructions: str) -> Dict[str, Any]:
        """Handle project update"""
        if not name:
            return {
                "success": False,
                "error": "Project name is required"
            }

        # Only update fields that were provided (not empty)
        update_description = description if description else None
        update_instructions = instructions if instructions else None

        result = ProjectHelper.update_project(
            project_name=name,
            description=update_description,
            instructions=update_instructions
        )

        return result