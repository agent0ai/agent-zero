#!/usr/bin/env python3
"""
Skills CLI - Easy skill management for Agent Zero

Usage:
    python -m python.helpers.skills_cli list              List all skills
    python -m python.helpers.skills_cli create <name>     Create a new skill
    python -m python.helpers.skills_cli show <name>       Show skill details
    python -m python.helpers.skills_cli validate <name>   Validate a skill
    python -m python.helpers.skills_cli search <query>    Search skills
"""

import argparse
import os
import re
import sys
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

import yaml

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from python.helpers import files


@dataclass
class Skill:
    """Represents a skill loaded from SKILL.md"""

    name: str
    description: str
    path: Path
    version: str = "1.0.0"
    author: str = ""
    tags: List[str] = field(default_factory=list)
    trigger_patterns: List[str] = field(default_factory=list)
    content: str = ""


def get_skills_dirs() -> List[Path]:
    """Get all skill directories"""
    base = Path(files.get_abs_path("usr", "skills"))
    return [
        base / "custom",
        base / "default",
    ]


def parse_skill_file(skill_path: Path) -> Optional[Skill]:
    """Parse a SKILL.md file and return a Skill object"""
    try:
        content = skill_path.read_text(encoding="utf-8")

        # Parse YAML frontmatter
        if content.startswith("---"):
            parts = content.split("---", 2)
            if len(parts) >= 3:
                frontmatter = yaml.safe_load(parts[1])
                body = parts[2].strip()

                return Skill(
                    name=frontmatter.get("name", skill_path.parent.name),
                    description=frontmatter.get("description", ""),
                    path=skill_path.parent,
                    version=frontmatter.get("version", "1.0.0"),
                    author=frontmatter.get("author", ""),
                    tags=frontmatter.get("tags", []),
                    trigger_patterns=frontmatter.get("trigger_patterns", []),
                    content=body,
                )

        return None
    except Exception as e:
        print(f"Error parsing {skill_path}: {e}")
        return None


def list_skills() -> List[Skill]:
    """List all available skills"""
    skills = []
    for skills_dir in get_skills_dirs():
        if not skills_dir.exists():
            continue
        for skill_dir in skills_dir.iterdir():
            if skill_dir.is_dir():
                skill_file = skill_dir / "SKILL.md"
                if skill_file.exists():
                    skill = parse_skill_file(skill_file)
                    if skill:
                        skills.append(skill)
    return skills


def find_skill(name: str) -> Optional[Skill]:
    """Find a skill by name"""
    for skill in list_skills():
        if skill.name == name or skill.path.name == name:
            return skill
    return None


def search_skills(query: str) -> List[Skill]:
    """Search skills by name, description, or tags"""
    query = query.lower()
    results = []
    for skill in list_skills():
        if (
            query in skill.name.lower()
            or query in skill.description.lower()
            or any(query in tag.lower() for tag in skill.tags)
            or any(query in trigger.lower() for trigger in skill.trigger_patterns)
        ):
            results.append(skill)
    return results


def validate_skill(skill: Skill) -> List[str]:
    """Validate a skill and return list of issues"""
    issues = []

    # Required fields
    if not skill.name:
        issues.append("Missing required field: name")
    if not skill.description:
        issues.append("Missing required field: description")

    # Name format
    if skill.name:
        if not (1 <= len(skill.name) <= 64):
            issues.append("Name must be 1-64 characters")
        if not re.match(r"^[a-z0-9-]+$", skill.name):
            issues.append(
                f"Invalid name format: '{skill.name}' (use lowercase letters, numbers, and hyphens)"
            )
        if skill.name.startswith("-") or skill.name.endswith("-"):
            issues.append("Name must not start or end with a hyphen")
        if "--" in skill.name:
            issues.append("Name must not contain consecutive hyphens")

    # Description length
    if skill.description and len(skill.description) < 20:
        issues.append("Description is too short (minimum 20 characters)")

    # Content
    if len(skill.content) < 100:
        issues.append("Skill content is too short (minimum 100 characters)")

    # Check for associated files
    skill_dir = skill.path
    has_scripts = (skill_dir / "scripts").exists()
    has_docs = (skill_dir / "docs").exists()

    return issues


def create_skill(name: str, description: str = "", author: str = "") -> Path:
    """Create a new skill from template"""
    # Use custom directory for user-created skills
    custom_dir = Path(files.get_abs_path("usr", "skills", "custom"))
    custom_dir.mkdir(parents=True, exist_ok=True)

    skill_dir = custom_dir / name
    if skill_dir.exists():
        raise ValueError(f"Skill '{name}' already exists at {skill_dir}")

    # Create directory structure
    skill_dir.mkdir(parents=True)
    (skill_dir / "scripts").mkdir()
    (skill_dir / "docs").mkdir()

    # Create SKILL.md from template
    skill_content = f'''---
name: "{name}"
description: "{description or "Description of what this skill does and when to use it"}"
version: "1.0.0"
author: "{author or "Your Name"}"
tags: ["custom"]
trigger_patterns:
  - "{name}"
---

# {name.replace("-", " ").replace("_", " ").title()}

## When to Use

Describe when this skill should be activated.

## Instructions

Provide detailed instructions for the agent to follow.

### Step 1: First Step

Description of what to do first.

### Step 2: Second Step

Description of what to do next.

## Examples

**User**: "Example prompt that triggers this skill"

**Agent Response**:
> Example of how the agent should respond

## Tips

- Tip 1: Helpful guidance
- Tip 2: More helpful guidance

## Anti-Patterns

- Don't do this
- Avoid that
'''

    skill_file = skill_dir / "SKILL.md"
    skill_file.write_text(skill_content, encoding="utf-8")

    # Create placeholder README in docs
    readme = skill_dir / "docs" / "README.md"
    readme.write_text(f"# {name}\n\nAdditional documentation for the {name} skill.\n")

    return skill_dir


