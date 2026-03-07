"""Extract code generation templates and framework-specific patterns.

Processes:
- advanced-code-generator.js — framework templates, language adapters
- tdd-project-generator.js — swarm agents, quality gates, test patterns
- BaseModel.js + middleware — data model patterns
- All test files — testing conventions
"""

from __future__ import annotations

import re
from collections import Counter
from typing import TYPE_CHECKING

from .config import CHUNKS_DIR, SILVER_SURFER_ROOT
from .utils import (
    chunk_by_function,
    chunk_to_record,
    count_tokens,
    read_file,
    write_jsonl,
)

if TYPE_CHECKING:
    from pathlib import Path

OUTPUT_FILE = CHUNKS_DIR / "code_patterns.jsonl"

# Framework detection patterns
FRAMEWORK_PATTERNS = {
    "react": re.compile(r"react|jsx|component|useState|useEffect|redux|next\.js", re.I),
    "express": re.compile(r"express|app\.get|app\.post|router\.|middleware", re.I),
    "fastapi": re.compile(r"fastapi|@app\.(get|post|put|delete)|pydantic|uvicorn", re.I),
    "flask": re.compile(r"flask|@app\.route|Blueprint", re.I),
    "docker": re.compile(r"docker|dockerfile|container|compose|kubernetes|k8s|helm", re.I),
    "testing": re.compile(r"describe\(|it\(|test\(|expect\(|jest|pytest|assert", re.I),
    "database": re.compile(r"CREATE TABLE|sequelize|sqlalchemy|migration|postgres", re.I),
    "auth": re.compile(r"rbac|auth|permission|jwt|token|session|oauth", re.I),
}


def detect_framework(text: str) -> str:
    """Detect the primary framework in a code chunk."""
    scores: dict[str, int] = {}
    for fw, pattern in FRAMEWORK_PATTERNS.items():
        scores[fw] = len(pattern.findall(text))
    if not scores or max(scores.values()) == 0:
        return "general"
    return max(scores, key=lambda k: scores[k])


def extract_code_generator_chunks(root: Path) -> list[dict]:
    """Extract patterns from advanced-code-generator.js."""
    records: list[dict] = []
    path = root / "src" / "services" / "advanced-code-generator.js"
    if not path.exists():
        print(f"  [warn] Not found: {path}")
        return records

    code = read_file(path)
    rel_path = str(path.relative_to(root))
    chunks = chunk_by_function(code, language="javascript")

    for chunk in chunks:
        chunk.source_file = rel_path
        chunk.chunk_type = "code_template"
        framework = detect_framework(chunk.content)
        chunk.extra["framework"] = framework
        records.append(chunk_to_record(chunk, framework=framework))

    return records


def extract_tdd_generator_chunks(root: Path) -> list[dict]:
    """Extract patterns from tdd-project-generator.js."""
    records: list[dict] = []
    path = root / "src" / "services" / "tdd-project-generator.js"
    if not path.exists():
        print(f"  [warn] Not found: {path}")
        return records

    code = read_file(path)
    rel_path = str(path.relative_to(root))
    chunks = chunk_by_function(code, language="javascript")

    for chunk in chunks:
        chunk.source_file = rel_path
        chunk.chunk_type = "quality_gate_pattern"
        framework = detect_framework(chunk.content)
        chunk.extra["framework"] = framework
        records.append(chunk_to_record(chunk, framework=framework))

    return records


