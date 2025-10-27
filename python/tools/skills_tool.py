"""
Skills Tool
Manage and use agent skills for specialized capabilities
"""

from typing import Optional
from python.helpers.tool import Tool, Response
from python.helpers.skills_manager import SkillsManager
from python.helpers.print_style import PrintStyle


class SkillsTool(Tool):
    """Tool for managing and using Agent Skills"""

    async def execute(self, **kwargs) -> Response:
        """
        Execute skills tool operation

        Args:
            method: Operation to perform (list, load, read_file, execute_script, search)
            skill_name: Name of skill (for load, read_file, execute_script)
            file_path: Relative file path (for read_file)
            script_path: Relative script path (for execute_script)
            script_args: Arguments for script (for execute_script)
            query: Search query (for search)
        """
        await self.agent.handle_intervention()

        method = self.args.get("method", "").lower().strip()

        if method == "list":
            return await self._list_skills()
        elif method == "load":
            return await self._load_skill()
        elif method == "read_file":
            return await self._read_file()
        elif method == "execute_script":
            return await self._execute_script()
        elif method == "search":
            return await self._search()
        else:
            return Response(
                message=f"Unknown method '{method}'. Use: list, load, read_file, execute_script, search",
                break_loop=False
            )

    async def _list_skills(self) -> Response:
        """List all available skills"""
        manager = SkillsManager.get_instance()
        skills = manager.get_all_metadata()

        if not skills:
            return Response(
                message="No skills available",
                break_loop=False
            )

        # Format skills list
        lines = ["Available skills:\n"]
        for name, metadata in sorted(skills.items()):
            tags_str = f" [{', '.join(metadata.tags)}]" if metadata.tags else ""
            lines.append(f"- **{name}** (v{metadata.version}){tags_str}")
            lines.append(f"  {metadata.description}")
            if metadata.author:
                lines.append(f"  Author: {metadata.author}")
            lines.append("")

        return Response(
            message="\n".join(lines),
            break_loop=False
        )

    async def _load_skill(self) -> Response:
        """Load full skill content"""
        skill_name = self.args.get("skill_name", "").strip()
        if not skill_name:
            return Response(
                message="Error: skill_name required for load method",
                break_loop=False
            )

        manager = SkillsManager.get_instance()
        content = manager.load_skill_content(skill_name)

        if not content:
            return Response(
                message=f"Error: Skill '{skill_name}' not found",
                break_loop=False
            )

        # Format response
        lines = [
            f"# Skill: {content.metadata.name}",
            f"Version: {content.metadata.version}",
            f"Description: {content.metadata.description}",
            ""
        ]

        if content.metadata.tags:
            lines.append(f"Tags: {', '.join(content.metadata.tags)}")
            lines.append("")

        if content.referenced_files:
            lines.append("Referenced files:")
            for ref_file in content.referenced_files:
                lines.append(f"- {ref_file}")
            lines.append("")

        lines.append("---\n")
        lines.append(content.content)

        return Response(
            message="\n".join(lines),
            break_loop=False
        )

    async def _read_file(self) -> Response:
        """Read referenced file from skill"""
        skill_name = self.args.get("skill_name", "").strip()
        file_path = self.args.get("file_path", "").strip()

        if not skill_name or not file_path:
            return Response(
                message="Error: skill_name and file_path required for read_file method",
                break_loop=False
            )

        manager = SkillsManager.get_instance()
        content = manager.get_skill_file(skill_name, file_path)

        if content is None:
            return Response(
                message=f"Error: File '{file_path}' not found in skill '{skill_name}'",
                break_loop=False
            )

        return Response(
            message=f"# {skill_name}/{file_path}\n\n{content}",
            break_loop=False
        )

    async def _search(self) -> Response:
        """Search skills by query"""
        query = self.args.get("query", "").strip().lower()
        if not query:
            return Response(
                message="Error: query required for search method",
                break_loop=False
            )

        manager = SkillsManager.get_instance()
        skills = manager.get_all_metadata()

        # Simple text search in name, description, and tags
        matches = []
        for name, metadata in skills.items():
            score = 0

            # Search in name
            if query in name.lower():
                score += 3

            # Search in description
            if query in metadata.description.lower():
                score += 2

            # Search in tags
            for tag in metadata.tags:
                if query in tag.lower():
                    score += 1

            if score > 0:
                matches.append((score, name, metadata))

        if not matches:
            return Response(
                message=f"No skills found matching '{query}'",
                break_loop=False
            )

        # Sort by score (descending)
        matches.sort(reverse=True, key=lambda x: x[0])

        # Format results
        lines = [f"Skills matching '{query}':\n"]
        for score, name, metadata in matches:
            tags_str = f" [{', '.join(metadata.tags)}]" if metadata.tags else ""
            lines.append(f"- **{name}**{tags_str}")
            lines.append(f"  {metadata.description}")
            lines.append("")

        return Response(
            message="\n".join(lines),
            break_loop=False
        )

    async def _execute_script(self) -> Response:
        """Execute skill script"""
        skill_name = self.args.get("skill_name", "").strip()
        script_path = self.args.get("script_path", "").strip()
        script_args = self.args.get("script_args", {})

        # Validate required parameters
        if not skill_name or not script_path:
            return Response(
                message="Error: skill_name and script_path required for execute_script method",
                break_loop=False
            )

        # Validate script_args type
        if not isinstance(script_args, dict):
            return Response(
                message="Error: script_args must be a dictionary",
                break_loop=False
            )

        manager = SkillsManager.get_instance()

        # Read script content using get_skill_file
        script_content = manager.get_skill_file(skill_name, script_path)
        if script_content is None:
            return Response(
                message=f"Error: Script '{script_path}' not found in skill '{skill_name}'",
                break_loop=False
            )

        # Determine runtime from extension
        if script_path.endswith('.py'):
            runtime = 'python'
        elif script_path.endswith('.js'):
            runtime = 'nodejs'
        elif script_path.endswith('.sh'):
            runtime = 'terminal'
        else:
            return Response(
                message=f"Error: Unsupported script type: {script_path}",
                break_loop=False
            )

        # Prepare script with arguments injected
        import json
        if runtime == 'python':
            # Inject args as JSON at the top for Python
            args_json = json.dumps(script_args, indent=2)
            code = f"import json\n_skill_args = {args_json}\n\n{script_content}"
        elif runtime == 'nodejs':
            # Inject args as const for Node.js
            args_json = json.dumps(script_args, indent=2)
            code = f"const _skill_args = {args_json};\n\n{script_content}"
        else:  # terminal
            # Pass args as environment variables for shell scripts
            env_vars = "\n".join([f'export {k}="{v}"' for k, v in script_args.items()])
            code = f"{env_vars}\n\n{script_content}" if env_vars else script_content

        # Execute using code_execution_tool
        code_tool = self.agent.get_tool(
            name="code_execution_tool",
            method=None,
            args={
                "runtime": runtime,
                "code": code,
                "session": 0
            },
            message=f"Executing skill script: {skill_name}/{script_path}",
            loop_data=self.loop_data
        )

        return await code_tool.execute()