def print_skill_table(skills: List[Skill]):
    """Print skills in a formatted table"""
    if not skills:
        print("No skills found.")
        return

    # Calculate column widths
    name_width = max(len(s.name) for s in skills) + 2
    desc_width = 50

    # Print header
    print(f"\n{'Name':<{name_width}} {'Version':<10} {'Tags':<20} Description")
    print("-" * (name_width + 80))

    # Print skills
    for skill in skills:
        tags = ", ".join(skill.tags[:3])
        if len(skill.tags) > 3:
            tags += "..."
        desc = skill.description[:desc_width]
        if len(skill.description) > desc_width:
            desc += "..."
        print(f"{skill.name:<{name_width}} {skill.version:<10} {tags:<20} {desc}")

    print(f"\nTotal: {len(skills)} skills")


def main():
    parser = argparse.ArgumentParser(
        description="Agent Zero Skills CLI",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s list                     List all skills
  %(prog)s create my-skill          Create a new skill
  %(prog)s show brainstorming       Show skill details
  %(prog)s validate my-skill        Validate a skill
  %(prog)s search python            Search for skills
        """,
    )

    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # List command
    list_parser = subparsers.add_parser("list", help="List all skills")
    list_parser.add_argument("--tags", help="Filter by tags (comma-separated)")

    # Create command
    create_parser = subparsers.add_parser("create", help="Create a new skill")
    create_parser.add_argument("name", help="Skill name (lowercase, use hyphens)")
    create_parser.add_argument("-d", "--description", help="Skill description")
    create_parser.add_argument("-a", "--author", help="Author name")

    # Show command
    show_parser = subparsers.add_parser("show", help="Show skill details")
    show_parser.add_argument("name", help="Skill name")

    # Validate command
    validate_parser = subparsers.add_parser("validate", help="Validate a skill")
    validate_parser.add_argument("name", help="Skill name")

    # Search command
    search_parser = subparsers.add_parser("search", help="Search skills")
    search_parser.add_argument("query", help="Search query")

    args = parser.parse_args()

    if args.command == "list":
        skills = list_skills()
        if args.tags:
            filter_tags = [t.strip().lower() for t in args.tags.split(",")]
            skills = [
                s
                for s in skills
                if any(t in [tag.lower() for tag in s.tags] for t in filter_tags)
            ]
        print_skill_table(skills)

    elif args.command == "create":
        try:
            skill_dir = create_skill(args.name, args.description, args.author)
            print(f"\n✅ Created skill at: {skill_dir}")
            print(f"\nNext steps:")
            print(f"  1. Edit {skill_dir / 'SKILL.md'} to add your instructions")
            print(f"  2. Add any helper scripts to {skill_dir / 'scripts'}/")
            print(f"  3. Run: python -m python.helpers.skills_cli validate {args.name}")
        except ValueError as e:
            print(f"\n❌ Error: {e}")
            sys.exit(1)

    elif args.command == "show":
        skill = find_skill(args.name)
        if skill:
            print(f"\n{'=' * 60}")
            print(f"Skill: {skill.name}")
            print(f"{'=' * 60}")
            print(f"Version:     {skill.version}")
            print(f"Author:      {skill.author or 'Unknown'}")
            print(f"Path:        {skill.path}")
            print(f"Tags:        {', '.join(skill.tags) if skill.tags else 'None'}")
            print(
                f"Triggers:    {', '.join(skill.trigger_patterns) if skill.trigger_patterns else 'None'}"
            )
            print(f"\nDescription:")
            print(f"  {skill.description}")
            print(f"\nContent Preview (first 500 chars):")
            print("-" * 60)
            print(skill.content[:500])
            if len(skill.content) > 500:
                print("...")
            print("-" * 60)
        else:
            print(f"\n❌ Skill '{args.name}' not found")
            sys.exit(1)

    elif args.command == "validate":
        skill = find_skill(args.name)
        if skill:
            issues = validate_skill(skill)
            if issues:
                print(f"\n⚠️ Validation issues for '{args.name}':")
                for issue in issues:
                    print(f"  - {issue}")
            else:
                print(f"\n✅ Skill '{args.name}' is valid!")
        else:
            print(f"\n❌ Skill '{args.name}' not found")
            sys.exit(1)

    elif args.command == "search":
        results = search_skills(args.query)
        if results:
            print(f"\nSearch results for '{args.query}':")
            print_skill_table(results)
        else:
            print(f"\nNo skills found matching '{args.query}'")

    else:
        parser.print_help()


if __name__ == "__main__":
    main()
