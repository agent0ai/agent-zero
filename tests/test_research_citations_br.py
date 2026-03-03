import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from python.helpers.citations_br import (
    format_brazil_citations_markdown,
    select_sources_official_first,
    source_identifier,
)


def test_select_sources_official_only_when_available_and_prioritized():
    items = [
        {"title": "Blog post", "url": "https://example.com/post", "content": "x"},
        {
            "title": "STJ page",
            "url": "https://www.stj.jus.br/sites/portalp/Paginas/default.aspx",
            "content": "y",
        },
        {
            "title": "Planalto page",
            "url": "https://www.planalto.gov.br/ccivil_03/leis/l8078.htm",
            "content": "z",
        },
        {"title": "Other gov", "url": "https://www.gov.br/pt-br/servicos", "content": "g"},
    ]

    selected = select_sources_official_first(items, limit=10)

    assert all("example.com" not in (s.get("url") or "") for s in selected)
    assert selected[0]["url"].startswith("https://www.planalto.gov.br/")


def test_select_sources_fallback_to_non_official_when_no_official():
    items = [
        {"title": "A", "url": "https://example.com/a", "content": "a"},
        {"title": "B", "url": "https://news.example.org/b", "content": "b"},
    ]

    selected = select_sources_official_first(items, limit=1)
    assert selected == [items[0]]


def test_format_brazil_citations_markdown_includes_required_fields_and_quote():
    items = [
        {
            "title": "LexML entry",
            "url": "https://www.lexml.gov.br/urn/urn:lex:br:federal:lei:1990-09-11;8078",
            "content": "Texto da lei com resumo curto.",
            "publishedDate": "1990-09-11T00:00:00",
        }
    ]

    md = format_brazil_citations_markdown(items, heading="Fontes")
    assert "## Fontes" in md
    assert "Tipo:" in md
    assert "Identificador:" in md
    assert "Data:" in md
    assert "URL:" in md
    assert "Trecho:" in md
    assert "\"Texto da lei com resumo curto.\"" in md


def test_format_handles_missing_url_and_weird_date_without_crashing():
    items = [
        {
            "title": "No URL",
            "url": "",
            "content": "Conteúdo",
            "publishedDate": "Data desconhecida",
        }
    ]

    md = format_brazil_citations_markdown(items, heading="Fontes")
    assert "URL: —" in md
    assert "Data: Data desconhecida" in md


def test_source_identifier_prefers_urn_lex_when_present():
    item = {
        "title": "Something",
        "url": "https://www.lexml.gov.br/urn/urn:lex:br:federal:lei:1990-09-11;8078",
        "content": "x",
    }
    assert source_identifier(item).lower().startswith("urn:lex:")


def test_source_identifier_extracts_common_query_identifiers():
    item = {
        "title": "STF detail",
        "url": "https://portal.stf.jus.br/processos/detalhe.asp?incidente=1234567",
        "content": "x",
    }
    assert source_identifier(item).endswith("?incidente=1234567")

