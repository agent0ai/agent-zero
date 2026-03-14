"""Central skill registry: manifest dataclass, CRUD, search, dependency checks."""

from __future__ import annotations

import contextlib
import os
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Literal

from python.helpers.skill_md_parser import parse_skill_md_file


@dataclass
class SkillManifest:
    """Describes a single installed (or discovered) skill."""

    name: str
    version: str
    author: str
    tier: Literal[1, 2]  # 1 = Markdown (SKILL.md), 2 = Python module
    trust_level: Literal["builtin", "verified", "community", "local"]
    categories: list[str] = field(default_factory=list)
    dependencies: list[str] = field(default_factory=list)
    capabilities: list[str] = field(default_factory=list)
    path: Path = field(default_factory=lambda: Path("."))
    enabled: bool = True
    installed_at: datetime | None = None
    description: str = ""

    # --- serialisation helpers ---------------------------------------------------

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "version": self.version,
            "author": self.author,
            "tier": self.tier,
            "trust_level": self.trust_level,
            "categories": self.categories,
            "dependencies": self.dependencies,
            "capabilities": self.capabilities,
            "path": str(self.path),
            "enabled": self.enabled,
            "installed_at": self.installed_at.isoformat() if self.installed_at else None,
            "description": self.description,
        }


def _manifest_from_frontmatter(fm: dict, path: Path) -> SkillManifest | None:
    """Build a SkillManifest from parsed YAML frontmatter.  Returns None when
    required fields (name, version, author) are missing."""
    name = fm.get("name")
    version = fm.get("version")
    author = fm.get("author")
    if not name or not version or not author:
        return None

    tier_raw = fm.get("tier", 1)
    tier: Literal[1, 2] = 2 if tier_raw == 2 else 1

    trust_raw = fm.get("trust_level", "community")
    valid_trust = {"builtin", "verified", "community", "local"}
    trust_level: Literal["builtin", "verified", "community", "local"] = (
        trust_raw if trust_raw in valid_trust else "community"
    )

    categories = fm.get("categories", [])
    if isinstance(categories, str):
        categories = [c.strip() for c in categories.split(",")]

    dependencies = fm.get("dependencies", [])
    if isinstance(dependencies, str):
        dependencies = [d.strip() for d in dependencies.split(",")]

    capabilities = fm.get("capabilities", [])
    if isinstance(capabilities, str):
        capabilities = [c.strip() for c in capabilities.split(",")]

    return SkillManifest(
        name=name,
        version=str(version),
        author=author,
        tier=tier,
        trust_level=trust_level,
        categories=categories,
        dependencies=dependencies,
        capabilities=capabilities,
        path=path,
        enabled=fm.get("enabled", True),
        installed_at=datetime.now(timezone.utc),
        description=fm.get("description", ""),
    )


class SkillRegistry:
    """In-memory registry of discovered / installed skills."""

    def __init__(self) -> None:
        self._skills: dict[str, SkillManifest] = {}

    # -- discovery ----------------------------------------------------------------

    def scan_directory(self, path: Path) -> list[SkillManifest]:
        """Walk *path* looking for ``SKILL.md`` files and register each one."""
        discovered: list[SkillManifest] = []
        root = Path(path)
        if not root.is_dir():
            return discovered

        for entry in sorted(os.listdir(root)):
            skill_dir = root / entry
            skill_md = skill_dir / "SKILL.md"
            if skill_md.is_file():
                try:
                    fm, _body = parse_skill_md_file(str(skill_md))
                    manifest = _manifest_from_frontmatter(fm, skill_dir)
                    if manifest is not None:
                        self._skills[manifest.name] = manifest
                        discovered.append(manifest)
                except Exception:
                    continue

            # Also look for tier-2 Python modules with a manifest dict
            init_py = skill_dir / "__init__.py"
            if init_py.is_file() and not skill_md.is_file():
                # Tier-2 skills without SKILL.md are discovered but need
                # explicit install via the loader.
                pass

        return discovered

    # -- CRUD ---------------------------------------------------------------------

    def install(self, manifest: SkillManifest) -> None:
        if manifest.installed_at is None:
            manifest.installed_at = datetime.now(timezone.utc)
        self._skills[manifest.name] = manifest

    def uninstall(self, name: str) -> None:
        self._skills.pop(name, None)

    def enable(self, name: str) -> None:
        skill = self._skills.get(name)
        if skill:
            skill.enabled = True

    def disable(self, name: str) -> None:
        skill = self._skills.get(name)
        if skill:
            skill.enabled = False

    def get(self, name: str) -> SkillManifest | None:
        return self._skills.get(name)

    def list(self, category: str | None = None) -> list[SkillManifest]:
        skills = list(self._skills.values())
        if category:
            skills = [s for s in skills if category in s.categories]
        return skills

    def search(self, query: str) -> list[SkillManifest]:
        """Simple case-insensitive substring search across name, description,
        categories and capabilities."""
        q = query.lower()
        results: list[SkillManifest] = []
        for skill in self._skills.values():
            haystack = " ".join(
                [
                    skill.name,
                    skill.description,
                    " ".join(skill.categories),
                    " ".join(skill.capabilities),
                ]
            ).lower()
            if q in haystack:
                results.append(skill)
        return results

    # -- dependency checking ------------------------------------------------------

    def check_dependencies(self, manifest: SkillManifest) -> list[str]:
        """Return a list of dependency names that are NOT currently installed /
        registered."""
        missing: list[str] = []
        for dep in manifest.dependencies:
            if dep not in self._skills:
                missing.append(dep)
        return missing


# Module-level singleton so other parts of the codebase can import it directly.
_global_registry: SkillRegistry | None = None
_auto_scanned = False


def get_registry() -> SkillRegistry:
    global _global_registry, _auto_scanned
    if _global_registry is None:
        _global_registry = SkillRegistry()
    if not _auto_scanned:
        # One-time lazy discovery so API endpoints (skills_list/skills_get)
        # can see local skills without requiring an explicit install call.
        candidate_dirs: list[Path] = []
        env_dir = os.getenv("A0_SKILLS_DIR", "").strip()
        if env_dir:
            candidate_dirs.append(Path(env_dir))
        candidate_dirs.extend([Path("skills"), Path("/a0/skills")])
        for skills_dir in candidate_dirs:
            with contextlib.suppress(Exception):
                _global_registry.scan_directory(skills_dir)
        _auto_scanned = True
    return _global_registry
