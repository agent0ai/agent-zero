from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


@dataclass
class ManifestEntry:
    doc_id: str
    record_id: str
    source: str
    doc_type: str
    title: str
    url: str
    published_date: str | None
    content_sha256: str
    path: str
    updated_at: str
    extra: dict[str, Any] = field(default_factory=dict)


@dataclass
class Manifest:
    schema_version: int = 1
    documents: dict[str, ManifestEntry] = field(default_factory=dict)

    @staticmethod
    def load(path: Path) -> "Manifest":
        if not path.exists():
            return Manifest()
        raw = json.loads(path.read_text(encoding="utf-8"))
        docs: dict[str, ManifestEntry] = {}
        for doc_id, entry in (raw.get("documents") or {}).items():
            docs[doc_id] = ManifestEntry(**entry)
        return Manifest(schema_version=int(raw.get("schema_version", 1)), documents=docs)

    def save(self, path: Path) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        payload = {
            "schema_version": self.schema_version,
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "documents": {k: vars(v) for k, v in sorted(self.documents.items())},
        }
        path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

