"""Interactive launcher menu for a0 CLI.

Displays a menu after the banner animation, allowing users to select
between different modes: TUI, REPL, Status, Docker, Settings.
"""

from __future__ import annotations

import sys
import tty
import termios
from typing import NamedTuple

from rich.console import Console
from rich.text import Text


class MenuItem(NamedTuple):
    """A menu item with key, label, and description."""
    key: str
    action: str
    label: str
    description: str


MENU_ITEMS: list[MenuItem] = [
    MenuItem("1", "tui", "Chat (TUI)", "Full terminal interface"),
    MenuItem("2", "repl", "Chat (REPL)", "Simple text chat"),
    MenuItem("3", "status", "Status", "Check Agent Zero"),
    MenuItem("4", "docker", "Start/Stop", "Docker container"),
    MenuItem("5", "settings", "Settings", "Configure a0"),
]


def _get_key() -> str:
    """Read a single keypress from stdin (raw mode)."""
    fd = sys.stdin.fileno()
    old_settings = termios.tcgetattr(fd)
    try:
        tty.setraw(fd)
        ch = sys.stdin.read(1)

        # Handle escape sequences (arrow keys)
        if ch == "\x1b":
            ch2 = sys.stdin.read(1)
            if ch2 == "[":
                ch3 = sys.stdin.read(1)
                if ch3 == "A":
                    return "up"
                elif ch3 == "B":
                    return "down"

        return ch
    finally:
        termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)


def _render_menu(console: Console, selected: int) -> None:
    """Render the menu with the current selection highlighted."""
    console.print()

    for i, item in enumerate(MENU_ITEMS):
        is_selected = i == selected

        # Build the line
        prefix = ">" if is_selected else " "
        key_style = "bold cyan" if is_selected else "dim"
        label_style = "bold white" if is_selected else "white"
        desc_style = "italic" if is_selected else "dim"

        line = Text()
        line.append(f"  {prefix} ", style="bold cyan" if is_selected else "")
        line.append(f"[{item.key}] ", style=key_style)
        line.append(item.label, style=label_style)
        line.append(f"  {item.description}", style=desc_style)

        console.print(line)

    console.print()
    console.print(
        "  [dim]↑↓ Navigate  •  Enter/Number Select  •  Esc Quit[/dim]"
    )


def _clear_menu(console: Console, line_count: int) -> None:
    """Move cursor up and clear the menu lines."""
    for _ in range(line_count):
        console.print("\033[A\033[2K", end="")


def run_menu() -> str | None:
    """Display interactive menu and return the selected action.

    Returns:
        The action string (e.g., "tui", "repl") or None if user pressed Escape.
    """
    console = Console()
    selected = 0
    menu_lines = len(MENU_ITEMS) + 3  # items + spacing + help line

    # Initial render
    _render_menu(console, selected)

    while True:
        key = _get_key()

        # Handle Escape
        if key == "\x1b" or key == "q":
            _clear_menu(console, menu_lines)
            return None

        # Handle Ctrl+C / Ctrl+Q
        if key == "\x03" or key == "\x11":
            _clear_menu(console, menu_lines)
            return None

        # Handle arrow keys
        if key == "up" or key == "k":
            selected = (selected - 1) % len(MENU_ITEMS)
        elif key == "down" or key == "j":
            selected = (selected + 1) % len(MENU_ITEMS)

        # Handle Enter
        elif key == "\r" or key == "\n":
            _clear_menu(console, menu_lines)
            return MENU_ITEMS[selected].action

        # Handle number keys
        elif key in "12345":
            idx = int(key) - 1
            if 0 <= idx < len(MENU_ITEMS):
                _clear_menu(console, menu_lines)
                return MENU_ITEMS[idx].action

        else:
            continue

        # Re-render menu
        _clear_menu(console, menu_lines)
        _render_menu(console, selected)
