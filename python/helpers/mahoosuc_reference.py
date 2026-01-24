"""
Mahoosuc OS Reference Mode

Provides read-only access to Mahoosuc commands, agents, and skills
for learning and pattern extraction.
"""

from python.helpers.mahoosuc_config import get_agents_dir, get_commands_dir, get_skills_dir


def list_command_categories() -> list[str]:
    """
    List all command categories

    Returns:
        List of category names (directories and standalone .md files)
    """
    commands_dir = get_commands_dir()
    categories = []

    # Add directory categories
    for item in commands_dir.iterdir():
        if item.is_dir() and not item.name.startswith("."):
            categories.append(item.name)
        elif item.suffix == ".md" and not item.name.startswith("."):
            # Standalone command file
            categories.append(item.stem)

    return sorted(categories)


def get_command_spec(category: str, command: str) -> str | None:
    """
    Get command specification/documentation

    Args:
        category: Command category (e.g., "devops")
        command: Command name (e.g., "deploy")

    Returns:
        Command specification as markdown string, or None if not found
    """
    commands_dir = get_commands_dir()

    # Try category directory first
    category_dir = commands_dir / category
    if category_dir.is_dir():
        command_file = category_dir / f"{command}.md"
        if command_file.exists():
            return command_file.read_text()

    # Try standalone file
    standalone_file = commands_dir / f"{category}.md"
    if standalone_file.exists():
        return standalone_file.read_text()

    return None


def search_commands(keyword: str) -> list[dict[str, str]]:
    """
    Search commands by keyword

    Args:
        keyword: Search term

    Returns:
        List of dicts with 'category', 'command', 'file', 'excerpt'
    """
    commands_dir = get_commands_dir()
    results = []
    keyword_lower = keyword.lower()

    # Search all .md files
    for md_file in commands_dir.rglob("*.md"):
        if md_file.name.startswith("."):
            continue

        try:
            content = md_file.read_text()
            if keyword_lower in content.lower():
                # Extract category and command
                relative = md_file.relative_to(commands_dir)
                parts = relative.parts

                if len(parts) == 1:
                    # Standalone file
                    category = parts[0].replace(".md", "")
                    command = category
                else:
                    category = parts[0]
                    command = parts[-1].replace(".md", "")

                # Find excerpt with keyword
                lines = content.split("\n")
                excerpt_lines = []
                for line in lines:
                    if keyword_lower in line.lower():
                        excerpt_lines.append(line.strip())
                        if len(excerpt_lines) >= 3:
                            break

                results.append(
                    {
                        "category": category,
                        "command": command,
                        "file": str(relative),
                        "excerpt": " ... ".join(excerpt_lines[:3]),
                    }
                )
        except Exception:
            # Skip files that can't be read
            continue

    return results


def list_agents_by_category() -> dict[str, list[str]]:
    """
    List all agents grouped by category

    Returns:
        Dict mapping category name to list of agent names
    """
    agents_dir = get_agents_dir()
    agents_by_category = {}

    for category_dir in agents_dir.iterdir():
        if not category_dir.is_dir() or category_dir.name.startswith("."):
            continue

        agent_files = [f.stem for f in category_dir.glob("*.md") if not f.name.startswith(".")]

        if agent_files:
            agents_by_category[category_dir.name] = sorted(agent_files)

    return agents_by_category


def get_agent_prompt(category: str, agent_name: str) -> str | None:
    """
    Get agent prompt/specification

    Args:
        category: Agent category (e.g., "agent-os")
        agent_name: Agent name (e.g., "implementer")

    Returns:
        Agent prompt as markdown string, or None if not found
    """
    agents_dir = get_agents_dir()
    agent_file = agents_dir / category / f"{agent_name}.md"

    if agent_file.exists():
        return agent_file.read_text()

    return None


def list_skills() -> list[str]:
    """
    List all available skills

    Returns:
        List of skill names
    """
    skills_dir = get_skills_dir()
    skills = []

    for skill_dir in skills_dir.iterdir():
        if skill_dir.is_dir() and not skill_dir.name.startswith("."):
            # Verify it has a SKILL.md file
            if (skill_dir / "SKILL.md").exists():
                skills.append(skill_dir.name)

    return sorted(skills)


def get_skill_spec(skill_name: str) -> str | None:
    """
    Get skill specification

    Args:
        skill_name: Skill name (e.g., "brand-voice")

    Returns:
        Skill specification as markdown string, or None if not found
    """
    skills_dir = get_skills_dir()
    skill_file = skills_dir / skill_name / "SKILL.md"

    if skill_file.exists():
        return skill_file.read_text()

    return None
