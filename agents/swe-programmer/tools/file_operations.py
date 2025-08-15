"""
File Operations Tool for SWE Programmer Agent
Handles file creation, viewing, and modification
"""

import os
import re
from pathlib import Path
from python.helpers.tool import Tool, Response
from python.helpers.swe_graph_state import GraphState

class FileOperations(Tool):
    """
    Tool for performing file operations like view, create, and modify
    """
    
    async def execute(self, **kwargs):
        """Execute file operations"""
        
        operation = kwargs.get("operation", "view")
        path = kwargs.get("path")
        
        if not path:
            return Response(
                message="Error: 'path' parameter is required for file operations",
                break_loop=False
            )
        
        if operation == "view":
            return await self.view_file(path, **kwargs)
        elif operation == "create":
            return await self.create_file(path, **kwargs)
        elif operation == "modify":
            return await self.modify_file(path, **kwargs)
        elif operation == "replace":
            return await self.replace_in_file(path, **kwargs)
        elif operation == "append":
            return await self.append_to_file(path, **kwargs)
        elif operation == "delete":
            return await self.delete_file(path, **kwargs)
        elif operation == "list":
            return await self.list_directory(path, **kwargs)
        else:
            return Response(
                message=f"Unknown operation: {operation}. Supported: view, create, modify, replace, append, delete, list",
                break_loop=False
            )
    
    async def view_file(self, path: str, **kwargs) -> Response:
        """View the contents of a file"""
        try:
            if not os.path.exists(path):
                return Response(
                    message=f"File not found: {path}",
                    break_loop=False
                )
            
            with open(path, 'r') as f:
                content = f.read()
            
            # Optional line range
            start_line = kwargs.get("start_line", 1)
            end_line = kwargs.get("end_line")
            
            if end_line:
                lines = content.split('\n')
                selected_lines = lines[start_line-1:end_line]
                content = '\n'.join(selected_lines)
                message = f"File: {path} (lines {start_line}-{end_line}):\n```\n{content}\n```"
            else:
                # Truncate if too long
                if len(content) > 10000:
                    content = content[:10000] + "\n... (truncated)"
                message = f"File: {path}:\n```\n{content}\n```"
            
            # Update state
            self.update_state_files(path, "viewed")
            
            return Response(message=message, break_loop=False)
            
        except Exception as e:
            return Response(
                message=f"Error viewing file {path}: {str(e)}",
                break_loop=False
            )
    
    async def create_file(self, path: str, **kwargs) -> Response:
        """Create a new file with content"""
        content = kwargs.get("content", "")
        
        try:
            # Create parent directories if needed
            parent_dir = os.path.dirname(path)
            if parent_dir:
                os.makedirs(parent_dir, exist_ok=True)
            
            # Check if file exists
            if os.path.exists(path):
                overwrite = kwargs.get("overwrite", False)
                if not overwrite:
                    return Response(
                        message=f"File already exists: {path}. Set overwrite=true to replace.",
                        break_loop=False
                    )
            
            # Write file
            with open(path, 'w') as f:
                f.write(content)
            
            # Update state
            self.update_state_files(path, "created")
            
            return Response(
                message=f"Successfully created file: {path}",
                break_loop=False
            )
            
        except Exception as e:
            return Response(
                message=f"Error creating file {path}: {str(e)}",
                break_loop=False
            )
    
    async def modify_file(self, path: str, **kwargs) -> Response:
        """Modify a file by replacing its entire content"""
        content = kwargs.get("content", "")
        
        try:
            if not os.path.exists(path):
                return Response(
                    message=f"File not found: {path}. Use operation='create' to create new files.",
                    break_loop=False
                )
            
            # Backup original content
            with open(path, 'r') as f:
                original = f.read()
            
            # Write new content
            with open(path, 'w') as f:
                f.write(content)
            
            # Update state
            self.update_state_files(path, "modified")
            
            return Response(
                message=f"Successfully modified file: {path}",
                break_loop=False
            )
            
        except Exception as e:
            return Response(
                message=f"Error modifying file {path}: {str(e)}",
                break_loop=False
            )
    
    async def replace_in_file(self, path: str, **kwargs) -> Response:
        """Replace text in a file"""
        old_text = kwargs.get("old_text")
        new_text = kwargs.get("new_text", "")
        regex = kwargs.get("regex", False)
        
        if not old_text:
            return Response(
                message="Error: 'old_text' parameter is required for replace operation",
                break_loop=False
            )
        
        try:
            if not os.path.exists(path):
                return Response(
                    message=f"File not found: {path}",
                    break_loop=False
                )
            
            with open(path, 'r') as f:
                content = f.read()
            
            # Perform replacement
            if regex:
                new_content = re.sub(old_text, new_text, content)
                count = len(re.findall(old_text, content))
            else:
                count = content.count(old_text)
                new_content = content.replace(old_text, new_text)
            
            if count == 0:
                return Response(
                    message=f"No occurrences of '{old_text}' found in {path}",
                    break_loop=False
                )
            
            # Write back
            with open(path, 'w') as f:
                f.write(new_content)
            
            # Update state
            self.update_state_files(path, "modified")
            
            return Response(
                message=f"Replaced {count} occurrence(s) in {path}",
                break_loop=False
            )
            
        except Exception as e:
            return Response(
                message=f"Error replacing text in {path}: {str(e)}",
                break_loop=False
            )
    
    async def append_to_file(self, path: str, **kwargs) -> Response:
        """Append content to a file"""
        content = kwargs.get("content", "")
        
        try:
            # Create file if it doesn't exist
            mode = 'a' if os.path.exists(path) else 'w'
            
            with open(path, mode) as f:
                f.write(content)
            
            # Update state
            action = "modified" if mode == 'a' else "created"
            self.update_state_files(path, action)
            
            return Response(
                message=f"Successfully appended to file: {path}",
                break_loop=False
            )
            
        except Exception as e:
            return Response(
                message=f"Error appending to file {path}: {str(e)}",
                break_loop=False
            )
    
    async def delete_file(self, path: str, **kwargs) -> Response:
        """Delete a file"""
        try:
            if not os.path.exists(path):
                return Response(
                    message=f"File not found: {path}",
                    break_loop=False
                )
            
            os.remove(path)
            
            # Update state
            self.update_state_files(path, "deleted")
            
            return Response(
                message=f"Successfully deleted file: {path}",
                break_loop=False
            )
            
        except Exception as e:
            return Response(
                message=f"Error deleting file {path}: {str(e)}",
                break_loop=False
            )
    
    async def list_directory(self, path: str, **kwargs) -> Response:
        """List contents of a directory"""
        try:
            if not os.path.exists(path):
                return Response(
                    message=f"Directory not found: {path}",
                    break_loop=False
                )
            
            if not os.path.isdir(path):
                return Response(
                    message=f"Not a directory: {path}",
                    break_loop=False
                )
            
            # Get directory contents
            items = []
            for item in sorted(os.listdir(path)):
                item_path = os.path.join(path, item)
                if os.path.isdir(item_path):
                    items.append(f"[DIR]  {item}/")
                else:
                    size = os.path.getsize(item_path)
                    items.append(f"[FILE] {item} ({size} bytes)")
            
            if not items:
                message = f"Directory {path} is empty"
            else:
                message = f"Contents of {path}:\n" + "\n".join(items)
            
            return Response(message=message, break_loop=False)
            
        except Exception as e:
            return Response(
                message=f"Error listing directory {path}: {str(e)}",
                break_loop=False
            )
    
    def update_state_files(self, path: str, action: str):
        """Update the GraphState with file operation information"""
        try:
            state = self.agent.get_data("swe_state")
            if isinstance(state, GraphState):
                # Add to repository context files
                if path not in state.repository_context.files:
                    state.repository_context.files.append(path)
                
                # Add to history
                state.add_history(f"File {action}: {path}")
                
                # Update current task artifacts if there's an active task
                for task in state.plan.tasks:
                    if task.status == "in-progress":
                        if "modified_files" not in task.artifacts:
                            task.artifacts["modified_files"] = []
                        task.artifacts["modified_files"].append({
                            "path": path,
                            "action": action
                        })
                        break
                
                self.agent.set_data("swe_state", state)
        except:
            pass  # Silently fail if state update fails