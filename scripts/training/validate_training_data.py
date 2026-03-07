"""Quality validation and statistics for generated seed pairs.

Checks format, length, reasoning traces, deduplication, diversity,
and taxonomy balance. Outputs validated data and a report.
"""

from __future__ import annotations

from collections import Counter

from .config import MAX_RESPONSE_TOKENS, MIN_RESPONSE_CHARS, SEED_PAIRS_DIR, VALIDATED_DIR
from .utils import content_hash, count_tokens, read_jsonl, write_jsonl


def validate_record(record: dict) -> tuple[bool, list[str]]:
    """Validate a single seed pair record. Returns (valid, issues)."""
    issues: list[str] = []

    # Format check
    messages = record.get("messages")
    if not isinstance(messages, list):
        issues.append("missing or invalid 'messages' field")
        return False, issues

    roles = [m.get("role") for m in messages]
    if "user" not in roles:
        issues.append("missing 'user' message")
    if "assistant" not in roles:
        issues.append("missing 'assistant' message")

    if issues:
        return False, issues

    # Extract assistant content
    assistant_msg = next((m for m in messages if m["role"] == "assistant"), None)
    if not assistant_msg:
        issues.append("no assistant message found")
        return False, issues

    content = assistant_msg.get("content", "")

    # Length checks
    if len(content) < MIN_RESPONSE_CHARS:
        issues.append(f"response too short ({len(content)} chars, min {MIN_RESPONSE_CHARS})")

    token_count = count_tokens(content)
    if token_count > MAX_RESPONSE_TOKENS:
        issues.append(f"response too long ({token_count} tokens, max {MAX_RESPONSE_TOKENS})")

    # Reasoning trace check
    if "<think>" not in content:
        issues.append("missing <think> reasoning block")

    return len(issues) == 0, issues


def compute_token_overlap(text_a: str, text_b: str) -> float:
    """Compute Jaccard token overlap between two texts."""
    tokens_a = set(text_a.lower().split())
    tokens_b = set(text_b.lower().split())
    if not tokens_a or not tokens_b:
        return 0.0
    intersection = tokens_a & tokens_b
    union = tokens_a | tokens_b
    return len(intersection) / len(union)


