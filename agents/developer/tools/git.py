import subprocess
import os
from python.helpers.tool import Tool, Response


class GitTool(Tool):
    async def execute(self, **kwargs) -> Response:
        # Routing method based on self.method from Tool base class
        if self.method == "init":
            return await self.init_repository(**kwargs)
        elif self.method == "commit":
            return await self.commit_changes(**kwargs)
        elif self.method == "status":
            return await self.get_status(**kwargs)
        elif self.method == "add":
            return await self.add_files(**kwargs)
        elif self.method == "log":
            return await self.get_log(**kwargs)
        else:
            return Response(message=f"Unknown git method: {self.method}", break_loop=False)

    async def init_repository(self, **kwargs) -> Response:
        """
        Initialize a Git repository with an initial commit.

        Args:
            path: Repository path (defaults to project path)
            message: Initial commit message (optional)
        """
        path = kwargs.get("path", None)
        message = kwargs.get("message", "Initial commit")

        if not path:
            path = self.agent.get_data("project_path")
            if not path:
                return Response(message="No project path available for Git initialization", break_loop=False)

        try:
            # Check if already a git repository
            if os.path.exists(os.path.join(path, ".git")):
                return Response(message=f"Git repository already exists at {path}", break_loop=False)

            # Initialize git repository
            result = subprocess.run(
                ["git", "init"],
                cwd=path,
                capture_output=True,
                text=True,
                timeout=10
            )

            if result.returncode != 0:
                return Response(message=f"Failed to initialize Git repository: {result.stderr}", break_loop=False)

            # Configure git user if not set (use generic defaults)
            subprocess.run(
                ["git", "config", "user.name", "Agent Zero Developer"],
                cwd=path,
                capture_output=True,
                timeout=5
            )
            subprocess.run(
                ["git", "config", "user.email", "developer@agentzero.local"],
                cwd=path,
                capture_output=True,
                timeout=5
            )

            # Create .gitignore if it doesn't exist
            gitignore_path = os.path.join(path, ".gitignore")
            if not os.path.exists(gitignore_path):
                gitignore_content = """# Common ignores
__pycache__/
*.pyc
*.pyo
*.pyd
.Python
.env
.venv
env/
venv/
.DS_Store
Thumbs.db
.idea/
.vscode/
*.log
*.tmp
node_modules/
.npm
.yarn-integrity
dist/
build/
"""
                with open(gitignore_path, 'w') as f:
                    f.write(gitignore_content)

            # Add all files and make initial commit
            subprocess.run(["git", "add", "."], cwd=path, capture_output=True, timeout=10)

            commit_result = subprocess.run(
                ["git", "commit", "-m", message],
                cwd=path,
                capture_output=True,
                text=True,
                timeout=10
            )

            if commit_result.returncode != 0:
                return Response(message=f"Git repository initialized but initial commit failed: {commit_result.stderr}", break_loop=False)

            return Response(
                message=f"Git repository initialized at {path} with initial commit: '{message}'",
                break_loop=False
            )

        except Exception as e:
            return Response(message=f"Error initializing Git repository: {e}", break_loop=False)

    async def commit_changes(self, **kwargs) -> Response:
        """
        Commit changes to the Git repository.

        Args:
            message: Commit message (required)
            path: Repository path (defaults to project path)
            add_all: Whether to add all changed files (default: True)
        """
        message = kwargs.get("message", None)
        path = kwargs.get("path", None)
        add_all = kwargs.get("add_all", True)

        if not message:
            return Response(message="Commit message is required", break_loop=False)

        if not path:
            path = self.agent.get_data("project_path")
            if not path:
                return Response(message="No project path available for Git commit", break_loop=False)

        try:
            # Check if git repository exists
            if not os.path.exists(os.path.join(path, ".git")):
                return Response(message=f"No Git repository found at {path}. Use git:init first.", break_loop=False)

            # Add files if requested
            if add_all:
                add_result = subprocess.run(
                    ["git", "add", "."],
                    cwd=path,
                    capture_output=True,
                    text=True,
                    timeout=10
                )

                if add_result.returncode != 0:
                    return Response(message=f"Failed to add files: {add_result.stderr}", break_loop=False)

            # Check if there are changes to commit
            status_result = subprocess.run(
                ["git", "status", "--porcelain"],
                cwd=path,
                capture_output=True,
                text=True,
                timeout=5
            )

            if not status_result.stdout.strip():
                return Response(message="No changes to commit", break_loop=False)

            # Commit changes
            commit_result = subprocess.run(
                ["git", "commit", "-m", message],
                cwd=path,
                capture_output=True,
                text=True,
                timeout=10
            )

            if commit_result.returncode != 0:
                return Response(message=f"Failed to commit changes: {commit_result.stderr}", break_loop=False)

            return Response(
                message=f"Successfully committed changes: '{message}'\n{commit_result.stdout}",
                break_loop=False
            )

        except Exception as e:
            return Response(message=f"Error committing changes: {e}", break_loop=False)

    async def get_status(self, **kwargs) -> Response:
        """Get Git repository status."""
        path = kwargs.get("path", None)

        if not path:
            path = self.agent.get_data("project_path")
            if not path:
                return Response(message="No project path available for Git status", break_loop=False)

        try:
            if not os.path.exists(os.path.join(path, ".git")):
                return Response(message=f"No Git repository found at {path}", break_loop=False)

            result = subprocess.run(
                ["git", "status", "--porcelain"],
                cwd=path,
                capture_output=True,
                text=True,
                timeout=5
            )

            if result.returncode != 0:
                return Response(message=f"Failed to get Git status: {result.stderr}", break_loop=False)

            if result.stdout.strip():
                return Response(
                    message=f"Git status (uncommitted changes):\n{result.stdout}",
                    break_loop=False
                )
            else:
                return Response(message="Git repository is clean (no uncommitted changes)", break_loop=False)

        except Exception as e:
            return Response(message=f"Error getting Git status: {e}", break_loop=False)

    async def add_files(self, **kwargs) -> Response:
        """Add files to Git staging area."""
        files = kwargs.get("files", ".")
        path = kwargs.get("path", None)

        if not path:
            path = self.agent.get_data("project_path")
            if not path:
                return Response(message="No project path available for Git add", break_loop=False)

        try:
            if not os.path.exists(os.path.join(path, ".git")):
                return Response(message=f"No Git repository found at {path}", break_loop=False)

            # Handle both single file and list of files
            if isinstance(files, str):
                file_args = [files]
            else:
                file_args = files

            result = subprocess.run(
                ["git", "add"] + file_args,
                cwd=path,
                capture_output=True,
                text=True,
                timeout=10
            )

            if result.returncode != 0:
                return Response(message=f"Failed to add files: {result.stderr}", break_loop=False)

            return Response(message=f"Successfully added files to Git staging: {', '.join(file_args)}", break_loop=False)

        except Exception as e:
            return Response(message=f"Error adding files to Git: {e}", break_loop=False)

    async def get_log(self, **kwargs) -> Response:
        """Get Git commit log."""
        path = kwargs.get("path", None)
        limit = kwargs.get("limit", 10)

        if not path:
            path = self.agent.get_data("project_path")
            if not path:
                return Response(message="No project path available for Git log", break_loop=False)

        try:
            if not os.path.exists(os.path.join(path, ".git")):
                return Response(message=f"No Git repository found at {path}", break_loop=False)

            result = subprocess.run(
                ["git", "log", f"--max-count={limit}", "--oneline"],
                cwd=path,
                capture_output=True,
                text=True,
                timeout=5
            )

            if result.returncode != 0:
                return Response(message=f"Failed to get Git log: {result.stderr}", break_loop=False)

            if result.stdout.strip():
                return Response(
                    message=f"Git commit history (last {limit} commits):\n{result.stdout}",
                    break_loop=False
                )
            else:
                return Response(message="No commits found in repository", break_loop=False)

        except Exception as e:
            return Response(message=f"Error getting Git log: {e}", break_loop=False)
