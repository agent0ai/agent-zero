#!/usr/bin/env python3
"""Initialize a new skill directory with SKILL.md and optional resources."""

from __future__ import annotations

import argparse
import re
from pathlib import Path

SKILL_TEMPLATE = """---\nname: {name}\ndescription: TODO - describe when to use this skill and its purpose in one line\n---\n\n# {title}\n\n## Overview\n\n- TODO: Explain core workflow and assumptions\n\n## Resources\n\n- TODO: Reference scripts/, references/, and assets/ as needed\n"""


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Initialize a new skill directory")
    parser.add_argument("skill_name", help="Skill name (lowercase, digits, hyphens)")
    parser.add_argument("--path", default="skills", help="Output directory for skill")
    parser.add_argument(
        "--resources",
        default="",
        help="Comma-separated resource directories to create: scripts,references,assets",
    )
    parser.add_argument(
        "--examples",
        action="store_true",
        help="Create placeholder example files in resource folders",
    )
    return parser.parse_args()


def validate_name(name: str) -> None:
    if not re.fullmatch(r"[a-z0-9-]+", name or ""):
        raise ValueError("Skill name must use lowercase letters, digits, and hyphens")


def create_skill_dir(base_path: Path, name: str, resources: list[str], examples: bool) -> None:
    skill_dir = base_path / name
    if skill_dir.exists():
        raise FileExistsError(f"Skill directory already exists: {skill_dir}")

    skill_dir.mkdir(parents=True)

    skill_md = skill_dir / "SKILL.md"
    skill_md.write_text(
        SKILL_TEMPLATE.format(name=name, title=name.replace("-", " ").title()),
        encoding="utf-8",
    )

    for resource in resources:
        resource_dir = skill_dir / resource
        resource_dir.mkdir(parents=True, exist_ok=True)
        if examples:
            if resource == "scripts":
                (resource_dir / "example.py").write_text(
                    "# TODO: Add scripts for this skill\n",
                    encoding="utf-8",
                )
            elif resource == "references":
                (resource_dir / "example.md").write_text(
                    "# TODO: Add reference material for this skill\n",
                    encoding="utf-8",
                )
            elif resource == "assets":
                (resource_dir / "example.txt").write_text(
                    "Add assets for this skill here.\n",
                    encoding="utf-8",
                )


def main() -> None:
    args = parse_args()
    validate_name(args.skill_name)

    base_path = Path(args.path).expanduser().resolve()
    resources = [r.strip() for r in args.resources.split(",") if r.strip()]

    create_skill_dir(base_path, args.skill_name, resources, args.examples)
    print(f"Skill initialized at {base_path / args.skill_name}")


if __name__ == "__main__":
    main()
