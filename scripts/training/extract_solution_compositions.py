"""Extract solution composition blueprints and business outcome mappings.

Processes:
- kits/*/kit.yaml and root-level kit files — kit definitions
- services/ai-solution-engine/src/ — composition logic, components
- solution_composer.js — the composition algorithm
"""

from __future__ import annotations

import re
from collections import Counter
from typing import TYPE_CHECKING

from .config import CHUNKS_DIR, SILVER_SURFER_ROOT
from .utils import (
    chunk_by_function,
    chunk_to_record,
    classify_taxonomy,
    count_tokens,
    read_file,
    write_jsonl,
)

if TYPE_CHECKING:
    from pathlib import Path

OUTPUT_FILE = CHUNKS_DIR / "solution_compositions.jsonl"


def _extract_yaml_field(content: str, field: str) -> str | None:
    match = re.search(rf"^\s*{field}:\s*(.+)$", content, re.MULTILINE)
    if match:
        return match.group(1).strip().strip("'\"")
    return None


def _extract_yaml_list(content: str, field: str) -> list[str]:
    """Extract a YAML list field (simple inline or block format)."""
    # Inline: field: [a, b, c]
    inline = re.search(rf"^\s*{field}:\s*\[([^\]]+)\]", content, re.MULTILINE)
    if inline:
        return [x.strip().strip("'\"") for x in inline.group(1).split(",")]
    # Block format
    block = re.search(rf"^\s*{field}:\s*\n((?:\s+-\s+.+\n?)+)", content, re.MULTILINE)
    if block:
        return [
            line.strip().lstrip("- ").strip("'\"")
            for line in block.group(1).strip().split("\n")
            if line.strip().startswith("-")
        ]
    return []


def extract_kit_compositions(root: Path) -> list[dict]:
    """Parse all kit definitions for composition blueprints."""
    records: list[dict] = []

    kit_paths: list[Path] = []
    for search_dir in ("kits", "kit-templates", "swarm-generated"):
        d = root / search_dir
        if d.exists():
            kit_paths.extend(d.rglob("kit.yaml"))
    kit_paths.extend(root.glob("*-kit.yaml"))
    kit_paths.extend(root.glob("*-kit.json"))

    for kit_path in sorted(set(kit_paths)):
        try:
            content = read_file(kit_path)
        except Exception:
            continue

        rel_path = str(kit_path.relative_to(root))
        kit_name = _extract_yaml_field(content, "name") or kit_path.stem
        description = _extract_yaml_field(content, "description") or ""
        category_field = _extract_yaml_field(content, "category") or ""
        tags = _extract_yaml_list(content, "tags")
        components = _extract_yaml_list(content, "components")

        # Extract business outcomes if present
        outcomes: list[str] = []
        outcomes_match = re.search(r"business[_-]?outcomes?:\s*\n((?:\s+-\s+.+\n?)+)", content, re.I | re.MULTILINE)
        if outcomes_match:
            outcomes = [
                line.strip().lstrip("- ").strip("'\"")
                for line in outcomes_match.group(1).strip().split("\n")
                if line.strip().startswith("-")
            ]

        # Detect industry from content
        industry = "general"
        for ind in ("healthcare", "fintech", "ecommerce", "saas", "education", "iot"):
            if ind in content.lower() or ind in " ".join(tags).lower():
                industry = ind
                break

        record = {
            "source_file": rel_path,
            "chunk_type": "solution_blueprint",
            "taxonomy_category": classify_taxonomy(content, f"kit {kit_name} {description} {category_field}"),
            "kit_name": kit_name,
            "industry": industry,
            "components": components,
            "business_outcomes": outcomes,
            "content": content,
            "context": f"Kit: {kit_name}\nCategory: {category_field}\nTags: {', '.join(tags)}",
            "token_count": count_tokens(content),
        }
        records.append(record)

    return records


def extract_solution_engine_chunks(root: Path) -> list[dict]:
    """Extract from ai-solution-engine service — composition logic."""
    records: list[dict] = []
    engine_dir = root / "services" / "ai-solution-engine" / "src"
    if not engine_dir.exists():
        return records

    for js_file in sorted(engine_dir.glob("*.js")):
        try:
            code = read_file(js_file)
        except Exception:
            continue

        if count_tokens(code) < 30:
            continue

        rel_path = str(js_file.relative_to(root))
        chunks = chunk_by_function(code, language="javascript")

        for chunk in chunks:
            chunk.source_file = rel_path
            chunk.chunk_type = "composition_logic"
            records.append(chunk_to_record(chunk))

    # Also check for a components subdirectory
    components_dir = engine_dir / "components"
    if components_dir.exists():
        for comp_file in sorted(components_dir.rglob("*.js")):
            try:
                code = read_file(comp_file)
            except Exception:
                continue
            rel_path = str(comp_file.relative_to(root))
            chunks = chunk_by_function(code, language="javascript")
            for chunk in chunks:
                chunk.source_file = rel_path
                chunk.chunk_type = "component_library"
                records.append(chunk_to_record(chunk))

    return records


def run() -> list[dict]:
    """Run the full solution compositions extraction pipeline."""
    print("Extracting solution compositions from Silver Surfer Platform...")
    print(f"  Source: {SILVER_SURFER_ROOT}")
    root = SILVER_SURFER_ROOT

    all_records: list[dict] = []

    print("  [1/2] Extracting from kit definitions...")
    kit_records = extract_kit_compositions(root)
    print(f"         {len(kit_records)} kit blueprints")
    all_records.extend(kit_records)

    print("  [2/2] Extracting from ai-solution-engine...")
    engine_records = extract_solution_engine_chunks(root)
    print(f"         {len(engine_records)} composition chunks")
    all_records.extend(engine_records)

    # Summary
    print(f"\n  Total: {len(all_records)} solution composition chunks")
    print(f"  Kits found: {len(kit_records)}")
    cat_counts = Counter(r["taxonomy_category"] for r in all_records)
    print("  Per category:")
    for cat, count in cat_counts.most_common():
        print(f"    {cat}: {count}")

    write_jsonl(all_records, OUTPUT_FILE)
    print(f"\n  Written to {OUTPUT_FILE}")

    return all_records


if __name__ == "__main__":
    run()
