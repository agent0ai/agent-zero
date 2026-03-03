from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Iterable
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

