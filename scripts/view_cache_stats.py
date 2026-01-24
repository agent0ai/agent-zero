#!/usr/bin/env python3
"""
View Anthropic Prompt Cache Statistics

Usage:
    python scripts/view_cache_stats.py [--hours 24] [--model claude-opus-4-5-20251101]
"""

import argparse
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from python.helpers.cache_metrics import get_cache_tracker


def main():
    parser = argparse.ArgumentParser(description="View Anthropic prompt cache statistics")
    parser.add_argument(
        "--hours",
        type=int,
        default=24,
        help="Look back this many hours (default: 24)",
    )
    parser.add_argument(
        "--model",
        type=str,
        default=None,
        help="Filter by model name (optional)",
    )

    args = parser.parse_args()

    tracker = get_cache_tracker()
    tracker.print_cache_report(hours=args.hours)


if __name__ == "__main__":
    main()
