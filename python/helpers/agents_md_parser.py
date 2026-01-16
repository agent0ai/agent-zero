"""
AGENTS.md Parser - Anthropic Agent Skills Specification compliant parser
Parses SKILL.md and AGENTS.md files with YAML frontmatter support
"""

import re
import yaml
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class SkillMetadata:
    """Skill metadata from YAML frontmatter"""
    name: str
    description: str
    license: Optional[str] = None
    compatibility: Optional[str] = None
    metadata: Dict[str, str] = field(default_factory=dict)
    triggers: List[str] = field(default_factory=list)
    version: Optional[str] = None
    author: Optional[str] = None
    dependencies: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation"""
        return {
            "name": self.name,
            "description": self.description,
            "license": self.license,
            "compatibility": self.compatibility,
            "metadata": self.metadata,
            "triggers": self.triggers,
            "version": self.version,
            "author": self.author,
            "dependencies": self.dependencies,
        }


@dataclass
class Skill:
    """Complete skill definition with metadata and content"""
    metadata: SkillMetadata
    content: str
    file_path: Optional[Path] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation"""
        result = self.metadata.to_dict()
        result["content"] = self.content
        if self.file_path:
            result["file_path"] = str(self.file_path)
        return result


class AgentsMdParser:
    """Parser for AGENTS.md and SKILL.md files following Anthropic specification"""

    # Name validation regex from spec: lowercase alphanumeric with hyphens
    NAME_PATTERN = re.compile(r'^[a-z0-9]+(-[a-z0-9]+)*$')

    # Frontmatter extraction pattern
    FRONTMATTER_PATTERN = re.compile(
        r'^---\s*\n(.*?)\n---\s*\n(.*)$',
        re.DOTALL | re.MULTILINE
    )

    @classmethod
    def parse_file(cls, file_path: Path) -> Optional[Skill]:
        """
        Parse a SKILL.md or AGENTS.md file

        Args:
            file_path: Path to the skill file

        Returns:
            Skill object or None if parsing fails
        """
        if not file_path.exists():
            return None

        try:
            content = file_path.read_text(encoding='utf-8')
            return cls.parse_content(content, file_path)
        except Exception as e:
            print(f"Error parsing {file_path}: {e}")
            return None

    @classmethod
    def parse_content(cls, content: str, file_path: Optional[Path] = None) -> Optional[Skill]:
        """
        Parse skill content with YAML frontmatter

        Args:
            content: File content as string
            file_path: Optional path to the source file

        Returns:
            Skill object or None if parsing fails
        """
        # Try to extract YAML frontmatter
        match = cls.FRONTMATTER_PATTERN.match(content)

        if match:
            frontmatter_str = match.group(1)
            body_content = match.group(2).strip()

            try:
                frontmatter = yaml.safe_load(frontmatter_str)
            except yaml.YAMLError as e:
                print(f"YAML parsing error: {e}")
                return None
        else:
            # No frontmatter found - try to parse as plain AGENTS.md
            frontmatter = {}
            body_content = content.strip()

        # Validate and extract metadata
        metadata = cls._extract_metadata(frontmatter, body_content)
        if not metadata:
            return None

        return Skill(
            metadata=metadata,
            content=body_content,
            file_path=file_path
        )

    @classmethod
    def _extract_metadata(cls, frontmatter: Dict[str, Any], content: str) -> Optional[SkillMetadata]:
        """
        Extract and validate skill metadata

        Args:
            frontmatter: Parsed YAML frontmatter
            content: Body content for fallback extraction

        Returns:
            SkillMetadata or None if validation fails
        """
        # Get required fields
        name = frontmatter.get('name', '').strip()
        description = frontmatter.get('description', '').strip()

        # If name/description not in frontmatter, try to extract from content
        if not name or not description:
            extracted = cls._extract_from_content(content)
            name = name or extracted.get('name', '')
            description = description or extracted.get('description', '')

        # Validate name
        if not name:
            print("Error: Skill name is required")
            return None

        if not cls.NAME_PATTERN.match(name):
            print(f"Error: Invalid skill name '{name}'. Must be lowercase alphanumeric with hyphens")
            return None

        if len(name) > 64:
            print(f"Error: Skill name too long (max 64 chars): {name}")
            return None

        # Validate description
        if not description:
            print("Error: Skill description is required")
            return None

        if len(description) > 1024:
            print(f"Warning: Description truncated to 1024 characters")
            description = description[:1024]

        # Extract triggers
        triggers = frontmatter.get('triggers', [])
        if isinstance(triggers, str):
            triggers = [t.strip() for t in triggers.split(',')]

        # Build metadata object
        return SkillMetadata(
            name=name,
            description=description,
            license=frontmatter.get('license'),
            compatibility=frontmatter.get('compatibility'),
            metadata=frontmatter.get('metadata', {}),
            triggers=triggers,
            version=frontmatter.get('version'),
            author=frontmatter.get('author'),
            dependencies=frontmatter.get('dependencies', []),
        )

    @classmethod
    def _extract_from_content(cls, content: str) -> Dict[str, str]:
        """
        Fallback: Extract name and description from markdown content
        Useful for AGENTS.md files without frontmatter

        Args:
            content: Markdown content

        Returns:
            Dictionary with extracted name and description
        """
        result = {}

        # Try to find first H1 or H2 heading as name
        heading_match = re.search(r'^#{1,2}\s+(.+?)$', content, re.MULTILINE)
        if heading_match:
            result['name'] = cls._normalize_name(heading_match.group(1).strip())

        # Try to find first paragraph as description
        # Skip headings and find first substantial text block
        lines = content.split('\n')
        desc_lines = []
        in_description = False

        for line in lines:
            line = line.strip()
            if not line or line.startswith('#'):
                if desc_lines:
                    break
                continue
            if not line.startswith('**') and not line.startswith('*'):
                in_description = True
                desc_lines.append(line)
                if len(' '.join(desc_lines)) > 200:
                    break

        if desc_lines:
            result['description'] = ' '.join(desc_lines)

        return result

    @classmethod
    def _normalize_name(cls, name: str) -> str:
        """
        Normalize a name to match the required pattern

        Args:
            name: Raw name string

        Returns:
            Normalized name (lowercase with hyphens)
        """
        # Convert to lowercase and replace spaces/underscores with hyphens
        normalized = name.lower()
        normalized = re.sub(r'[_\s]+', '-', normalized)
        # Remove any characters that aren't alphanumeric or hyphens
        normalized = re.sub(r'[^a-z0-9-]', '', normalized)
        # Remove multiple consecutive hyphens
        normalized = re.sub(r'-+', '-', normalized)
        # Remove leading/trailing hyphens
        normalized = normalized.strip('-')
        return normalized

    @classmethod
    def parse_agents_md(cls, file_path: Path) -> List[Skill]:
        """
        Parse an AGENTS.md file that may contain multiple skill definitions

        Args:
            file_path: Path to AGENTS.md file

        Returns:
            List of Skill objects
        """
        if not file_path.exists():
            return []

        try:
            content = file_path.read_text(encoding='utf-8')
            return cls.parse_multiple_skills(content, file_path)
        except Exception as e:
            print(f"Error parsing AGENTS.md: {e}")
            return []

    @classmethod
    def parse_multiple_skills(cls, content: str, file_path: Optional[Path] = None) -> List[Skill]:
        """
        Parse content that may contain multiple skill definitions
        Split by H2 headers (##) as skill boundaries

        Args:
            content: File content
            file_path: Optional source file path

        Returns:
            List of Skill objects
        """
        skills = []

        # Split by H2 headers
        sections = re.split(r'\n##\s+', content)

        # First section might be a header/intro - try to parse it
        if sections and not sections[0].strip().startswith('##'):
            intro = sections[0].strip()
            if intro and not intro.startswith('#'):
                # Could be a single skill with H1
                skill = cls.parse_content(intro, file_path)
                if skill:
                    skills.append(skill)
            sections = sections[1:]

        # Parse each section as a skill
        for section in sections:
            # Add back the H2 marker
            section_content = '## ' + section

            # Extract skill name from H2
            match = re.match(r'^##\s+(.+?)$', section_content, re.MULTILINE)
            if not match:
                continue

            skill_name = cls._normalize_name(match.group(1).strip())

            # Extract description and triggers
            description = ""
            triggers = []

            # Split into lines for parsing
            lines = section_content.split('\n')[1:]  # Skip H2

            desc_lines = []
            for line in lines:
                line = line.strip()
                if not line:
                    continue

                # Check for triggers
                if line.startswith('**Triggers:**'):
                    trigger_text = line.replace('**Triggers:**', '').strip()
                    triggers = [t.strip() for t in trigger_text.split(',')]
                elif not desc_lines and not line.startswith('**'):
                    desc_lines.append(line)

            description = ' '.join(desc_lines) if desc_lines else skill_name

            # Create skill metadata
            metadata = SkillMetadata(
                name=skill_name,
                description=description,
                triggers=triggers
            )

            skill = Skill(
                metadata=metadata,
                content=section_content.strip(),
                file_path=file_path
            )

            skills.append(skill)

        return skills
