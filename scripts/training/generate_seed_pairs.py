"""Convert extracted chunks into ChatML instruction-response seed pairs using Claude API.

Supports:
- --dry-run: preview what would be generated without API calls
- --resume: skip already-generated pairs
- --category: process only one taxonomy category
- --limit: max chunks to process (for cost control)
"""

from __future__ import annotations

import json
import os
import time

from .config import (
    CHUNKS_DIR,
    CLAUDE_BATCH_SIZE,
    CLAUDE_MAX_TOKENS,
    CLAUDE_MODEL_BULK,
    CLAUDE_MODEL_COMPLEX,
    SEED_PAIRS_DIR,
    chatml_record,
)
from .utils import content_hash, read_jsonl, write_jsonl

# Categories that benefit from the more capable model
COMPLEX_CATEGORIES = {
    "skills.architecture_design.microservices_decomposition",
    "skills.architecture_design.event_driven_patterns",
    "skills.solution_composition.kit_selection_and_customization",
    "skills.solution_composition.business_outcome_mapping",
}

META_PROMPT = """\
You are a training data generator for an AI software architect clone.

Given this code/documentation chunk from Aaron's Silver Surfer Platform, \
generate an instruction-response pair that teaches an AI to make the same \
architectural decision Aaron made here.

The instruction should be a realistic user request that a developer or \
business stakeholder would ask — natural, specific, and actionable. \
Do NOT reference Silver Surfer or Aaron by name in the instruction.

The response should include <think>...</think> reasoning traces showing \
WHY this approach was chosen (referencing patterns like kit-based composition, \
85% coverage gates, RBAC-from-day-one, BaseModel inheritance, event-driven \
microservices), then the actual solution.

Category: {category}
Source file: {source_file}

Chunk:
```
{content}
```

Context:
{context}

Respond with valid JSON only:
{{"instruction": "...", "response": "..."}}
"""


def _select_model(category: str) -> str:
    """Pick Claude model based on category complexity."""
    if category in COMPLEX_CATEGORIES:
        return CLAUDE_MODEL_COMPLEX
    return CLAUDE_MODEL_BULK


def _get_existing_hashes(category: str) -> set[str]:
    """Load hashes of already-generated pairs for resume support."""
    safe_name = category.replace(".", "_")
    output_path = SEED_PAIRS_DIR / f"{safe_name}.jsonl"
    if not output_path.exists():
        return set()
    existing = read_jsonl(output_path)
    return {r.get("metadata", {}).get("chunk_hash", "") for r in existing}


def generate_pair(
    client,  # anthropic.Anthropic
    chunk: dict,
    model: str,
) -> dict | None:
    """Call Claude API to generate one instruction-response pair from a chunk."""
    prompt = META_PROMPT.format(
        category=chunk.get("taxonomy_category", ""),
        source_file=chunk.get("source_file", ""),
        content=chunk.get("content", "")[:6000],  # truncate very large chunks
        context=chunk.get("context", "")[:1000],
    )

    try:
        response = client.messages.create(
            model=model,
            max_tokens=CLAUDE_MAX_TOKENS,
            messages=[{"role": "user", "content": prompt}],
        )
        text = response.content[0].text.strip()

        # Parse JSON from response (handle markdown code blocks)
        if text.startswith("```"):
            text = text.split("```")[1]
            if text.startswith("json"):
                text = text[4:]
            text = text.strip()

        parsed = json.loads(text)
        instruction = parsed.get("instruction", "")
        resp = parsed.get("response", "")

        if not instruction or not resp:
            return None

        chunk_h = content_hash(chunk.get("content", ""))
        return chatml_record(
            user_content=instruction,
            assistant_content=resp,
            source_file=chunk.get("source_file", ""),
            taxonomy_category=chunk.get("taxonomy_category", ""),
            chunk_hash=chunk_h,
        )
    except json.JSONDecodeError:
        return None
    except Exception as e:
        print(f"    [error] API call failed: {e}")
        return None


