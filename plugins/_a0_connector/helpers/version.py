"""Version metadata helpers for the A0 connector plugin."""
from __future__ import annotations


def agent_zero_version() -> str:
    try:
        from helpers import git

        return str(git.get_version()).strip() or "unknown"
    except Exception:
        return "unknown"
