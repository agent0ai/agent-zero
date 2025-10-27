"""
Skills Manager
Singleton class managing Agent Skills lifecycle
"""

from __future__ import annotations
from typing import Any, Optional
from python.helpers.skill_loader import (
    SkillMetadata,
    SkillContent,
    discover_skills,
    parse_skill_file,
    validate_skill_structure
)
from python.helpers.print_style import PrintStyle
from pathlib import Path


class SkillsManager:
    """Singleton manager for Agent Skills"""

    _instance: Optional['SkillsManager'] = None

    def __init__(self):
        """Private constructor - use get_instance()"""
        if SkillsManager._instance is not None:
            raise RuntimeError("Use SkillsManager.get_instance()")

        self._skills_metadata: dict[str, SkillMetadata] = {}
        self._loaded_skills: dict[str, SkillContent] = {}
        self._usage_stats: dict[str, int] = {}

    @staticmethod
    def get_instance() -> 'SkillsManager':
        """Get singleton instance"""
        if SkillsManager._instance is None:
            SkillsManager._instance = SkillsManager()
        return SkillsManager._instance

    def discover_skills(self, skills_dirs: list[str]) -> dict[str, SkillMetadata]:
        """
        Discover and register skills from directories

        Args:
            skills_dirs: List of absolute paths to search

        Returns:
            Dictionary of discovered skills
        """
        self._skills_metadata = discover_skills(skills_dirs)
        PrintStyle().print(f"Discovered {len(self._skills_metadata)} skills")
        return self._skills_metadata

    def get_skill_metadata(self, skill_name: str) -> Optional[SkillMetadata]:
        """Get skill metadata by name"""
        return self._skills_metadata.get(skill_name)

    def get_all_metadata(self) -> dict[str, SkillMetadata]:
        """Get all skill metadata"""
        return self._skills_metadata.copy()

    def load_skill_content(self, skill_name: str) -> Optional[SkillContent]:
        """
        Load full skill content

        Args:
            skill_name: Name of skill to load

        Returns:
            SkillContent or None if not found
        """
        # Check cache first
        if skill_name in self._loaded_skills:
            return self._loaded_skills[skill_name]

        # Get metadata
        metadata = self._skills_metadata.get(skill_name)
        if not metadata or not metadata.skill_dir:
            PrintStyle().error(f"Skill '{skill_name}' not found")
            return None

        # Load from file
        skill_file = Path(metadata.skill_dir) / "SKILL.md"
        try:
            content = parse_skill_file(str(skill_file))
            self._loaded_skills[skill_name] = content

            # Track usage
            self._usage_stats[skill_name] = self._usage_stats.get(skill_name, 0) + 1

            return content
        except Exception as e:
            PrintStyle().error(f"Error loading skill '{skill_name}': {e}")
            return None

    def get_skill_file(self, skill_name: str, file_path: str) -> Optional[str]:
        """
        Read a referenced file from skill directory

        Args:
            skill_name: Name of skill
            file_path: Relative path to file within skill directory

        Returns:
            File content or None if not found
        """
        metadata = self._skills_metadata.get(skill_name)
        if not metadata or not metadata.skill_dir:
            return None

        # Validate file path (security: no directory traversal)
        if '..' in file_path or file_path.startswith('/'):
            PrintStyle().error(f"Invalid file path: {file_path}")
            return None

        full_path = Path(metadata.skill_dir) / file_path

        # Ensure file is within skill directory
        try:
            full_path = full_path.resolve()
            skill_dir_resolved = Path(metadata.skill_dir).resolve()
            if not str(full_path).startswith(str(skill_dir_resolved)):
                PrintStyle().error(f"File path outside skill directory: {file_path}")
                return None
        except Exception as e:
            PrintStyle().error(f"Error resolving path: {e}")
            return None

        # Read file
        if not full_path.exists():
            PrintStyle().error(f"File not found: {file_path}")
            return None

        try:
            with open(full_path, 'r', encoding='utf-8') as f:
                return f.read()
        except Exception as e:
            PrintStyle().error(f"Error reading file: {e}")
            return None

    def refresh_skills(self, skills_dirs: list[str]) -> None:
        """Refresh skill discovery and clear cache"""
        self._loaded_skills.clear()
        self.discover_skills(skills_dirs)

    def get_usage_stats(self) -> dict[str, int]:
        """Get skill usage statistics"""
        return self._usage_stats.copy()
