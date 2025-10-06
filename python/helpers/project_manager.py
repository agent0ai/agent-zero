import os
import json
import time
from dataclasses import dataclass, asdict
from datetime import datetime
from typing import Dict, List, Optional, Any, Iterator, TYPE_CHECKING

from python.helpers import files
from python.helpers.print_style import PrintStyle


@dataclass
class ProjectEntity:
    """Enhanced project entity model for Agent Zero project management system"""
    id: str
    name: str
    path: str
    description: str
    instructions: Optional[str] = None
    active: bool = False
    created_at: Optional[str] = None
    last_opened_at: Optional[str] = None

    def __post_init__(self):
        """Set default timestamps if not provided"""
        if self.created_at is None:
            self.created_at = datetime.now().isoformat()
        if self.last_opened_at is None:
            self.last_opened_at = self.created_at

    def to_dict(self) -> Dict[str, Any]:
        """Convert entity to dictionary for JSON serialization"""
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ProjectEntity':
        """Create entity from dictionary"""
        try:
            # Filter data to only include fields that exist in the dataclass
            valid_fields = {
                'id', 'name', 'path', 'description', 'instructions',
                'active', 'created_at', 'last_opened_at'
            }
            filtered_data = {k: v for k, v in data.items() if k in valid_fields}
            return cls(**filtered_data)
        except Exception as e:
            PrintStyle(font_color="red", padding=True).print(f"Failed to create ProjectEntity from dict: {str(e)}")
            PrintStyle(font_color="red", padding=True).print(f"Data: {data}")
            raise

    def update_last_opened(self) -> None:
        """Update the last_opened_at timestamp to current time"""
        self.last_opened_at = datetime.now().isoformat()


if TYPE_CHECKING:
    from agent import Agent


