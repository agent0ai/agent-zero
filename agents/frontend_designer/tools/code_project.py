from python.helpers.tool import Tool, Response
from python.helpers import files
import os
import json


class CodeProjectTool(Tool):
    """Generate Next.js/React code projects with proper file structure."""

    async def execute(self, **kwargs) -> Response:
        # Extract arguments
        project_id = self.args.get("project_id", "")
        file_list = self.args.get("files", [])
        framework = self.args.get("framework", "nextjs")
        styling = self.args.get("styling", "tailwind")

        # Validate required arguments
        if not project_id:
            return Response(
                message="Error: project_id is required",
                break_loop=False
            )

        if not file_list:
            return Response(
                message="Error: files array is required",
                break_loop=False
            )

        # Create project directory structure
        base_path = f"tmp/{project_id}"
        created_files = []

        try:
            # Create base directory
            os.makedirs(base_path, exist_ok=True)

            # Create each file
            for file_info in file_list:
                file_path = file_info.get("path", "")
                file_content = file_info.get("content", "")

                if not file_path:
                    continue

                # Full path
                full_path = os.path.join(base_path, file_path)

                # Create parent directories
                os.makedirs(os.path.dirname(full_path), exist_ok=True)

                # Write file
                with open(full_path, 'w', encoding='utf-8') as f:
                    f.write(file_content)

                created_files.append(file_path)

            # Generate summary message
            message = f"Created {framework} project '{project_id}' with {len(created_files)} files\n\n"
            message += f"Project path: {base_path}\n"
            message += f"Styling: {styling}\n\n"
            message += "Files created:\n"
            for file_path in created_files:
                message += f"  - {file_path}\n"

            return Response(message=message, break_loop=False)

        except Exception as e:
            return Response(
                message=f"Error creating project: {str(e)}",
                break_loop=False
            )
