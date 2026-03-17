from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable


DEFAULT_PREDICTIONS_PATH = Path("memory") / "survey_predictions.jsonl"


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _stable_hash(data: Any) -> str:
    raw = json.dumps(data, sort_keys=True, ensure_ascii=False, separators=(",", ":")).encode(
        "utf-8"
    )
    return hashlib.sha256(raw).hexdigest()[:16]


def build_question_id(*, url: str, field: dict[str, Any]) -> str:
    key = {
        "url": url,
        "kind": field.get("kind"),
        "input_type": field.get("input_type"),
        "name": field.get("name"),
        "id": field.get("id"),
        "label": field.get("label"),
        "options": field.get("options") or [],
    }
    return f"q_{_stable_hash(key)}"


@dataclass
class Candidate:
    value: str
    confidence: float


@dataclass
class PredictionRecord:
    """
    A single predicted answer for a question/field, stored for later review/clarification.
    """

    id: str
    timestamp: str
    url: str
    title: str
    field_index: int
    field: dict[str, Any]
    selected: str
    confidence: float
    candidates: list[Candidate]
    rationale: str
    needs_clarification: bool
    source: str  # llm|heuristic|profile

    def to_jsonl(self) -> str:
        data = asdict(self)
        data["candidates"] = [asdict(c) for c in self.candidates]
        return json.dumps(data, ensure_ascii=False)


def append_predictions(
    records: Iterable[PredictionRecord],
    *,
    path: str | Path = DEFAULT_PREDICTIONS_PATH,
) -> Path:
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    with p.open("a", encoding="utf-8") as f:
        for r in records:
            f.write(r.to_jsonl() + "\n")
    return p


def load_predictions(path: str | Path = DEFAULT_PREDICTIONS_PATH) -> list[dict[str, Any]]:
    p = Path(path)
    if not p.exists():
        return []
    out: list[dict[str, Any]] = []
    for line in p.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            obj = json.loads(line)
            if isinstance(obj, dict):
                out.append(obj)
        except Exception:
            continue
    return out


def pending_predictions(
    path: str | Path = DEFAULT_PREDICTIONS_PATH,
) -> list[dict[str, Any]]:
    return [r for r in load_predictions(path) if r.get("needs_clarification") is True]


def write_clarifications(
    clarifications: dict[str, str],
    *,
    path: str | Path = Path("memory") / "survey_clarifications.json",
) -> Path:
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    existing: dict[str, str] = {}
    if p.exists():
        try:
            obj = json.loads(p.read_text(encoding="utf-8"))
            if isinstance(obj, dict):
                existing = {str(k): str(v) for k, v in obj.items()}
        except Exception:
            existing = {}
    existing.update({str(k): str(v) for k, v in clarifications.items()})
    p.write_text(json.dumps(existing, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return p


def utc_now_iso() -> str:
    # exported helper
    return _utc_now_iso()

