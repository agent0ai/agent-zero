#!/usr/bin/env python3
"""
Google Voice Check-in Message Test Script
Sends welcome messages to customers checking in today via Google Voice SMS

Usage:
    python scripts/test_google_voice_checkin.py [--dry-run] [--auto-send]

Options:
    --dry-run      Show what would be sent without sending (default: True)
    --auto-send    Actually send messages (requires user confirmation)
"""

import sys
import asyncio
from pathlib import Path
from datetime import datetime, date
from typing import Optional
import argparse

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from instruments.custom.pms_hub.canonical_models import (
    Reservation,
    ReservationStatus,
    MessageType,
)
from python.helpers import files


async def get_todays_checkins() -> list[Reservation]:
    """
    Get sample reservations checking in today
    In production, this would query from PMS providers

    For testing, we'll create sample data with today's date
    """
    today = date.today()

    # Sample customer data for today's check-ins
    sample_checkins = [
        Reservation(
            provider_id="res_001",
            provider="hostaway",
            property_provider_id="prop_001",
            guest_name="John Smith",
            guest_email="john.smith@example.com",
            guest_phone="+14155551234",  # San Francisco
            check_in_date=today,
            check_out_date=date(today.year, today.month, today.day + 3),
            status=ReservationStatus.CONFIRMED,
        ),
        Reservation(
            provider_id="res_002",
            provider="lodgify",
            property_provider_id="prop_002",
            guest_name="Maria Garcia",
            guest_email="maria.garcia@example.com",
            guest_phone="+13105555678",  # Los Angeles
            check_in_date=today,
            check_out_date=date(today.year, today.month, today.day + 2),
            status=ReservationStatus.CONFIRMED,
        ),
        Reservation(
            provider_id="res_003",
            provider="airbnb",
            property_provider_id="prop_003",
            guest_name="Robert Johnson",
            guest_email="robert.j@example.com",
            guest_phone="+1212555910",  # New York
            check_in_date=today,
            check_out_date=date(today.year, today.month, today.day + 5),
            status=ReservationStatus.CONFIRMED,
        ),
    ]

    return sample_checkins


def format_checkin_message(guest_name: str, property_name: str = "Your Property") -> str:
    """
    Format a friendly check-in message

    Args:
        guest_name: Name of the guest
        property_name: Name of the property

    Returns:
        Formatted message text
    """
    return (
        f"Hi {guest_name.split()[0]}! Welcome to {property_name}! 🎉\n\n"
        f"We're excited to host you! Check-in is ready. If you have any questions, "
        f"reply here or call. Enjoy your stay!"
    )


async def create_google_voice_messages(
    reservations: list[Reservation],
    dry_run: bool = True,
) -> list[dict]:
    """
    Create Google Voice SMS messages for check-ins

    Args:
        reservations: List of reservations checking in today
        dry_run: If True, don't actually send (default: True)

    Returns:
        List of message dictionaries
    """
    from instruments.custom.google_voice.google_voice_manager import GoogleVoiceManager

    db_path = Path(files.get_abs_path("./instruments/custom/google_voice/data/google_voice.db"))

    # Ensure directory exists
    db_path.parent.mkdir(parents=True, exist_ok=True)

    manager = GoogleVoiceManager(str(db_path))
    messages = []

    print(f"\n{'='*70}")
    print(f"  GOOGLE VOICE CHECK-IN MESSAGE TEST")
    print(f"{'='*70}")
    print(f"\n📅 Check-in Date: {date.today()}")
    print(f"⏰ Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Mode: {'DRY RUN (preview only)' if dry_run else 'SENDING MESSAGES'}")

    for i, reservation in enumerate(reservations, 1):
        phone = reservation.guest_phone
        guest_name = reservation.guest_name
        property_id = reservation.property_provider_id

        # Create friendly message
        message_text = format_checkin_message(guest_name, f"Property {property_id}")

        print(f"\n{'─'*70}")
        print(f"Message {i}/{len(reservations)}")
        print(f"├─ To: {guest_name} <{phone}>")
        print(f"├─ Property: {property_id}")
        print(f"├─ Reservation ID: {reservation.provider_id}")
        print(f"├─ Provider: {reservation.provider}")
        print(f"├─ Check-in: {reservation.check_in_date}")
        print(f"├─ Check-out: {reservation.check_out_date}")
        print(f"└─ Message:")
        print(f"   {message_text.replace(chr(10), chr(10) + '   ')}")

        if not dry_run:
            try:
                # Draft message
                draft_msg = manager.draft_outbound(phone, message_text)
                print(f"\n   ✓ Drafted message ID: {draft_msg['id']}")

                # Send message
                result = await manager.approve_and_send(draft_msg["id"])
                if result["success"]:
                    sent_at = result["message"].get("sent_at", "unknown")
                    print(f"   ✓ SENT at {sent_at}")
                    messages.append(
                        {
                            "message_id": draft_msg["id"],
                            "reservation_id": reservation.provider_id,
                            "to_number": phone,
                            "guest_name": guest_name,
                            "status": "sent",
                            "sent_at": sent_at,
                        }
                    )
                else:
                    error = result.get("error", "unknown error")
                    print(f"   ✗ FAILED: {error}")
                    messages.append(
                        {
                            "message_id": draft_msg["id"],
                            "reservation_id": reservation.provider_id,
                            "to_number": phone,
                            "guest_name": guest_name,
                            "status": "failed",
                            "error": error,
                        }
                    )
            except Exception as e:
                print(f"   ✗ ERROR: {str(e)}")
                messages.append(
                    {
                        "reservation_id": reservation.provider_id,
                        "to_number": phone,
                        "guest_name": guest_name,
                        "status": "error",
                        "error": str(e),
                    }
                )
        else:
            messages.append(
                {
                    "reservation_id": reservation.provider_id,
                    "to_number": phone,
                    "guest_name": guest_name,
                    "status": "draft",
                }
            )

    return messages


