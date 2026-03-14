"""CLI entry point for Agent Jumbo skill management.

Usage::

    python -m python.cli.skill_cli <command> [options]

Commands:
    list                    List installed skills
    search <query>          Search JumboHub for skills
    install <name|path>     Install a skill from JumboHub or local path
    uninstall <name>        Uninstall a skill
    scan <name|path>        Run security scan on a skill
    package <path>          Create a distributable package
    publish <path>          Publish to JumboHub (requires token)
    info <name>             Show detailed skill information
"""

from __future__ import annotations

import argparse
import asyncio
import sys
from pathlib import Path

# ---------------------------------------------------------------------------
# ANSI helpers
# ---------------------------------------------------------------------------

_BOLD = "\033[1m"
_GREEN = "\033[32m"
_YELLOW = "\033[33m"
_RED = "\033[31m"
_CYAN = "\033[36m"
_RESET = "\033[0m"


def _ok(msg: str) -> str:
    return f"{_GREEN}[OK]{_RESET} {msg}"


def _warn(msg: str) -> str:
    return f"{_YELLOW}[WARN]{_RESET} {msg}"


def _err(msg: str) -> str:
    return f"{_RED}[ERR]{_RESET} {msg}"


def _heading(msg: str) -> str:
    return f"\n{_BOLD}{_CYAN}{msg}{_RESET}"


# ---------------------------------------------------------------------------
# Commands
# ---------------------------------------------------------------------------


def cmd_list(args: argparse.Namespace) -> None:
    from python.helpers.skill_registry import get_registry

    registry = get_registry()
    skills_dir = Path(args.skills_dir)
    registry.scan_directory(skills_dir)
    skills = registry.list()

    if not skills:
        print("No skills installed.")
        return

    print(_heading("Installed Skills"))
    for s in skills:
        status = f"{_GREEN}enabled{_RESET}" if s.enabled else f"{_RED}disabled{_RESET}"
        tier_label = "Tier 1 (Markdown)" if s.tier == 1 else "Tier 2 (Python)"
        print(f"  {_BOLD}{s.name}{_RESET} v{s.version} [{tier_label}] - {status}")
        if s.description:
            desc = s.description[:80] + ("..." if len(s.description) > 80 else "")
            print(f"    {desc}")
    print(f"\n  Total: {len(skills)} skill(s)")


def cmd_search(args: argparse.Namespace) -> None:
    from python.helpers.skill_index import SkillIndex

    index = SkillIndex()
    results = asyncio.run(index.search(args.query))

    if not results:
        print(f"No skills found matching '{args.query}'.")
        return

    print(_heading(f"Search results for '{args.query}'"))
    for entry in results:
        name = entry.get("name", "unknown")
        version = entry.get("version", "?")
        desc = entry.get("description", "")[:80]
        author = entry.get("author", "unknown")
        print(f"  {_BOLD}{name}{_RESET} v{version} by {author}")
        if desc:
            print(f"    {desc}")
    print(f"\n  Found: {len(results)} skill(s)")


def cmd_install(args: argparse.Namespace) -> None:
    from python.helpers.skill_index import SkillIndex
    from python.helpers.skill_packager import SkillPackager
    from python.helpers.skill_registry import get_registry

    target = args.name_or_path
    skills_dir = Path(args.skills_dir)
    packager = SkillPackager()

    local_path = Path(target)
    if local_path.is_dir() and (local_path / "SKILL.md").is_file():
        # Local install: copy to skills dir.
        dest = skills_dir / local_path.name
        if dest.exists():
            print(_warn(f"Skill directory already exists: {dest}"))
            return
        import shutil

        shutil.copytree(str(local_path), str(dest))
        print(_ok(f"Installed '{local_path.name}' from local path."))
    elif local_path.is_file() and local_path.suffix == ".gz":
        # Install from a local .tar.gz package.
        packager.extract(local_path, skills_dir)
        print(_ok(f"Extracted and installed from {local_path}."))
    else:
        # Install from JumboHub.
        index = SkillIndex()
        try:
            pkg_path = asyncio.run(index.fetch(target))
            packager.extract(pkg_path, skills_dir)
            print(_ok(f"Installed '{target}' from JumboHub."))
        except (LookupError, ConnectionError, ValueError) as exc:
            print(_err(str(exc)))
            sys.exit(1)

    # Re-scan to register.
    registry = get_registry()
    registry.scan_directory(skills_dir)


def cmd_uninstall(args: argparse.Namespace) -> None:
    import shutil

    from python.helpers.skill_registry import get_registry

    registry = get_registry()
    skills_dir = Path(args.skills_dir)
    registry.scan_directory(skills_dir)

    skill = registry.get(args.name)
    if skill is None:
        print(_err(f"Skill '{args.name}' is not installed."))
        sys.exit(1)

    skill_path = Path(skill.path)
    if skill_path.is_dir():
        shutil.rmtree(skill_path)

    registry.uninstall(args.name)
    print(_ok(f"Uninstalled '{args.name}'."))


