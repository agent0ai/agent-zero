from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Iterable, Literal
from urllib.parse import parse_qs, urlparse


OFFICIAL_DOMAIN_PRIORITY: list[tuple[str, int, str]] = [
    ("planalto.gov.br", 0, "Planalto"),
    ("stf.jus.br", 1, "STF"),
    ("stj.jus.br", 2, "STJ"),
    ("in.gov.br", 3, "DOU"),
    ("lexml.gov.br", 4, "LexML"),
]


def _hostname(url: str) -> str:
    try:
        return (urlparse(url).hostname or "").lower()
    except Exception:
        return ""


def is_official_brazil_source(url: str) -> bool:
    host = _hostname(url)
    if not host:
        return False
    if host.endswith(".gov.br") or host.endswith(".jus.br"):
        return True
    return any(host == d or host.endswith("." + d) for d, _, _ in OFFICIAL_DOMAIN_PRIORITY)


def official_source_priority(url: str) -> int:
    host = _hostname(url)
    if not host:
        return 10_000

    for domain, priority, _label in OFFICIAL_DOMAIN_PRIORITY:
        if host == domain or host.endswith("." + domain):
            return priority

    if host.endswith(".gov.br") or host.endswith(".jus.br"):
        return 100

    return 10_000


def official_source_label(url: str) -> str | None:
    host = _hostname(url)
    if not host:
        return None

    for domain, _priority, label in OFFICIAL_DOMAIN_PRIORITY:
        if host == domain or host.endswith("." + domain):
            return label

    if host.endswith(".gov.br"):
        return "gov.br"
    if host.endswith(".jus.br"):
        return "jus.br"
    return None


def select_sources_official_first(
    items: Iterable[dict[str, Any]], *, limit: int
) -> list[dict[str, Any]]:
    indexed = [(idx, item) for idx, item in enumerate(items) if isinstance(item, dict)]

    official = [
        (idx, item)
        for idx, item in indexed
        if is_official_brazil_source(str(item.get("url", "")))
    ]
    if official:
        official_sorted = sorted(
            official,
            key=lambda pair: (
                official_source_priority(str(pair[1].get("url", ""))),
                pair[0],
            ),
        )
        return [item for _idx, item in official_sorted[:limit]]

    return [item for _idx, item in indexed[:limit]]


def _normalize_date(value: Any) -> str | None:
    if value is None:
        return None
    if isinstance(value, (int, float)) and value > 0:
        try:
            return datetime.utcfromtimestamp(value).date().isoformat()
        except Exception:
            return None

    text = str(value).strip()
    if not text:
        return None

    match = re.match(r"^(\d{4}-\d{2}-\d{2})", text)
    if match:
        return match.group(1)

    return text


_URN_RE = re.compile(r"(urn:lex:[^\s\"'>]+)", re.IGNORECASE)


def _extract_urn_lex(text: str) -> str | None:
    if not text:
        return None
    match = _URN_RE.search(text)
    if not match:
        return None
    return match.group(1)


def _safe_identifier_from_url(url: str) -> str:
    parsed = urlparse(url)
    host = (parsed.hostname or "").lower()
    path = (parsed.path or "").strip()
    if not host:
        return url.strip()

    query = parse_qs(parsed.query or "")
    for key in ("incidente", "processo", "id", "numero", "numero_registro"):
        if key in query and query[key]:
            return f"{host}{path}?{key}={query[key][0]}"

    if not path or path == "/":
        return host

    normalized_path = re.sub(r"/+", "/", path).rstrip("/")
    return f"{host}{normalized_path}"


def source_identifier(item: dict[str, Any]) -> str:
    url = str(item.get("url", "")).strip()
    title = str(item.get("title", "")).strip()
    content = str(item.get("content", "")).strip()

    urn = _extract_urn_lex(url) or _extract_urn_lex(title) or _extract_urn_lex(content)
    if urn:
        return urn

    explicit_id = item.get("id")
    if explicit_id:
        return str(explicit_id).strip()

    return _safe_identifier_from_url(url) if url else (title or "—")


def _quote_snippet(text: str, *, max_len: int = 240) -> str:
    cleaned = re.sub(r"\s+", " ", (text or "").strip())
    if not cleaned:
        return "—"
    if len(cleaned) > max_len:
        cleaned = cleaned[: max_len - 1].rstrip() + "…"
    cleaned = cleaned.replace('"', "'")
    return f"\"{cleaned}\""


@dataclass(frozen=True)
class BrazilCitation:
    index: int
    source_type: str
    identifier: str
    date: str | None
    url: str
    snippet: str
    title: str | None = None

    def to_markdown(self) -> str:
        date_value = self.date if self.date else "—"
        title_line = f"Título: {self.title}\n" if self.title else ""
        return (
            f"[{self.index}] Tipo: {self.source_type}\n"
            f"{title_line}"
            f"Identificador: {self.identifier}\n"
            f"Data: {date_value}\n"
            f"URL: {self.url}\n"
            f"Trecho: {self.snippet}"
        )


