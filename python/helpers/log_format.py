"""Structured logging format used across Agent Zero.

Format: ``2026-03-07T12:34:56Z INFO     [a0.addon] message``

- Timestamp: RFC 3339 / ISO 8601 UTC
- Level: standard Python logging levels (DEBUG, INFO, WARNING, ERROR, CRITICAL)
- Component: dot-separated hierarchy in brackets (= logger name)
"""

import datetime as _dt
import logging

_UTC = _dt.timezone.utc


def format_prefix(level: str = "INFO", component: str = "a0") -> str:
    ts = _dt.datetime.now(_UTC).strftime("%Y-%m-%dT%H:%M:%SZ")
    return f"{ts} {level:<8s} [{component}]"


class StructuredFormatter(logging.Formatter):
    """``logging.Formatter`` that produces the unified structured format."""

    def format(self, record: logging.LogRecord) -> str:
        ts = _dt.datetime.fromtimestamp(record.created, tz=_UTC)
        msg = record.getMessage()
        formatted = f"{ts:%Y-%m-%dT%H:%M:%SZ} {record.levelname:<8s} [{record.name}] {msg}"
        if record.exc_info and not record.exc_text:
            record.exc_text = self.formatException(record.exc_info)
        if record.exc_text:
            formatted += "\n" + record.exc_text
        return formatted


def configure_logging(root_level: int = logging.WARNING) -> None:
    """Replace all handlers on the root logger with a single structured handler."""
    handler = logging.StreamHandler()
    handler.setFormatter(StructuredFormatter())

    root = logging.getLogger()
    root.handlers.clear()
    root.addHandler(handler)
    root.setLevel(root_level)

    for name in ("uvicorn", "uvicorn.error", "uvicorn.access"):
        lg = logging.getLogger(name)
        lg.handlers.clear()
        lg.addHandler(handler)
        lg.propagate = False
