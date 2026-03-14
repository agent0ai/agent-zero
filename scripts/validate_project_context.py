#!/usr/bin/env python3
from __future__ import annotations

import argparse
import sys
from pathlib import Path

import yaml

REQUIRED_TOP_LEVEL = [
    "version",
    "project",
    "skills",
    "commands",
    "workflows",
    "runbooks",
    "guardrails",
    "success_criteria",
]


def _err(msg: str) -> None:
    print(f"[FAIL] {msg}")


def _ok(msg: str) -> None:
    print(f"[PASS] {msg}")


def validate_manifest(path: Path) -> int:
    if not path.exists():
        _err(f"manifest not found: {path}")
        return 1

    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        _err("manifest root must be a mapping")
        return 1

    failures = 0
    for key in REQUIRED_TOP_LEVEL:
        if key not in data:
            failures += 1
            _err(f"missing top-level key: {key}")

    project = data.get("project", {})
    for key in ["id", "name", "mission", "owners"]:
        if key not in project:
            failures += 1
            _err(f"project missing key: {key}")

    def validate_refs(section: str) -> None:
        nonlocal failures
        items = data.get(section, [])
        if not isinstance(items, list) or len(items) == 0:
            failures += 1
            _err(f"{section} must be a non-empty list")
            return

        for idx, item in enumerate(items):
            if not isinstance(item, dict):
                failures += 1
                _err(f"{section}[{idx}] must be a mapping")
                continue
            if "id" not in item:
                failures += 1
                _err(f"{section}[{idx}] missing id")
            if "ref" not in item:
                failures += 1
                _err(f"{section}[{idx}] missing ref")
                continue
            ref = str(item["ref"])
            if ref.startswith("http://") or ref.startswith("https://"):
                continue
            ref_path = (Path.cwd() / ref).resolve()
            if not ref_path.exists():
                failures += 1
                _err(f"{section}[{idx}] ref not found: {ref}")

    for section in ["skills", "commands", "workflows", "runbooks"]:
        validate_refs(section)

    guardrails = data.get("guardrails", [])
    if not isinstance(guardrails, list) or len(guardrails) == 0:
        failures += 1
        _err("guardrails must be a non-empty list")
    else:
        for idx, item in enumerate(guardrails):
            if not isinstance(item, dict) or "id" not in item or "rule" not in item:
                failures += 1
                _err(f"guardrails[{idx}] must include id and rule")

    criteria = data.get("success_criteria", [])
    if not isinstance(criteria, list) or len(criteria) == 0:
        failures += 1
        _err("success_criteria must be a non-empty list")
    else:
        for idx, item in enumerate(criteria):
            if not isinstance(item, dict):
                failures += 1
                _err(f"success_criteria[{idx}] must be a mapping")
                continue
            for key in ["id", "metric", "target", "evidence"]:
                if key not in item:
                    failures += 1
                    _err(f"success_criteria[{idx}] missing {key}")

    if failures:
        _err(f"validation failed with {failures} issue(s)")
        return 1

    _ok(f"manifest valid: {path}")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate unified project context manifest")
    parser.add_argument(
        "--manifest",
        default="project_context/agent_jumbo.context.yaml",
        help="Path to context manifest",
    )
    args = parser.parse_args()
    return validate_manifest(Path(args.manifest))


if __name__ == "__main__":
    sys.exit(main())
