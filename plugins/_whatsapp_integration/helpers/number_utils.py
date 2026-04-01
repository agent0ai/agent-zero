"""Phone-number normalization helpers for WhatsApp integration."""

from __future__ import annotations

import re
from collections.abc import Iterable


_JID_SUFFIX_RE = re.compile(r"[@:].*")
_NON_DIGIT_RE = re.compile(r"\D+")
_LEADING_ZERO_RE = re.compile(r"^0+")


def normalize_number(raw: str) -> str:
    """Normalize WhatsApp sender identifiers and phone numbers to comparable digits."""
    text = _JID_SUFFIX_RE.sub("", str(raw or ""))
    digits = _NON_DIGIT_RE.sub("", text)
    return _LEADING_ZERO_RE.sub("", digits)


def normalize_allowed_numbers(value: object) -> set[str]:
    """Accept stored config as a list/tuple/set or comma-delimited string."""
    if isinstance(value, str):
        candidates = value.split(",")
    elif isinstance(value, Iterable):
        candidates = value
    else:
        return set()

    normalized = {normalize_number(item) for item in candidates}
    normalized.discard("")
    return normalized
