from __future__ import annotations

from dataclasses import dataclass
import hashlib
import re
from typing import Any

from python.helpers.citations_br import BrazilCitationBlockValidation, validate_brazil_citation_block


_PLACEHOLDER_RE = re.compile(
    r"(?is)\b("
    r"todo|tbd|fixme|"
    r"insert\s+\w+|"
    r"\[\[.*?\]\]|"
    r"<\s*insert.*?>"
    r")\b"
)


def _sha256(text: str) -> str:
    h = hashlib.sha256()
    h.update((text or "").encode("utf-8", errors="ignore"))
    return "sha256:" + h.hexdigest()


@dataclass(frozen=True)
class ReviewChecklistItem:
    name: str
    passed: bool
    details: str


@dataclass(frozen=True)
class ReviewReport:
    passed: bool
    checklist: list[ReviewChecklistItem]
    risk_flags: list[str]
    citation_validation: BrazilCitationBlockValidation
    document_hash: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "passed": self.passed,
            "checklist": [
                {"name": i.name, "passed": i.passed, "details": i.details}
                for i in self.checklist
            ],
            "risk_flags": self.risk_flags,
            "citation_validation": {
                "status": self.citation_validation.status,
                "entry_count": self.citation_validation.entry_count,
                "urls": self.citation_validation.urls,
                "errors": self.citation_validation.errors,
            },
            "document_hash": self.document_hash,
        }

    def to_markdown(self) -> str:
        status = "PASS" if self.passed else "FAIL"
        lines: list[str] = []
        lines.append(f"Review status: {status}")
        lines.append("")
        lines.append("Checklist:")
        for item in self.checklist:
            lines.append(f"- {item.name}: {'PASS' if item.passed else 'FAIL'} — {item.details}")
        lines.append("")
        lines.append("Risk flags:")
        if self.risk_flags:
            for flag in self.risk_flags:
                lines.append(f"- {flag}")
        else:
            lines.append("- none")
        lines.append("")
        lines.append("Citation validation (Brazil 'Fontes'):")
        cv = self.citation_validation
        lines.append(f"- status: {cv.status}")
        lines.append(f"- entries: {cv.entry_count}")
        lines.append(f"- urls: {len(cv.urls)}")
        if cv.errors:
            lines.append("- errors:")
            for err in cv.errors[:10]:
                lines.append(f"  - {err}")
        return "\n".join(lines).strip() + "\n"


def build_review_report(document_text: str) -> ReviewReport:
    doc = (document_text or "").strip()
    doc_hash = _sha256(doc)

    risk_flags: list[str] = []
    checklist: list[ReviewChecklistItem] = []

    has_doc = len(doc) >= 30
    checklist.append(
        ReviewChecklistItem(
            name="Document provided",
            passed=has_doc,
            details="non-empty document text" if has_doc else "missing/too short",
        )
    )
    if not has_doc:
        risk_flags.append("document_missing_or_too_short")

    placeholders = bool(_PLACEHOLDER_RE.search(doc))
    checklist.append(
        ReviewChecklistItem(
            name="No placeholders",
            passed=not placeholders,
            details="no TODO/TBD/[[...]] placeholders detected"
            if not placeholders
            else "placeholders detected (TODO/TBD/[[...]]/insert...)",
        )
    )
    if placeholders:
        risk_flags.append("placeholders_present")

    citation_validation = validate_brazil_citation_block(doc)
    citations_ok = citation_validation.status != "invalid"
    checklist.append(
        ReviewChecklistItem(
            name="Citations block valid (Brazil 'Fontes')",
            passed=citations_ok,
            details=(
                "valid format"
                if citation_validation.status == "ok"
                else (
                    "missing 'Fontes' section (warning)"
                    if citation_validation.status == "missing"
                    else "invalid 'Fontes' section"
                )
            ),
        )
    )
    if citation_validation.status == "missing":
        risk_flags.append("citations_missing_fontes_section")
    elif citation_validation.status == "invalid":
        risk_flags.append("citations_invalid_fontes_section")

    passed = all(i.passed for i in checklist if i.name != "Citations block valid (Brazil 'Fontes')") and citations_ok

    return ReviewReport(
        passed=passed,
        checklist=checklist,
        risk_flags=risk_flags,
        citation_validation=citation_validation,
        document_hash=doc_hash,
    )

