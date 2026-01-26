import os
from pathlib import Path

from python.helpers.extension import Extension
from agent import LoopData
from python.helpers.memory import Memory
from python.helpers import files
from python.helpers import skills as skills_helper
from python.helpers import frameworks


class RecallSkills(Extension):
    """
    Surface relevant SKILL.md-based Skills into the prompt (token-efficient).

    The Memory subsystem already indexes `skills/**/SKILL.md` into area "skills".
    This extension does a lightweight similarity lookup and injects a small
    "relevant skills" list into extras for the current user message.
    """

    async def execute(self, loop_data: LoopData = LoopData(), **kwargs):
        # Only on the first iteration of the message loop (new user instruction)
        if loop_data.iteration != 0:
            return

        # Determine query from current user message
        user_instruction = (
            loop_data.user_message.output_text() if loop_data.user_message else ""
        ).strip()
        if not user_instruction or len(user_instruction) < 8:
            return

        try:
            db = await Memory.get(self.agent)
            docs = await db.search_similarity_threshold(
                query=user_instruction,
                limit=12,
                threshold=0.55,
                filter=f"area == '{Memory.Area.SKILLS.value}'",
            )
        except Exception:
            docs = []

        # Fallback: simple keyword search over discovered skills if vector recall yields nothing
        recalled = []
        if docs:
            seen = set()
            for doc in docs:
                src = (doc.metadata or {}).get("source_path") or ""
                if not src:
                    continue
                if src in seen:
                    continue
                seen.add(src)
                recalled.append(src)
                if len(recalled) >= 6:
                    break

        if not recalled:
            # cheap lexical fallback - include framework skills if a framework is active
            framework = frameworks.get_active_framework(self.agent.context)
            framework_id = framework.id if framework else None
            matches = skills_helper.search_skills(user_instruction, limit=6, framework_id=framework_id)
            for s in matches:
                recalled.append(str(s.skill_md_path))

        if not recalled:
            return

        # Build compact metadata list
        base_skills_dir = Path(files.get_abs_path("skills")).resolve()
        lines = []
        for src_path in recalled[:6]:
            try:
                p = Path(src_path)
                # Some docs may store /a0/... paths; map to dev path when needed
                abs_path = Path(files.fix_dev_path(str(p)))
                text = abs_path.read_text(encoding="utf-8", errors="replace")
                fm, body = skills_helper.split_frontmatter(text)

                # Infer source if possible (custom/builtin/shared/framework), else "unknown"
                source = "unknown"
                try:
                    rel = abs_path.resolve().relative_to(base_skills_dir)
                    if rel.parts and rel.parts[0] in ("custom", "builtin", "shared", "frameworks"):
                        source = rel.parts[0]
                        # Normalize "frameworks" to "framework" for display
                        if source == "frameworks":
                            source = "framework"
                except Exception:
                    pass

                name = str(fm.get("name") or abs_path.parent.name).strip()
                desc = str(fm.get("description") or "").strip()
                if not desc:
                    # fallback to first non-empty line of body
                    for line in (body or "").splitlines():
                        if line.strip():
                            desc = line.strip()
                            break
                if len(desc) > 220:
                    desc = desc[:220].rstrip() + "…"

                lines.append(f"- {name} [{source}]: {desc}")
            except Exception:
                continue

        if not lines:
            return

        skills_block = "\n".join(lines)
        loop_data.extras_temporary["skills"] = self.agent.parse_prompt(
            "agent.system.skills.md", skills=skills_block
        )

