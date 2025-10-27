"""
Skill Loader Module
Handles parsing and loading of SKILL.md files with YAML frontmatter
"""

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Optional
import re
import yaml
from python.helpers.print_style import PrintStyle


@dataclass
class SkillMetadata:
    """Skill metadata extracted from YAML frontmatter"""
    name: str
    description: str
    version: str = "1.0.0"
    author: Optional[str] = None
    tags: list[str] = field(default_factory=list)
    skill_dir: Optional[str] = None  # Absolute path to skill directory


@dataclass
class SkillContent:
    """Full skill content including metadata and markdown body"""
    metadata: SkillMetadata
    content: str  # Markdown content without frontmatter
    referenced_files: list[str] = field(default_factory=list)  # Relative paths


def parse_skill_file(skill_path: str) -> SkillContent:
    """
    Parse a SKILL.md file with YAML frontmatter

    Args:
        skill_path: Absolute path to SKILL.md file

    Returns:
        SkillContent with metadata and content

    Raises:
        FileNotFoundError: If skill file doesn't exist
        ValueError: If YAML frontmatter is invalid or missing required fields
    """
    path = Path(skill_path)
    if not path.exists():
        raise FileNotFoundError(f"Skill file not found: {skill_path}")

    with open(path, 'r', encoding='utf-8') as f:
        content = f.read()

    # Extract YAML frontmatter
    frontmatter_pattern = r'^---\s*\n(.*?)\n---\s*\n(.*)$'
    match = re.match(frontmatter_pattern, content, re.DOTALL)

    if not match:
        raise ValueError(f"YAML frontmatter not found in {skill_path}")

    yaml_content, markdown_content = match.groups()

    # Parse YAML
    try:
        yaml_data = yaml.safe_load(yaml_content)
    except yaml.YAMLError as e:
        raise ValueError(f"Invalid YAML in {skill_path}: {e}")

    # Validate required fields
    required_fields = ['name', 'description']
    for field in required_fields:
        if field not in yaml_data:
            raise ValueError(f"Required field '{field}' missing in {skill_path}")

    # Create metadata
    metadata = SkillMetadata(
        name=yaml_data['name'],
        description=yaml_data['description'],
        version=yaml_data.get('version', '1.0.0'),
        author=yaml_data.get('author'),
        tags=yaml_data.get('tags', []),
        skill_dir=str(path.parent)
    )

    # Extract referenced files from markdown links
    referenced_files = extract_referenced_files(markdown_content)

    return SkillContent(
        metadata=metadata,
        content=markdown_content,
        referenced_files=referenced_files
    )


def extract_referenced_files(markdown: str) -> list[str]:
    """
    Extract referenced files from markdown links

    Args:
        markdown: Markdown content

    Returns:
        List of relative file paths referenced in markdown
    """
    # Match markdown links: [text](path)
    pattern = r'\[([^\]]+)\]\(([^)]+)\)'
    matches = re.findall(pattern, markdown)

    # Filter out URLs and anchors, keep only relative file paths
    files = []
    for text, path in matches:
        # Skip URLs (http://, https://, etc.)
        if '://' in path:
            continue
        # Skip anchors (#)
        if path.startswith('#'):
            continue
        files.append(path)

    return files


def discover_skills(skills_dirs: list[str]) -> dict[str, SkillMetadata]:
    """
    Discover all skills in given directories

    Args:
        skills_dirs: List of absolute paths to search for skills

    Returns:
        Dictionary mapping skill names to SkillMetadata
    """
    skills: dict[str, SkillMetadata] = {}

    for skills_dir in skills_dirs:
        dir_path = Path(skills_dir)
        if not dir_path.exists():
            continue

        # Find all SKILL.md files
        for skill_file in dir_path.glob("*/SKILL.md"):
            try:
                skill_content = parse_skill_file(str(skill_file))
                metadata = skill_content.metadata

                # Check for duplicate names
                if metadata.name in skills:
                    PrintStyle().warning(
                        f"Duplicate skill name '{metadata.name}' found in {skill_file}, skipping"
                    )
                    continue

                skills[metadata.name] = metadata

            except Exception as e:
                PrintStyle().error(f"Error loading skill from {skill_file}: {e}")
                continue

    return skills


def validate_skill_structure(skill_dir: str) -> tuple[bool, str]:
    """
    Validate skill directory structure

    Args:
        skill_dir: Absolute path to skill directory

    Returns:
        Tuple of (is_valid, error_message)
    """
    dir_path = Path(skill_dir)

    # Check directory exists
    if not dir_path.exists():
        return False, f"Skill directory does not exist: {skill_dir}"

    # Check SKILL.md exists
    skill_file = dir_path / "SKILL.md"
    if not skill_file.exists():
        return False, f"SKILL.md not found in {skill_dir}"

    # Try to parse it
    try:
        parse_skill_file(str(skill_file))
    except Exception as e:
        return False, f"Invalid SKILL.md: {e}"

    return True, ""
