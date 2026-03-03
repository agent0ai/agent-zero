from __future__ import annotations

import argparse
import ast
import json
from collections import defaultdict
from dataclasses import asdict
from pathlib import Path

from python.helpers import files

from legalflow.public_corpus.manifest import Manifest


def _default_corpus_dir() -> Path:
    return Path(files.get_abs_path("usr/knowledge/custom/legalflow/public_corpus"))


def _parse_front_matter(md_text: str) -> dict[str, object]:
    lines = md_text.splitlines()
    if not lines or lines[0].strip() != "---":
        return {}
    out: dict[str, object] = {}
    i = 1
    while i < len(lines):
        line = lines[i].rstrip("\n")
        if line.strip() == "---":
            break
        if not line.strip():
            i += 1
            continue
        if ":" not in line:
            i += 1
            continue
        key, rest = line.split(":", 1)
        key = key.strip()
        rest = rest.strip()
        if rest == "null":
            out[key] = None
        else:
            try:
                out[key] = ast.literal_eval(rest)
            except Exception:
                out[key] = rest
        i += 1
    return out


def validate_public_corpus(corpus_dir: Path) -> dict[str, object]:
    manifest_path = corpus_dir / "manifest.json"
    manifest = Manifest.load(manifest_path)

    ok = True
    missing_files: list[str] = []
    hash_mismatches: list[str] = []

    counts_by_source: dict[str, int] = defaultdict(int)
    counts_by_source_type: dict[str, dict[str, int]] = defaultdict(lambda: defaultdict(int))
    examples_by_source: dict[str, list[str]] = defaultdict(list)

    for doc_id, entry in manifest.documents.items():
        counts_by_source[entry.source] += 1
        counts_by_source_type[entry.source][entry.doc_type] += 1
        if len(examples_by_source[entry.source]) < 3:
            examples_by_source[entry.source].append(doc_id)

        file_path = corpus_dir / entry.path
        if not file_path.exists():
            ok = False
            missing_files.append(entry.path)
            continue

        front = _parse_front_matter(file_path.read_text(encoding="utf-8"))
        file_hash = front.get("content_sha256")
        if isinstance(file_hash, str) and file_hash != entry.content_sha256:
            ok = False
            hash_mismatches.append(entry.path)

    return {
        "ok": ok,
        "manifest_path": str(manifest_path),
        "total": len(manifest.documents),
        "counts_by_source": {k: int(v) for k, v in counts_by_source.items()},
        "counts_by_source_type": {k: dict(v) for k, v in counts_by_source_type.items()},
        "examples_by_source": dict(examples_by_source),
        "missing_files": missing_files,
        "hash_mismatches": hash_mismatches,
    }


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(prog="python -m legalflow.validate_public_corpus")
    p.add_argument("--output-dir", type=str, default=None, help="Override corpus output directory.")
    p.add_argument("--json", action="store_true", help="Print JSON output.")
    args = p.parse_args(argv)

    corpus_dir = Path(args.output_dir) if args.output_dir else _default_corpus_dir()
    result = validate_public_corpus(corpus_dir)
    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        print(f"ok={result['ok']}")
        print(f"total={result['total']}")
        print(f"manifest_path={result['manifest_path']}")
        print(f"counts_by_source={result['counts_by_source']}")
        print(f"examples_by_source={result['examples_by_source']}")
    return 0 if result["ok"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
