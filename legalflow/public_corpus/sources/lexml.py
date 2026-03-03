from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import date
from typing import Iterator
from urllib.parse import urlencode

from ..fetchers import Fetcher
from ..model import DiscoveredDoc, ParsedDoc
from ..utils import parse_ddmmyyyy, years_ago


_ITEMCOUNT_RE = re.compile(r'id="itemCount"\s*>\s*([0-9]+)\s*<', re.IGNORECASE)
_DOC_BLOCK_RE = re.compile(r'<div\s+id="main_\d+"\s+class="docHit".*?>', re.IGNORECASE)
_URN_RE = re.compile(r"(urn:lex:[^<\s\"']+)")
_TITLE_LINK_RE = re.compile(
    r'<a\s+href="(?P<href>/urn/[^"]+)">(?P<title>[^<]+)</a>', re.IGNORECASE
)
_DATE_RE = re.compile(
    r"<b>Data.*?</b></td>\s*<td\s+class=\"col3\">\s*([^<]+)\s*<",
    re.IGNORECASE | re.DOTALL,
)
_EMENTA_RE = re.compile(
    r"<b>Ementa.*?</b></td>\s*<td\s+class=\"col3\">\s*(.*?)\s*</td>",
    re.IGNORECASE | re.DOTALL,
)


def _strip_tags(html: str) -> str:
    return re.sub(r"<[^>]+>", "", html).replace("\xa0", " ").strip()


def _extract_doc_blocks(html: str) -> list[str]:
    starts = [m.start() for m in _DOC_BLOCK_RE.finditer(html)]
    blocks: list[str] = []
    for i, start in enumerate(starts):
        end = starts[i + 1] if i + 1 < len(starts) else len(html)
        blocks.append(html[start:end])
    return blocks


def parse_lexml_search_results(html: str) -> tuple[int | None, list[DiscoveredDoc]]:
    m = _ITEMCOUNT_RE.search(html)
    item_count = int(m.group(1)) if m else None

    docs: list[DiscoveredDoc] = []
    for block in _extract_doc_blocks(html):
        urn_m = _URN_RE.search(block)
        if not urn_m:
            continue
        urn = urn_m.group(1).strip()
        t = "lei" if ":lei:" in urn else ("decreto" if ":decreto:" in urn else None)
        if not t:
            continue

        title_m = _TITLE_LINK_RE.search(block)
        title = _strip_tags(title_m.group("title")) if title_m else None
        href = title_m.group("href") if title_m else None
        url = f"https://www.lexml.gov.br{href}" if href else f"https://www.lexml.gov.br/urn/{urn}"

        date_m = _DATE_RE.search(block)
        published = parse_ddmmyyyy(_strip_tags(date_m.group(1))) if date_m else None

        ementa_m = _EMENTA_RE.search(block)
        ementa = _strip_tags(ementa_m.group(1)) if ementa_m else None

        docs.append(
            DiscoveredDoc(
                source="lexml",
                doc_type=t,
                doc_id=f"lexml:{urn}",
                url=url,
                title=title,
                published_date=published,
                extra={"urn": urn, "ementa": ementa} if ementa else {"urn": urn},
            )
        )
    return item_count, docs


_DETAIL_FIELD_RE = re.compile(
    r"<strong>(?P<label>[^<]+)</strong></div><div[^>]*>(?P<value>.*?)</div>",
    re.IGNORECASE,
)
_DETAIL_LINK_RE = re.compile(r'<a[^>]+href="(?P<href>https?://[^"]+)"', re.IGNORECASE)


def parse_lexml_urn_page(html: str, *, url: str, doc_id: str, doc_type: str) -> ParsedDoc:
    fields: dict[str, str] = {}
    for m in _DETAIL_FIELD_RE.finditer(html):
        label = _strip_tags(m.group("label")).lower()
        value = _strip_tags(m.group("value"))
        if label and value:
            fields[label] = value

    title = fields.get("título") or fields.get("titulo") or fields.get("título  ")
    if not title:
        title = "LexML Document"
    published = parse_ddmmyyyy(fields.get("data", "")) if fields.get("data") else None

    ementa = fields.get("ementa")
    urn = fields.get("nome uniforme") or fields.get("nome uniforme  ")

    publication_urls = [m.group("href") for m in _DETAIL_LINK_RE.finditer(html)]
    publication_urls = list(dict.fromkeys(publication_urls))  # stable de-dupe

    body_lines = [f"# {title}", ""]
    if published:
        body_lines.append(f"**Data**: {published.isoformat()}")
        body_lines.append("")
    if urn:
        body_lines.append(f"**URN**: `{urn}`")
        body_lines.append("")
    if ementa:
        body_lines.append("## Ementa")
        body_lines.append("")
        body_lines.append(ementa)
        body_lines.append("")
    if publication_urls:
        body_lines.append("## Publicações (links)")
        body_lines.append("")
        for u in publication_urls[:10]:
            body_lines.append(f"- {u}")
        body_lines.append("")

    return ParsedDoc(
        source="lexml",
        doc_type=doc_type,
        doc_id=doc_id,
        url=url,
        title=title,
        published_date=published,
        body_markdown="\n".join(body_lines).rstrip() + "\n",
        citations=[url],
        extra={"urn": urn} if urn else {},
    )


@dataclass
class LexMLSource:
    fetcher: Fetcher
    today: date
    years: int = 5

    def discover(self, *, limit: int | None = None) -> Iterator[DiscoveredDoc]:
        cutoff = years_ago(self.today, self.years)
        cutoff_year = self.today.year - self.years
        params_base = {
            "smode": "advanced",
            "f1-tipoDocumento": "Legislação",
            "year": str(cutoff_year),
            "year-max": str(self.today.year),
            "sort": "reverse-year",
        }

        yielded = 0
        for tipo in ("Lei", "Decreto"):
            start_doc = 1
            while True:
                params = dict(params_base)
                params["tipoDocumento"] = tipo
                params["startDoc"] = str(start_doc)
                url = "https://www.lexml.gov.br/busca/search?" + urlencode(params, safe=";:")
                res = self.fetcher.fetch_text(url)
                if not res.text:
                    break
                _, docs = parse_lexml_search_results(res.text)
                if not docs:
                    break
                for d in docs:
                    if d.published_date and d.published_date < cutoff:
                        continue
                    yield d
                    yielded += 1
                    if limit is not None and yielded >= limit:
                        return
                start_doc += 20

    def parse(self, discovered: DiscoveredDoc) -> ParsedDoc:
        res = self.fetcher.fetch_text(discovered.url)
        if not res.text:
            raise ValueError(f"Failed to fetch LexML detail: {discovered.url} ({res.status}) {res.error}")
        return parse_lexml_urn_page(
            res.text, url=discovered.url, doc_id=discovered.doc_id, doc_type=discovered.doc_type
        )