def run() -> dict:
    """Run validation on all seed pair JSONL files."""
    print("Validating training data...")

    # Load all seed pairs
    all_pairs: list[dict] = []
    if not SEED_PAIRS_DIR.exists():
        print(f"  [warn] No seed pairs directory found at {SEED_PAIRS_DIR}")
        print("  Run 'generate' first to create seed pairs.")
        return {"total": 0, "valid": 0, "invalid": 0}

    for seed_file in sorted(SEED_PAIRS_DIR.glob("*.jsonl")):
        all_pairs.extend(read_jsonl(seed_file))

    if not all_pairs:
        print("  No seed pairs found. Run 'generate' first.")
        return {"total": 0, "valid": 0, "invalid": 0}

    print(f"  Total pairs loaded: {len(all_pairs)}")

    # Validation
    valid_pairs: list[dict] = []
    invalid_pairs: list[dict] = []
    issue_counts: Counter = Counter()

    # Dedup tracking
    seen_hashes: set[str] = set()
    duplicates_removed = 0

    for pair in all_pairs:
        # Dedup by instruction content
        user_msg = next((m for m in pair.get("messages", []) if m.get("role") == "user"), None)
        if user_msg:
            h = content_hash(user_msg.get("content", ""))
            if h in seen_hashes:
                duplicates_removed += 1
                continue
            seen_hashes.add(h)

        valid, issues = validate_record(pair)
        if valid:
            valid_pairs.append(pair)
        else:
            for issue in issues:
                issue_counts[issue] += 1
            pair["_validation_issues"] = issues
            invalid_pairs.append(pair)

    # Category distribution
    category_counts: Counter = Counter()
    category_tokens: dict[str, list[int]] = {}
    for pair in valid_pairs:
        cat = pair.get("metadata", {}).get("taxonomy_category", "unknown")
        category_counts[cat] += 1
        assistant_msg = next((m for m in pair.get("messages", []) if m["role"] == "assistant"), None)
        if assistant_msg:
            tc = count_tokens(assistant_msg["content"])
            category_tokens.setdefault(cat, []).append(tc)

    # Balance check — flag categories with < 5% of total
    total_valid = len(valid_pairs)
    threshold = total_valid * 0.05 if total_valid > 0 else 0
    underrepresented = [cat for cat, count in category_counts.items() if count < threshold and total_valid > 20]

    # Token stats
    all_token_counts = []
    for pair in valid_pairs:
        assistant_msg = next((m for m in pair.get("messages", []) if m["role"] == "assistant"), None)
        if assistant_msg:
            all_token_counts.append(count_tokens(assistant_msg["content"]))

    avg_tokens = sum(all_token_counts) / len(all_token_counts) if all_token_counts else 0
    min_tokens = min(all_token_counts) if all_token_counts else 0
    max_tokens = max(all_token_counts) if all_token_counts else 0

    # Build report
    report_lines = [
        "# Training Data Validation Report",
        "",
        "## Summary",
        "",
        f"- **Total pairs loaded**: {len(all_pairs)}",
        f"- **Duplicates removed**: {duplicates_removed}",
        f"- **Valid pairs**: {total_valid}",
        f"- **Invalid pairs**: {len(invalid_pairs)}",
        f"- **Validation rate**: {total_valid / len(all_pairs) * 100:.1f}%" if all_pairs else "",
        "",
        "## Token Statistics",
        "",
        f"- **Average response tokens**: {avg_tokens:.0f}",
        f"- **Min response tokens**: {min_tokens}",
        f"- **Max response tokens**: {max_tokens}",
        "",
        "## Category Distribution",
        "",
        "| Category | Count | % |",
        "|----------|-------|---|",
    ]
    for cat, count in category_counts.most_common():
        pct = count / total_valid * 100 if total_valid else 0
        flag = " (underrepresented)" if cat in underrepresented else ""
        report_lines.append(f"| {cat} | {count} | {pct:.1f}%{flag} |")

    if issue_counts:
        report_lines.extend(
            [
                "",
                "## Validation Issues",
                "",
                "| Issue | Count |",
                "|-------|-------|",
            ]
        )
        for issue, count in issue_counts.most_common():
            report_lines.append(f"| {issue} | {count} |")

    if underrepresented:
        report_lines.extend(
            [
                "",
                "## Balance Warnings",
                "",
                f"Categories below 5% threshold ({threshold:.0f} pairs):",
                "",
            ]
        )
        for cat in underrepresented:
            report_lines.append(f"- {cat}: {category_counts[cat]} pairs")

    report_text = "\n".join(report_lines) + "\n"

    # Write outputs
    VALIDATED_DIR.mkdir(parents=True, exist_ok=True)
    if valid_pairs:
        write_jsonl(valid_pairs, VALIDATED_DIR / "training_data.jsonl")
        print(f"  Written {total_valid} validated pairs to {VALIDATED_DIR / 'training_data.jsonl'}")

    report_path = VALIDATED_DIR / "report.md"
    report_path.write_text(report_text, encoding="utf-8")
    print(f"  Written report to {report_path}")

    # Print summary
    print(f"\n  Valid: {total_valid} | Invalid: {len(invalid_pairs)} | Dupes removed: {duplicates_removed}")
    if all_token_counts:
        print(f"  Tokens: avg={avg_tokens:.0f}, min={min_tokens}, max={max_tokens}")

    return {
        "total": len(all_pairs),
        "valid": total_valid,
        "invalid": len(invalid_pairs),
        "duplicates_removed": duplicates_removed,
        "categories": len(category_counts),
    }


if __name__ == "__main__":
    run()