def cmd_scan(args: argparse.Namespace) -> None:
    from python.helpers.skill_registry import SkillManifest, get_registry
    from python.helpers.skill_scanner import scan_skill

    target = Path(args.name_or_path)
    registry = get_registry()

    if target.is_dir():
        # Scan a directory directly by building a minimal manifest.
        manifest = SkillManifest(
            name=target.name,
            version="0.0.0",
            author="unknown",
            tier=1,
            trust_level="local",
            path=target,
        )
    else:
        # Look up by name in the registry.
        skills_dir = Path(args.skills_dir)
        registry.scan_directory(skills_dir)
        manifest = registry.get(args.name_or_path)
        if manifest is None:
            print(_err(f"Skill '{args.name_or_path}' not found."))
            sys.exit(1)

    result = scan_skill(manifest)

    print(_heading(f"Security Scan: {result.skill_name}"))
    if result.passed:
        print(f"  {_GREEN}PASSED{_RESET} - No critical or high findings.")
    else:
        print(f"  {_RED}FAILED{_RESET} - Issues found.")

    if result.findings:
        for f in result.findings:
            sev = f.severity.value.upper()
            color = _RED if sev in ("HIGH", "CRITICAL") else _YELLOW
            loc = f" ({f.file}:{f.line})" if f.file else ""
            print(f"  {color}[{sev}]{_RESET} {f.category}: {f.message}{loc}")
    else:
        print("  No findings.")


def cmd_package(args: argparse.Namespace) -> None:
    from python.helpers.skill_packager import SkillPackager

    skill_dir = Path(args.path)
    packager = SkillPackager()

    try:
        output = args.output if args.output else None
        pkg_path = packager.package(skill_dir, Path(output) if output else None)
        sha256 = packager.get_sha256(pkg_path)
        print(_ok(f"Package created: {pkg_path}"))
        print(f"  SHA256: {sha256}")
    except (FileNotFoundError, ValueError) as exc:
        print(_err(str(exc)))
        sys.exit(1)


def cmd_publish(args: argparse.Namespace) -> None:
    import os as _os

    from python.helpers.skill_index import SkillIndex

    token = args.token or _os.environ.get("JUMBOHUB_TOKEN", "")
    if not token:
        print(_err("GitHub token required. Use --token or set JUMBOHUB_TOKEN env var."))
        sys.exit(1)

    skill_path = Path(args.path)
    index = SkillIndex()

    try:
        result = asyncio.run(index.publish(skill_path, token))
        print(_ok(f"Published '{skill_path.name}' to JumboHub."))
        print(f"  SHA256: {result.get('sha256', 'N/A')}")
        print(f"  URL: {result.get('html_url', 'N/A')}")
    except Exception as exc:
        print(_err(f"Publish failed: {exc}"))
        sys.exit(1)


def cmd_info(args: argparse.Namespace) -> None:
    from python.helpers.skill_registry import get_registry

    registry = get_registry()
    skills_dir = Path(args.skills_dir)
    registry.scan_directory(skills_dir)

    skill = registry.get(args.name)
    if skill is None:
        print(_err(f"Skill '{args.name}' not found."))
        sys.exit(1)

    print(_heading(f"Skill: {skill.name}"))
    print(f"  Version:      {skill.version}")
    print(f"  Author:       {skill.author}")
    print(f"  Tier:         {skill.tier} ({'Markdown' if skill.tier == 1 else 'Python'})")
    print(f"  Trust Level:  {skill.trust_level}")
    print(f"  Enabled:      {skill.enabled}")
    print(f"  Path:         {skill.path}")
    if skill.description:
        print(f"  Description:  {skill.description}")
    if skill.categories:
        print(f"  Categories:   {', '.join(skill.categories)}")
    if skill.dependencies:
        print(f"  Dependencies: {', '.join(skill.dependencies)}")
    if skill.capabilities:
        print(f"  Capabilities: {', '.join(skill.capabilities)}")
    if skill.installed_at:
        print(f"  Installed:    {skill.installed_at.isoformat()}")


# ---------------------------------------------------------------------------
# Argument parser
# ---------------------------------------------------------------------------


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="python -m python.cli.skill_cli",
        description="Agent Jumbo skill management CLI",
    )
    parser.add_argument(
        "--skills-dir",
        default="skills",
        help="Path to the skills directory (default: skills)",
    )
    sub = parser.add_subparsers(dest="command", help="Available commands")

    # list
    sub.add_parser("list", help="List installed skills")

    # search
    p_search = sub.add_parser("search", help="Search JumboHub for skills")
    p_search.add_argument("query", help="Search query")

    # install
    p_install = sub.add_parser("install", help="Install a skill from JumboHub or local path")
    p_install.add_argument("name_or_path", help="Skill name (from JumboHub) or local path")

    # uninstall
    p_uninstall = sub.add_parser("uninstall", help="Uninstall a skill")
    p_uninstall.add_argument("name", help="Name of the skill to uninstall")

    # scan
    p_scan = sub.add_parser("scan", help="Run security scan on a skill")
    p_scan.add_argument("name_or_path", help="Skill name or path to scan")

    # package
    p_package = sub.add_parser("package", help="Create a distributable package")
    p_package.add_argument("path", help="Path to the skill directory")
    p_package.add_argument("-o", "--output", help="Output directory for the package")

    # publish
    p_publish = sub.add_parser("publish", help="Publish to JumboHub (requires token)")
    p_publish.add_argument("path", help="Path to the skill directory")
    p_publish.add_argument("--token", help="GitHub personal access token")

    # info
    p_info = sub.add_parser("info", help="Show detailed skill information")
    p_info.add_argument("name", help="Name of the skill")

    return parser


def main(argv: list[str] | None = None) -> None:
    parser = build_parser()
    args = parser.parse_args(argv)

    if not args.command:
        parser.print_help()
        sys.exit(0)

    dispatch = {
        "list": cmd_list,
        "search": cmd_search,
        "install": cmd_install,
        "uninstall": cmd_uninstall,
        "scan": cmd_scan,
        "package": cmd_package,
        "publish": cmd_publish,
        "info": cmd_info,
    }

    handler = dispatch.get(args.command)
    if handler:
        handler(args)
    else:
        parser.print_help()
        sys.exit(1)


if __name__ == "__main__":
    main()
