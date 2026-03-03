from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from pathlib import Path
from typing import Any

from python.helpers import files

from .fetchers import AutoFetcher, Fetcher
from .manifest import Manifest, ManifestEntry
from .model import DiscoveredDoc, ParsedDoc
from .sources import LexMLSource, STFSumulasSource
from .storage import write_markdown
from .utils import stable_content_hash


@dataclass(frozen=True)
class IngestConfig:
    dry_run: bool
    full_run: bool
    limit: int | None = None
    resume: bool = True
    corpus_dir: Path | None = None
    today: date | None = None
    fetcher: Fetcher | None = None
    stf_fetcher: Fetcher | None = None
    stf_sumulas_url: str | None = None
    stf_vinculantes_url: str | None = None


@dataclass
class IngestSummary:
    ok: bool
    discovered_total: int = 0
    fetched_total: int = 0
    planned_writes: int = 0
    wrote: int = 0
    skipped_unchanged: int = 0
    parse_errors: int = 0
    fetch_errors: int = 0
    sources: dict[str, dict[str, int]] | None = None
    examples: dict[str, str] | None = None
    output_dir: str | None = None
    manifest_path: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "ok": self.ok,
            "discovered_total": self.discovered_total,
            "fetched_total": self.fetched_total,
            "planned_writes": self.planned_writes,
            "wrote": self.wrote,
            "skipped_unchanged": self.skipped_unchanged,
            "parse_errors": self.parse_errors,
            "fetch_errors": self.fetch_errors,
            "sources": self.sources or {},
            "examples": self.examples or {},
            "output_dir": self.output_dir,
            "manifest_path": self.manifest_path,
        }


def _default_corpus_dir() -> Path:
    return Path(files.get_abs_path("usr/knowledge/custom/legalflow/public_corpus"))


def ingest_public_corpus(cfg: IngestConfig) -> IngestSummary:
    if not cfg.dry_run and not cfg.full_run:
        raise SystemExit("Must pass --dry-run or --full-run.")

    today = cfg.today or date.today()
    corpus_dir = cfg.corpus_dir or _default_corpus_dir()
    manifest_path = corpus_dir / "manifest.json"

    manifest = Manifest.load(manifest_path)

    base_fetcher = cfg.fetcher or AutoFetcher()
    stf_fetcher = cfg.stf_fetcher or base_fetcher

    lexml = LexMLSource(fetcher=base_fetcher, today=today, years=5)
    stf = STFSumulasSource(
        fetcher=stf_fetcher,
        today=today,
        sumulas_url=cfg.stf_sumulas_url or STFSumulasSource.sumulas_url,
        vinculantes_url=cfg.stf_vinculantes_url or STFSumulasSource.vinculantes_url,
    )

    summary = IngestSummary(ok=True, sources={}, examples={}, output_dir=str(corpus_dir), manifest_path=str(manifest_path))

    remaining = cfg.limit
    for source in (lexml, stf):
        src_name = "lexml" if isinstance(source, LexMLSource) else "stf"
        if summary.sources is not None:
            summary.sources.setdefault(src_name, {"discovered": 0, "wrote": 0, "skipped_unchanged": 0, "parse_errors": 0})

        src_limit = None if remaining is None else max(0, remaining)
        for discovered in source.discover(limit=src_limit):
            summary.discovered_total += 1
            if summary.sources is not None:
                summary.sources[src_name]["discovered"] += 1

            existing = manifest.documents.get(discovered.doc_id)
            try:
                parsed = source.parse(discovered)
                summary.fetched_total += 1
            except Exception:
                summary.parse_errors += 1
                if summary.sources is not None:
                    summary.sources[src_name]["parse_errors"] += 1
                continue

            content_payload = {
                "doc_id": parsed.doc_id,
                "source": parsed.source,
                "type": parsed.doc_type,
                "title": parsed.title,
                "published_date": parsed.published_date.isoformat() if parsed.published_date else None,
                "url": parsed.url,
                "body": parsed.body_markdown,
                "citations": parsed.citations,
                "extra": parsed.extra,
            }
            content_sha = stable_content_hash(content_payload)
            record_id = f"{parsed.doc_id}:sha256-{content_sha[:12]}"

            if existing and existing.content_sha256 == content_sha:
                summary.skipped_unchanged += 1
                if summary.sources is not None:
                    summary.sources[src_name]["skipped_unchanged"] += 1
            else:
                summary.planned_writes += 1
                if not cfg.dry_run:
                    out_path = write_markdown(corpus_dir, parsed, content_sha256=content_sha, record_id=record_id)
                    rel_path = str(out_path.relative_to(corpus_dir))
                    manifest.documents[parsed.doc_id] = ManifestEntry(
                        doc_id=parsed.doc_id,
                        record_id=record_id,
                        source=parsed.source,
                        doc_type=parsed.doc_type,
                        title=parsed.title,
                        url=parsed.url,
                        published_date=parsed.published_date.isoformat() if parsed.published_date else None,
                        content_sha256=content_sha,
                        path=rel_path,
                        updated_at=today.isoformat(),
                        extra=parsed.extra,
                    )
                    summary.wrote += 1
                    if summary.sources is not None:
                        summary.sources[src_name]["wrote"] += 1

                    if summary.examples is not None:
                        k = f"{src_name}:{parsed.doc_id}"
                        if len(summary.examples) < 6 and k not in summary.examples:
                            summary.examples[k] = rel_path

            if remaining is not None:
                remaining -= 1
                if remaining <= 0:
                    break
        if remaining is not None and remaining <= 0:
            break

    if not cfg.dry_run:
        manifest.save(manifest_path)

    return summary