class ProjectManager:
    """Enhanced project manager for Agent Zero with full CRUD operations and API support"""

    PROJECT_FILE_NAME = "a0project.json"
    PROJECTS_INDEX_FILE = "projects_index.json"

    def __init__(self):
        """Initialize project manager"""
        self.projects_root = files.get_abs_path("root")
        self.index_file = files.get_abs_path(self.PROJECTS_INDEX_FILE)
        self._ensure_projects_directory()

    def _ensure_projects_directory(self) -> None:
        """Ensure projects root directory exists"""
        if not os.path.exists(self.projects_root):
            os.makedirs(self.projects_root, exist_ok=True)

    def _load_projects_index(self) -> Dict[str, Dict[str, Any]]:
        """Load the projects index file"""
        try:
            if os.path.exists(self.index_file):
                with open(self.index_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            return {}
        except Exception as e:
            PrintStyle(font_color="red", padding=True).print(f"Failed to load projects index: {str(e)}")
            return {}

    def _save_projects_index(self, index_data: Dict[str, Dict[str, Any]]) -> bool:
        """Save the projects index file"""
        try:
            with open(self.index_file, 'w', encoding='utf-8') as f:
                json.dump(index_data, f, indent=2, ensure_ascii=False)
            return True
        except Exception as e:
            PrintStyle(font_color="red", padding=True).print(f"Failed to save projects index: {str(e)}")
            return False

    def _persist_project_entity(self, project: ProjectEntity) -> None:
        """Persist a project's metadata to disk."""
        project_file = self._get_project_file_path(project.id)
        with open(project_file, 'w', encoding='utf-8') as f:
            json.dump(project.to_dict(), f, indent=2, ensure_ascii=False)

    def _get_current_active_project(self, index_data: Dict[str, Dict[str, Any]]) -> Optional[ProjectEntity]:
        """Return the currently active project entity if one exists."""
        for pid, project_info in index_data.items():
            if project_info.get("active"):
                return self.get_project_by_id(pid)
        return None

    def _clear_all_project_active_flags(self, index_data: Dict[str, Dict[str, Any]]) -> None:
        """Mark every project as inactive and persist the change."""
        for pid, project_info in index_data.items():
            if project_info.get("active"):
                project_info["active"] = False
                project = self.get_project_by_id(pid)
                if project:
                    project.active = False
                    self._persist_project_entity(project)

    def _iter_context_agents(self, context) -> Iterator["Agent"]:
        """Yield unique agents associated with an `AgentContext`."""
        seen_ids: set[int] = set()

        # Agent Zero (primary agent)
        if hasattr(context, "agent0") and context.agent0:
            agent0 = context.agent0
            seen_ids.add(id(agent0))
            yield agent0

        # Subordinate agents (A1 - A9)
        for agent_num in range(1, 10):
            attr = f"agent{agent_num}"
            if hasattr(context, attr):
                agent = getattr(context, attr)
                if agent and id(agent) not in seen_ids:
                    seen_ids.add(id(agent))
                    yield agent

        # Currently streaming agent (if different)
        if hasattr(context, "get_agent"):
            try:
                current_agent = context.get_agent()
            except Exception:
                current_agent = None
            if current_agent and id(current_agent) not in seen_ids:
                seen_ids.add(id(current_agent))
                yield current_agent

    def _broadcast_project_state(self, project_id: Optional[str], project_data: Optional[Dict[str, Any]]) -> int:
        """Propagate project context updates to every active agent.
        
        Returns:
            Number of agents updated
        """
        updated_count = 0
        try:
            from agent import AgentContext

            for context in AgentContext.all():
                for agent in self._iter_context_agents(context):
                    try:
                        agent.set_data("active_project", project_id)
                        agent.set_data("active_project_entity", project_data)
                        agent.set_data("project_context_refresh", True)
                        updated_count += 1
                    except Exception:
                        pass  # Continue updating other agents
        except Exception as e:
            PrintStyle(font_color="red", padding=True).print(
                f"Critical error in _broadcast_project_state: {str(e)}"
            )
        
        return updated_count

    def _generate_project_id(self, name: str) -> str:
        """Generate unique project ID based on name and timestamp"""
        sanitized_name = self._sanitize_project_name(name)
        timestamp = str(int(time.time()))
        return f"{sanitized_name}_{timestamp}"

    def _sanitize_project_name(self, name: str) -> str:
        """Sanitize project name for filesystem safety"""
        allowed_chars = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789-_"
        sanitized = ''.join(c if c in allowed_chars else '_' for c in name)

        if not sanitized or sanitized[0] in '-_':
            sanitized = 'project_' + sanitized

        return sanitized[:50]

    def _get_project_directory(self, project_id: str) -> str:
        """Get the full path to a project directory"""
        return os.path.join(self.projects_root, project_id)

    def _get_project_file_path(self, project_id: str) -> str:
        """Get the full path to a project's JSON file"""
        return os.path.join(self._get_project_directory(project_id), self.PROJECT_FILE_NAME)

    def create_project(self, name: str, description: str, path: Optional[str] = None, instructions: Optional[str] = None) -> Dict[str, Any]:
        """
        Create a new project

        Args:
            name: Project name
            description: Project description
            path: Optional custom path (defaults to auto-generated)

        Returns:
            Dict with success status and project data or error message
        """
        try:
            # Validate input
            if not name or not name.strip():
                return {
                    "success": False,
                    "error": "Project name is required"
                }

            if not description or not description.strip():
                return {
                    "success": False,
                    "error": "Project description is required"
                }

            # Check for duplicate names
            existing_projects = self.get_all_projects()
            for project in existing_projects:
                if project.name.lower() == name.strip().lower():
                    return {
                        "success": False,
                        "error": f"Project with name '{name}' already exists"
                    }

            # Generate project ID and create entity
            project_id = self._generate_project_id(name.strip())
            project_path = path or self._get_project_directory(project_id)

            project_entity = ProjectEntity(
                id=project_id,
                name=name.strip(),
                path=project_path,
                description=description.strip(),
                instructions=instructions.strip() if instructions else None
            )

            # Create project metadata directory (where a0project.json is stored)
            project_metadata_dir = self._get_project_directory(project_id)
            os.makedirs(project_metadata_dir, exist_ok=True)

            # Create user's project directory if it's different and specified
            if path and path != project_metadata_dir:
                try:
                    os.makedirs(project_path, exist_ok=True)
                except OSError as e:
                    return {
                        "success": False,
                        "error": f"Cannot create project directory at '{project_path}': {str(e)}"
                    }

            # Save project file in metadata directory
            project_file = self._get_project_file_path(project_id)
            with open(project_file, 'w', encoding='utf-8') as f:
                json.dump(project_entity.to_dict(), f, indent=2, ensure_ascii=False)

            # Update projects index
            index_data = self._load_projects_index()
            index_data[project_id] = {
                "id": project_id,
                "name": project_entity.name,
                "path": project_entity.path,
                "description": project_entity.description,
                "active": False,
                "created_at": project_entity.created_at,
                "last_opened_at": project_entity.last_opened_at
            }

            if not self._save_projects_index(index_data):
                # Cleanup on failure
                try:
                    os.remove(project_file)
                    if os.path.exists(project_path) and not os.listdir(project_path):
                        os.rmdir(project_path)
                except:
                    pass
                return {
                    "success": False,
                    "error": "Failed to save project index"
                }

            return {
                "success": True,
                "project": project_entity.to_dict()
            }

        except Exception as e:
            PrintStyle(font_color="red", padding=True).print(f"Failed to create project: {str(e)}")
            return {
                "success": False,
                "error": f"Failed to create project: {str(e)}"
            }

    def get_project_by_id(self, project_id: str) -> Optional[ProjectEntity]:
        """
        Get project by ID

        Args:
            project_id: Unique project identifier

        Returns:
            ProjectEntity object or None if not found
        """
        try:
            project_file = self._get_project_file_path(project_id)

            if not os.path.exists(project_file):
                return None

            with open(project_file, 'r', encoding='utf-8') as f:
                data = json.load(f)

            # Ensure we have the required fields
            if not isinstance(data, dict):
                PrintStyle(font_color="red", padding=True).print(f"Invalid project data format for '{project_id}'")
                return None

            if not all(key in data for key in ['id', 'name', 'path', 'description']):
                PrintStyle(font_color="red", padding=True).print(f"Missing required fields in project '{project_id}'")
                return None

            return ProjectEntity.from_dict(data)

        except Exception as e:
            PrintStyle(font_color="red", padding=True).print(f"Failed to load project '{project_id}': {str(e)}")
            return None

    def get_project_by_name(self, name: str) -> Optional[ProjectEntity]:
        """
        Get project by name

        Args:
            name: Project name

        Returns:
            ProjectEntity object or None if not found
        """
        index_data = self._load_projects_index()

        for project_id, project_info in index_data.items():
            if project_info.get("name", "").lower() == name.lower():
                return self.get_project_by_id(project_id)

        return None

    def get_all_projects(self) -> List[ProjectEntity]:
        """
        Get all projects

        Returns:
            List of ProjectEntity objects
        """
        projects = []
        index_data = self._load_projects_index()

        for project_id in index_data.keys():
            project = self.get_project_by_id(project_id)
            if project:
                projects.append(project)

        # Sort by last_opened_at descending (most recent first)
        def get_sort_key(project):
            if not project.last_opened_at:
                return datetime.min
            try:
                # Parse ISO format datetime string
                return datetime.fromisoformat(project.last_opened_at.replace('Z', '+00:00'))
            except (ValueError, AttributeError):
                return datetime.min

        projects.sort(key=get_sort_key, reverse=True)
        return projects

    def update_project(self, project_id: str, name: Optional[str] = None,
                      description: Optional[str] = None, path: Optional[str] = None) -> Dict[str, Any]:
        """
        Update an existing project

        Args:
            project_id: Project ID to update
            name: New project name (optional)
            description: New description (optional)
            path: New path (optional)

        Returns:
            Dict with success status and updated project data or error message
        """
        try:
            project = self.get_project_by_id(project_id)

            if not project:
                return {
                    "success": False,
                    "error": f"Project with ID '{project_id}' not found"
                }

            # Check for name conflicts if name is being changed
            if name and name.strip() != project.name:
                existing_projects = self.get_all_projects()
                for existing_project in existing_projects:
                    if existing_project.id != project_id and existing_project.name.lower() == name.strip().lower():
                        return {
                            "success": False,
                            "error": f"Project with name '{name}' already exists"
                        }

            # Update fields if provided
            if name is not None:
                project.name = name.strip()
            if description is not None:
                project.description = description.strip()
            if path is not None:
                project.path = path

            # Save updated project
            project_file = self._get_project_file_path(project_id)
            with open(project_file, 'w', encoding='utf-8') as f:
                json.dump(project.to_dict(), f, indent=2, ensure_ascii=False)

            # Update index
            index_data = self._load_projects_index()
            if project_id in index_data:
                index_data[project_id].update({
                    "name": project.name,
                    "description": project.description,
                    "path": project.path
                })
                self._save_projects_index(index_data)

            return {
                "success": True,
                "project": project.to_dict()
            }

        except Exception as e:
            PrintStyle(font_color="red", padding=True).print(f"Failed to update project: {str(e)}")
            return {
                "success": False,
                "error": f"Failed to update project: {str(e)}"
            }

    def delete_project(self, project_id: str) -> Dict[str, Any]:
        """
        Delete a project

        Args:
            project_id: Project ID to delete

        Returns:
            Dict with success status or error message
        """
        try:
            project = self.get_project_by_id(project_id)

            if not project:
                return {
                    "success": False,
                    "error": f"Project with ID '{project_id}' not found"
                }

            # Remove from index
            index_data = self._load_projects_index()
            if project_id in index_data:
                del index_data[project_id]
                self._save_projects_index(index_data)

            # Delete project directory if it exists
            project_dir = self._get_project_directory(project_id)
            if os.path.exists(project_dir):
                try:
                    files.delete_dir(project_dir.replace(files.get_base_dir() + "/", ""))
                except Exception as e:
                    PrintStyle(font_color="red", padding=True).print(f"Failed to delete project directory: {str(e)}")

            return {
                "success": True,
                "message": f"Project '{project.name}' deleted successfully"
            }
        except Exception as e:
            PrintStyle(font_color="red", padding=True).print(f"Failed to delete project: {str(e)}")
            return {
                "success": False,
                "error": f"Failed to delete project: {str(e)}"
            }

    def activate_project(self, agent, project_id: str) -> Dict[str, Any]:
        """
        Activate a project for an agent

        Args:
            agent: Agent instance
            project_id: Project ID to activate

        Returns:
            Dict with success status and project data or error message
        """
        try:
            project = self.get_project_by_id(project_id)

            if not project:
                return {
                    "success": False,
                    "error": f"Project with ID '{project_id}' not found"
                }

            # Deactivate current project if any
            current_active = self.get_active_project(agent)
            if current_active:
                self.deactivate_project(agent)

            # Update project's last_opened_at and active status
            project.update_last_opened()
            project.active = True

            # Save updated project
            self._persist_project_entity(project)

            # Update index
            index_data = self._load_projects_index()
            self._clear_all_project_active_flags(index_data)
            if project_id in index_data:
                index_data[project_id]["active"] = True
                index_data[project_id]["last_opened_at"] = project.last_opened_at
            else:
                index_data[project_id] = {
                    "id": project_id,
                    "name": project.name,
                    "path": project.path,
                    "description": project.description,
                    "active": True,
                    "created_at": project.created_at,
                    "last_opened_at": project.last_opened_at,
                }
            self._save_projects_index(index_data)

            # Set active project in agent data
            agent.set_data("active_project", project_id)
            agent.set_data("active_project_entity", project.to_dict())
            agent.set_data("project_context_refresh", True)

            # Keep other contexts synchronized when activation happens via tool
            self._broadcast_project_state(project_id, project.to_dict())

            return {
                "success": True,
                "project": project.to_dict(),
            }

        except Exception as e:
            PrintStyle(font_color="red", padding=True).print(
                f"Failed to activate project: {str(e)}"
            )
            return {
                "success": False,
                "error": f"Failed to activate project: {str(e)}"
            }

    def deactivate_project(self, agent) -> Dict[str, Any]:
        """
        Deactivate a project for an agent

        Args:
            agent: Agent instance

        Returns:
            Dict with success status and project data or error message
        """
        try:
            current_active = self.get_active_project(agent)

            if not current_active:
                # There was nothing to deactivate, but still broadcast so every
                # agent clears any stale context they may be holding.
                self._broadcast_project_state(None, None)
                return {
                    "success": True,
                    "message": "No active project to deactivate"
                }

            # Update project's last_opened_at and active status
            current_active.active = False

            # Save updated project
            self._persist_project_entity(current_active)

            # Update index
            index_data = self._load_projects_index()
            if current_active.id in index_data:
                index_data[current_active.id]["active"] = False
                index_data[current_active.id]["last_opened_at"] = current_active.last_opened_at
                self._save_projects_index(index_data)

            # Clear active project from agent data
            agent.set_data("active_project", None)
            agent.set_data("active_project_entity", None)
            agent.set_data("project_context_refresh", True)

            # Propagate context clear to other agents
            self._broadcast_project_state(None, None)

            return {
                "success": True,
                "message": "Project deactivated successfully",
            }

        except Exception as e:
            PrintStyle(font_color="red", padding=True).print(
                f"Failed to deactivate project: {str(e)}"
            )
            return {
                "success": False,
                "error": f"Failed to deactivate project: {str(e)}"
            }

    def get_active_project(self, agent) -> Optional[ProjectEntity]:
        """
        Get the currently active project for an agent

        Args:
            agent: Agent instance

        Returns:
            ProjectEntity object or None if no active project
        """
        active_project_id = agent.get_data("active_project")

        if not active_project_id:
            return None

        return self.get_project_by_id(active_project_id)

    def get_project_file_structure(self, project_id: str, max_depth: int = 3) -> List[str]:
        """
        Get the file structure of a project directory

        Args:
            project_id: Project ID
            max_depth: Maximum depth to traverse

        Returns:
            List of file/directory paths relative to project root
        """
        try:
            project = self.get_project_by_id(project_id)

            if not project:
                return []

            project_dir = project.path

            if not os.path.exists(project_dir):
                return []

            file_list = []

            def scan_directory(path: str, current_depth: int = 0, prefix: str = ""):
                if current_depth > max_depth:
                    return

                try:
                    items = sorted(os.listdir(path))
                    for item in items:
                        if item.startswith('.') or item == self.PROJECT_FILE_NAME:
                            continue

                        item_path = os.path.join(path, item)
                        relative_path = prefix + item

                        if os.path.isdir(item_path):
                            file_list.append(f"{relative_path}/")
                            scan_directory(item_path, current_depth + 1, relative_path + "/")
                        else:
                            file_list.append(relative_path)

                except PermissionError:
                    file_list.append(f"{prefix}[Permission Denied]")

            scan_directory(project_dir)
            return file_list

        except Exception as e:
            PrintStyle(font_color="red", padding=True).print(f"Failed to scan project structure: {str(e)}")
            return []

    def activate_project_api(self, project_id: str) -> Dict[str, Any]:
        """
        Activate a project for API calls and update agent context

        Args:
            project_id: Project ID to activate

        Returns:
            Dict with success status and project data or error message
        """
        try:
            project = self.get_project_by_id(project_id)

            if not project:
                return {
                    "success": False,
                    "error": f"Project with ID '{project_id}' not found"
                }

            # Deactivate all projects first
            index_data = self._load_projects_index()

            previous_active = self._get_current_active_project(index_data)

            self._clear_all_project_active_flags(index_data)

            # Activate the target project
            project.update_last_opened()
            project.active = True

            # Save updated project
            self._persist_project_entity(project)
            
            PrintStyle(font_color="blue", padding=False).print(f"[Project] Activated: {project.name} (id: {project_id})")

            # Update index
            index_data[project_id]["active"] = True
            index_data[project_id]["last_opened_at"] = project.last_opened_at
            self._save_projects_index(index_data)

            # Update all agent contexts for proper project switching
            updated_count = self._broadcast_project_state(project_id, project.to_dict())

            return {
                "success": True,
                "project": project.to_dict(),
                "previous_active": previous_active.to_dict() if previous_active else None,
                "agents_updated": updated_count,
            }

        except Exception as e:
            PrintStyle(font_color="red", padding=True).print(f"Failed to activate project via API: {str(e)}")
            return {
                "success": False,
                "error": f"Failed to activate project: {str(e)}"
            }

    def deactivate_project_api(self) -> Dict[str, Any]:
        """
        Deactivate all projects via API and update agent context

        Returns:
            Dict with success status or error message
        """
        try:
            index_data = self._load_projects_index()

            # Get the currently active project for return data
            current_active = self._get_current_active_project(index_data)
            
            # Save the active project entity file with active=False
            if current_active:
                current_active.active = False
                self._persist_project_entity(current_active)
                PrintStyle(font_color="blue", padding=False).print(f"[Project] Deactivated: {current_active.name}")
            else:
                PrintStyle(font_color="blue", padding=False).print(f"[Project] No active project to deactivate")

            # Deactivate all projects in index
            self._clear_all_project_active_flags(index_data)

            # Save the updated index
            self._save_projects_index(index_data)

            # Clear agent context so Agent Zero recognizes no active project
            updated_count = self._broadcast_project_state(None, None)

            return {
                "success": True,
                "message": "All projects deactivated successfully",
                "previous_active": current_active.to_dict() if current_active else None,
                "agents_updated": updated_count,
            }

        except Exception as e:
            PrintStyle(font_color="red", padding=True).print(f"Failed to deactivate projects via API: {str(e)}")
            return {
                "success": False,
                "error": f"Failed to deactivate projects: {str(e)}"
            }

    def cleanup_stale_projects(self) -> Dict[str, Any]:
        """
        Clean up projects that have missing directories or corrupted data

        Returns:
            Dict with cleanup results
        """
        try:
            index_data = self._load_projects_index()
            removed_projects = []

            for project_id, project_info in list(index_data.items()):
                project_file = self._get_project_file_path(project_id)

                # Check if project file exists and is valid
                if not os.path.exists(project_file):
                    removed_projects.append(project_info.get("name", project_id))
                    del index_data[project_id]
                    continue

                try:
                    with open(project_file, 'r', encoding='utf-8') as f:
                        json.load(f)
                except (json.JSONDecodeError, IOError):
                    # Corrupted project file
                    removed_projects.append(project_info.get("name", project_id))
                    del index_data[project_id]
                    try:
                        os.remove(project_file)
                    except:
                        pass

            # Save cleaned index
            if removed_projects:
                self._save_projects_index(index_data)

            return {
                "success": True,
                "removed_count": len(removed_projects),
                "removed_projects": removed_projects
            }

        except Exception as e:
            PrintStyle(font_color="red", padding=True).print(f"Failed to cleanup projects: {str(e)}")
            return {
                "success": False,
                "error": f"Failed to cleanup projects: {str(e)}"
            }


# Convenience instance for global use
project_manager = ProjectManager()