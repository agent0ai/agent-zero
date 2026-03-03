from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date
from typing import Any


@dataclass(frozen=True)
class DiscoveredDoc:
    source: str
    doc_type: str
    doc_id: str
    url: str
    title: str | None = None
    published_date: date | None = None
    extra: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class ParsedDoc:
    source: str
    doc_type: str
    doc_id: str
    url: str
    title: str
    published_date: date | None
    body_markdown: str
    citations: list[str] = field(default_factory=list)
    extra: dict[str, Any] = field(default_factory=dict)

