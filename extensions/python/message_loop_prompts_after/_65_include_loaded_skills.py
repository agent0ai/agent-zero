from helpers.extension import Extension
from helpers import skills, tokens
from agent import LoopData


SKILL_REATTACHMENT_TOKEN_BUDGET = 12_000
SKILL_REATTACHMENT_HEADER = (
    "Reattached loaded skill instructions after history compaction."
)


class IncludeLoadedSkills(Extension):
    async def execute(self, loop_data: LoopData = LoopData(), **kwargs):
        if not self.agent:
            return

        skill_names = skills.get_loaded_skill_names(self.agent)
        if not skill_names:
            return

        # Loaded skill bodies live in tool-result history. This hook only keeps
        # the ledger clean and restores bodies that compaction hid.
        visible_skill_names = []
        loaded_skills = []
        for skill_name in skill_names:
            skill = skills.find_skill(skill_name, agent=self.agent)
            if not skill:
                continue
            visible_skill_names.append(skill.name)
            loaded_skills.append(skill)
        skills.set_loaded_skill_names(self.agent, visible_skill_names)

        self._reattach_missing_skill_bodies(loop_data, loaded_skills)

    def _reattach_missing_skill_bodies(self, loop_data: LoopData, loaded_skills):
        if not self.agent or not loaded_skills:
            return

        visible_skill_names = _visible_skill_names(loop_data.history_output)
        selected = []
        used_tokens = 0

        for skill in reversed(loaded_skills):
            if skill.name in visible_skill_names:
                continue

            skill_data = skills.load_skill_for_agent(
                skill_name=skill.name,
                agent=self.agent,
            )
            message = f"{SKILL_REATTACHMENT_HEADER}\n\n{skill_data}"
            message_tokens = tokens.approximate_tokens(message)
            if used_tokens + message_tokens > SKILL_REATTACHMENT_TOKEN_BUDGET:
                continue

            selected.append((skill, message))
            used_tokens += message_tokens

        for skill, message in reversed(selected):
            history_message = self.agent.hist_add_tool_result(
                "skills_tool",
                message,
                skill_instructions={
                    "name": skill.name,
                    "path": str(skill.path),
                    "source": "skills_tool:reattach",
                    "content_included": True,
                },
            )
            loop_data.history_output.extend(history_message.output())


def _visible_skill_names(history_output) -> set[str]:
    return {
        name
        for message in history_output or []
        if (name := skills.skill_instruction_name(message))
    }
