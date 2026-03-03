from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
import re
from typing import Any


class LegalFlowIntent(str, Enum):
    RESEARCH = "research"
    DRAFT = "draft"
    REVIEW = "review"
    DOCS = "docs"


INTENT_ALIASES: dict[str, LegalFlowIntent] = {
    "research": LegalFlowIntent.RESEARCH,
    "analyze": LegalFlowIntent.RESEARCH,
    "analysis": LegalFlowIntent.RESEARCH,
    "draft": LegalFlowIntent.DRAFT,
    "write": LegalFlowIntent.DRAFT,
    "compose": LegalFlowIntent.DRAFT,
    "review": LegalFlowIntent.REVIEW,
    "redline": LegalFlowIntent.REVIEW,
    "revise": LegalFlowIntent.REVIEW,
    "docs": LegalFlowIntent.DOCS,
    "documentation": LegalFlowIntent.DOCS,
    "playbook": LegalFlowIntent.DOCS,
    "template": LegalFlowIntent.DOCS,
}


def _norm_key(key: str) -> str:
    key = key.strip().lower()
    key = re.sub(r"[^a-z0-9]+", "_", key)
    return key.strip("_")


def parse_key_values(text: str) -> dict[str, str]:
    """
    Parses a lightweight "key: value" intake block from free-form text.
    Example:
      intent: draft
      jurisdiction: CA, USA
    """
    result: dict[str, str] = {}
    if not text:
        return result

    for raw_line in text.splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        match = re.match(r"^([A-Za-z0-9][A-Za-z0-9 _-]{0,60}?)\s*:\s*(.+)$", line)
        if not match:
            continue
        key = _norm_key(match.group(1))
        value = match.group(2).strip()
        if key and value:
            result[key] = value
    return result


def infer_intent(text: str) -> LegalFlowIntent | None:
    if not text:
        return None
    lowered = text.lower()

    signals: dict[LegalFlowIntent, list[str]] = {
        LegalFlowIntent.RESEARCH: ["research", "find", "citations", "case law", "authority", "precedent"],
        LegalFlowIntent.DRAFT: ["draft", "write", "prepare", "compose", "letter", "motion", "agreement", "contract"],
        LegalFlowIntent.REVIEW: ["review", "redline", "revise", "mark up", "issue spot", "risks"],
        LegalFlowIntent.DOCS: ["docs", "documentation", "playbook", "sop", "runbook", "guide", "template"],
    }

    scored: dict[LegalFlowIntent, int] = {k: 0 for k in LegalFlowIntent}
    for intent, keywords in signals.items():
        for kw in keywords:
            if kw in lowered:
                scored[intent] += 1

    best = max(scored.items(), key=lambda kv: kv[1])
    if best[1] == 0:
        return None
    if list(scored.values()).count(best[1]) > 1:
        return None
    return best[0]


def parse_intent(value: str | None) -> LegalFlowIntent | None:
    if not value:
        return None
    key = _norm_key(value)
    return INTENT_ALIASES.get(key)


def extract_fenced_block(text: str) -> str | None:
    if not text:
        return None
    match = re.search(r"```(?:[A-Za-z0-9_-]+)?\n(.*?)\n```", text, flags=re.DOTALL)
    if not match:
        return None
    block = match.group(1).strip()
    if len(block) < 30:
        return None
    return block


def required_fields(intent: LegalFlowIntent) -> list[str]:
    base = ["jurisdiction"]
    if intent == LegalFlowIntent.RESEARCH:
        return ["question", *base]
    if intent == LegalFlowIntent.DRAFT:
        return ["document_type", "facts", *base]
    if intent == LegalFlowIntent.REVIEW:
        return ["document_text", "review_focus", *base]
    if intent == LegalFlowIntent.DOCS:
        return ["topic", "audience", "format", *base]
    return base


def intent_to_profile(intent: LegalFlowIntent) -> str:
    return {
        LegalFlowIntent.RESEARCH: "legalflow_research",
        LegalFlowIntent.DRAFT: "legalflow_draft",
        LegalFlowIntent.REVIEW: "legalflow_review",
        LegalFlowIntent.DOCS: "legalflow_docs",
    }[intent]


@dataclass
class GatekeeperDecision:
    intent: LegalFlowIntent | None
    fields: dict[str, str]
    missing_fields: list[str]


def decide(text: str, existing_fields: dict[str, str] | None = None) -> GatekeeperDecision:
    fields: dict[str, str] = dict(existing_fields or {})
    parsed = parse_key_values(text)

    if "doc_type" in parsed and "document_type" not in parsed:
        parsed["document_type"] = parsed["doc_type"]
    if "jurisdiction" in parsed:
        parsed["jurisdiction"] = parsed["jurisdiction"].strip()

    fields.update(parsed)

    intent = parse_intent(fields.get("intent")) or infer_intent(text)
    fenced = extract_fenced_block(text)
    if fenced:
        # A new fenced document should override any previous captured document,
        # especially for review flows where users iteratively fix issues.
        if intent in {LegalFlowIntent.REVIEW, LegalFlowIntent.DRAFT}:
            fields["document_text"] = fenced
        elif "document_text" not in fields:
            fields["document_text"] = fenced
    missing: list[str] = []
    if intent is None:
        missing = ["intent"]
    else:
        for key in required_fields(intent):
            if not fields.get(key, "").strip():
                missing.append(key)

    return GatekeeperDecision(intent=intent, fields=fields, missing_fields=missing)


def build_intake_questions(missing: list[str]) -> str:
    from python.helpers.legalflow_draft_templates import (
        supported_draft_document_types_markdown,
    )

    questions: list[str] = []
    for key in missing:
        if key == "intent":
            questions.append("- intent (choose one): research | draft | review | docs")
        elif key == "jurisdiction":
            questions.append("- jurisdiction (e.g., CA, USA; England & Wales; EU)")
        elif key == "question":
            questions.append("- question (what do you need answered?)")
        elif key == "document_type":
            questions.append(
                "- document_type (choose exactly one):\n"
                f"{supported_draft_document_types_markdown()}"
            )
        elif key == "facts":
            questions.append("- facts (key facts / timeline; what happened?)")
        elif key == "document_text":
            questions.append("- document_text (paste the document in a ``` fenced block ```)")
        elif key == "review_focus":
            questions.append("- review_focus (e.g., issue-spot, risks, redlines, compliance)")
        elif key == "topic":
            questions.append("- topic (what documentation should be produced?)")
        elif key == "audience":
            questions.append("- audience (who is this for?)")
        elif key == "format":
            questions.append("- format (bullets, checklist, SOP, memo, template)")
        else:
            questions.append(f"- {key}")
    return "\n".join(questions)


def format_fields_for_downstream(fields: dict[str, Any]) -> str:
    lines: list[str] = []
    for key in sorted(fields.keys()):
        value = fields.get(key)
        if value is None:
            continue
        text = str(value).strip()
        if not text:
            continue
        lines.append(f"{key}: {text}")
    return "\n".join(lines)
