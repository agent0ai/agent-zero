"""Launcher module for a0 CLI.

Provides an interactive menu that appears after the banner animation.
"""

from .menu import run_menu
from .actions import (
    launch_repl,
    show_status,
    toggle_docker,
    open_settings,
    check_health,
)

__all__ = [
    "run_menu",
    "launch_repl",
    "show_status",
    "toggle_docker",
    "open_settings",
    "check_health",
]