def extract_base_model_chunks(root: Path) -> list[dict]:
    """Extract data model and middleware patterns."""
    records: list[dict] = []

    # BaseModel.js
    base_model_path = root / "src" / "models" / "BaseModel.js"
    if base_model_path.exists():
        code = read_file(base_model_path)
        rel_path = str(base_model_path.relative_to(root))
        chunks = chunk_by_function(code, language="javascript")
        for chunk in chunks:
            chunk.source_file = rel_path
            chunk.chunk_type = "data_model_pattern"
            records.append(
                chunk_to_record(
                    chunk,
                    taxonomy_category="knowledge.operational_standards.base_model_inheritance",
                )
            )

    # Other model files
    models_dir = root / "src" / "models"
    if models_dir.exists():
        for model_file in sorted(models_dir.glob("*.js")):
            if model_file.name == "BaseModel.js":
                continue
            code = read_file(model_file)
            rel_path = str(model_file.relative_to(root))
            chunks = chunk_by_function(code, language="javascript")
            for chunk in chunks:
                chunk.source_file = rel_path
                chunk.chunk_type = "data_model_pattern"
                records.append(chunk_to_record(chunk))

    # Middleware files
    middleware_dir = root / "src" / "middleware"
    if middleware_dir.exists():
        for mw_file in sorted(middleware_dir.glob("*.js")):
            code = read_file(mw_file)
            rel_path = str(mw_file.relative_to(root))
            chunks = chunk_by_function(code, language="javascript")
            for chunk in chunks:
                chunk.source_file = rel_path
                chunk.chunk_type = "middleware_pattern"
                records.append(chunk_to_record(chunk))

    # Common middleware (Python services)
    common_dir = root / "services" / "common"
    if common_dir.exists():
        for py_file in sorted(common_dir.glob("*.py")):
            if "middleware" in py_file.name:
                code = read_file(py_file)
                rel_path = str(py_file.relative_to(root))
                chunks = chunk_by_function(code, language="python")
                for chunk in chunks:
                    chunk.source_file = rel_path
                    chunk.chunk_type = "middleware_pattern"
                    records.append(chunk_to_record(chunk))

    return records


def extract_test_patterns(root: Path) -> list[dict]:
    """Scan test files for testing patterns and conventions."""
    records: list[dict] = []

    # Find all test files (skip node_modules, venv, coverage)
    test_patterns = ["**/*.test.js", "**/*.spec.js", "**/test_*.py"]
    test_files: list[Path] = []
    for pattern in test_patterns:
        test_files.extend(root.glob(pattern))

    test_files = [
        f
        for f in test_files
        if "node_modules" not in str(f)
        and "venv" not in str(f)
        and "coverage" not in str(f)
        and "__pycache__" not in str(f)
    ]

    for test_file in sorted(test_files):
        try:
            code = read_file(test_file)
        except Exception:
            continue

        if count_tokens(code) < 30:
            continue

        rel_path = str(test_file.relative_to(root))
        lang = "python" if test_file.suffix == ".py" else "javascript"
        chunks = chunk_by_function(code, language=lang)

        for chunk in chunks:
            chunk.source_file = rel_path
            chunk.chunk_type = "test_pattern"
            framework = detect_framework(chunk.content)
            chunk.extra["framework"] = framework
            records.append(
                chunk_to_record(
                    chunk,
                    taxonomy_category="skills.code_generation.test_generation",
                    framework=framework,
                )
            )

    return records


def run() -> list[dict]:
    """Run the full code patterns extraction pipeline."""
    print("Extracting code patterns from Silver Surfer Platform...")
    print(f"  Source: {SILVER_SURFER_ROOT}")
    root = SILVER_SURFER_ROOT

    all_records: list[dict] = []

    print("  [1/4] Extracting from advanced-code-generator.js...")
    gen_records = extract_code_generator_chunks(root)
    print(f"         {len(gen_records)} chunks")
    all_records.extend(gen_records)

    print("  [2/4] Extracting from tdd-project-generator.js...")
    tdd_records = extract_tdd_generator_chunks(root)
    print(f"         {len(tdd_records)} chunks")
    all_records.extend(tdd_records)

    print("  [3/4] Extracting from BaseModel.js + middleware...")
    model_records = extract_base_model_chunks(root)
    print(f"         {len(model_records)} chunks")
    all_records.extend(model_records)

    print("  [4/4] Extracting from test files...")
    test_records = extract_test_patterns(root)
    print(f"         {len(test_records)} chunks")
    all_records.extend(test_records)

    # Per-framework breakdown
    fw_counts = Counter(r.get("framework", "general") for r in all_records)
    print(f"\n  Total: {len(all_records)} code pattern chunks")
    print("  Per-framework breakdown:")
    for fw, count in fw_counts.most_common():
        print(f"    {fw}: {count}")

    write_jsonl(all_records, OUTPUT_FILE)
    print(f"\n  Written to {OUTPUT_FILE}")

    return all_records


if __name__ == "__main__":
    run()
