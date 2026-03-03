from __future__ import annotations

from datetime import date
from pathlib import Path

from legalflow.public_corpus import IngestConfig, ingest_public_corpus
from legalflow.public_corpus.fetchers import FetchResult


FIXTURES = Path(__file__).parent / "fixtures" / "legalflow_public_corpus"


class FixtureFetcher:
    def __init__(self, mapping: dict[str, str]):
        self._mapping = mapping

    def fetch_text(self, url: str) -> FetchResult:
        for key, value in self._mapping.items():
            if key in url:
                return FetchResult(url=url, status=200, text=value)
        return FetchResult(url=url, status=404, text=None, error="fixture-miss")


def test_ingest_is_idempotent_and_skips_unchanged(tmp_path: Path):
    lexml_lei_search_1 = (FIXTURES / "lexml_search_lei_start1.html").read_text(encoding="utf-8")
    lexml_lei_search_21 = (FIXTURES / "lexml_search_lei_start21.html").read_text(encoding="utf-8")
    lexml_dec_search_1 = (FIXTURES / "lexml_search_decreto_start1.html").read_text(encoding="utf-8")
    lexml_dec_search_21 = (FIXTURES / "lexml_search_decreto_start21.html").read_text(encoding="utf-8")
    lexml_lei_detail = (FIXTURES / "lexml_urn_lei.html").read_text(encoding="utf-8")
    lexml_dec_detail = (FIXTURES / "lexml_urn_decreto.html").read_text(encoding="utf-8")
    stf_listing = (FIXTURES / "stf_sumulas_listing.html").read_text(encoding="utf-8")
    stf_vinc_listing = (FIXTURES / "stf_vinculantes_listing.html").read_text(encoding="utf-8")
    stf_detail = (FIXTURES / "stf_sumula_detail.html").read_text(encoding="utf-8")

    fetcher = FixtureFetcher(
        {
            # LexML discovery
            "tipoDocumento=Lei&startDoc=1": lexml_lei_search_1,
            "tipoDocumento=Lei&startDoc=21": lexml_lei_search_21,
            "tipoDocumento=Decreto&startDoc=1": lexml_dec_search_1,
            "tipoDocumento=Decreto&startDoc=21": lexml_dec_search_21,
            # LexML details
            "urn:lex:br;federal:lei:2024-01-02;123": lexml_lei_detail,
            "urn:lex:br;federal:decreto:2025-02-03;456": lexml_dec_detail,
            # STF discovery + detail
            "example.invalid/stf/sumulas": stf_listing,
            "example.invalid/stf/vinculantes": stf_vinc_listing,
            "sumula.asp?sumula=123": stf_detail,
        }
    )

    cfg = IngestConfig(
        dry_run=False,
        full_run=True,
        limit=None,
        corpus_dir=tmp_path,
        today=date(2026, 3, 3),
        fetcher=fetcher,
        stf_sumulas_url="https://example.invalid/stf/sumulas",
        stf_vinculantes_url="https://example.invalid/stf/vinculantes",
    )

    first = ingest_public_corpus(cfg)
    assert first.wrote == 3
    assert first.skipped_unchanged == 0
    assert (tmp_path / "manifest.json").exists()

    second = ingest_public_corpus(cfg)
    assert second.wrote == 0
    assert second.skipped_unchanged == 3

