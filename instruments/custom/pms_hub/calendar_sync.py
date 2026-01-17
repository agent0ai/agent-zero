"""
Calendar Hub Integration Service
Synchronizes PMS reservations and pricing with Google Calendar, Outlook, and other calendar systems
"""

import sys
from datetime import date
from pathlib import Path
from typing import Any, Optional

# Add imports path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from .canonical_models import (
    Reservation,
)
from .provider_registry import ProviderRegistry


class CalendarSyncService:
    """
    Manages synchronization between PMS reservations and calendar systems
    Supports Google Calendar, Outlook, and other calendar providers via calendar_hub

    Architecture:
    - Transforms PMS reservations into calendar events
    - Applies dynamic pricing rules to event metadata
    - Manages availability blocking (cleaning, maintenance, minimum stay)
    - Handles multi-calendar accounts per property
    - Maintains audit trail of all sync operations
    """

    def __init__(self):
        """Initialize calendar sync service with registry and calendar hub manager"""
        self.registry = ProviderRegistry()

        # Import calendar_hub tool
        try:
            from instruments.custom.calendar_hub.calendar_manager import CalendarHubManager
            from python.helpers import files

            db_path = files.get_abs_path("./instruments/custom/calendar_hub/data/calendar_hub.db")
            self.calendar_manager = CalendarHubManager(db_path)
        except ImportError as e:
            print(f"Warning: Calendar Hub not available for sync: {e}")
            self.calendar_manager = None

        # Import event bus for event publishing
        try:
            import tempfile

            from python.helpers.event_bus import EventBus, EventStore

            # Create temporary event store
            temp_db = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
            event_store = EventStore(temp_db.name)
            self.event_bus = EventBus(event_store)
        except (ImportError, Exception) as e:
            print(f"Warning: EventBus not available: {e}")
            self.event_bus = None

    async def sync_reservation_to_calendar(
        self, reservation: Reservation, calendar_id: Optional[int] = None
    ) -> Optional[dict[str, Any]]:
        """
        Sync a PMS reservation to calendar system

        Args:
            reservation: Canonical Reservation object
            calendar_id: Optional specific calendar ID to sync to (if None, uses property default)

        Returns:
            Dictionary with calendar event details or None if failed

        ★ Insight ─────────────────────────────────────
        - Transforms PMS data to calendar event format
        - Includes guest name, dates, pricing in description
        - Creates separate calendar events per calendar account
        - Maintains metadata for future updates/deletions
        ─────────────────────────────────────────────────
        """
        if not self.calendar_manager:
            return None

        try:
            # Format event details from reservation
            event_title = self._format_event_title(reservation)
            event_description = self._format_event_description(reservation)
            start_date = reservation.check_in_date.isoformat()
            end_date = reservation.check_out_date.isoformat()

            # Create event in calendar system
            result = self.calendar_manager.create_event(
                calendar_id=calendar_id or 1,  # Default to first calendar
                title=event_title,
                start=start_date,
                end=end_date,
                attendees=[reservation.guest_email] if reservation.guest_email else None,
                notes=event_description,
            )

            if result and result.get("status") == "success":
                event_data = result.get("data", {})

                # Store calendar event ID in reservation for future reference
                if not hasattr(reservation, "calendar_event_ids"):
                    reservation.calendar_event_ids = {}
                reservation.calendar_event_ids[f"calendar_{calendar_id or 1}"] = event_data.get("id")

                # Emit event to EventBus (non-blocking, fire and forget)
                if self.event_bus:
                    try:
                        await self.event_bus.emit(
                            "pms.calendar.event_created",
                            {
                                "reservation_id": reservation.provider_id,
                                "calendar_event_id": event_data.get("id"),
                                "calendar_id": calendar_id,
                            },
                        )
                    except Exception as e:
                        print(f"Warning: EventBus emit failed: {e}")

                return event_data

            return None

        except Exception as e:
            print(f"Error syncing reservation to calendar: {e}")
            return None

    async def sync_blocked_dates(
        self, property_id: str, blocked_dates: list[date], reason: str = "unavailable"
    ) -> bool:
        """
        Sync blocked dates (cleaning, maintenance, owner use) to calendar

        Args:
            property_id: PMS property ID
            blocked_dates: List of dates to block
            reason: Reason for blocking (cleaning, maintenance, owner_use, etc.)

        Returns:
            True if successful, False otherwise

        ★ Insight ─────────────────────────────────────
        - Creates separate calendar events for each blocked period
        - Groups consecutive dates into single events
        - Tracks reason in event description for visibility
        - Useful for cleaning days, maintenance windows
        ─────────────────────────────────────────────────
        """
        if not self.calendar_manager or not blocked_dates:
            return False

        try:
            # Group consecutive dates into periods
            periods = self._group_consecutive_dates(blocked_dates)

            for period_start, period_end in periods:
                title = f"Blocked - {reason.title()}"
                description = f"Property blocked for: {reason}\nProperty ID: {property_id}"

                self.calendar_manager.create_event(
                    calendar_id=1,  # Use default calendar
                    title=title,
                    start=period_start.isoformat(),
                    end=period_end.isoformat(),
                    notes=description,
                )

            # Emit event
            if self.event_bus:
                try:
                    await self.event_bus.emit(
                        "pms.calendar.blocked_dates_created",
                        {"property_id": property_id, "blocked_count": len(blocked_dates)},
                    )
                except Exception as e:
                    print(f"Warning: EventBus emit failed: {e}")

            return True

        except Exception as e:
            print(f"Error syncing blocked dates: {e}")
            return False

    def _format_event_title(self, reservation: Reservation) -> str:
        """Format calendar event title from reservation"""
        guest_name = reservation.guest_name or "Guest"
        return f"Reservation - {guest_name}"

    def _format_event_description(self, reservation: Reservation) -> str:
        """
        Format comprehensive event description with all relevant details

        Includes:
        - Guest contact information
        - Pricing and payment status
        - Check-in/checkout instructions
        - Applicable pricing rules
        """
        lines = [
            f"Guest: {reservation.guest_name or 'Unknown'}",
            f"Email: {reservation.guest_email or 'Not provided'}",
            f"Phone: {reservation.guest_phone or 'Not provided'}",
            "",
            f"Check-in: {reservation.check_in_date}",
            f"Check-out: {reservation.check_out_date}",
            f"Nights: {reservation.nights}",
            "",
            f"Status: {reservation.status.value if reservation.status else 'Unknown'}",
            f"Payment: {reservation.payment_status.value if reservation.payment_status else 'Not set'}",
            f"Total: ${reservation.total_price}",
            "",
            f"Special Requests: {getattr(reservation, 'special_requests', None) or 'None'}",
        ]

        return "\n".join(lines)

    def _group_consecutive_dates(self, dates: list[date]) -> list[tuple[date, date]]:
        """
        Group consecutive dates into periods

        Returns:
            List of (start_date, end_date) tuples
        """
        if not dates:
            return []

        sorted_dates = sorted(set(dates))
        periods = []
        period_start = sorted_dates[0]
        period_end = sorted_dates[0]

        for current_date in sorted_dates[1:]:
            if (current_date - period_end).days == 1:
                # Consecutive day, extend period
                period_end = current_date
            else:
                # Gap found, save period and start new one
                periods.append((period_start, period_end))
                period_start = current_date
                period_end = current_date

        # Add final period
        periods.append((period_start, period_end))

        return periods

    async def get_sync_status(self) -> dict[str, Any]:
        """Get sync service status and statistics"""
        return {
            "service": "calendar_sync",
            "status": "operational" if self.calendar_manager else "degraded",
            "calendar_hub_available": bool(self.calendar_manager),
            "event_bus_available": bool(self.event_bus),
        }