async def list_pending_messages() -> None:
    """List all pending and draft messages in the system"""
    from instruments.custom.google_voice.google_voice_manager import GoogleVoiceManager

    db_path = Path(files.get_abs_path("./instruments/custom/google_voice/data/google_voice.db"))
    db_path.parent.mkdir(parents=True, exist_ok=True)

    manager = GoogleVoiceManager(str(db_path))

    print(f"\n{'='*70}")
    print(f"  PENDING GOOGLE VOICE MESSAGES")
    print(f"{'='*70}")

    draft_messages = manager.list_outbound("draft")
    pending_messages = manager.list_outbound("approved")
    sent_messages = manager.list_outbound("sent")

    if draft_messages:
        print(f"\n📝 DRAFT ({len(draft_messages)}):")
        for msg in draft_messages[:5]:
            print(f"  ID {msg['id']}: To {msg['to_number']}")
            print(f"    Message: {msg['body'][:60]}...")

    if pending_messages:
        print(f"\n⏳ APPROVED ({len(pending_messages)}):")
        for msg in pending_messages[:5]:
            print(f"  ID {msg['id']}: To {msg['to_number']}")

    if sent_messages:
        print(f"\n✓ SENT ({len(sent_messages)}):")
        for msg in sent_messages[:5]:
            print(f"  ID {msg['id']}: To {msg['to_number']} at {msg.get('sent_at', '?')}")

    print(f"\n")


async def main():
    """Main test runner"""
    parser = argparse.ArgumentParser(
        description="Test Google Voice check-in messaging",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Preview messages without sending
  python scripts/test_google_voice_checkin.py

  # Send messages (with confirmation)
  python scripts/test_google_voice_checkin.py --auto-send
        """,
    )
    parser.add_argument(
        "--auto-send",
        action="store_true",
        help="Actually send messages (default: dry run only)",
    )
    parser.add_argument(
        "--list-pending",
        action="store_true",
        help="List pending messages in system",
    )

    args = parser.parse_args()

    try:
        if args.list_pending:
            await list_pending_messages()
            return

        # Get today's check-ins
        checkins = await get_todays_checkins()

        if not checkins:
            print("❌ No check-ins found for today")
            return

        print(f"\n✓ Found {len(checkins)} customers checking in today")

        # Create and optionally send messages
        dry_run = not args.auto_send
        messages = await create_google_voice_messages(checkins, dry_run=dry_run)

        # Summary
        print(f"\n{'='*70}")
        print(f"  SUMMARY")
        print(f"{'='*70}")
        print(f"Total customers: {len(checkins)}")
        print(f"Mode: {'DRY RUN (preview)' if dry_run else 'LIVE SEND'}")

        if dry_run:
            print(f"\n💡 To actually send these messages, run:")
            print(f"   python scripts/test_google_voice_checkin.py --auto-send")
        else:
            sent = sum(1 for m in messages if m.get("status") == "sent")
            failed = sum(1 for m in messages if m.get("status") == "failed")
            print(f"\n✓ Sent: {sent}")
            if failed:
                print(f"✗ Failed: {failed}")

        print(f"\n{'='*70}\n")

    except Exception as e:
        print(f"\n❌ Error: {str(e)}")
        import traceback

        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
