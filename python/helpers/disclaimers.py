from __future__ import annotations

import re


_LEGAL_DISCLAIMER_HEADER = "Disclaimer"
LEGALFLOW_DISCLAIMER_TEXT = (
    "I am not a lawyer and this is not legal advice. This is general information and drafting assistance "
    "based on the details provided; laws vary by jurisdiction. Consider consulting a qualified attorney "
    "for advice on your specific situation. This does not create an attorney-client relationship."
)


_DISCLAIMER_RE = re.compile(
    r"(?is)\b("
    r"not\s+legal\s+advice|"
    r"no\s+legal\s+advice|"
    r"i\s+am\s+not\s+a\s+lawyer|"
    r"não\s+constitui\s+aconselhamento\s+jur[ií]dico|"
    r"isto\s+não\s+[eé]\s+aconselhamento\s+jur[ií]dico|"
    r"n[aã]o\s+sou\s+advogad[oa]"
    r")\b"
)


def has_legal_disclaimer(text: str) -> bool:
    if not text:
        return False
    return bool(_DISCLAIMER_RE.search(text))


def ensure_legal_disclaimer(text: str) -> str:
    """
    Ensures a legal disclaimer exists in assistant-facing output.

    Intentionally appends a standalone section so it doesn't contaminate drafted documents.
    """
    text = (text or "").rstrip()
    if not text:
        return text
    if has_legal_disclaimer(text):
        return text
    return (
        f"{text}\n\n"
        f"## {_LEGAL_DISCLAIMER_HEADER}\n"
        f"{LEGALFLOW_DISCLAIMER_TEXT}\n"
    )

