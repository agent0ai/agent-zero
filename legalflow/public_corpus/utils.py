from __future__ import annotations

import hashlib
import json
import re
from datetime import date


def sha256_hex(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def stable_content_hash(payload: object) -> str:
    data = json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode(
        "utf-8"
    )
    return sha256_hex(data)


_FILENAME_SAFE_RE = re.compile(r"[^a-zA-Z0-9._-]+")


def safe_filename(value: str, *, max_len: int = 180) -> str:
    cleaned = _FILENAME_SAFE_RE.sub("_", value).strip("._-")
    if not cleaned:
        cleaned = "doc"
    if len(cleaned) > max_len:
        cleaned = cleaned[:max_len]
    return cleaned


def parse_ddmmyyyy(value: str) -> date | None:
    value = value.strip()
    m = re.fullmatch(r"(\d{2})/(\d{2})/(\d{4})", value)
    if not m:
        return None
    day, month, year = (int(m.group(1)), int(m.group(2)), int(m.group(3)))
    try:
        return date(year, month, day)
    except ValueError:
        return None


def years_ago(today: date, years: int) -> date:
    target_year = today.year - years
    month = today.month
    day = today.day
    # Clamp day to last day of target month (handles Feb 29)
    for d in range(day, 27, -1):
        try:
            return date(target_year, month, d)
        except ValueError:
            continue
    return date(target_year, month, 1)

