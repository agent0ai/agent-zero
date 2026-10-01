"""Monkeypatch installed json_repair classify_object_value_comma.

Guards all 4 classification paths against false member-boundary detection
when unescaped quotes, backtick+colon patterns, or timestamp injections
appear inside string values.

Safe assumptions for A0 tool_args keys:
- Letters and underscore only (no digits, hyphens, or other symbols)
- Length <= 24 characters

TODO: Replace with checks against actual tool schemas
"""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Callable

    from json_repair.json_parser import JSONParser

_MAX_KEY_LENGTH = 24


def _load_string_delimiters() -> tuple[str, ...]:
    try:
        from json_repair.utils.constants import STRING_DELIMITERS

        return tuple(STRING_DELIMITERS)
    except Exception:
        return ('"', "'")


STRING_DELIMITERS_CACHE: tuple[str, ...] = _load_string_delimiters()


def _has_four_consecutive_digits(text: str) -> bool:
    count = 0
    for char in text:
        if char.isdigit():
            count += 1
            if count >= 4:
                return True
        else:
            count = 0
    return False


def _key_text_is_plausible(parser: JSONParser, key_start: int, key_end: int) -> bool:
    if key_end - key_start > _MAX_KEY_LENGTH:
        return False
    text = parser.json_str[key_start:key_end]
    if "\n" in text:
        return False
    if _has_four_consecutive_digits(text):
        return False
    return True


def _colon_follows(parser: JSONParser, idx: int) -> bool:
    return parser.get_char_at(parser.scroll_whitespaces(idx=idx)) == ":"


def _has_recoverable_value(
    parser: JSONParser,
    value_start: int,
    skip_to_character: Callable[[str | list[str], int], int],
) -> bool:
    """Delegate to original _bare_member_has_recoverable_value, but at EOF treat
    as recoverable only when stream_stable=False (default streaming mode)."""
    from json_repair.parse_string_helpers.object_value_context import (
        _bare_member_has_recoverable_value,
    )

    if _bare_member_has_recoverable_value(parser, value_start, skip_to_character):
        return True
    # Original returns False at EOF; override for streaming mode
    value_start_idx = parser.scroll_whitespaces(idx=value_start)
    value_end_idx = skip_to_character([*STRING_DELIMITERS_CACHE, "}"], value_start_idx)
    if parser.get_char_at(value_end_idx) is None:
        return not parser.stream_stable
    return False


def _patched_classify_object_value_comma(
    parser: JSONParser,
    cached_skip_to_character: Callable[[str | list[str], int], int] | None = None,
) -> str:
    from json_repair.utils.constants import STRING_DELIMITERS

    skip_to_character = cached_skip_to_character or parser.skip_to_character
    next_idx = parser.scroll_whitespaces(idx=1)
    next_c = parser.get_char_at(next_idx)
    if next_c in ["}", None]:
        return "member"

    # Quoted key
    if next_c in STRING_DELIMITERS:
        key_end_idx = parser.skip_to_character(character=next_c, idx=next_idx + 1)
        if not parser.get_char_at(key_end_idx):
            return "string"
        abs_start = parser.index + next_idx + 1
        abs_end = parser.index + key_end_idx
        if _key_text_is_plausible(parser, abs_start, abs_end) and _colon_follows(
            parser, key_end_idx + 1
        ):
            return "member"
        return "string"

    # Backtick key
    if next_c == "`":
        bare_key_idx = next_idx + 1
        while True:
            key_char = parser.get_char_at(bare_key_idx)
            if not key_char or not (key_char.isalnum() or key_char in ["_", "-"]):
                break
            bare_key_idx += 1
        abs_start = parser.index + next_idx + 1
        abs_end = parser.index + bare_key_idx
        if (
            _key_text_is_plausible(parser, abs_start, abs_end)
            and _colon_follows(parser, bare_key_idx)
            and _has_recoverable_value(parser, bare_key_idx + 1, skip_to_character)
        ):
            return "member"
        return "string"

    # Bare alnum/underscore key
    if next_c and (next_c.isalnum() or next_c == "_"):
        bare_key_idx = next_idx
        while True:
            key_char = parser.get_char_at(bare_key_idx)
            if not key_char or not (key_char.isalnum() or key_char in ["_", "-"]):
                break
            bare_key_idx += 1
        abs_start = parser.index + next_idx
        abs_end = parser.index + bare_key_idx
        if (
            _key_text_is_plausible(parser, abs_start, abs_end)
            and _colon_follows(parser, bare_key_idx)
            and _has_recoverable_value(parser, bare_key_idx + 1, skip_to_character)
        ):
            return "member"

    if next_c in ["{", "["]:
        return "container"

    # Fallback: skip to next string delimiter
    next_special_idx = skip_to_character([*STRING_DELIMITERS, "{", "["], next_idx)
    next_special = parser.get_char_at(next_special_idx)
    if not next_special:
        return "string_no_future_delimiter"
    if next_special in ["{", "["]:
        return "string"

    key_end_idx = skip_to_character(next_special, next_special_idx + 1)
    if not parser.get_char_at(key_end_idx):
        return "string"
    abs_start = parser.index + next_special_idx + 1
    abs_end = parser.index + key_end_idx
    if _key_text_is_plausible(parser, abs_start, abs_end) and _colon_follows(
        parser, key_end_idx + 1
    ):
        return "member"
    return "string"


_applied = False


def apply_patch() -> None:
    global _applied
    if _applied:
        return

    from json_repair.parse_string_helpers import object_value_context as ovc
    from json_repair import parse_string as ps

    ovc.classify_object_value_comma = _patched_classify_object_value_comma
    ps.classify_object_value_comma = _patched_classify_object_value_comma
    _applied = True
