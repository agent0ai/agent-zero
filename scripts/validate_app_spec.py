#!/usr/bin/env python3
import json
import os
import sys
from typing import Any


def _load_json(path: str) -> Any:
    with open(path, "r", encoding="utf-8") as handle:
        return json.load(handle)


def _resolve(root: str, rel: str) -> str:
    return os.path.normpath(os.path.join(root, rel))


def main() -> int:
    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    spec_root = os.path.join(root, "app_spec")
    manifest_path = os.path.join(spec_root, "manifest.json")

    if not os.path.exists(manifest_path):
        print("Missing app_spec/manifest.json")
        return 1

    try:
        import jsonschema  # type: ignore
    except ImportError:
        print("Missing dependency: jsonschema")
        print("Install with: pip install jsonschema")
        return 1

    manifest = _load_json(manifest_path)
    specs = manifest.get("specs", [])
    schemas = manifest.get("schemas", [])

    schema_map = {}
    for schema in schemas:
        schema_path = _resolve(spec_root, schema)
        if not os.path.exists(schema_path):
            print(f"Missing schema: {schema_path}")
            return 1
        schema_map[os.path.basename(schema_path)] = _load_json(schema_path)

    failures = 0

    for spec in specs:
        spec_path = _resolve(spec_root, spec)
        if not os.path.exists(spec_path):
            print(f"Missing spec: {spec_path}")
            failures += 1
            continue
        data = _load_json(spec_path)
        schema_ref = data.get("$schema")
        if not schema_ref:
            print(f"Missing $schema in {spec_path}")
            failures += 1
            continue
        schema_name = os.path.basename(schema_ref)
        schema = schema_map.get(schema_name)
        if not schema:
            print(f"Schema not found for {spec_path}: {schema_ref}")
            failures += 1
            continue
        try:
            jsonschema.validate(instance=data, schema=schema)
        except jsonschema.ValidationError as exc:
            print(f"Validation failed for {spec_path}: {exc.message}")
            failures += 1

    if failures:
        print(f"Validation failed: {failures} issue(s)")
        return 1

    print("App spec validation passed")
    return 0


if __name__ == "__main__":
    sys.exit(main())
