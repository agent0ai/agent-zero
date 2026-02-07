"""Animated ANSI banner for the a0 CLI.

Renders the Agent Zero logo with "AGENT ZERO" text below,
aligned to the left side with cyan-to-blue gradient.
"""

from __future__ import annotations

import shutil
import sys
import time

_BLOCK = "\u2588"  # Full block

# Animation tuning
_FRAME_DELAY = 0.004
_STAGGER_DELAY = 0.010
_FINAL_PAUSE = 0.08
_MIN_WIDTH = 50
_LEFT_MARGIN = 4  # Distance from left edge

# Logo shape
_LOGO_ROWS = [
    (2, 0, 2),
    (2, 2, 2),
    (3, 2, 3),
    (3, 4, 3),
    (4, 4, 4),
    (4, 6, 4),
    (5, 6, 5),
    (5, 8, 5),
    (6, 8, 6),
    (6, 10, 6),
    (7, 10, 7),
    (7, 12, 7),
    (8, 12, 8),
    (8, 4, 4, 4, 8),
]

# Clean pixel-art text "AGENT ZERO" using standard 5-high blocky font
_TEXT_ART = [
    "  ███   ████  ████  █   █  █████    █████  ████  ████    ███  ",
    " █   █  █     █     ██  █    █         █   █     █   █  █   █ ",
    " █████  █  █  ████  █ █ █    █        █    ████  ████   █   █ ",
    " █   █  █   █ █     █  ██    █       █     █     █  █   █   █ ",
    " █   █   ███  ████  █   █    █      █████  ████  █   █   ███  ",
]


def _ease_out_cubic(t: float) -> float:
    return 1.0 - (1.0 - t) ** 3


def _rgb(r: int, g: int, b: int) -> str:
    return f"\033[38;2;{r};{g};{b}m"


def _get_color(row: int, total_rows: int) -> str:
    """Cyan-to-blue gradient."""
    progress = row / max(1, total_rows - 1)
    r = int(0 + 30 * progress)
    g = int(255 - 155 * progress)
    b = int(255 - 55 * progress)
    return _rgb(r, g, b)


def _build_logo_row(row_def: tuple) -> str:
    """Build logo row as string."""
    if len(row_def) == 3:
        left, gap, right = row_def
        return _BLOCK * left + " " * gap + _BLOCK * right
    else:
        left, gap1, center, gap2, right = row_def
        return _BLOCK * left + " " * gap1 + _BLOCK * center + " " * gap2 + _BLOCK * right


def _logo_width(row_def: tuple) -> int:
    return sum(row_def)


def show_banner() -> None:
    """Display the banner with logo on top, text below, left-aligned."""
    if not sys.stdout.isatty():
        return

    term_width = shutil.get_terminal_size((80, 24)).columns
    if term_width < _MIN_WIDTH:
        return

    clear_line = "\033[2K"
    hide_cursor = "\033[?25l"
    show_cursor = "\033[?25h"
    reset = "\033[0m"

    sys.stdout.write(hide_cursor)
    sys.stdout.write("\n")
    sys.stdout.flush()

    max_logo_width = max(_logo_width(r) for r in _LOGO_ROWS)
    total_rows = len(_LOGO_ROWS) + 1 + len(_TEXT_ART)  # logo + gap + text

    try:
        row_counter = 0

        # Render logo rows
        for row_def in _LOGO_ROWS:
            color = _get_color(row_counter, total_rows)
            logo_str = _build_logo_row(row_def)

            # Center logo within its max width, then left-align
            logo_pad = max_logo_width - _logo_width(row_def)
            centered_logo = " " * (logo_pad // 2) + logo_str

            line = f"{color}{centered_logo}{reset}"

            # Animate slide-in
            start_x = term_width + 5
            final_x = _LEFT_MARGIN

            for frame in range(4):
                t = (frame + 1) / 4
                eased = _ease_out_cubic(t)
                cur_x = int(start_x + (final_x - start_x) * eased)
                padding = " " * max(0, cur_x)
                sys.stdout.write(f"\r{clear_line}{padding}{line}")
                sys.stdout.flush()
                time.sleep(_FRAME_DELAY)

            padding = " " * _LEFT_MARGIN
            sys.stdout.write(f"\r{clear_line}{padding}{line}\n")
            sys.stdout.flush()
            time.sleep(_STAGGER_DELAY)
            row_counter += 1

        # Gap between logo and text
        sys.stdout.write("\n")
        row_counter += 1

        # Render text rows
        for text_row in _TEXT_ART:
            color = _get_color(row_counter, total_rows)
            line = f"{color}{text_row}{reset}"

            # Animate slide-in
            start_x = term_width + 5
            final_x = _LEFT_MARGIN

            for frame in range(4):
                t = (frame + 1) / 4
                eased = _ease_out_cubic(t)
                cur_x = int(start_x + (final_x - start_x) * eased)
                padding = " " * max(0, cur_x)
                sys.stdout.write(f"\r{clear_line}{padding}{line}")
                sys.stdout.flush()
                time.sleep(_FRAME_DELAY)

            padding = " " * _LEFT_MARGIN
            sys.stdout.write(f"\r{clear_line}{padding}{line}\n")
            sys.stdout.flush()
            time.sleep(_STAGGER_DELAY)
            row_counter += 1

        time.sleep(_FINAL_PAUSE)

    finally:
        sys.stdout.write(show_cursor)
        sys.stdout.write("\n")
        sys.stdout.flush()