def build_brazil_citations(items: Iterable[dict[str, Any]]) -> list[BrazilCitation]:
    citations: list[BrazilCitation] = []
    for index, item in enumerate(items, start=1):
        url = str(item.get("url", "")).strip()
        host_label = official_source_label(url)
        is_official = is_official_brazil_source(url)
        source_type = (
            "Oficial" + (f" ({host_label})" if host_label else "")
            if is_official
            else "Não-oficial"
        )

        date = _normalize_date(
            item.get("publishedDate") or item.get("published_date") or item.get("date")
        )
        title = str(item.get("title", "")).strip() or None

        raw_snippet = str(item.get("qa") or item.get("content") or "").strip()
        snippet = _quote_snippet(raw_snippet)

        citations.append(
            BrazilCitation(
                index=index,
                source_type=source_type,
                identifier=source_identifier(item),
                date=date,
                url=url or "—",
                snippet=snippet,
                title=title,
            )
        )
    return citations


def format_brazil_citations_markdown(
    items: Iterable[dict[str, Any]],
    *,
    heading: str = "Fontes",
    include_heading: bool = True,
) -> str:
    citations = build_brazil_citations(items)
    if not citations:
        return ""
    body = "\n\n".join(c.to_markdown() for c in citations)
    return f"## {heading}\n{body}" if include_heading else body


BrazilCitationBlockStatus = Literal["ok", "missing", "invalid"]


@dataclass(frozen=True)
class BrazilCitationBlockValidation:
    status: BrazilCitationBlockStatus
    entry_count: int
    urls: list[str]
    errors: list[str]

    @property
    def ok(self) -> bool:
        return self.status == "ok"


_FONTES_HEADING_RE = re.compile(r"(?im)^(#{2,3})\s*Fontes\s*$")
_NEXT_HEADING_RE = re.compile(r"(?im)^#{1,6}\s+\S+")
_ENTRY_START_RE = re.compile(r"(?im)^\[(\d+)\]\s*Tipo\s*:\s*(.+)$")
_FIELD_RE = {
    "identificador": re.compile(r"(?im)^Identificador\s*:\s*(.+)$"),
    "data": re.compile(r"(?im)^Data\s*:\s*(.+)$"),
    "url": re.compile(r"(?im)^URL\s*:\s*(.+)$"),
    "trecho": re.compile(r"(?im)^Trecho\s*:\s*(.+)$"),
}
_URL_RE = re.compile(r"https?://[^\s]+")


def _clean_url(url: str) -> str:
    return (url or "").strip().rstrip(").,;\"'>]}")  # common trailing punctuation


def validate_brazil_citation_block(text: str) -> BrazilCitationBlockValidation:
    """
    Syntactic validation for the Brazil (PT-BR) citation block format.

    This is intentionally offline-only (no live URL fetch).
    """
    content = (text or "").strip()
    if not content:
        return BrazilCitationBlockValidation(
            status="missing", entry_count=0, urls=[], errors=["empty text"]
        )

    heading_match = _FONTES_HEADING_RE.search(content)
    if not heading_match:
        return BrazilCitationBlockValidation(
            status="missing",
            entry_count=0,
            urls=[],
            errors=["missing 'Fontes' heading"],
        )

    start = heading_match.end()
    after = content[start:]
    next_heading = _NEXT_HEADING_RE.search(after)
    section = after[: next_heading.start()] if next_heading else after
    section = section.strip()
    if not section:
        return BrazilCitationBlockValidation(
            status="invalid",
            entry_count=0,
            urls=[],
            errors=["empty 'Fontes' section"],
        )

    entries = list(_ENTRY_START_RE.finditer(section))
    if not entries:
        return BrazilCitationBlockValidation(
            status="invalid",
            entry_count=0,
            urls=[],
            errors=["no numbered entries found"],
        )

    errors: list[str] = []
    urls: list[str] = []
    for i, match in enumerate(entries):
        entry_no = match.group(1)
        entry_start = match.start()
        entry_end = entries[i + 1].start() if i + 1 < len(entries) else len(section)
        entry_text = section[entry_start:entry_end].strip()

        for field_name, field_re in _FIELD_RE.items():
            if not field_re.search(entry_text):
                errors.append(f"entry [{entry_no}] missing field: {field_name}")

        url_line = _FIELD_RE["url"].search(entry_text)
        url_value = (url_line.group(1).strip() if url_line else "").strip()
        extracted = [_clean_url(u) for u in _URL_RE.findall(url_value)]
        extracted = [u for u in extracted if u.startswith("http://") or u.startswith("https://")]
        if not extracted:
            errors.append(f"entry [{entry_no}] URL missing or invalid")
        else:
            urls.extend(extracted)

    # Deduplicate while preserving order
    urls = list(dict.fromkeys(urls))

    if errors:
        return BrazilCitationBlockValidation(
            status="invalid",
            entry_count=len(entries),
            urls=urls,
            errors=errors,
        )

    return BrazilCitationBlockValidation(
        status="ok", entry_count=len(entries), urls=urls, errors=[]
    )
