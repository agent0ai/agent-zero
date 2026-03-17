from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


DEFAULT_PROFILE_PATH = Path("memory") / "survey_profile.json"


@dataclass
class SurveyProfile:
    """
    A user-owned profile used to answer surveys honestly and consistently.

    This is not a "made-up persona" generator. It's meant to store real, user-approved facts
    and preferences that can be reused across surveys.
    """

    demographics: dict[str, Any] = field(default_factory=dict)
    preferences: dict[str, Any] = field(default_factory=dict)
    writing_style: dict[str, Any] = field(default_factory=dict)
    misc: dict[str, Any] = field(default_factory=dict)

    @classmethod
    def load(cls, path: str | Path = DEFAULT_PROFILE_PATH) -> "SurveyProfile":
        p = Path(path)
        if not p.exists():
            return cls()
        data = json.loads(p.read_text(encoding="utf-8"))
        if not isinstance(data, dict):
            return cls()
        return cls(
            demographics=dict(data.get("demographics") or {}),
            preferences=dict(data.get("preferences") or {}),
            writing_style=dict(data.get("writing_style") or {}),
            misc=dict(data.get("misc") or {}),
        )

    def save(self, path: str | Path = DEFAULT_PROFILE_PATH) -> None:
        p = Path(path)
        p.parent.mkdir(parents=True, exist_ok=True)
        payload = {
            "demographics": self.demographics,
            "preferences": self.preferences,
            "writing_style": self.writing_style,
            "misc": self.misc,
        }
        p.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    def as_dict(self) -> dict[str, Any]:
        return {
            "demographics": self.demographics,
            "preferences": self.preferences,
            "writing_style": self.writing_style,
            "misc": self.misc,
        }

    def merge_updates(self, updates: dict[str, Any]) -> None:
        """
        Shallow-merge updates into the profile. Intended for user-approved updates.
        """
        for key in ("demographics", "preferences", "writing_style", "misc"):
            val = updates.get(key)
            if isinstance(val, dict):
                getattr(self, key).update(val)

