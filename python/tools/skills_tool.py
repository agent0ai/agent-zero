from __future__ import annotations

from pathlib import Path
from typing import List

from python.helpers.tool import Tool, Response
from python.helpers import projects, files, file_tree
from python.helpers import skills as skills_helper, runtime


class SkillsTool(Tool):
    """
    Manage and use SKILL.md-based Skills (Anthropic open standard).

    Methods (tool_args.method):
      - list
      - search (query)
      - load (skill_name)
      - read_file (skill_name, file_path)

    Script execution is handled by code_execution_tool directly.
    """

    async def execute(self, **kwargs) -> Response:
        method = (
            (kwargs.get("method") or self.args.get("method") or self.method or "")
            .strip()
            .lower()
        )

        try:
            if method == "list":
                return Response(message=self._list(), break_loop=False)
            # if method == "search":
            #     query = str(kwargs.get("query") or "").strip()
            #     return Response(message=self._search(query), break_loop=False)
            if method == "load":
                skill_name = str(kwargs.get("skill_name") or "").strip()
                return Response(message=self._load(skill_name), break_loop=False)
            if method == "read_file":
                skill_name = str(kwargs.get("skill_name") or "").strip()
                file_path = str(kwargs.get("file_path") or "").strip()
                return Response(
                    message=self._read_file(skill_name, file_path), break_loop=False
                )

            return Response(
                message=(
                    "Error: missing/invalid 'method'. Supported methods: "
                    "list, search, load, read_file."
                ),
                break_loop=False,
            )
        except (
            Exception
        ) as e:  # keep tool robust; return error instead of crashing loop
            return Response(message=f"Error in skills_tool: {e}", break_loop=False)

    def _list(self) -> str:
        skills = skills_helper.list_skills(
            include_content=False,
            agent=self.agent,
        )
        if not skills:
            return "No skills found."

        # Stable output: sort by name
        skills_sorted = sorted(skills, key=lambda s: s.name.lower())

        lines: List[str] = []
        lines.append(f"Available skills ({len(skills_sorted)}):")
        for s in skills_sorted:
            tags = f" tags={','.join(s.tags)}" if s.tags else ""
            ver = f" v{s.version}" if s.version else ""
            desc = (s.description or "").strip()
            if len(desc) > 200:
                desc = desc[:200].rstrip() + "…"
            lines.append(f"- {s.name}{ver}{tags}: {desc}")
        lines.append("")
        lines.append("Tip: use skills_tool method=search or method=load for details.")
        return "\n".join(lines)

    def _search(self, query: str) -> str:
        if not query:
            return "Error: 'query' is required for method=search."

        results = skills_helper.search_skills(
            query,
            limit=25,
            agent=self.agent,
        )
        if not results:
            return f"No skills matched query: {query!r}"

        lines: List[str] = []
        lines.append(f"Skills matching {query!r} ({len(results)}):")
        for s in results:
            desc = (s.description or "").strip()
            if len(desc) > 200:
                desc = desc[:200].rstrip() + "…"
            lines.append(f"- {s.name}: {desc}")
        lines.append("")
        lines.append(
            "Tip: use skills_tool method=load skill_name=<name> to load full instructions."
        )
        return "\n".join(lines)

    def _load(self, skill_name: str) -> str:

        skill_name = skill_name.strip()
        if skill_name.startswith("**") and skill_name.endswith("**"):
            skill_name = skill_name[
                2:-2
            ]  # remove markdown bold markers if used by agent

        if not skill_name:
            return "Error: 'skill_name' is required for method=load."

        skill = skills_helper.find_skill(
            skill_name,
            include_content=True,
            agent=self.agent,
        )
        if not skill:
            return f"Error: skill not found: {skill_name!r}. Try skills_tool method=list or method=search."

        # Enumerate files under the skill directory for progressive disclosure
        referenced_files = self._list_skill_files(skill.path, max_files=80)
        rel_skill_dir = Path(files.deabsolute_path(str(skill.path)))
        if self.agent.config.code_exec_ssh_enabled:
            runtime_path = files.normalize_a0_path(str(skill.path))
        else:
            runtime_path = str(skill.path)

        lines: List[str] = []
        lines.append(f"Skill: {skill.name}")
        # lines.append(f"Path: {rel_skill_dir}")
        lines.append(f"Path: {runtime_path}")
        if skill.version:
            lines.append(f"Version: {skill.version}")
        if skill.author:
            lines.append(f"Author: {skill.author}")
        if skill.license:
            lines.append(f"License: {skill.license}")
        if skill.compatibility:
            lines.append(f"Compatibility: {skill.compatibility}")
        if skill.tags:
            lines.append(f"Tags: {', '.join(skill.tags)}")
        if skill.allowed_tools:
            lines.append(f"Allowed tools: {', '.join(skill.allowed_tools)}")
        if skill.triggers:
            lines.append(f"Triggers: {', '.join(skill.triggers)}")

        lines.append("")
        if skill.description:
            lines.append("Description:")
            lines.append(skill.description.strip())
            lines.append("")

        lines.append("Content (SKILL.md body):")
        lines.append(skill.content.strip() or "(empty)")
        lines.append("")

        if referenced_files:
            lines.append(
                "Files in skill directory (use skills_tool method=read_file to open):"
            )
            lines.append(referenced_files)
        else:
            lines.append("No additional files found in skill directory.")

        return "\n".join(lines)

    def _read_file(self, skill_name: str, file_path: str) -> str:
        if not skill_name:
            return "Error: 'skill_name' is required for method=read_file."
        if not file_path:
            return "Error: 'file_path' is required for method=read_file."

        skill = skills_helper.find_skill(
            skill_name,
            include_content=False,
            agent=self.agent,
        )
        if not skill:
            return f"Error: skill not found: {skill_name!r}."

        try:
            target = skills_helper.safe_path_within_dir(skill.path, file_path)
        except Exception as e:
            return f"Error: invalid file_path: {e}"

        if not target.exists() or not target.is_file():
            return f"Error: file not found: {file_path!r} (within skill {skill.name})"

        # Basic binary guard: if null byte present, do not dump
        content = target.read_bytes()
        if b"\x00" in content[:4096]:
            return f"Error: file appears to be binary; refusing to print raw bytes ({file_path})."

        text = content.decode("utf-8", errors="replace")
        return f"File: {file_path}\n\n{text}"

    def _list_skill_files(self, skill_dir: Path, *, max_files: int = 80) -> str:
        if not skill_dir.exists():
            return ""

        tree = str(file_tree.file_tree(
            str(skill_dir),
            max_depth=10,
            folders_first=True,
            max_files=100,
            max_folders=100,
            output_mode="string",
            max_lines=300,
            ignore=files.read_file("conf/skill.default.gitignore"),
        ))

        # replace absolute path with runtime path (for dev env only)
        if tree and runtime.is_development():
            runtime_path = files.normalize_a0_path(str(skill_dir))
            tree = tree.replace(str(skill_dir), runtime_path)

        return str(tree)
