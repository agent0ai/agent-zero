from agent import LoopData
from helpers.extension import Extension
from helpers import skills as skills_helper


class RecallRelevantSkills(Extension):
    async def execute(self, loop_data: LoopData = LoopData(), **kwargs):
        if not self.agent or loop_data.iteration != 0:
            return

        user_instruction = (
            loop_data.user_message.output_text() if loop_data.user_message else ""
        ).strip()
        if len(user_instruction) < 8:
            return

        matches = skills_helper.search_skills(
            user_instruction,
            limit=6,
            agent=self.agent,
        )
        if not matches:
            return

        lines: list[str] = []
        for skill in matches:
            name = skill.name.strip().replace("\n", " ")[:100]
            desc = (skill.description or "").replace("\n", " ").strip()
            if len(desc) > 220:
                desc = desc[:220].rstrip() + "…"
            lines.append(f"- {name}: {desc}")

        if not lines:
            return

        loop_data.extras_temporary["relevant_skills"] = self.agent.read_prompt(
            "agent.system.skills.relevant.md",
            skills="\n".join(lines),
        )
