from __future__ import annotations

from datetime import date, datetime, timezone


def utc_now() -> datetime:
    """Return timezone-aware UTC now."""
    return datetime.now(timezone.utc)


def isoformat_z(value: datetime, timespec: str = "seconds") -> str:
    """Serialize datetime as ISO-8601 in UTC with a trailing Z."""
    normalized = value
    if normalized.tzinfo is None:
        normalized = normalized.replace(tzinfo=timezone.utc)
    else:
        normalized = normalized.astimezone(timezone.utc)
    return normalized.isoformat(timespec=timespec).replace("+00:00", "Z")


def parse_iso_datetime(value: str | None, default: datetime | None = None) -> datetime:
    """
    Parse ISO-8601 datetime strings, accepting a trailing 'Z' as UTC.
    Returns a timezone-aware UTC datetime.
    """
    if not value:
        return default or utc_now()

    normalized = value.strip()
    if normalized.endswith("Z"):
        normalized = normalized[:-1] + "+00:00"

    try:
        parsed = datetime.fromisoformat(normalized)
    except ValueError:
        # Handle date-only strings like YYYY-MM-DD
        try:
            parsed_date = date.fromisoformat(normalized[:10])
        except ValueError as exc:
            raise ValueError(f"Invalid ISO datetime: {value}") from exc
        parsed = datetime.combine(parsed_date, datetime.min.time())

    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    else:
        parsed = parsed.astimezone(timezone.utc)

    return parsed


def parse_iso_date(value: str | None, default: date | None = None) -> date:
    """
    Parse ISO-8601 date/datetime strings into a date.
    Accepts datetime strings with timezone suffixes (including 'Z').
    """
    if not value:
        return default or utc_now().date()

    parsed = parse_iso_datetime(value, default=None)
    return parsed.date()
