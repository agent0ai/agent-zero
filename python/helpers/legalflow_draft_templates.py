from __future__ import annotations

import re
import unicodedata

from python.helpers import files


CANONICAL_DRAFT_DOCUMENT_TYPES: tuple[str, ...] = (
    "petição inicial",
    "contestação",
    "apelação",
    "contrato prestação de serviços",
)


_TEMPLATE_BY_CANONICAL: dict[str, str] = {
    "petição inicial": "agents/legalflow_draft/templates/peticao_inicial.md",
    "contestação": "agents/legalflow_draft/templates/contestacao.md",
    "apelação": "agents/legalflow_draft/templates/apelacao.md",
    "contrato prestação de serviços": "agents/legalflow_draft/templates/contrato_prestacao_servicos.md",
}


def _strip_accents(text: str) -> str:
    normalized = unicodedata.normalize("NFKD", text)
    return "".join(ch for ch in normalized if not unicodedata.combining(ch))


def _norm_spaces(text: str) -> str:
    return re.sub(r"\s+", " ", (text or "").strip())


def _norm_doc_type(text: str) -> str:
    text = _norm_spaces(text).lower()
    text = text.replace("–", "-").replace("—", "-")
    text = _strip_accents(text)
    text = re.sub(r"[^a-z0-9 ]+", " ", text)
    text = _norm_spaces(text)
    return text


_ALIASES: dict[str, str] = {
    _norm_doc_type("petição inicial"): "petição inicial",
    _norm_doc_type("contestação"): "contestação",
    _norm_doc_type("apelação"): "apelação",
    _norm_doc_type("contrato prestação de serviços"): "contrato prestação de serviços",
    _norm_doc_type("contrato de prestação de serviços"): "contrato prestação de serviços",
}


def normalize_draft_document_type(value: str | None) -> str | None:
    if not value:
        return None
    normalized = _norm_doc_type(value)
    return _ALIASES.get(normalized)


def is_supported_draft_document_type(value: str | None) -> bool:
    return normalize_draft_document_type(value) in _TEMPLATE_BY_CANONICAL


def supported_draft_document_types_markdown() -> str:
    return "\n".join(f"- {t}" for t in CANONICAL_DRAFT_DOCUMENT_TYPES)


def load_draft_template(canonical_document_type: str) -> str:
    path = _TEMPLATE_BY_CANONICAL.get(canonical_document_type)
    if not path:
        raise ValueError(f"Unsupported canonical_document_type: {canonical_document_type!r}")
    return files.read_file(path)

