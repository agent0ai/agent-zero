#!/usr/bin/env python3
"""
Skills CLI - Easy skill management for Agent Zero

Usage:
    python -m helpers.skills_cli list              List all skills
    python -m helpers.skills_cli create <name>     Create a new skill
    python -m helpers.skills_cli show <name>       Show skill details
    python -m helpers.skills_cli validate <name>   Validate a skill
    python -m helpers.skills_cli search <query>    Search skills
"""

import argparse
import sys
from pathlib import Path

from helpers import files, skills as skills_runtime


Skill = skills_runtime.Skill


def get_skills_dirs() -> list[Path]:
    """Get all skill directories"""
    return [Path(root) for root in skills_runtime.get_skill_roots()]


def parse_skill_file(skill_path: Path) -> Skill | None:
    """Parse a SKILL.md file and return a Skill object"""
    return skills_runtime.skill_from_markdown(
        skill_path,
        include_content=True,
        validate=False,
    )


def list_skills() -> list[Skill]:
    """List all available skills"""
    return skills_runtime.list_skills(include_content=True)


def find_skill(name: str) -> Skill | None:
    """Find a skill by name"""
    return skills_runtime.find_skill(name, include_content=True, validate=False)


def search_skills(query: str) -> list[Skill]:
    """Search skills by name, description, or tags"""
    return skills_runtime.search_skills(query)


def validate_skill(skill: Skill) -> list[str]:
    """Validate a skill and return list of issues"""
    return skills_runtime.validate_skill(skill)


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
description: "{description or 'Description of what this skill does and when to use it'}"
version: "1.0.0"
author: "{author or 'Your Name'}"
tags: ["custom"]
triggers:
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


def print_skill_table(skills: list[Skill]):
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
        """
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
            skills = [s for s in skills if any(t in [tag.lower() for tag in s.tags] for t in filter_tags)]
        print_skill_table(skills)

    elif args.command == "create":
        try:
            skill_dir = create_skill(args.name, args.description, args.author)
            print(f"\n✅ Created skill at: {skill_dir}")
            print(f"\nNext steps:")
            print(f"  1. Edit {skill_dir / 'SKILL.md'} to add your instructions")
            print(f"  2. Add any helper scripts to {skill_dir / 'scripts'}/")
            print(f"  3. Run: python -m helpers.skills_cli validate {args.name}")
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
            print(f"Triggers:    {', '.join(skill.triggers) if skill.triggers else 'None'}")
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
