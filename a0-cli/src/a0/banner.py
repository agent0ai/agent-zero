"""Animated ANSI banner for the a0 CLI.

Renders the Agent Zero "A" logo with horizontal slats that slide in
from the right, creating a venetian blinds / kinetic motion effect.
"""

from __future__ import annotations

import shutil
import sys
import time

# Each row defines: (left_margin, solid_width, gap_start, gap_width, trail_length)
# - left_margin: spaces from center to start of solid "A" shape
# - solid_width: width of the solid part of the A
# - gap_start: where the internal triangle hole starts (0 = no hole)
# - gap_width: width of the hole
# - trail_length: extra slat length extending right (the "blinds" effect)
#
# The A shape: starts narrow at top, widens, has a triangular hole, then legs

_ROWS = [
    # Top point of A (narrow)
    (19, 2, 0, 0, 35),
    (18, 4, 0, 0, 32),
    (17, 6, 0, 0, 29),
    (16, 8, 0, 0, 26),
    (15, 10, 0, 0, 23),
    (14, 12, 0, 0, 20),
    (13, 14, 0, 0, 17),
    (12, 16, 0, 0, 14),
    (11, 18, 0, 0, 11),
    # Start of inner triangle hole
    (10, 20, 6, 8, 8),
    (9, 22, 7, 8, 6),
    (8, 24, 8, 8, 5),
    # Crossbar (solid)
    (7, 26, 0, 0, 4),
    # Legs (with larger hole)
    (6, 28, 10, 8, 3),
    (5, 30, 11, 8, 2),
    (4, 32, 12, 8, 1),
    (3, 34, 13, 8, 0),
]

_BLOCK = "\u2588"  # Full block
_HALF_BLOCK = "\u2592"  # Medium shade for trail fade

# Animation tuning
_FRAME_DELAY = 0.008
_STAGGER_DELAY = 0.02
_FINAL_PAUSE = 0.25
_MIN_WIDTH = 60


def _ease_out_cubic(t: float) -> float:
    """Easing function for smooth deceleration."""
    return 1.0 - (1.0 - t) ** 3


def _rgb(r: int, g: int, b: int) -> str:
    """Generate ANSI true color escape sequence."""
    return f"\033[38;2;{r};{g};{b}m"


def _gradient_color(progress: float, row: int, total_rows: int) -> str:
    """Generate color based on position.

    Brighter at the left/center of the A, fading toward edges and trails.
    Vertical gradient: brightest in middle rows.
    """
    # Vertical brightness (center rows brightest)
    center = total_rows / 2
    vert_factor = 1.0 - abs(row - center) / center * 0.4

    # Horizontal brightness (left = bright, right = dim for trail)
    horiz_factor = 1.0 - progress * 0.6

    brightness = vert_factor * horiz_factor

    # Blue-white color scheme
    r = int(180 + 75 * brightness)
    g = int(190 + 65 * brightness)
    b = int(220 + 35 * brightness)

    return _rgb(min(r, 255), min(g, 255), min(b, 255))


def _build_row(
    solid_width: int,
    gap_start: int,
    gap_width: int,
    trail_length: int,
    row_idx: int,
    total_rows: int,
) -> list[tuple[str, str]]:
    """Build a row as list of (character, color) tuples."""
    result = []

    # The solid A part
    if gap_start > 0 and gap_width > 0:
        # Row with hole: left side, gap, right side
        left_side = gap_start
        right_side = solid_width - gap_start - gap_width

        # Left part of A
        for i in range(left_side):
            progress = i / solid_width
            color = _gradient_color(progress, row_idx, total_rows)
            result.append((_BLOCK, color))

        # Gap (internal triangle)
        for _ in range(gap_width):
            result.append((" ", ""))

        # Right part of A
        for i in range(right_side):
            progress = (gap_start + gap_width + i) / solid_width
            color = _gradient_color(progress, row_idx, total_rows)
            result.append((_BLOCK, color))
    else:
        # Solid row (no hole)
        for i in range(solid_width):
            progress = i / solid_width
            color = _gradient_color(progress, row_idx, total_rows)
            result.append((_BLOCK, color))

    # Trail extending right (the slat/blinds effect)
    for i in range(trail_length):
        progress = (solid_width + i) / (solid_width + trail_length)
        # Fade out the trail
        fade = 1.0 - (i / trail_length) ** 0.5
        color = _gradient_color(progress * 1.5, row_idx, total_rows)

        # Use lighter blocks for trail fade
        if fade > 0.7:
            result.append((_BLOCK, color))
        elif fade > 0.4:
            result.append(("\u2593", color))  # Dark shade
        elif fade > 0.2:
            result.append(("\u2592", color))  # Medium shade
        else:
            result.append(("\u2591", color))  # Light shade

    return result


def _render_row(chars: list[tuple[str, str]], x_offset: int) -> str:
    """Render a row at the given x offset."""
    reset = "\033[0m"
    padding = " " * max(0, x_offset)

    parts = [padding]
    for char, color in chars:
        if color:
            parts.append(f"{color}{char}")
        else:
            parts.append(char)
    parts.append(reset)

    return "".join(parts)


def show_banner() -> None:
    """Display the animated A-logo banner.

    Guards:
    - Only runs when stdout is a TTY
    - Only runs when terminal is wide enough
    """
    if not sys.stdout.isatty():
        return

    term_width = shutil.get_terminal_size((80, 24)).columns
    if term_width < _MIN_WIDTH:
        return

    clear_line = "\033[2K"
    hide_cursor = "\033[?25l"
    show_cursor = "\033[?25h"

    sys.stdout.write(hide_cursor)
    sys.stdout.write("\n")
    sys.stdout.flush()

    center = term_width // 2
    total_rows = len(_ROWS)

    try:
        for row_idx, (left_margin, solid_width, gap_start, gap_width, trail_length) in enumerate(_ROWS):
            # Build the row content
            chars = _build_row(
                solid_width, gap_start, gap_width, trail_length,
                row_idx, total_rows
            )

            # Calculate final position (centered, offset by left_margin)
            final_x = center - left_margin - (solid_width // 2)
            start_x = term_width + 10  # Start off-screen right

            # Animate: slide in from right
            frames = 6
            for frame in range(frames):
                t = (frame + 1) / frames
                eased = _ease_out_cubic(t)
                cur_x = int(start_x + (final_x - start_x) * eased)

                line = _render_row(chars, cur_x)
                sys.stdout.write(f"\r{clear_line}{line}")
                sys.stdout.flush()
                time.sleep(_FRAME_DELAY)

            # Final position
            line = _render_row(chars, final_x)
            sys.stdout.write(f"\r{clear_line}{line}\n")
            sys.stdout.flush()
            time.sleep(_STAGGER_DELAY)

        time.sleep(_FINAL_PAUSE)

    finally:
        sys.stdout.write(show_cursor)
        sys.stdout.write("\n")
        sys.stdout.flush()
