from __future__ import annotations

from datetime import date
from pathlib import Path

from legalflow.public_corpus.sources.lexml import (
    parse_lexml_search_results,
    parse_lexml_urn_page,
)
from legalflow.public_corpus.sources.stf_sumulas import (
    parse_stf_listing,
    parse_stf_sumula_detail,
)


FIXTURES = Path(__file__).parent / "fixtures" / "legalflow_public_corpus"


def test_lexml_parse_search_results_extracts_docs():
    html = (FIXTURES / "lexml_search_lei_start1.html").read_text(encoding="utf-8")
    item_count, docs = parse_lexml_search_results(html)
    assert item_count == 1
    assert len(docs) == 1
    assert docs[0].doc_type == "lei"
    assert docs[0].doc_id.startswith("lexml:urn:lex:")
    assert docs[0].published_date == date(2024, 1, 2)
    assert "urn:lex:" in docs[0].extra.get("urn", "")


def test_lexml_parse_urn_page_renders_markdown():
    html = (FIXTURES / "lexml_urn_lei.html").read_text(encoding="utf-8")
    parsed = parse_lexml_urn_page(
        html,
        url="https://www.lexml.gov.br/urn/urn:lex:br;federal:lei:2024-01-02;123",
        doc_id="lexml:urn:lex:br;federal:lei:2024-01-02;123",
        doc_type="lei",
    )
    assert parsed.title.startswith("Lei")
    assert "## Ementa" in parsed.body_markdown
    assert "Publicações" in parsed.body_markdown


def test_stf_listing_and_detail_parsing():
    listing = (FIXTURES / "stf_sumulas_listing.html").read_text(encoding="utf-8")
    docs = parse_stf_listing(
        listing,
        base_url="https://example.invalid/jurisprudencia/sumulas.asp",
        doc_type="sumula",
    )
    assert len(docs) == 1
    assert docs[0].doc_id == "stf:sumula:123"

    detail = (FIXTURES / "stf_sumula_detail.html").read_text(encoding="utf-8")
    parsed = parse_stf_sumula_detail(detail, discovered=docs[0])
    assert parsed.title == "Súmula 123"
    assert "cláusula de exemplo" in parsed.body_markdown

