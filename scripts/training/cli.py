"""Unified CLI for the training data extraction pipeline.

Usage:
    python -m scripts.training.cli extract --all
    python -m scripts.training.cli extract --architecture
    python -m scripts.training.cli extract --code-patterns
    python -m scripts.training.cli extract --solutions
    python -m scripts.training.cli extract --quality
    python -m scripts.training.cli generate --dry-run
    python -m scripts.training.cli generate --category skills.architecture_design
    python -m scripts.training.cli generate --resume
    python -m scripts.training.cli generate --limit 50
    python -m scripts.training.cli validate
    python -m scripts.training.cli stats
"""

from __future__ import annotations

import argparse
import sys
from collections import Counter

from .config import CHUNKS_DIR, OUTPUT_DIR, SEED_PAIRS_DIR, VALIDATED_DIR
from .utils import read_jsonl


def cmd_extract(args: argparse.Namespace) -> None:
    """Run extraction pipeline(s)."""
    extractors = []

    if args.all or args.architecture:
        from .extract_architecture_decisions import run as run_arch

        extractors.append(("architecture_decisions", run_arch))

    if args.all or args.code_patterns:
        from .extract_code_patterns import run as run_code

        extractors.append(("code_patterns", run_code))

    if args.all or args.solutions:
        from .extract_solution_compositions import run as run_sol

        extractors.append(("solution_compositions", run_sol))

    if args.all or args.quality:
        from .extract_quality_standards import run as run_qual

        extractors.append(("quality_standards", run_qual))

    if not extractors:
        print("No extractor selected. Use --all or specify one:")
        print("  --architecture  --code-patterns  --solutions  --quality")
        sys.exit(1)

    for name, runner in extractors:
        print(f"\n{'=' * 60}")
        print(f"  Running: {name}")
        print(f"{'=' * 60}\n")
        runner()


def cmd_generate(args: argparse.Namespace) -> None:
    """Run seed pair generation."""
    from .generate_seed_pairs import run as run_gen

    run_gen(
        dry_run=args.dry_run,
        category_filter=args.category,
        resume=args.resume,
        limit=args.limit,
    )


def cmd_validate(args: argparse.Namespace) -> None:
    """Run validation on generated seed pairs."""
    from .validate_training_data import run as run_val

    run_val()


def cmd_stats(args: argparse.Namespace) -> None:
    """Print pipeline statistics."""
    print("Training Data Pipeline Statistics")
    print("=" * 50)

    # Chunk stats
    print("\n## Extracted Chunks")
    total_chunks = 0
    if CHUNKS_DIR.exists():
        for chunk_file in sorted(CHUNKS_DIR.glob("*.jsonl")):
            records = read_jsonl(chunk_file)
            total_chunks += len(records)
            print(f"  {chunk_file.stem}: {len(records)} chunks")
    print(f"  Total: {total_chunks} chunks")

    # Category breakdown across all chunks
    if total_chunks > 0:
        all_chunks: list[dict] = []
        for chunk_file in CHUNKS_DIR.glob("*.jsonl"):
            all_chunks.extend(read_jsonl(chunk_file))
        cat_counts = Counter(c.get("taxonomy_category", "unknown") for c in all_chunks)
        print(f"\n## Category Distribution ({len(cat_counts)} categories)")
        for cat, count in cat_counts.most_common(10):
            print(f"  {cat}: {count}")
        if len(cat_counts) > 10:
            print(f"  ... and {len(cat_counts) - 10} more")

    # Seed pair stats
    print("\n## Seed Pairs")
    total_pairs = 0
    if SEED_PAIRS_DIR.exists():
        for seed_file in sorted(SEED_PAIRS_DIR.glob("*.jsonl")):
            records = read_jsonl(seed_file)
            total_pairs += len(records)
            print(f"  {seed_file.stem}: {len(records)} pairs")
    if total_pairs:
        print(f"  Total: {total_pairs} pairs")
    else:
        print("  No seed pairs generated yet.")

    # Validated stats
    print("\n## Validated Data")
    validated_path = VALIDATED_DIR / "training_data.jsonl"
    if validated_path.exists():
        records = read_jsonl(validated_path)
        print(f"  Validated pairs: {len(records)}")
    else:
        print("  No validated data yet.")

    report_path = VALIDATED_DIR / "report.md"
    if report_path.exists():
        print(f"  Report: {report_path}")

    # Disk usage
    print("\n## Disk Usage")
    for d in (CHUNKS_DIR, SEED_PAIRS_DIR, VALIDATED_DIR):
        if d.exists():
            size = sum(f.stat().st_size for f in d.rglob("*") if f.is_file())
            print(f"  {d.relative_to(OUTPUT_DIR)}: {size / 1024 / 1024:.1f} MB")


def main() -> None:
    parser = argparse.ArgumentParser(
        prog="scripts.training.cli",
        description="Training data extraction pipeline for AI architect clone",
    )
    subparsers = parser.add_subparsers(dest="command", help="Pipeline commands")

    # extract
    p_extract = subparsers.add_parser("extract", help="Run extraction pipeline(s)")
    p_extract.add_argument("--all", action="store_true", help="Run all extractors")
    p_extract.add_argument("--architecture", action="store_true", help="Architecture decisions")
    p_extract.add_argument("--code-patterns", action="store_true", help="Code patterns")
    p_extract.add_argument("--solutions", action="store_true", help="Solution compositions")
    p_extract.add_argument("--quality", action="store_true", help="Quality standards")
    p_extract.set_defaults(func=cmd_extract)

    # generate
    p_generate = subparsers.add_parser("generate", help="Generate seed pairs via Claude API")
    p_generate.add_argument("--dry-run", action="store_true", help="Preview without API calls")
    p_generate.add_argument("--category", type=str, default=None, help="Filter by category prefix")
    p_generate.add_argument("--resume", action="store_true", help="Skip already-generated pairs")
    p_generate.add_argument("--limit", type=int, default=0, help="Max chunks to process")
    p_generate.set_defaults(func=cmd_generate)

    # validate
    p_validate = subparsers.add_parser("validate", help="Validate generated seed pairs")
    p_validate.set_defaults(func=cmd_validate)

    # stats
    p_stats = subparsers.add_parser("stats", help="Print pipeline statistics")
    p_stats.set_defaults(func=cmd_stats)

    args = parser.parse_args()
    if not args.command:
        parser.print_help()
        sys.exit(1)

    args.func(args)


if __name__ == "__main__":
    main()
