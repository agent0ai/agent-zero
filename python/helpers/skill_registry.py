"""
Skill Registry - Discovery, caching, and lazy-loading for Agent Skills
Compatible with skilz, n-skills, and OpenSkills marketplaces
"""

import os
from pathlib import Path
from typing import Dict, List, Optional, Set
from dataclasses import dataclass, field
import json
from datetime import datetime

from python.helpers.agents_md_parser import AgentsMdParser, Skill, SkillMetadata
from python.helpers import files


@dataclass
class SkillLocation:
    """Location metadata for a discovered skill"""
    name: str
    path: Path
    source: str  # "global", "project", "agent", "manifest"
    priority: int  # Higher priority = loaded first
    last_modified: Optional[datetime] = None

    def to_dict(self) -> Dict:
        return {
            "name": self.name,
            "path": str(self.path),
            "source": self.source,
            "priority": self.priority,
            "last_modified": self.last_modified.isoformat() if self.last_modified else None,
        }


class SkillRegistry:
    """
    Central registry for Agent Skills with lazy-loading support
    Discovers skills from multiple locations following the standard hierarchy
    """

    # Discovery paths (in priority order)
    SKILL_PATHS = [
        # Project-local (highest priority)
        ".agent-zero/skills",
        ".opencode/skills",
        ".claude/skills",

        # Global config paths
        "~/.config/agent-zero/skills",
        "~/.config/opencode/skills",
        "~/.config/claude/skills",

        # Alternative global paths
        "~/.agent-zero/skills",
    ]

    def __init__(self, project_root: Optional[Path] = None):
        """
        Initialize the skill registry

        Args:
            project_root: Root directory for project-local skills (defaults to CWD)
        """
        self.project_root = project_root or Path.cwd()

        # Registry state
        self._skill_locations: Dict[str, List[SkillLocation]] = {}  # name -> [locations]
        self._loaded_skills: Dict[str, Skill] = {}  # name -> Skill object
        self._triggers_map: Dict[str, Set[str]] = {}  # trigger -> {skill_names}

        # Discovery cache
        self._discovery_complete = False
        self._last_discovery: Optional[datetime] = None

    def discover_skills(self, force_refresh: bool = False) -> List[SkillLocation]:
        """
        Discover all available skills from configured paths

        Args:
            force_refresh: Force rediscovery even if already done

        Returns:
            List of discovered skill locations
        """
        if self._discovery_complete and not force_refresh:
            return self._get_all_locations()

        self._skill_locations.clear()
        self._triggers_map.clear()

        # Discover from each path in priority order
        priority = len(self.SKILL_PATHS)

        for path_template in self.SKILL_PATHS:
            # Resolve path
            if path_template.startswith("~"):
                skill_path = Path(path_template).expanduser()
                source = "global"
            else:
                skill_path = self.project_root / path_template
                source = "project"

            # Check if path exists
            if not skill_path.exists():
                priority -= 1
                continue

            # Discover skills in this path
            discovered = self._discover_in_path(skill_path, source, priority)

            priority -= 1

        # Discover from AGENTS.md manifest
        self._discover_from_manifest()

        self._discovery_complete = True
        self._last_discovery = datetime.now()

        return self._get_all_locations()

    def _discover_in_path(self, base_path: Path, source: str, priority: int) -> List[SkillLocation]:
        """
        Discover skills in a specific directory

        Args:
            base_path: Directory to search
            source: Source type (global/project)
            priority: Priority level

        Returns:
            List of discovered locations
        """
        discovered = []

        if not base_path.is_dir():
            return discovered

        # Look for SKILL.md files in subdirectories
        for skill_dir in base_path.iterdir():
            if not skill_dir.is_dir():
                continue

            skill_file = skill_dir / "SKILL.md"
            if not skill_file.exists():
                # Also check for lowercase
                skill_file = skill_dir / "skill.md"
                if not skill_file.exists():
                    continue

            # Get skill name (directory name or from file)
            skill_name = skill_dir.name

            # Get last modified time
            last_modified = datetime.fromtimestamp(skill_file.stat().st_mtime)

            # Create location entry
            location = SkillLocation(
                name=skill_name,
                path=skill_file,
                source=source,
                priority=priority,
                last_modified=last_modified,
            )

            # Add to registry
            if skill_name not in self._skill_locations:
                self._skill_locations[skill_name] = []

            self._skill_locations[skill_name].append(location)
            discovered.append(location)

        return discovered

    def _discover_from_manifest(self):
        """
        Discover skills from AGENTS.md manifest file
        """
        # Check for AGENTS.md in project root
        agents_md = self.project_root / "AGENTS.md"

        if not agents_md.exists():
            return

        # Parse AGENTS.md
        skills = AgentsMdParser.parse_agents_md(agents_md)

        for skill in skills:
            skill_name = skill.metadata.name

            # Create location entry
            location = SkillLocation(
                name=skill_name,
                path=agents_md,
                source="manifest",
                priority=5,  # Medium priority
                last_modified=datetime.fromtimestamp(agents_md.stat().st_mtime),
            )

            # Add to registry
            if skill_name not in self._skill_locations:
                self._skill_locations[skill_name] = []

            self._skill_locations[skill_name].append(location)

            # Pre-load skills from manifest (they're already parsed)
            self._loaded_skills[skill_name] = skill

            # Build triggers map
            for trigger in skill.metadata.triggers:
                if trigger not in self._triggers_map:
                    self._triggers_map[trigger] = set()
                self._triggers_map[trigger].add(skill_name)

    def get_skill(self, name: str, force_reload: bool = False) -> Optional[Skill]:
        """
        Get a skill by name (lazy-loads if needed)

        Args:
            name: Skill name
            force_reload: Force reload from disk

        Returns:
            Skill object or None if not found
        """
        # Ensure discovery has been done
        if not self._discovery_complete:
            self.discover_skills()

        # Check if already loaded
        if name in self._loaded_skills and not force_reload:
            return self._loaded_skills[name]

        # Get skill locations
        locations = self._skill_locations.get(name)
        if not locations:
            return None

        # Sort by priority (highest first)
        locations.sort(key=lambda loc: loc.priority, reverse=True)

        # Try to load from highest priority location
        for location in locations:
            skill = self._load_skill(location)
            if skill:
                # Cache the loaded skill
                self._loaded_skills[name] = skill

                # Build triggers map
                for trigger in skill.metadata.triggers:
                    if trigger not in self._triggers_map:
                        self._triggers_map[trigger] = set()
                    self._triggers_map[trigger].add(name)

                return skill

        return None

    def _load_skill(self, location: SkillLocation) -> Optional[Skill]:
        """
        Load a skill from a location

        Args:
            location: Skill location metadata

        Returns:
            Skill object or None if loading fails
        """
        try:
            if location.source == "manifest":
                # Already loaded from AGENTS.md
                return self._loaded_skills.get(location.name)

            # Parse SKILL.md file
            skill = AgentsMdParser.parse_file(location.path)
            return skill

        except Exception as e:
            print(f"Error loading skill '{location.name}' from {location.path}: {e}")
            return None

    def get_skills_by_trigger(self, trigger: str) -> List[Skill]:
        """
        Get all skills that match a trigger keyword

        Args:
            trigger: Trigger keyword

        Returns:
            List of matching skills (lazy-loaded)
        """
        # Ensure discovery has been done
        if not self._discovery_complete:
            self.discover_skills()

        # Get skill names for this trigger
        skill_names = self._triggers_map.get(trigger.lower(), set())

        # Load and return skills
        skills = []
        for name in skill_names:
            skill = self.get_skill(name)
            if skill:
                skills.append(skill)

        return skills

    def list_available_skills(self) -> List[Dict]:
        """
        List all available skills with metadata (discovery only, no loading)

        Returns:
            List of skill metadata dictionaries
        """
        # Ensure discovery has been done
        if not self._discovery_complete:
            self.discover_skills()

        skills_list = []

        for name, locations in self._skill_locations.items():
            # Get highest priority location
            location = max(locations, key=lambda loc: loc.priority)

            # Try to get metadata without full loading
            if name in self._loaded_skills:
                skill = self._loaded_skills[name]
                metadata = skill.metadata.to_dict()
            else:
                # Quick metadata extraction
                metadata = self._get_quick_metadata(location)

            metadata["source"] = location.source
            metadata["priority"] = location.priority
            metadata["path"] = str(location.path)

            skills_list.append(metadata)

        return skills_list

    def _get_quick_metadata(self, location: SkillLocation) -> Dict:
        """
        Quickly extract metadata without full parsing

        Args:
            location: Skill location

        Returns:
            Partial metadata dictionary
        """
        try:
            if location.source == "manifest":
                skill = self._loaded_skills.get(location.name)
                if skill:
                    return skill.metadata.to_dict()

            # Read first few lines to get name and description
            with open(location.path, 'r', encoding='utf-8') as f:
                content = f.read(2000)  # First 2000 chars

            # Quick parse
            skill = AgentsMdParser.parse_content(content, location.path)
            if skill:
                return skill.metadata.to_dict()

        except Exception:
            pass

        # Fallback
        return {
            "name": location.name,
            "description": f"Skill: {location.name}",
            "triggers": [],
        }

    def _get_all_locations(self) -> List[SkillLocation]:
        """Get all discovered skill locations"""
        locations = []
        for locs in self._skill_locations.values():
            locations.extend(locs)
        return locations

    def search_skills(self, query: str) -> List[Dict]:
        """
        Search skills by name, description, or triggers

        Args:
            query: Search query

        Returns:
            List of matching skill metadata
        """
        query_lower = query.lower()
        results = []

        all_skills = self.list_available_skills()

        for skill_meta in all_skills:
            # Search in name
            if query_lower in skill_meta['name'].lower():
                results.append(skill_meta)
                continue

            # Search in description
            if query_lower in skill_meta['description'].lower():
                results.append(skill_meta)
                continue

            # Search in triggers
            triggers = skill_meta.get('triggers', [])
            if any(query_lower in trigger.lower() for trigger in triggers):
                results.append(skill_meta)
                continue

        return results

    def get_skill_content(self, name: str) -> Optional[str]:
        """
        Get the full content of a skill

        Args:
            name: Skill name

        Returns:
            Skill content or None
        """
        skill = self.get_skill(name)
        return skill.content if skill else None

    def refresh(self):
        """Force refresh of skill discovery"""
        self.discover_skills(force_refresh=True)

    def get_stats(self) -> Dict:
        """
        Get registry statistics

        Returns:
            Statistics dictionary
        """
        if not self._discovery_complete:
            self.discover_skills()

        return {
            "total_skills": len(self._skill_locations),
            "loaded_skills": len(self._loaded_skills),
            "triggers_registered": len(self._triggers_map),
            "last_discovery": self._last_discovery.isoformat() if self._last_discovery else None,
            "sources": self._get_source_counts(),
        }

    def _get_source_counts(self) -> Dict[str, int]:
        """Get count of skills per source"""
        counts = {}
        for locations in self._skill_locations.values():
            for location in locations:
                source = location.source
                counts[source] = counts.get(source, 0) + 1
        return counts


# Global registry instance
_global_registry: Optional[SkillRegistry] = None


def get_registry(project_root: Optional[Path] = None) -> SkillRegistry:
    """
    Get the global skill registry instance

    Args:
        project_root: Optional project root (defaults to CWD)

    Returns:
        Global SkillRegistry instance
    """
    global _global_registry

    if _global_registry is None:
        _global_registry = SkillRegistry(project_root)

    return _global_registry


def discover_skills(force_refresh: bool = False) -> List[SkillLocation]:
    """
    Convenience function to discover skills

    Args:
        force_refresh: Force rediscovery

    Returns:
        List of skill locations
    """
    registry = get_registry()
    return registry.discover_skills(force_refresh)


def get_skill(name: str) -> Optional[Skill]:
    """
    Convenience function to get a skill

    Args:
        name: Skill name

    Returns:
        Skill object or None
    """
    registry = get_registry()
    return registry.get_skill(name)
