from __future__ import annotations

from dataclasses import asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .model import ParsedDoc
from .utils import safe_filename


def doc_rel_path(doc: ParsedDoc) -> str:
    # Keep a stable path that doesn't change across versions.
    filename = safe_filename(doc.doc_id) + ".md"
    return str(Path(doc.source) / doc.doc_type / filename)


def render_markdown(doc: ParsedDoc, *, content_sha256: str, record_id: str) -> str:
    published = doc.published_date.isoformat() if doc.published_date else None
    header: dict[str, Any] = {
        "doc_id": doc.doc_id,
        "record_id": record_id,
        "source": doc.source,
        "type": doc.doc_type,
        "title": doc.title,
        "published_date": published,
        "url": doc.url,
        "content_sha256": content_sha256,
        "retrieved_at": datetime.now(timezone.utc).isoformat(),
    }
    if doc.citations:
        header["citations"] = doc.citations
    if doc.extra:
        header["extra"] = doc.extra

    # YAML-ish front matter (simple, explicit, and easy to grep).
    lines = ["---"]
    for key, value in header.items():
        if value is None:
            lines.append(f"{key}: null")
        elif isinstance(value, (int, float)):
            lines.append(f"{key}: {value}")
        elif isinstance(value, list):
            lines.append(f"{key}:")
            for item in value:
                lines.append(f"  - {item!r}")
        elif isinstance(value, dict):
            lines.append(f"{key}: {asdict(value) if hasattr(value, '__dataclass_fields__') else value!r}")
        else:
            lines.append(f"{key}: {value!r}")
    lines.append("---")
    lines.append("")
    lines.append(doc.body_markdown.rstrip() + "\n")
    return "\n".join(lines)


def write_markdown(corpus_dir: Path, doc: ParsedDoc, *, content_sha256: str, record_id: str) -> Path:
    rel = doc_rel_path(doc)
    abs_path = corpus_dir / rel
    abs_path.parent.mkdir(parents=True, exist_ok=True)
    abs_path.write_text(render_markdown(doc, content_sha256=content_sha256, record_id=record_id), encoding="utf-8")
    return abs_path

