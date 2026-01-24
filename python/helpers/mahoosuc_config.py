"""
Mahoosuc OS Configuration Management

Handles configuration loading, validation, and path resolution
for Mahoosuc OS integration.
"""

import os
from pathlib import Path
from typing import Any

VALID_INTEGRATION_MODES = ["reference", "mcp-bridge", "native-tools"]


def get_commands_dir() -> Path:
    """Get absolute path to Mahoosuc commands directory"""
    commands_dir = os.getenv("MAHOOSUC_COMMANDS_DIR", ".claude/commands")
    path = Path(commands_dir)

    # Resolve to absolute path if relative
    if not path.is_absolute():
        path = Path.cwd() / path

    return path.resolve()


def get_agents_dir() -> Path:
    """Get absolute path to Mahoosuc agents directory"""
    agents_dir = os.getenv("MAHOOSUC_AGENTS_DIR", ".claude/agents")
    path = Path(agents_dir)

    if not path.is_absolute():
        path = Path.cwd() / path

    return path.resolve()


def get_skills_dir() -> Path:
    """Get absolute path to Mahoosuc skills directory"""
    skills_dir = os.getenv("MAHOOSUC_SKILLS_DIR", ".claude/skills")
    path = Path(skills_dir)

    if not path.is_absolute():
        path = Path.cwd() / path

    return path.resolve()


def get_integration_mode() -> str:
    """Get configured integration mode (defaults to 'reference')"""
    return os.getenv("MAHOOSUC_INTEGRATION_MODE", "reference")


def validate_integration_mode(mode: str) -> bool:
    """
    Validate integration mode is valid

    Raises:
        ValueError: If mode is not valid
    """
    if mode not in VALID_INTEGRATION_MODES:
        raise ValueError(f"Invalid integration mode: {mode}. " f"Must be one of: {', '.join(VALID_INTEGRATION_MODES)}")
    return True


def validate_config() -> dict[str, Any]:
    """
    Validate complete Mahoosuc configuration

    Returns:
        Dict with 'valid' (bool) and 'errors' (list of str)
    """
    errors = []

    # Check integration mode
    mode = get_integration_mode()
    try:
        validate_integration_mode(mode)
    except ValueError as e:
        errors.append(str(e))

    # Check directories exist
    commands_dir = get_commands_dir()
    if not commands_dir.exists():
        errors.append(f"Commands directory not found: {commands_dir}")

    agents_dir = get_agents_dir()
    if not agents_dir.exists():
        errors.append(f"Agents directory not found: {agents_dir}")

    skills_dir = get_skills_dir()
    if not skills_dir.exists():
        errors.append(f"Skills directory not found: {skills_dir}")

    # MCP bridge mode requires Claude Code
    if mode == "mcp-bridge":
        claude_code_enabled = os.getenv("CLAUDE_CODE_ENABLED", "false").lower()
        if claude_code_enabled != "true":
            errors.append("MCP bridge mode requires CLAUDE_CODE_ENABLED=true")

    return {
        "valid": len(errors) == 0,
        "errors": errors,
        "mode": mode,
        "commands_dir": str(commands_dir),
        "agents_dir": str(agents_dir),
        "skills_dir": str(skills_dir),
    }
