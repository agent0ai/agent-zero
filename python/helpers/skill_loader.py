"""Skill loaders for Tier 1 (SKILL.md) and Tier 2 (Python module) skills."""

from __future__ import annotations

import importlib.util
from pathlib import Path
from typing import TYPE_CHECKING, Any

from python.helpers.skill_md_parser import parse_skill_md_file

if TYPE_CHECKING:
    from python.helpers.skill_registry import SkillManifest

# ---------------------------------------------------------------------------
# Tier 1 – Markdown skills
# ---------------------------------------------------------------------------


def load_tier1(manifest: SkillManifest) -> str:
    """Parse the SKILL.md file and return the markdown body as a system-prompt
    injection string.

    The returned string is intended to be appended to the agent's system
    prompt so that the LLM gains the skill's knowledge / instructions.
    """
    skill_md = Path(manifest.path) / "SKILL.md"
    if not skill_md.is_file():
        raise FileNotFoundError(f"SKILL.md not found at {skill_md}")

    _frontmatter, body = parse_skill_md_file(str(skill_md))

    # Build a labelled prompt section
    header = f"## Skill: {manifest.name} (v{manifest.version})"
    parts = [header]
    if manifest.description:
        parts.append(manifest.description)
    if body:
        parts.append(body)
    return "\n\n".join(parts)


# ---------------------------------------------------------------------------
# Tier 2 – Python module skills
# ---------------------------------------------------------------------------


def load_tier2(manifest: SkillManifest) -> Any:
    """Dynamically import the Python module for a Tier 2 skill and return the
    first ``Tool`` subclass found in it.

    Convention: the skill directory must contain either ``__init__.py`` or a
    single ``.py`` file that exposes a class inheriting from
    ``python.helpers.tool.Tool``.

    Returns the *class* (not an instance).  Returns ``None`` if no suitable
    class is found or if loading fails.
    """
    skill_dir = Path(manifest.path)

    # Determine the module file to load
    init_py = skill_dir / "__init__.py"
    if init_py.is_file():
        module_path = init_py
    else:
        # Fall back to the first .py file in the directory
        py_files = sorted(skill_dir.glob("*.py"))
        if not py_files:
            return None
        module_path = py_files[0]

    try:
        spec = importlib.util.spec_from_file_location(f"skill_{manifest.name}", str(module_path))
        if spec is None or spec.loader is None:
            return None

        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)  # type: ignore[union-attr]
    except Exception:
        return None

    # Find a Tool subclass
    from python.helpers.tool import Tool

    for attr_name in dir(module):
        attr = getattr(module, attr_name)
        if isinstance(attr, type) and issubclass(attr, Tool) and attr is not Tool:
            return attr

    return None
