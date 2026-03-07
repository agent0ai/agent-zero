"""Extract testing patterns, quality gates, and code review standards.

Processes:
- tdd-project-generator.js — quality gate definitions
- Test files across the platform — test conventions
- CI/CD configs (docker-compose, cloudbuild) — operational standards
- Middleware and auth patterns — security standards
"""

from __future__ import annotations

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

OUTPUT_FILE = CHUNKS_DIR / "quality_standards.jsonl"


def extract_quality_gate_definitions(root: Path) -> list[dict]:
    """Extract quality gate definitions from TDD generator."""
    records: list[dict] = []
    path = root / "src" / "services" / "tdd-project-generator.js"
    if not path.exists():
        return records

    code = read_file(path)
    rel_path = str(path.relative_to(root))
    chunks = chunk_by_function(code, language="javascript")

    # Look for quality-gate-related functions
    gate_keywords = ["coverage", "quality", "gate", "threshold", "validation", "check"]
    for chunk in chunks:
        chunk.source_file = rel_path
        name_lower = chunk.name.lower()
        content_lower = chunk.content.lower()

        if any(kw in name_lower or kw in content_lower for kw in gate_keywords):
            chunk.chunk_type = "quality_gate"
            records.append(
                chunk_to_record(
                    chunk,
                    taxonomy_category="skills.quality_engineering.test_coverage_analysis",
                )
            )
        else:
            chunk.chunk_type = "tdd_pattern"
            records.append(chunk_to_record(chunk))

    return records


def extract_cicd_patterns(root: Path) -> list[dict]:
    """Extract CI/CD and deployment configuration patterns."""
    records: list[dict] = []

    # Docker compose files
    compose_files = list(root.glob("docker-compose*.yml")) + list(root.glob("docker-compose*.yaml"))

    # Cloud build configs
    compose_files.extend(root.glob("cloudbuild*.yaml"))

    # Dockerfiles
    dockerfiles = list(root.glob("Dockerfile*"))
    for subdir in ("services", "kit-marketplace", "grateful-house"):
        d = root / subdir
        if d.exists():
            dockerfiles.extend(d.rglob("Dockerfile*"))

    # Kubernetes configs
    k8s_dir = root / "k8s"
    k8s_files: list[Path] = []
    if k8s_dir.exists():
        k8s_files = list(k8s_dir.rglob("*.yaml")) + list(k8s_dir.rglob("*.yml"))

    kubernetes_dir = root / "kubernetes"
    if kubernetes_dir.exists():
        k8s_files.extend(kubernetes_dir.rglob("*.yaml"))
        k8s_files.extend(kubernetes_dir.rglob("*.yml"))

    all_config_files = list(set(compose_files + dockerfiles + k8s_files))

    for config_file in sorted(all_config_files):
        try:
            content = read_file(config_file)
        except Exception:
            continue

        if count_tokens(content) < 10:
            continue

        rel_path = str(config_file.relative_to(root))
        record = {
            "source_file": rel_path,
            "chunk_type": "operational_config",
            "taxonomy_category": classify_taxonomy(content, f"deployment config {rel_path}"),
            "content": content,
            "context": f"Configuration file: {rel_path}",
            "token_count": count_tokens(content),
        }
        records.append(record)

    return records


def extract_security_patterns(root: Path) -> list[dict]:
    """Extract RBAC, auth middleware, and security patterns."""
    records: list[dict] = []

    # Auth and RBAC middleware
    security_files = [
        root / "src" / "middleware" / "auth.js",
        root / "src" / "middleware" / "auth-simple.js",
        root / "src" / "middleware" / "rbac.js",
        root / "services" / "common" / "middleware.py",
        root / "services" / "common" / "security_middleware.py",
        root / "services" / "enterprise-auth",
        root / "services" / "auth",
    ]

    for path in security_files:
        if path.is_file():
            try:
                code = read_file(path)
            except Exception:
                continue
            rel_path = str(path.relative_to(root))
            lang = "python" if path.suffix == ".py" else "javascript"
            chunks = chunk_by_function(code, language=lang)
            for chunk in chunks:
                chunk.source_file = rel_path
                chunk.chunk_type = "security_pattern"
                records.append(
                    chunk_to_record(
                        chunk,
                        taxonomy_category="knowledge.operational_standards.rbac_from_day_one",
                    )
                )
        elif path.is_dir():
            for src_file in sorted(path.rglob("*.py")) + sorted(path.rglob("*.js")):
                if "node_modules" in str(src_file) or "venv" in str(src_file):
                    continue
                try:
                    code = read_file(src_file)
                except Exception:
                    continue
                if count_tokens(code) < 20:
                    continue
                rel_path = str(src_file.relative_to(root))
                lang = "python" if src_file.suffix == ".py" else "javascript"
                chunks = chunk_by_function(code, language=lang)
                for chunk in chunks:
                    chunk.source_file = rel_path
                    chunk.chunk_type = "security_pattern"
                    records.append(
                        chunk_to_record(
                            chunk,
                            taxonomy_category="skills.quality_engineering.security_audit",
                        )
                    )

    return records


def extract_quality_docs(root: Path) -> list[dict]:
    """Extract quality-related documentation."""
    records: list[dict] = []

    quality_keywords = [
        "test",
        "coverage",
        "quality",
        "tdd",
        "security",
        "review",
        "validation",
        "performance",
        "benchmark",
    ]

    # Check docs/ and root-level .md files
    md_files = list((root / "docs").rglob("*.md")) if (root / "docs").exists() else []
    md_files.extend(root.glob("*.md"))

    for md_file in sorted(set(md_files)):
        name_lower = md_file.stem.lower()
        if not any(kw in name_lower for kw in quality_keywords):
            continue

        try:
            content = read_file(md_file)
        except Exception:
            continue

        if count_tokens(content) < 50:
            continue

        rel_path = str(md_file.relative_to(root))
        doc_chunks = chunk_by_heading(content)
        for chunk in doc_chunks:
            chunk.source_file = rel_path
            chunk.chunk_type = "quality_documentation"
            records.append(chunk_to_record(chunk))

    return records


def run() -> list[dict]:
    """Run the full quality standards extraction pipeline."""
    print("Extracting quality standards from Silver Surfer Platform...")
    print(f"  Source: {SILVER_SURFER_ROOT}")
    root = SILVER_SURFER_ROOT

    all_records: list[dict] = []

    print("  [1/4] Extracting quality gate definitions...")
    gate_records = extract_quality_gate_definitions(root)
    print(f"         {len(gate_records)} chunks")
    all_records.extend(gate_records)

    print("  [2/4] Extracting CI/CD and deployment patterns...")
    cicd_records = extract_cicd_patterns(root)
    print(f"         {len(cicd_records)} chunks")
    all_records.extend(cicd_records)

    print("  [3/4] Extracting security and auth patterns...")
    security_records = extract_security_patterns(root)
    print(f"         {len(security_records)} chunks")
    all_records.extend(security_records)

    print("  [4/4] Extracting quality documentation...")
    doc_records = extract_quality_docs(root)
    print(f"         {len(doc_records)} chunks")
    all_records.extend(doc_records)

    # Summary
    print(f"\n  Total: {len(all_records)} quality standard chunks")
    cat_counts = Counter(r["taxonomy_category"] for r in all_records)
    print("  Per category:")
    for cat, count in cat_counts.most_common():
        print(f"    {cat}: {count}")

    write_jsonl(all_records, OUTPUT_FILE)
    print(f"\n  Written to {OUTPUT_FILE}")

    return all_records


if __name__ == "__main__":
    run()
