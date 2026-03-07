"""Extract architecture decision traces from Silver Surfer Platform.

Processes:
- services/ — service code, README/docstrings, inter-service patterns
- kits/ and kit-templates/ — kit.yaml composition definitions
- docs/ — documentation chunked by H2 heading
- Key architecture files (orchestrator, solution_composer, design-engine)
"""

from __future__ import annotations

import re
from collections import Counter
from typing import TYPE_CHECKING

from .config import CHUNKS_DIR, SILVER_SURFER_ROOT
from .utils import (
    chunk_by_function,
    chunk_by_heading,
    chunk_to_record,
    classify_taxonomy,
    count_tokens,
    read_file,
    write_jsonl,
)

if TYPE_CHECKING:
    from pathlib import Path

OUTPUT_FILE = CHUNKS_DIR / "architecture_decisions.jsonl"

# Key architecture files to always process
KEY_FILES = [
    "services/claude-agent-orchestrator/src/universal_solution_orchestrator.py",
    "services/ai-solution-engine/src/solution_composer.js",
    "src/services/design-engine.js",
]


def extract_service_chunks(root: Path) -> list[dict]:
    """Walk services/ and extract architecture chunks from each service."""
    records: list[dict] = []
    services_dir = root / "services"
    if not services_dir.exists():
        return records

    for service_dir in sorted(services_dir.iterdir()):
        if not service_dir.is_dir():
            continue

        service_name = service_dir.name

        # Try to find README or top-level docstring
        readme_content = ""
        for readme_name in ("README.md", "readme.md", "README"):
            readme_path = service_dir / readme_name
            if readme_path.exists():
                readme_content = read_file(readme_path)
                break

        # Find source files
        source_files = []
        for ext in ("*.py", "*.js", "*.ts"):
            source_files.extend(service_dir.rglob(ext))

        # Skip test files and node_modules
        source_files = [
            f
            for f in source_files
            if "node_modules" not in str(f) and "test" not in f.name.lower() and "__pycache__" not in str(f)
        ]

        for src_file in sorted(source_files):
            try:
                code = read_file(src_file)
            except Exception:
                continue

            if not code.strip() or count_tokens(code) < 20:
                continue

            lang = "python" if src_file.suffix == ".py" else "javascript"
            rel_path = str(src_file.relative_to(root))

            chunks = chunk_by_function(code, language=lang)
            for chunk in chunks:
                chunk.source_file = rel_path
                chunk.chunk_type = "service_architecture"
                chunk.context = f"Service: {service_name}\nFile: {rel_path}\n" + (
                    f"README excerpt: {readme_content[:300]}\n" if readme_content else ""
                )
                records.append(chunk_to_record(chunk, service_name=service_name))

        # Also chunk README as documentation
        if readme_content and count_tokens(readme_content) > 50:
            doc_chunks = chunk_by_heading(readme_content)
            rel_readme = str((service_dir / "README.md").relative_to(root))
            for dc in doc_chunks:
                dc.source_file = rel_readme
                dc.chunk_type = "service_documentation"
                records.append(chunk_to_record(dc, service_name=service_name))

    return records


def extract_kit_chunks(root: Path) -> list[dict]:
    """Parse kit.yaml files from kits/, kit-templates/, and root-level kit files."""
    records: list[dict] = []

    # Collect all kit.yaml paths
    kit_paths: list[Path] = []
    for search_dir in ("kits", "kit-templates", "swarm-generated"):
        d = root / search_dir
        if d.exists():
            kit_paths.extend(d.rglob("kit.yaml"))

    # Root-level kit files (starter-crm-kit.yaml, etc.)
    kit_paths.extend(root.glob("*-kit.yaml"))
    kit_paths.extend(root.glob("*-kit.json"))

    for kit_path in sorted(set(kit_paths)):
        try:
            content = read_file(kit_path)
        except Exception:
            continue

        rel_path = str(kit_path.relative_to(root))

        # Extract kit metadata from YAML content
        kit_name = _extract_yaml_field(content, "name") or kit_path.parent.name
        description = _extract_yaml_field(content, "description") or ""
        category = _extract_yaml_field(content, "category") or ""

        record = {
            "source_file": rel_path,
            "chunk_type": "kit_definition",
            "taxonomy_category": classify_taxonomy(content, f"kit {kit_name} {description} {category}"),
            "content": content,
            "context": f"Kit: {kit_name}\nDescription: {description}",
            "kit_name": kit_name,
            "token_count": count_tokens(content),
        }
        records.append(record)

    return records


def extract_doc_chunks(root: Path) -> list[dict]:
    """Chunk documentation files from docs/ by H2 heading."""
    records: list[dict] = []
    docs_dir = root / "docs"
    if not docs_dir.exists():
        return records

    for md_file in sorted(docs_dir.rglob("*.md")):
        try:
            content = read_file(md_file)
        except Exception:
            continue

        if count_tokens(content) < 30:
            continue

        rel_path = str(md_file.relative_to(root))
        chunks = chunk_by_heading(content)
        for chunk in chunks:
            chunk.source_file = rel_path
            chunk.chunk_type = "documentation"
            records.append(chunk_to_record(chunk))

    return records


def extract_key_architecture_files(root: Path) -> list[dict]:
    """Extract chunks from the key architecture files listed in the plan."""
    records: list[dict] = []

    for rel_path in KEY_FILES:
        full_path = root / rel_path
        if not full_path.exists():
            print(f"  [warn] Key file not found: {rel_path}")
            continue

        code = read_file(full_path)
        lang = "python" if full_path.suffix == ".py" else "javascript"
        chunks = chunk_by_function(code, language=lang)

        for chunk in chunks:
            chunk.source_file = rel_path
            chunk.chunk_type = "key_architecture"
            chunk.context = f"Key architecture file: {rel_path}"
            records.append(chunk_to_record(chunk))

    return records


def _extract_yaml_field(content: str, field: str) -> str | None:
    """Simple regex extraction of a YAML field value."""
    match = re.search(rf"^\s*{field}:\s*(.+)$", content, re.MULTILINE)
    if match:
        return match.group(1).strip().strip("'\"")
    return None


def run() -> list[dict]:
    """Run the full architecture decisions extraction pipeline."""
    print("Extracting architecture decisions from Silver Surfer Platform...")
    print(f"  Source: {SILVER_SURFER_ROOT}")
    root = SILVER_SURFER_ROOT

    all_records: list[dict] = []

    print("  [1/4] Extracting from key architecture files...")
    key_records = extract_key_architecture_files(root)
    print(f"         {len(key_records)} chunks")
    all_records.extend(key_records)

    print("  [2/4] Extracting from services/...")
    service_records = extract_service_chunks(root)
    print(f"         {len(service_records)} chunks")
    all_records.extend(service_records)

    print("  [3/4] Extracting from kits...")
    kit_records = extract_kit_chunks(root)
    print(f"         {len(kit_records)} chunks")
    all_records.extend(kit_records)

    print("  [4/4] Extracting from docs/...")
    doc_records = extract_doc_chunks(root)
    print(f"         {len(doc_records)} chunks")
    all_records.extend(doc_records)

    # Summary
    category_counts = Counter(r["taxonomy_category"] for r in all_records)
    print(f"\n  Total: {len(all_records)} architecture decision chunks")
    print("  Chunks per category:")
    for cat, count in category_counts.most_common():
        print(f"    {cat}: {count}")

    write_jsonl(all_records, OUTPUT_FILE)
    print(f"\n  Written to {OUTPUT_FILE}")

    return all_records


if __name__ == "__main__":
    run()