def run(
    dry_run: bool = False,
    category_filter: str | None = None,
    resume: bool = False,
    limit: int = 0,
) -> list[dict]:
    """Run the seed pair generation pipeline."""
    print("Generating seed pairs from extracted chunks...")
    print(f"  Dry run: {dry_run}")
    print(f"  Category filter: {category_filter or 'all'}")
    print(f"  Resume: {resume}")

    # Load all chunk files
    all_chunks: list[dict] = []
    for chunk_file in sorted(CHUNKS_DIR.glob("*.jsonl")):
        all_chunks.extend(read_jsonl(chunk_file))

    print(f"  Total chunks available: {len(all_chunks)}")

    # Filter by category if specified
    if category_filter:
        all_chunks = [c for c in all_chunks if c.get("taxonomy_category", "").startswith(category_filter)]
        print(f"  After category filter: {len(all_chunks)}")

    # Group by category
    by_category: dict[str, list[dict]] = {}
    for chunk in all_chunks:
        cat = chunk.get("taxonomy_category", "unknown")
        by_category.setdefault(cat, []).append(chunk)

    if dry_run:
        print("\n  === DRY RUN — No API calls will be made ===")
        print(f"\n  Categories: {len(by_category)}")
        total_estimated = 0
        for cat in sorted(by_category):
            count = len(by_category[cat])
            total_estimated += count
            model = _select_model(cat)
            print(f"    {cat}: {count} chunks → {model}")
        print(f"\n  Total pairs to generate: {total_estimated}")

        # Cost estimate
        avg_input_tokens = 800
        avg_output_tokens = 600
        haiku_cost_per_m_input = 1.0
        haiku_cost_per_m_output = 5.0
        sonnet_cost_per_m_input = 3.0
        sonnet_cost_per_m_output = 15.0

        haiku_chunks = sum(len(v) for k, v in by_category.items() if k not in COMPLEX_CATEGORIES)
        sonnet_chunks = sum(len(v) for k, v in by_category.items() if k in COMPLEX_CATEGORIES)

        haiku_cost = (
            haiku_chunks * avg_input_tokens * haiku_cost_per_m_input / 1_000_000
            + haiku_chunks * avg_output_tokens * haiku_cost_per_m_output / 1_000_000
        )
        sonnet_cost = (
            sonnet_chunks * avg_input_tokens * sonnet_cost_per_m_input / 1_000_000
            + sonnet_chunks * avg_output_tokens * sonnet_cost_per_m_output / 1_000_000
        )
        print("\n  Estimated cost:")
        print(f"    Haiku ({haiku_chunks} chunks): ${haiku_cost:.2f}")
        print(f"    Sonnet ({sonnet_chunks} chunks): ${sonnet_cost:.2f}")
        print(f"    Total: ${haiku_cost + sonnet_cost:.2f}")
        return []

    # Live generation requires anthropic SDK
    try:
        import anthropic
    except ImportError:
        print("\n  [error] anthropic package not installed. Run: pip install anthropic")
        return []

    api_key = os.environ.get("ANTHROPIC_API_KEY", "")
    if not api_key:
        print("\n  [error] ANTHROPIC_API_KEY not set in environment")
        return []

    client = anthropic.Anthropic(api_key=api_key)

    all_pairs: list[dict] = []
    total_processed = 0
    total_success = 0
    total_failed = 0

    for cat in sorted(by_category):
        chunks = by_category[cat]
        model = _select_model(cat)
        safe_name = cat.replace(".", "_")
        output_path = SEED_PAIRS_DIR / f"{safe_name}.jsonl"

        # Resume support: skip already-generated
        existing_pairs: list[dict] = []
        skip_hashes: set[str] = set()
        if resume and output_path.exists():
            existing_pairs = read_jsonl(output_path)
            skip_hashes = _get_existing_hashes(cat)
            print(f"\n  [{cat}] Resuming — {len(existing_pairs)} existing pairs")

        category_pairs = list(existing_pairs)
        pending = [c for c in chunks if content_hash(c.get("content", "")) not in skip_hashes]

        if limit > 0:
            pending = pending[:limit]

        if not pending:
            print(f"\n  [{cat}] All {len(chunks)} chunks already processed")
            all_pairs.extend(category_pairs)
            continue

        print(f"\n  [{cat}] Processing {len(pending)} chunks with {model}...")

        for batch_start in range(0, len(pending), CLAUDE_BATCH_SIZE):
            batch = pending[batch_start : batch_start + CLAUDE_BATCH_SIZE]
            batch_num = batch_start // CLAUDE_BATCH_SIZE + 1
            total_batches = (len(pending) + CLAUDE_BATCH_SIZE - 1) // CLAUDE_BATCH_SIZE

            print(f"    Batch {batch_num}/{total_batches} ({len(batch)} chunks)...")

            for chunk in batch:
                total_processed += 1
                pair = generate_pair(client, chunk, model)
                if pair:
                    category_pairs.append(pair)
                    total_success += 1
                else:
                    total_failed += 1

                # Rate limiting: small delay between calls
                time.sleep(0.1)

            # Save after each batch
            write_jsonl(category_pairs, output_path)
            print(f"    Saved {len(category_pairs)} pairs to {output_path}")

        all_pairs.extend(category_pairs)

    # Final summary
    print("\n  === Generation Complete ===")
    print(f"  Processed: {total_processed}")
    print(f"  Success: {total_success}")
    print(f"  Failed: {total_failed}")
    print(f"  Total pairs: {len(all_pairs)}")

    return all_pairs


if __name__ == "__main__":
    import sys

    dry = "--dry-run" in sys.argv
    res = "--resume" in sys.argv
    cat = None
    lim = 0
    for arg in sys.argv:
        if arg.startswith("--category="):
            cat = arg.split("=", 1)[1]
        if arg.startswith("--limit="):
            lim = int(arg.split("=", 1)[1])
    run(dry_run=dry, category_filter=cat, resume=res, limit=lim)
