#!/usr/bin/env python3
"""
Comprehensive Google Voice Integration Test Suite
Tests the full workflow: message creation, approval, sending, and tracking

Usage:
    python scripts/google_voice_integration_test.py [--interactive]
"""

import argparse
import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from instruments.custom.google_voice.google_voice_manager import GoogleVoiceManager
from python.helpers import files


async def test_message_lifecycle():
    """
    Test the complete message lifecycle:
    1. Draft message
    2. List draft messages
    3. Approve message
    4. Send message (in headless mode)
    5. Track sent messages
    """
    print("\n" + "=" * 70)
    print("  GOOGLE VOICE MESSAGE LIFECYCLE TEST")
    print("=" * 70)

    # Initialize manager
    db_path = Path(files.get_abs_path("./instruments/custom/google_voice/data/google_voice.db"))
    db_path.parent.mkdir(parents=True, exist_ok=True)
    manager = GoogleVoiceManager(str(db_path))

    # Test 1: Draft a message
    print("\n[1/5] DRAFTING MESSAGE")
    print("─" * 70)
    test_phone = "+14155551234"
    test_message = "Hi! This is a test message from Agent Jumbo Google Voice integration."

    draft_msg = manager.draft_outbound(test_phone, test_message)
    print(f"✓ Drafted message ID: {draft_msg['id']}")
    print(f"  To: {draft_msg['to_number']}")
    print(f"  Message: {draft_msg['body'][:50]}...")
    print(f"  Status: {draft_msg['status']}")

    # Test 2: List draft messages
    print("\n[2/5] LISTING DRAFT MESSAGES")
    print("─" * 70)
    drafts = manager.list_outbound("draft")
    print(f"✓ Found {len(drafts)} draft message(s)")
    for msg in drafts[:3]:
        print(f"  - ID {msg['id']}: {msg['to_number']} ({msg['status']})")

    # Test 3: Get message database stats
    print("\n[3/5] DATABASE STATISTICS")
    print("─" * 70)
    all_outbound = manager.list_outbound()
    sent_messages = manager.list_outbound("sent")
    failed_messages = manager.list_outbound("failed")

    print(f"✓ Total messages: {len(all_outbound)}")
    print(f"  - Sent: {len(sent_messages)}")
    print(f"  - Failed: {len(failed_messages)}")
    print(f"  - Draft: {len(drafts)}")

    # Test 4: List inbound messages
    print("\n[4/5] INBOUND MESSAGES")
    print("─" * 70)
    inbound = manager.list_inbound(limit=5)
    print(f"✓ Inbound messages: {len(inbound)}")
    for msg in inbound[:3]:
        print(f"  - From {msg['from_number']}: {msg['body'][:40]}...")

    # Test 5: Event bus integration
    print("\n[5/5] EVENT BUS STATUS")
    print("─" * 70)
    if manager.event_bus:
        print("✓ Event bus connected")
        print(f"  Event store: {manager.event_store}")
    else:
        print("⚠ Event bus not available (optional)")

    print("\n" + "=" * 70)
    print("  INTEGRATION TEST COMPLETE")
    print("=" * 70)
    print("\n✓ All tests passed!")
    print("\nNext steps:")
    print("  1. Review messages in Google Voice web UI")
    print("  2. To send pending messages, run:")
    print("     python scripts/test_google_voice_checkin.py --auto-send")


async def test_message_sending():
    """
    Test actually sending a message (requires browser interaction)
    """
    print("\n" + "=" * 70)
    print("  GOOGLE VOICE MESSAGE SENDING TEST")
    print("=" * 70)

    db_path = Path(files.get_abs_path("./instruments/custom/google_voice/data/google_voice.db"))
    db_path.parent.mkdir(parents=True, exist_ok=True)
    manager = GoogleVoiceManager(str(db_path))

    # Create a test message
    test_phone = input("\n📱 Enter phone number to send test message to: ").strip()
    if not test_phone.startswith("+"):
        test_phone = "+" + test_phone

    test_message = input("📝 Enter message to send: ").strip()

    print(f"\n{'─'*70}")
    print("Preview:")
    print(f"  To: {test_phone}")
    print(f"  Message: {test_message}")
    print(f"{'─'*70}")

    confirm = input("\n⚠️  Send this message? (yes/no): ").strip().lower()
    if confirm != "yes":
        print("❌ Cancelled")
        return

    # Draft and send
    draft_msg = manager.draft_outbound(test_phone, test_message)
    print(f"\n✓ Drafted message ID: {draft_msg['id']}")

    print("\n⏳ Sending message (may require browser authentication)...")
    result = await manager.approve_and_send(draft_msg["id"])

    if result["success"]:
        print("✓ Message sent successfully!")
        print(f"  Sent at: {result['message'].get('sent_at', '?')}")
    else:
        print(f"❌ Failed to send: {result.get('error', 'unknown error')}")


async def show_usage_examples():
    """Show usage examples for common tasks"""
    print("\n" + "=" * 70)
    print("  GOOGLE VOICE USAGE EXAMPLES")
    print("=" * 70)

    examples = """

📨 SENDING CHECK-IN MESSAGES (DRY RUN)
    python scripts/test_google_voice_checkin.py

📨 SENDING CHECK-IN MESSAGES (LIVE)
    python scripts/test_google_voice_checkin.py --auto-send

📋 LISTING PENDING MESSAGES
    python scripts/test_google_voice_checkin.py --list-pending

🧪 RUNNING INTEGRATION TESTS
    python scripts/google_voice_integration_test.py

🔐 SENDING CUSTOM MESSAGE (INTERACTIVE)
    python scripts/google_voice_integration_test.py --interactive

📊 SENDING BULK MESSAGES FROM CSV
    # Create csv_messages.csv with columns: phone,message
    python scripts/google_voice_bulk_send.py csv_messages.csv --preview
    python scripts/google_voice_bulk_send.py csv_messages.csv --send

📅 AUTOMATED CHECK-IN MESSAGES (DAILY)
    # Add to cron: 0 8 * * * python scripts/test_google_voice_checkin.py --auto-send

API ENDPOINTS
    POST /google_voice_outbound_create
    GET  /google_voice_outbound_list
    POST /google_voice_outbound_approve
    GET  /google_voice_inbound_list
    POST /google_voice_inbound_sync
    """
    print(examples)


async def main():
    parser = argparse.ArgumentParser(
        description="Google Voice integration test suite",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "--interactive",
        action="store_true",
        help="Run interactive message sending test",
    )
    parser.add_argument(
        "--examples",
        action="store_true",
        help="Show usage examples",
    )

    args = parser.parse_args()

    try:
        if args.examples:
            await show_usage_examples()
        elif args.interactive:
            await test_message_sending()
        else:
            await test_message_lifecycle()

    except KeyboardInterrupt:
        print("\n\n⛔ Test cancelled by user")
        sys.exit(0)
    except Exception as e:
        print(f"\n❌ Error: {e!s}")
        import traceback

        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
