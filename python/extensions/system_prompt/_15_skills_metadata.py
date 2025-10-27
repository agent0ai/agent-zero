"""
Skills Metadata Extension
Loads skill metadata into system prompt at initialization
"""

from typing import Any
from python.helpers.extension import Extension
from python.helpers.skills_manager import SkillsManager
from python.helpers import files
from python.helpers.settings import get_settings
from agent import Agent, LoopData


class SkillsMetadata(Extension):
    """Extension to load skill metadata into system prompt"""

    async def execute(
        self,
        system_prompt: list[str] = [],
        loop_data: LoopData = LoopData(),
        **kwargs: Any
    ):
        """Load skills metadata into system prompt"""
        settings = get_settings()

        # Check if skills are enabled
        if not settings.get("skills_enabled", True):
            return

        # Check if metadata should be in prompt
        if not settings.get("skills_metadata_in_prompt", True):
            return

        skills_meta = get_skills_metadata_prompt(self.agent)
        if skills_meta:
            system_prompt.append(skills_meta)


def get_skills_metadata_prompt(agent: Agent) -> str:
    """
    Generate skills metadata prompt

    Args:
        agent: Agent instance

    Returns:
        Formatted skills metadata prompt
    """
    manager = SkillsManager.get_instance()
    skills = manager.get_all_metadata()

    if not skills:
        return ""

    # Format skills metadata compactly
    skills_list = []
    for name, metadata in sorted(skills.items()):
        tags_str = f" [{', '.join(metadata.tags)}]" if metadata.tags else ""
        skills_list.append(f"- **{name}**{tags_str}: {metadata.description}")

    skills_metadata = "\n".join(skills_list)

    # Load template
    try:
        template = agent.read_prompt("agent.system.skills_available.md", skills_metadata=skills_metadata)
        return template
    except Exception:
        # Fallback if template not found
        return f"## Available Skills\n\n{skills_metadata}"
