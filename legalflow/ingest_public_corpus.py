from __future__ import annotations

import argparse
import json
from pathlib import Path

from legalflow.public_corpus import IngestConfig, ingest_public_corpus
from legalflow.public_corpus.fetchers import FetchResult


def _build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="python -m legalflow.ingest_public_corpus")
    mode = p.add_mutually_exclusive_group(required=True)
    mode.add_argument("--dry-run", action="store_true", help="Fetch/parse and show summary without writing.")
    mode.add_argument("--full-run", action="store_true", help="Write corpus files + update manifest.")
    p.add_argument("--limit", type=int, default=None, help="Process at most N documents total.")
    p.add_argument("--no-resume", action="store_true", help="Disable resume behavior (currently a no-op).")
    p.add_argument("--output-dir", type=str, default=None, help="Override output directory.")
    p.add_argument("--stf-sumulas-url", type=str, default=None, help="Override STF Súmulas listing URL.")
    p.add_argument("--stf-vinculantes-url", type=str, default=None, help="Override STF Súmulas Vinculantes listing URL.")
    p.add_argument(
        "--fixtures-dir",
        type=str,
        default=None,
        help="Use local HTML fixtures for offline runs (intended for tests/QA).",
    )
    p.add_argument("--json", action="store_true", help="Print machine-readable summary JSON.")
    return p


class _FixtureFetcher:
    def __init__(self, fixtures_dir: Path):
        self._dir = fixtures_dir

    def _read(self, name: str) -> str:
        return (self._dir / name).read_text(encoding="utf-8")

    def fetch_text(self, url: str) -> FetchResult:
        # LexML searches
        if "tipoDocumento=Lei" in url and "startDoc=1" in url:
            return FetchResult(url=url, status=200, text=self._read("lexml_search_lei_start1.html"))
        if "tipoDocumento=Lei" in url and "startDoc=21" in url:
            return FetchResult(url=url, status=200, text=self._read("lexml_search_lei_start21.html"))
        if "tipoDocumento=Decreto" in url and "startDoc=1" in url:
            return FetchResult(url=url, status=200, text=self._read("lexml_search_decreto_start1.html"))
        if "tipoDocumento=Decreto" in url and "startDoc=21" in url:
            return FetchResult(url=url, status=200, text=self._read("lexml_search_decreto_start21.html"))

        # LexML details
        if "urn:lex:" in url and ":lei:" in url:
            return FetchResult(url=url, status=200, text=self._read("lexml_urn_lei.html"))
        if "urn:lex:" in url and ":decreto:" in url:
            return FetchResult(url=url, status=200, text=self._read("lexml_urn_decreto.html"))

        # STF listing/detail fixtures
        if url.endswith("/stf/sumulas"):
            return FetchResult(url=url, status=200, text=self._read("stf_sumulas_listing.html"))
        if url.endswith("/stf/vinculantes"):
            return FetchResult(url=url, status=200, text=self._read("stf_vinculantes_listing.html"))
        if "sumula.asp?sumula=123" in url:
            return FetchResult(url=url, status=200, text=self._read("stf_sumula_detail.html"))

        return FetchResult(url=url, status=404, text=None, error="fixture-miss")


def main(argv: list[str] | None = None) -> int:
    args = _build_parser().parse_args(argv)
    fixture_fetcher = _FixtureFetcher(Path(args.fixtures_dir)) if args.fixtures_dir else None
    cfg = IngestConfig(
        dry_run=bool(args.dry_run),
        full_run=bool(args.full_run),
        limit=args.limit,
        resume=not args.no_resume,
        corpus_dir=Path(args.output_dir) if args.output_dir else None,
        fetcher=fixture_fetcher,
        stf_fetcher=fixture_fetcher,
        stf_sumulas_url=args.stf_sumulas_url,
        stf_vinculantes_url=args.stf_vinculantes_url,
    )
    summary = ingest_public_corpus(cfg)
    if args.json:
        print(json.dumps(summary.to_dict(), ensure_ascii=False, indent=2))
    else:
        data = summary.to_dict()
        print("SUMMARY")
        for k in ("ok","discovered_total","planned_writes","wrote","skipped_unchanged","parse_errors","fetch_errors","output_dir","manifest_path"):
            print(f"{k}={data.get(k)}")
    return 0 if summary.ok else 2


if __name__ == "__main__":
    raise SystemExit(main())
