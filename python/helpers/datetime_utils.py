from __future__ import annotations

from datetime import UTC, date, datetime


def parse_iso_datetime(value: str | None, default: datetime | None = None) -> datetime:
    """
    Parse ISO-8601 datetime strings, accepting a trailing 'Z' as UTC.
    Returns a timezone-aware UTC datetime.
    """
    if not value:
        return default or datetime.now(UTC)

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
        parsed = parsed.replace(tzinfo=UTC)
    else:
        parsed = parsed.astimezone(UTC)

    return parsed


def parse_iso_date(value: str | None, default: date | None = None) -> date:
    """
    Parse ISO-8601 date/datetime strings into a date.
    Accepts datetime strings with timezone suffixes (including 'Z').
    """
    if not value:
        return default or datetime.now(UTC).date()

    parsed = parse_iso_datetime(value, default=None)
    return parsed.date()
