#!/usr/bin/env python3
"""
Manage Anthropic Batch Jobs

Usage:
    python scripts/manage_batches.py list             # List all batches
    python scripts/manage_batches.py status <batch_id> # Get batch status
    python scripts/manage_batches.py poll              # Poll all pending batches
"""

import argparse
import asyncio
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from python.helpers.batch_processor import get_batch_processor


async def list_batches():
    """List all pending batches"""
    processor = get_batch_processor()
    batches = processor.db.list_pending_batches()

    if not batches:
        print("No pending or processing batches found.")
        return

    print(f"\nFound {len(batches)} pending/processing batches:\n")
    print(f"{'Batch ID':<25} {'Status':<12} {'Requests':<10} {'Created':<20}")
    print("=" * 70)

    for batch in batches:
        print(f"{batch.batch_id:<25} {batch.status.value:<12} {batch.request_count:<10} {batch.created_at:<20}")

    print()


async def get_status(batch_id: str):
    """Get status of a specific batch"""
    processor = get_batch_processor()
    batch = await processor.poll_batch(batch_id)

    if not batch:
        print(f"Batch {batch_id} not found.")
        return

    print("\nBatch Status:")
    print(f"  ID:           {batch.batch_id}")
    print(f"  Status:       {batch.status.value}")
    print(f"  Requests:     {batch.request_count}")
    print(f"  Completed:    {batch.completed_count}")
    print(f"  Failed:       {batch.failed_count}")
    print(f"  Created:      {batch.created_at}")
    print(f"  Submitted:    {batch.submitted_at or 'Not yet'}")
    print(f"  Completed:    {batch.completed_at or 'Not yet'}")
    print(f"  Cost:         ${batch.cost:.4f}")
    print()


async def poll_all():
    """Poll all pending batches"""
    processor = get_batch_processor()
    print("Polling all pending batches...")
    await processor.poll_all_pending()
    print("Done.")


async def main():
    parser = argparse.ArgumentParser(description="Manage Anthropic batch jobs")
    subparsers = parser.add_subparsers(dest="command", help="Command to execute")

    # List command
    subparsers.add_parser("list", help="List all batches")

    # Status command
    status_parser = subparsers.add_parser("status", help="Get batch status")
    status_parser.add_argument("batch_id", help="Batch ID to check")

    # Poll command
    subparsers.add_parser("poll", help="Poll all pending batches")

    args = parser.parse_args()

    if args.command == "list":
        await list_batches()
    elif args.command == "status":
        await get_status(args.batch_id)
    elif args.command == "poll":
        await poll_all()
    else:
        parser.print_help()


if __name__ == "__main__":
    asyncio.run(main())
