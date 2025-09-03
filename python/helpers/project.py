import os
import json
from typing import Dict, List, Optional, Any
from python.helpers import files
from python.helpers.print_style import PrintStyle
from dataclasses import dataclass


@dataclass
class ProjectData:
    """Data structure for project information"""
    name: str
    description: str
    instructions: str


class ProjectHelper:
    """Helper class for managing Agent Zero projects"""
    
    @staticmethod
    def get_projects_root() -> str:
        """Get the root directory where all projects are stored"""
        return files.get_abs_path("root")
    
    @staticmethod
    def get_project_directory(project_name: str) -> str:
        """Get the full path to a project directory"""
        return os.path.join(ProjectHelper.get_projects_root(), project_name)
    
    @staticmethod
    def get_project_file_path(project_name: str) -> str:
        """Get the full path to a project's JSON file"""
        return os.path.join(ProjectHelper.get_project_directory(project_name), "a0project.json")
    
    @staticmethod
    def sanitize_project_name(name: str) -> str:
        """Sanitize project name for filesystem safety"""
        # Remove potentially dangerous characters
        allowed_chars = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789-_"
        sanitized = ''.join(c for c in name if c in allowed_chars)
        
        # Ensure it's not empty and doesn't start with special chars
        if not sanitized or sanitized[0] in '-_':
            sanitized = 'project_' + sanitized
            
        # Limit length
        return sanitized[:50]
    
    @staticmethod
    def create_project(name: str, description: str, instructions: str) -> Dict[str, Any]:
        """
        Create a new project with the given parameters
        
        Args:
            name: Project name
            description: Project description
            instructions: Detailed project instructions
            
        Returns:
            Dict with success status and project data or error message
        """
        try:
            # Sanitize project name
            sanitized_name = ProjectHelper.sanitize_project_name(name)
            
            if not sanitized_name:
                return {
                    "success": False,
                    "error": "Invalid project name"
                }
            
            # Check if project already exists
            project_dir = ProjectHelper.get_project_directory(sanitized_name)
            if os.path.exists(project_dir):
                return {
                    "success": False,
                    "error": f"Project '{sanitized_name}' already exists"
                }
            
            # Create project directory
            os.makedirs(project_dir, exist_ok=True)
            
            # Create project data
            project_data = {
                "name": sanitized_name,
                "description": description,
                "instructions": instructions
            }
            
            # Save project JSON file
            project_file = ProjectHelper.get_project_file_path(sanitized_name)
            with open(project_file, 'w', encoding='utf-8') as f:
                json.dump(project_data, f, indent=2, ensure_ascii=False)
            
            PrintStyle(font_color="green", padding=True).print(f"Project '{sanitized_name}' created successfully")
            
            return {
                "success": True,
                "project": project_data
            }
            
        except Exception as e:
            PrintStyle(font_color="red", padding=True).print(f"Failed to create project: {str(e)}")
            return {
                "success": False,
                "error": f"Failed to create project: {str(e)}"
            }
    
    @staticmethod
    def load_project(project_name: str) -> Optional[ProjectData]:
        """
        Load project data from JSON file
        
        Args:
            project_name: Name of the project to load
            
        Returns:
            ProjectData object or None if not found/invalid
        """
        try:
            sanitized_name = ProjectHelper.sanitize_project_name(project_name)
            project_file = ProjectHelper.get_project_file_path(sanitized_name)
            
            if not os.path.exists(project_file):
                return None
                
            with open(project_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                
            return ProjectData(
                name=data.get("name", sanitized_name),
                description=data.get("description", ""),
                instructions=data.get("instructions", "")
            )
            
        except Exception as e:
            PrintStyle(font_color="red", padding=True).print(f"Failed to load project '{project_name}': {str(e)}")
            return None
    
    @staticmethod
    def list_projects() -> List[ProjectData]:
        """
        List all available projects
        
        Returns:
            List of ProjectData objects
        """
        projects = []
        projects_root = ProjectHelper.get_projects_root()
        
        try:
            if not os.path.exists(projects_root):
                return projects
                
            for item in os.listdir(projects_root):
                item_path = os.path.join(projects_root, item)
                project_file = os.path.join(item_path, "a0project.json")
                
                # Check if it's a directory with a project file
                if os.path.isdir(item_path) and os.path.exists(project_file):
                    project_data = ProjectHelper.load_project(item)
                    if project_data:
                        projects.append(project_data)
                        
        except Exception as e:
            PrintStyle(font_color="red", padding=True).print(f"Failed to list projects: {str(e)}")
            
        return projects
    
    @staticmethod
    def get_active_project(agent) -> Optional[str]:
        """
        Get the currently active project for an agent
        
        Args:
            agent: Agent instance
            
        Returns:
            Active project name or None
        """
        return agent.get_data("active_project")
    
    @staticmethod
    def set_active_project(agent, project_name: Optional[str]) -> bool:
        """
        Set the active project for an agent
        
        Args:
            agent: Agent instance
            project_name: Name of project to activate, or None to deactivate
            
        Returns:
            True if successful, False otherwise
        """
        try:
            if project_name is None:
                agent.set_data("active_project", None)
                PrintStyle(font_color="yellow", padding=True).print("Project deactivated")
                return True
                
            # Validate project exists
            sanitized_name = ProjectHelper.sanitize_project_name(project_name)
            project_data = ProjectHelper.load_project(sanitized_name)
            
            if not project_data:
                PrintStyle(font_color="red", padding=True).print(f"Project '{sanitized_name}' not found")
                return False
                
            agent.set_data("active_project", sanitized_name)
            PrintStyle(font_color="green", padding=True).print(f"Project '{sanitized_name}' activated")
            return True
            
        except Exception as e:
            PrintStyle(font_color="red", padding=True).print(f"Failed to set active project: {str(e)}")
            return False
    
    @staticmethod
    def update_project(project_name: str, description: str = None, instructions: str = None) -> Dict[str, Any]:
        """
        Update an existing project's details
        
        Args:
            project_name: Name of the project to update
            description: New description (optional)
            instructions: New instructions (optional)
            
        Returns:
            Dict with success status and updated project data or error message
        """
        try:
            sanitized_name = ProjectHelper.sanitize_project_name(project_name)
            project_data = ProjectHelper.load_project(sanitized_name)
            
            if not project_data:
                return {
                    "success": False,
                    "error": f"Project '{sanitized_name}' not found"
                }
            
            # Update fields if provided
            if description is not None:
                project_data.description = description
            if instructions is not None:
                project_data.instructions = instructions
            
            # Save updated data
            updated_data = {
                "name": project_data.name,
                "description": project_data.description,
                "instructions": project_data.instructions
            }
            
            project_file = ProjectHelper.get_project_file_path(sanitized_name)
            with open(project_file, 'w', encoding='utf-8') as f:
                json.dump(updated_data, f, indent=2, ensure_ascii=False)
            
            PrintStyle(font_color="green", padding=True).print(f"Project '{sanitized_name}' updated successfully")
            
            return {
                "success": True,
                "project": updated_data
            }
            
        except Exception as e:
            PrintStyle(font_color="red", padding=True).print(f"Failed to update project: {str(e)}")
            return {
                "success": False,
                "error": f"Failed to update project: {str(e)}"
            }
    
    @staticmethod
    def get_project_file_structure(project_name: str, max_depth: int = 3) -> List[str]:
        """
        Get the file structure of a project directory
        
        Args:
            project_name: Name of the project
            max_depth: Maximum depth to traverse
            
        Returns:
            List of file/directory paths relative to project root
        """
        try:
            sanitized_name = ProjectHelper.sanitize_project_name(project_name)
            project_dir = ProjectHelper.get_project_directory(sanitized_name)
            
            if not os.path.exists(project_dir):
                return []
            
            file_list = []
            
            def scan_directory(path: str, current_depth: int = 0, prefix: str = ""):
                if current_depth > max_depth:
                    return
                    
                try:
                    items = sorted(os.listdir(path))
                    for item in items:
                        if item.startswith('.') or item == 'a0project.json':
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