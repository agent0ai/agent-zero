from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import date
from typing import Iterator
from urllib.parse import urljoin

from ..fetchers import Fetcher
from ..model import DiscoveredDoc, ParsedDoc


_HREF_RE = re.compile(r'href="(?P<href>[^"]+)"', re.IGNORECASE)
_SUMULA_NUM_RE = re.compile(r"sumula\s*(?:n[ºo]\s*)?(\d+)", re.IGNORECASE)
_TEXT_BLOCK_RE = re.compile(r'<div[^>]+class="texto-sumula"[^>]*>(?P<body>.*?)</div>', re.IGNORECASE | re.DOTALL)


def _strip_tags(html: str) -> str:
    text = re.sub(r"<br\s*/?>", "\n", html, flags=re.IGNORECASE)
    text = re.sub(r"</p\s*>", "\n", text, flags=re.IGNORECASE)
    text = re.sub(r"<[^>]+>", "", text)
    text = text.replace("\xa0", " ")
    return "\n".join(line.strip() for line in text.splitlines()).strip()


def parse_stf_listing(html: str, *, base_url: str, doc_type: str) -> list[DiscoveredDoc]:
    docs: list[DiscoveredDoc] = []
    for m in _HREF_RE.finditer(html):
        href = m.group("href")
        if "sumula" not in href.lower():
            continue
        num_m = re.search(r"(?:sumula=|sumula\s*)(\d+)", href, flags=re.IGNORECASE)
        if not num_m:
            continue
        num = int(num_m.group(1))
        url = urljoin(base_url, href)
        doc_id = f"stf:{doc_type}:{num}"
        docs.append(
            DiscoveredDoc(
                source="stf",
                doc_type=doc_type,
                doc_id=doc_id,
                url=url,
                title=f"STF {doc_type.replace('_', ' ')} {num}",
                published_date=None,
                extra={"number": num},
            )
        )
    # stable de-dupe
    seen: set[str] = set()
    out: list[DiscoveredDoc] = []
    for d in docs:
        if d.doc_id in seen:
            continue
        seen.add(d.doc_id)
        out.append(d)
    return out


def parse_stf_sumula_detail(html: str, *, discovered: DiscoveredDoc) -> ParsedDoc:
    title = discovered.title or "STF Súmula"
    # Best-effort: pull a dedicated text block if present; otherwise fallback to stripped page text.
    block_m = _TEXT_BLOCK_RE.search(html)
    if block_m:
        statement = _strip_tags(block_m.group("body"))
    else:
        statement = _strip_tags(html)

    num = None
    m = _SUMULA_NUM_RE.search(statement) or _SUMULA_NUM_RE.search(title)
    if m:
        num = int(m.group(1))
        if discovered.doc_type == "sumula_vinculante":
            title = f"Súmula Vinculante {num}"
        else:
            title = f"Súmula {num}"

    body = f"# {title}\n\n{statement.strip()}\n"
    return ParsedDoc(
        source=discovered.source,
        doc_type=discovered.doc_type,
        doc_id=discovered.doc_id,
        url=discovered.url,
        title=title,
        published_date=None,
        body_markdown=body,
        citations=[discovered.url],
        extra={"number": num} if num is not None else {},
    )


@dataclass
class STFSumulasSource:
    fetcher: Fetcher
    today: date
    sumulas_url: str = "https://portal.stf.jus.br/jurisprudencia/sumulas.asp"
    vinculantes_url: str = "https://portal.stf.jus.br/jurisprudencia/sumulasVinculantes.asp"

    def discover(self, *, limit: int | None = None) -> Iterator[DiscoveredDoc]:
        yielded = 0
        for doc_type, url in (
            ("sumula", self.sumulas_url),
            ("sumula_vinculante", self.vinculantes_url),
        ):
            res = self.fetcher.fetch_text(url)
            if not res.text:
                continue
            docs = parse_stf_listing(res.text, base_url=url, doc_type=doc_type)
            for d in docs:
                yield d
                yielded += 1
                if limit is not None and yielded >= limit:
                    return

    def parse(self, discovered: DiscoveredDoc) -> ParsedDoc:
        res = self.fetcher.fetch_text(discovered.url)
        if not res.text:
            raise ValueError(f"Failed to fetch STF: {discovered.url} ({res.status}) {res.error}")
        return parse_stf_sumula_detail(res.text, discovered=discovered)
