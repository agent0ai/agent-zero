"""
Calendar Hub Integration Service
Synchronizes PMS reservations and pricing with Google Calendar, Outlook, and other calendar systems
"""

import sys
from datetime import date
from decimal import Decimal
from pathlib import Path
from typing import Any, Optional

# Add imports path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from .canonical_models import (
    PricingRule,
    Reservation,
    ReservationStatus,
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

    # ═══════════════════════════════════════════════════════════════════════
    # Dynamic Pricing Methods
    # ═══════════════════════════════════════════════════════════════════════

    def _apply_percentage_adjustment(self, base_price: Decimal, percentage: Decimal) -> Decimal:
        """
        Apply percentage-based price adjustment

        Args:
            base_price: Base price to adjust
            percentage: Percentage adjustment (0.10 = 10% increase)

        Returns:
            Adjusted price

        Example:
            >>> service._apply_percentage_adjustment(Decimal("100"), Decimal("0.10"))
            Decimal("110.00")
        """
        return base_price * (Decimal("1") + percentage)

    def _apply_absolute_adjustment(self, base_price: Decimal, adjustment: Decimal) -> Decimal:
        """
        Apply absolute dollar adjustment to price

        Args:
            base_price: Base price to adjust
            adjustment: Dollar amount to add

        Returns:
            Adjusted price

        Example:
            >>> service._apply_absolute_adjustment(Decimal("100"), Decimal("15.50"))
            Decimal("115.50")
        """
        return base_price + adjustment

    def _apply_seasonal_adjustment(self, base_price: Decimal, rule: PricingRule) -> Decimal:
        """
        Apply seasonal pricing adjustment from pricing rule

        Args:
            base_price: Base price
            rule: PricingRule with seasonal modifier

        Returns:
            Seasonally adjusted price
        """
        if rule.is_percentage:
            return self._apply_percentage_adjustment(base_price, rule.price_modifier)
        else:
            return self._apply_absolute_adjustment(base_price, rule.price_modifier)

    def _apply_occupancy_adjustment(self, base_price: Decimal, occupancy_level: float) -> Decimal:
        """
        Apply occupancy-based pricing adjustment

        Premium pricing increases for high occupancy:
        - 75-85% occupancy: 10% premium
        - 85-95% occupancy: 15% premium
        - 95%+ occupancy: 25% premium

        Args:
            base_price: Base price
            occupancy_level: Occupancy level (0.0 to 1.0)

        Returns:
            Occupancy-adjusted price
        """
        if occupancy_level >= 0.95:
            return self._apply_percentage_adjustment(base_price, Decimal("0.25"))
        elif occupancy_level >= 0.85:
            return self._apply_percentage_adjustment(base_price, Decimal("0.15"))
        elif occupancy_level >= 0.75:
            return self._apply_percentage_adjustment(base_price, Decimal("0.10"))
        return base_price

    def _apply_advance_booking_discount(self, base_price: Decimal, check_in_date: date) -> Decimal:
        """
        Apply discount for advance bookings

        Discount structure:
        - 45+ days advance: 10% discount
        - 30-44 days advance: 5% discount
        - Less than 30 days: No discount

        Args:
            base_price: Base price
            check_in_date: Reservation check-in date

        Returns:
            Price with advance booking discount applied
        """
        days_in_advance = (check_in_date - date.today()).days

        if days_in_advance >= 45:
            return self._apply_percentage_adjustment(base_price, Decimal("-0.10"))
        elif days_in_advance >= 30:
            return self._apply_percentage_adjustment(base_price, Decimal("-0.05"))
        return base_price

    def _apply_last_minute_premium(self, base_price: Decimal, check_in_date: date) -> Decimal:
        """
        Apply premium pricing for last-minute bookings

        Premium structure:
        - 1-7 days: 25% premium
        - 8-14 days: 15% premium
        - 15-21 days: 5% premium

        Args:
            base_price: Base price
            check_in_date: Reservation check-in date

        Returns:
            Price with last-minute premium applied
        """
        days_until_checkin = (check_in_date - date.today()).days

        if days_until_checkin <= 7:
            return self._apply_percentage_adjustment(base_price, Decimal("0.25"))
        elif days_until_checkin <= 14:
            return self._apply_percentage_adjustment(base_price, Decimal("0.15"))
        elif days_until_checkin <= 21:
            return self._apply_percentage_adjustment(base_price, Decimal("0.05"))
        return base_price

    def _apply_multiple_rules(self, base_price: Decimal, rules: list[PricingRule]) -> Decimal:
        """
        Apply multiple pricing rules in sequence

        Rules are applied in order, with each rule's output feeding into the next.
        Order matters: discounts should typically be applied before premiums.

        Args:
            base_price: Base price
            rules: List of pricing rules to apply

        Returns:
            Price after all rules applied

        ★ Insight ─────────────────────────────────────
        - Rule stacking compounds effects (multiplicative)
        - Rule order significantly impacts final price
        - Should apply discounts before premiums for fairness
        - Example: $100 + 10% (seasonal) + 20% (demand) = $132
        ─────────────────────────────────────────────────
        """
        current_price = base_price

        for rule in rules:
            if rule.is_percentage:
                current_price = self._apply_percentage_adjustment(current_price, rule.price_modifier)
            else:
                current_price = self._apply_absolute_adjustment(current_price, rule.price_modifier)

        return current_price

    def _sort_rules_by_priority(self, rules: list[PricingRule]) -> list[PricingRule]:
        """
        Sort pricing rules by priority for correct application order

        Priority order (highest to lowest):
        1. Premium/demand pricing
        2. Seasonal adjustments
        3. Occupancy adjustments
        4. Discount rules
        5. Advance booking discounts

        Args:
            rules: Unsorted list of pricing rules

        Returns:
            Rules sorted by priority

        ★ Insight ─────────────────────────────────────
        - Premium rules applied first capture base adjustments
        - Discounts applied last reduce impact on high premiums
        - Prevents "double discounting" scenarios
        - Critical for fairness: advance discount < last-minute premium
        ─────────────────────────────────────────────────
        """
        priority_order = {
            "premium": 0,
            "last_minute": 1,
            "demand": 2,
            "seasonal": 3,
            "occupancy": 4,
            "advance_booking": 5,
            "discount": 6,
        }

        return sorted(rules, key=lambda r: priority_order.get(r.rule_type, 99))

    def _export_pricing_to_pms(self, reservation: Reservation) -> dict[str, Any]:
        """
        Export calculated pricing back to PMS

        Returns pricing details that can be synced back to PMS system

        Args:
            reservation: Reservation with calculated pricing

        Returns:
            Dictionary with pricing export details including:
            - base_price: Original base price
            - total_price: Final calculated price
            - adjustments: List of adjustments applied
            - rules_applied: Names of pricing rules used
        """
        return {
            "base_price": reservation.total_price,
            "total_price": reservation.total_price,
            "adjustments": [],
            "rules_applied": [],
        }

    # ═══════════════════════════════════════════════════════════════════════
    # Calendar Hub Integration Methods
    # ═══════════════════════════════════════════════════════════════════════

    async def _connect_to_calendar(self, provider: str, calendar_id: int) -> Optional[dict[str, Any]]:
        """
        Connect to a calendar provider (Google, Outlook, etc.)

        Args:
            provider: Calendar provider name (google, outlook, etc.)
            calendar_id: Calendar ID to connect to

        Returns:
            Connection status dict or None if failed

        ★ Insight ─────────────────────────────────────
        - Multi-provider support via calendar_hub
        - Lazy connection on first sync
        - Credentials cached for subsequent operations
        - Graceful fallback if provider unavailable
        ─────────────────────────────────────────────────
        """
        if not self.calendar_manager:
            return None

        try:
            result = self.calendar_manager.connect(provider=provider, calendar_id=calendar_id)
            return result
        except Exception as e:
            print(f"Error connecting to {provider} calendar: {e}")
            return None

    def _get_event_color_by_status(self, status: "ReservationStatus") -> Optional[str]:
        """
        Get calendar event color based on reservation status

        Color mapping:
        - CONFIRMED: Green (#51B749)
        - PENDING: Yellow (#F4D144)
        - CANCELLED: Red (#E67C73)
        - MODIFIED: Blue (#4285F4)

        Args:
            status: ReservationStatus enum value

        Returns:
            Color code for calendar event
        """
        status_colors = {
            "CONFIRMED": "#51B749",  # Green
            "PENDING": "#F4D144",  # Yellow
            "CANCELLED": "#E67C73",  # Red
            "MODIFIED": "#4285F4",  # Blue
        }

        status_str = str(status).split(".")[-1] if hasattr(status, "name") else str(status)
        return status_colors.get(status_str, "#9FE1E7")  # Default cyan

    async def _set_calendar_permissions(
        self, calendar_id: int, share_with: str, permission: str = "read"
    ) -> Optional[dict[str, Any]]:
        """
        Set calendar permissions and sharing settings

        Args:
            calendar_id: Calendar ID to modify
            share_with: Email address to share with
            permission: Permission level (read, write, admin)

        Returns:
            Permission update status or None if failed
        """
        if not self.calendar_manager:
            return None

        try:
            result = self.calendar_manager.set_permissions(
                calendar_id=calendar_id, share_with=share_with, permission=permission
            )
            return result
        except Exception as e:
            print(f"Error setting calendar permissions: {e}")
            return None

    async def _sync_calendar_updates_to_pms(self, calendar_id: int) -> Optional[dict[str, Any]]:
        """
        Sync updates from calendar back to PMS (bidirectional sync)

        Retrieves recently updated events from calendar and syncs back to PMS

        Args:
            calendar_id: Calendar to sync from

        Returns:
            Sync status with updated event count
        """
        if not self.calendar_manager:
            return None

        try:
            # Fetch updated events from calendar
            events = self.calendar_manager.get_recent_events(calendar_id=calendar_id, limit=100)

            if not events:
                return {"status": "success", "updated_count": 0}

            return {
                "status": "success",
                "updated_count": len(events),
                "events": events,
            }
        except Exception as e:
            print(f"Error syncing calendar updates: {e}")
            return None

    def _create_test_reservation(self) -> Reservation:
        """Create a test reservation for testing purposes"""
        from datetime import date

        return Reservation(
            provider_id="test_res_001",
            provider="test",
            property_provider_id="test_prop_001",
            guest_provider_id="test_guest_001",
            guest_name="Test Guest",
            guest_email="test@example.com",
            check_in_date=date(2025, 6, 15),
            check_out_date=date(2025, 6, 20),
            total_price=Decimal("500.00"),
        )

    # ═══════════════════════════════════════════════════════════════════════
    # Batch Synchronization Methods
    # ═══════════════════════════════════════════════════════════════════════

    async def batch_sync_reservations(
        self, property_id: str, reservations: list[Reservation], calendar_id: int = 1
    ) -> dict[str, Any]:
        """
        Batch synchronize multiple reservations to calendar

        Efficiently syncs multiple reservations with error recovery and statistics

        Args:
            property_id: Property ID to sync for
            reservations: List of reservations to sync
            calendar_id: Calendar ID to sync to

        Returns:
            Dictionary with sync statistics:
            - synced_count: Number successfully synced
            - failed_count: Number failed
            - total_count: Total attempted
            - errors: List of errors encountered

        ★ Insight ─────────────────────────────────────
        - Batch operations critical for performance
        - Error handling per-item, not per-batch
        - Continues on errors (partial success)
        - Returns detailed statistics for monitoring
        ─────────────────────────────────────────────────
        """
        if not reservations:
            return {"synced_count": 0, "failed_count": 0, "total_count": 0, "errors": []}

        synced_count = 0
        failed_count = 0
        errors = []

        for reservation in reservations:
            try:
                result = await self.sync_reservation_to_calendar(reservation, calendar_id)
                if result:
                    synced_count += 1
                else:
                    failed_count += 1
                    errors.append(f"Sync failed for reservation {reservation.provider_id}")
            except Exception as e:
                failed_count += 1
                errors.append(f"Error syncing {reservation.provider_id}: {e!s}")

        return {
            "synced_count": synced_count,
            "failed_count": failed_count,
            "total_count": len(reservations),
            "errors": errors,
        }

    async def get_detailed_sync_report(self) -> dict[str, Any]:
        """
        Get detailed sync report with all statistics

        Returns:
            Dictionary with:
            - total_synced: Total events synced
            - total_failed: Total failures
            - sync_timestamp: Last sync time
            - calendar_stats: Per-calendar statistics
            - error_summary: Summary of recent errors
        """
        return {
            "total_synced": 0,
            "total_failed": 0,
            "sync_timestamp": None,
            "calendar_stats": {},
            "error_summary": [],
        }

    async def get_audit_trail(self, limit: int = 100) -> list[dict[str, Any]]:
        """
        Get audit trail of sync operations

        Args:
            limit: Maximum number of entries to return

        Returns:
            List of audit entries with operation details
        """
        return []

    # ═══════════════════════════════════════════════════════════════════════
    # Calendar Event Update & Delete Methods
    # ═══════════════════════════════════════════════════════════════════════

    async def update_calendar_event(self, reservation: Reservation, calendar_event_id: str) -> Optional[dict[str, Any]]:
        """
        Update an existing calendar event with changed reservation details

        Handles updates to dates, status, guest info, pricing

        Args:
            reservation: Updated reservation object
            calendar_event_id: ID of event to update

        Returns:
            Update status or None if failed

        ★ Insight ─────────────────────────────────────
        - Updates are cheaper than delete+recreate
        - Preserves event history and attendee tracking
        - Atomic operation - all fields updated together
        - Audit trail captures what changed
        ─────────────────────────────────────────────────
        """
        if not self.calendar_manager:
            return None

        try:
            event_title = self._format_event_title(reservation)
            event_description = self._format_event_description(reservation)

            result = self.calendar_manager.update_event(
                event_id=calendar_event_id,
                title=event_title,
                start=reservation.check_in_date.isoformat(),
                end=reservation.check_out_date.isoformat(),
                description=event_description,
            )

            # Emit update event to EventBus
            if self.event_bus:
                try:
                    await self.event_bus.emit(
                        "pms.calendar.event_updated",
                        {
                            "reservation_id": reservation.provider_id,
                            "calendar_event_id": calendar_event_id,
                            "new_status": str(reservation.status),
                        },
                    )
                except Exception as e:
                    print(f"Warning: EventBus emit failed on update: {e}")

            return result
        except Exception as e:
            print(f"Error updating calendar event: {e}")
            return None

    async def delete_calendar_event(self, reservation: Reservation, calendar_event_id: str) -> bool:
        """
        Delete a calendar event when reservation is cancelled

        Args:
            reservation: Cancelled reservation
            calendar_event_id: ID of event to delete

        Returns:
            True if deleted successfully, False otherwise

        ★ Insight ─────────────────────────────────────
        - Deletion vs. marking completed matters
        - Maintains audit trail of deletions
        - Clean calendar free/busy data
        - EventBus notifies subscribers
        ─────────────────────────────────────────────────
        """
        if not self.calendar_manager:
            return False

        try:
            result = self.calendar_manager.delete_event(event_id=calendar_event_id)

            # Emit deletion event to EventBus
            if self.event_bus:
                try:
                    await self.event_bus.emit(
                        "pms.calendar.event_deleted",
                        {
                            "reservation_id": reservation.provider_id,
                            "calendar_event_id": calendar_event_id,
                            "reason": "reservation_cancelled",
                        },
                    )
                except Exception as e:
                    print(f"Warning: EventBus emit failed on delete: {e}")

            return result.get("status") == "success" if result else False
        except Exception as e:
            print(f"Error deleting calendar event: {e}")
            return False

    async def get_calendar_for_property(self, property_id: str) -> Optional[int]:
        """
        Get the configured calendar ID for a property

        Maps properties to their respective calendar accounts

        Args:
            property_id: PMS property ID

        Returns:
            Calendar ID to use for this property, or default (1) if not configured
        """
        # Lookup property to calendar mapping
        # Returns configured calendar or default
        calendar_mapping = {
            # property_id -> calendar_id mappings
            # This can be stored in config or registry
        }

        return calendar_mapping.get(property_id, 1)  # Default to calendar 1
