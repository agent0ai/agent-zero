import json
from pathlib import Path

import jsonschema

ROOT = Path(__file__).resolve().parents[1]


def _load(path: Path):
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def test_eval_cases_extended_schema():
    data = _load(ROOT / "app_spec" / "eval_cases_extended.json")
    schema = _load(ROOT / "app_spec" / "eval_cases_extended.schema.json")
    jsonschema.validate(instance=data, schema=schema)
