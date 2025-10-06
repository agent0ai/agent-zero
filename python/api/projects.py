"""
API endpoints for project management.
Provides REST API for CRUD operations on projects.
"""

from flask import Response
from typing import Optional
import json

from python.helpers.api import ApiHandler, Request
from python.helpers.project_manager import ProjectManager


class Projects(ApiHandler):
    """Project management API handler for Agent Zero's Flask API system."""

    @classmethod
    def requires_auth(cls) -> bool:
        return True

    @classmethod
    def requires_csrf(cls) -> bool:
        return True

    @classmethod
    def get_methods(cls) -> list[str]:
        return ["GET", "POST", "PUT", "DELETE"]

    async def process(self, input: dict, request: Request) -> dict | Response:
        """
        Process project API requests based on HTTP method and URL parameters.

        Routes:
        - GET /projects -> list all projects
        - POST /projects -> create new project
        - GET /projects?id=<project_id> -> get project by ID
        - PUT /projects -> update project (requires id in request body)
        - DELETE /projects -> delete project (requires id in request body)
        - POST /projects -> activate project (requires id and action=activate in request body)
        """
        try:
            method = request.method
            project_manager = ProjectManager()

            # Ensure input is not None for methods that need it
            if input is None:
                input = {}

            # GET: List all projects or get specific project
            if method == "GET":
                # GET requests don't require JSON input, use query parameters
                project_id = request.args.get("id")
                if project_id:
                    return await self._get_project(project_manager, project_id)
                else:
                    return await self._list_projects(project_manager)

            # POST: Create new project or activate existing project
            elif method == "POST":
                action = input.get("action")
                if action == "activate":
                    project_id = input.get("id")
                    if not project_id:
                        return self._error_response(
                            "Project ID is required for activation", 400
                        )
                    return await self._activate_project(project_manager, project_id)
                elif action == "deactivate":
                    return await self._deactivate_project(project_manager)
                else:
                    return await self._create_project(project_manager, input)

            # PUT: Update existing project
            elif method == "PUT":
                project_id = input.get("id")
                if not project_id:
                    return self._error_response(
                        "Project ID is required for update", 400
                    )
                return await self._update_project(project_manager, project_id, input)

            # DELETE: Delete existing project
            elif method == "DELETE":
                project_id = input.get("id")
                if not project_id:
                    return self._error_response(
                        "Project ID is required for deletion", 400
                    )
                return await self._delete_project(project_manager, project_id)

            else:
                return self._error_response(f"Method {method} not allowed", 405)

        except Exception as e:
            return self._error_response(f"Internal server error: {str(e)}", 500)

    async def _list_projects(self, project_manager: ProjectManager) -> dict:
        """Get all projects."""
        projects = project_manager.get_all_projects()

        project_list = []
        active_project_id = None

        for project in projects:
            project_data = {
                "id": project.id,
                "name": project.name,
                "path": project.path,
                "description": project.description,
                "instructions": project.instructions,
                "active": project.active,
                "created_at": project.created_at,
                "last_opened_at": project.last_opened_at,
            }
            project_list.append(project_data)

            if project.active:
                active_project_id = project.id

        return {
            "success": True,
            "projects": project_list,
            "total_count": len(project_list),
            "active_project_id": active_project_id,
        }

    async def _get_project(
        self, project_manager: ProjectManager, project_id: str
    ) -> dict | Response:
        """Get a specific project by ID."""
        project = project_manager.get_project_by_id(project_id)

        if not project:
            return self._error_response(f"Project with ID {project_id} not found", 404)

        return {
            "success": True,
            "project": {
                "id": project.id,
                "name": project.name,
                "path": project.path,
                "description": project.description,
                "instructions": project.instructions,
                "active": project.active,
                "created_at": project.created_at,
                "last_opened_at": project.last_opened_at,
            },
        }

    async def _create_project(
        self, project_manager: ProjectManager, input: dict
    ) -> dict | Response:
        """Create a new project."""
        name = input.get("name")
        path = input.get("path")
        description = input.get("description")
        instructions = input.get("instructions")

        if not name:
            return self._error_response("Project name is required", 400)
        if not description:
            return self._error_response("Project description is required", 400)

        # Path is optional - pass None if empty
        if path and not path.strip():
            path = None

        try:
            result = project_manager.create_project(
                name=name, path=path, description=description, instructions=instructions
            )

            if not result.get("success"):
                return self._error_response(
                    result.get("error", "Failed to create project"), 400
                )

            project_data = result.get("project", {})
            return {
                "success": True,
                "project": {
                    "id": project_data.get("id"),
                    "name": project_data.get("name"),
                    "path": project_data.get("path"),
                    "description": project_data.get("description"),
                    "active": project_data.get("active", False),
                    "created_at": project_data.get("created_at"),
                    "last_opened_at": project_data.get("last_opened_at"),
                },
            }

        except Exception as e:
            return self._error_response(str(e), 500)

    async def _update_project(
        self, project_manager: ProjectManager, project_id: str, input: dict
    ) -> dict | Response:
        """Update an existing project."""
        # Check if project exists
        existing_project = project_manager.get_project_by_id(project_id)
        if not existing_project:
            return self._error_response(f"Project with ID {project_id} not found", 404)

        # Prepare update data (only include non-None values)
        update_data = {}
        if "name" in input and input["name"] is not None:
            update_data["name"] = input["name"]
        if "path" in input and input["path"] is not None:
            update_data["path"] = input["path"]
        if "description" in input and input["description"] is not None:
            update_data["description"] = input["description"]

        if not update_data:
            return self._error_response("No update data provided", 400)

        try:
            result = project_manager.update_project(project_id, **update_data)

            if not result.get("success"):
                return self._error_response(
                    result.get("error", "Failed to update project"), 400
                )

            project_data = result.get("project", {})
            return {
                "success": True,
                "project": {
                    "id": project_data.get("id"),
                    "name": project_data.get("name"),
                    "path": project_data.get("path"),
                    "description": project_data.get("description"),
                    "active": project_data.get("active", False),
                    "created_at": project_data.get("created_at"),
                    "last_opened_at": project_data.get("last_opened_at"),
                },
            }

        except Exception as e:
            return self._error_response(str(e), 500)

    async def _delete_project(
        self, project_manager: ProjectManager, project_id: str
    ) -> dict | Response:
        """Delete an existing project."""
        # Check if project exists
        existing_project = project_manager.get_project_by_id(project_id)
        if not existing_project:
            return self._error_response(f"Project with ID {project_id} not found", 404)

        try:
            project_manager.delete_project(project_id)
            return {
                "success": True,
                "message": f"Project {project_id} deleted successfully",
            }

        except Exception as e:
            return self._error_response(f"Error deleting project: {str(e)}", 500)

    async def _activate_project(
        self, project_manager: ProjectManager, project_id: str
    ) -> dict | Response:
        """Activate a specific project (deactivates all others)."""
        # Check if project exists
        existing_project = project_manager.get_project_by_id(project_id)
        if not existing_project:
            return self._error_response(f"Project with ID {project_id} not found", 404)

        try:
            result = project_manager.activate_project_api(project_id)

            if not result.get("success"):
                return self._error_response(
                    result.get("error", "Failed to activate project"), 400
                )

            project_data = result.get("project", {})

            return {
                "success": True,
                "project": {
                    "id": project_data.get("id"),
                    "name": project_data.get("name"),
                    "path": project_data.get("path"),
                    "description": project_data.get("description"),
                    "active": project_data.get("active", False),
                    "created_at": project_data.get("created_at"),
                    "last_opened_at": project_data.get("last_opened_at"),
                },
            }

        except Exception as e:
            return self._error_response(f"Error activating project: {str(e)}", 500)

    async def _deactivate_project(
        self, project_manager: ProjectManager
    ) -> dict | Response:
        """Deactivate all projects."""
        try:
            result = project_manager.deactivate_project_api()

            if not result.get("success"):
                return self._error_response(
                    result.get("error", "Failed to deactivate projects"), 400
                )

            return {
                "success": True,
                "message": result.get("message", "Projects deactivated successfully"),
                "previous_active": result.get("previous_active"),
            }

        except Exception as e:
            return self._error_response(f"Error deactivating projects: {str(e)}", 500)

    def _error_response(self, message: str, status_code: int) -> Response:
        """Create a standardized error response."""
        error_data = {"success": False, "error": message}
        return Response(
            response=json.dumps(error_data),
            status=status_code,
            mimetype="application/json",
        )
