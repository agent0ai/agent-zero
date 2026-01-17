#!/usr/bin/env python3
"""Register knowledge ingestion sources from a JSON file."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from instruments.custom.knowledge_ingest.knowledge_ingest_db import KnowledgeIngestDatabase

DEFAULT_SOURCES = "data/digital_clone_sources.json"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Register knowledge sources")
    parser.add_argument("--sources", default=DEFAULT_SOURCES, help="Path to sources JSON")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    source_path = Path(args.sources)
    if not source_path.is_absolute():
        source_path = ROOT / source_path

    data = json.loads(source_path.read_text(encoding="utf-8"))
    db_path = ROOT / "instruments/custom/knowledge_ingest/data/knowledge_ingest.db"
    db = KnowledgeIngestDatabase(str(db_path))

    results = []
    for entry in data:
        name = entry.get("name")
        uri = entry.get("uri")
        existing = db.find_source(name, uri)
        if existing:
            results.append({"name": name, "status": "exists", "source_id": existing})
            continue

        source_id = db.add_source(
            name=name,
            source_type=entry.get("type"),
            uri=uri,
            tags=entry.get("tags") or [],
            cadence=entry.get("cadence"),
            config=entry.get("config") or {},
        )
        results.append({"name": name, "status": "registered", "source_id": source_id})

    print(json.dumps(results, indent=2))


if __name__ == "__main__":
    main()
