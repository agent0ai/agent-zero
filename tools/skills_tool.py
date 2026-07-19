from __future__ import annotations

from pathlib import Path
from typing import List

from helpers.tool import Tool, Response
from helpers import skills as skills_helper
from helpers.print_style import PrintStyle


DATA_NAME_LOADED_SKILLS = skills_helper.AGENT_DATA_NAME_LOADED_SKILLS


class SkillsTool(Tool):
    """
    Manage and use SKILL.md-based Skills (Anthropic open standard).

    Actions (tool_args.action):
      - list
      - search (query)
      - load (skill_name)
      - read_file (skill_name, file_path)

    Script execution is handled by code_execution_tool directly.
    """

    def _current_action(self) -> str:
        return (
            str(
                self.args.get("action")
                or ""
            )
            .strip()
            .lower()
            .replace("-", "_")
        )

    @staticmethod
    def _normalize_skill_name(skill_name: str) -> str:
        skill_name = skill_name.strip()
        if skill_name.startswith("**") and skill_name.endswith("**"):
            skill_name = skill_name[2:-2]
        return skill_name.strip()

    def get_log_object(self):
        import uuid

        if self._current_action() == "load":
            skill_name = self._normalize_skill_name(
                str(self.args.get("skill_name") or "")
            )
            heading = (
                f"icon://construction Loading skill {skill_name}"
                if skill_name
                else "icon://construction Loading skill"
            )
            return self.agent.context.log.log(
                type="tool",
                heading=heading,
                content="",
                kvps={"_tool_name": self.name},
                id=str(uuid.uuid4()),
            )

        return super().get_log_object()

    async def before_execution(self, **kwargs):
        if self._current_action() != "load":
            await super().before_execution(**kwargs)
            return

        skill_name = self._normalize_skill_name(
            str(kwargs.get("skill_name") or self.args.get("skill_name") or "")
        )
        label = f"{self.name} action {self._current_action()}"
        if skill_name:
            PrintStyle(
                font_color="#1B4F72",
                padding=True,
                background_color="white",
                bold=True,
            ).print(f"{self.agent.agent_name}: Loading skill '{skill_name}'")
        else:
            PrintStyle(
                font_color="#1B4F72",
                padding=True,
                background_color="white",
                bold=True,
            ).print(f"{self.agent.agent_name}: Using tool '{label}'")
        self.log = self.get_log_object()

    async def execute(self, **kwargs) -> Response:
        action = (
            str(
                kwargs.get("action")
                or self.args.get("action")
                or ""
            )
            .strip()
            .lower()
            .replace("-", "_")
        )

        try:
            if action == "list":
                return Response(message=self._list(), break_loop=False)
            if action == "search":
                query = str(kwargs.get("query") or self.args.get("query") or "").strip()
                return Response(message=self._search(query), break_loop=False)
            if action == "load":
                skill_name = self._normalize_skill_name(
                    str(kwargs.get("skill_name") or self.args.get("skill_name") or "")
                )
                return Response(message=self._load(skill_name), break_loop=False)
            if action == "read_file":
                skill_name = self._normalize_skill_name(
                    str(kwargs.get("skill_name") or self.args.get("skill_name") or "")
                )
                file_path = str(
                    kwargs.get("file_path") or self.args.get("file_path") or ""
                ).strip()
                return Response(
                    message=self._read_file(skill_name, file_path),
                    break_loop=False,
                )

            return Response(
                message=(
                    "Error: missing/invalid 'action'. Supported actions: "
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
            agent=self.agent,
            include_content=False,
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
        lines.append("Tip: use skills_tool action=search or action=load for details.")
        return "\n".join(lines)

    def _search(self, query: str) -> str:
        if not query:
            return "Error: 'query' is required for action=search."

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
            "Tip: use skills_tool action=load skill_name=<name> to load full instructions."
        )
        return "\n".join(lines)

    def _load(self, skill_name: str) -> str:
        skill_name = self._normalize_skill_name(skill_name)

        if not skill_name:
            return "Error: 'skill_name' is required for action=load."

        # Verify skill exists
        skill = skills_helper.find_skill(
            skill_name,
            include_content=False,
            agent=self.agent,
        )
        if not skill:
            return f"Error: skill not found: {skill_name!r}. Try skills_tool action=list or action=search."

        # Store skill name for fresh loading each turn
        if not self.agent.data.get(DATA_NAME_LOADED_SKILLS):
            self.agent.data[DATA_NAME_LOADED_SKILLS] = []
        loaded = self.agent.data[DATA_NAME_LOADED_SKILLS]
        if skill.name in loaded:
            loaded.remove(skill.name)
        loaded.append(skill.name)
        self.agent.data[DATA_NAME_LOADED_SKILLS] = loaded[-max_loaded_skills():]

        return f"Loaded skill '{skill.name}' into EXTRAS."

    def _read_file(self, skill_name: str, file_path: str) -> str:
        if not skill_name:
            return "Error: 'skill_name' is required for action=read_file."
        if not file_path:
            return "Error: 'file_path' is required for action=read_file."

        skill = skills_helper.find_skill(
            skill_name,
            include_content=False,
            agent=self.agent,
        )
        if not skill:
            return f"Error: skill not found: {skill_name!r}."

        skill_root = skill.path.resolve()
        target = Path(file_path)
        if not target.is_absolute():
            target = skill_root / target

        try:
            resolved = target.resolve()
            resolved.relative_to(skill_root)
        except Exception:
            return "Error: file_path must stay inside the skill directory."

        if not resolved.is_file():
            return f"Error: skill file not found: {file_path!r}."

        content = resolved.read_text(encoding="utf-8", errors="replace")
        if len(content) > 24000:
            content = content[:24000].rstrip() + "\n\n[truncated]"

        return (
            f"Skill file: {skill.name}/{resolved.relative_to(skill_root)}\n\n"
            f"{content}"
        )


def max_loaded_skills() -> int:
    return skills_helper.MAX_ACTIVE_SKILLS
