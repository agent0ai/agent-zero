from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Literal


class FieldKind(str, Enum):
    TEXT = "text"
    TEXTAREA = "textarea"
    EMAIL = "email"
    NUMBER = "number"
    DATE = "date"
    SELECT = "select"
    RADIO = "radio"
    CHECKBOX = "checkbox"
    BUTTON = "button"
    UNKNOWN = "unknown"


@dataclass(frozen=True)
class Persona:
    id: str
    name: str
    description: str
    constraints: dict[str, Any] = field(default_factory=dict)


@dataclass
class UserProfile:
    id: str
    persona_id: str | None
    data: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class SurveyField:
    selector: str
    kind: FieldKind
    name: str | None = None
    label: str | None = None
    placeholder: str | None = None
    options: list[str] = field(default_factory=list)  # for select/radio/checkbox
    option_selectors: dict[str, str] = field(default_factory=dict)
    required: bool = False


@dataclass(frozen=True)
class SurveyPage:
    url: str
    title: str | None
    fields: list[SurveyField]
    raw_dom: str


@dataclass(frozen=True)
class AnswerAction:
    action: Literal["fill", "click", "press", "select"]
    selector: str | None = None
    text: str | None = None
    key: str | None = None
    meta: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class SurveyAnswer:
    field: SurveyField
    answer_text: str
    confidence: float = 0.5
    rationale: str | None = None

