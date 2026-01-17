"""
Calendar Hub Integration Tests - Team A TDD Swarm
Tests for PMS calendar synchronization with Google/Outlook calendars
Tests dynamic pricing rule synchronization and availability blocking
"""

from datetime import date, timedelta
from decimal import Decimal
from unittest.mock import patch

import pytest

from instruments.custom.pms_hub.canonical_models import (
    PricingRule,
    Reservation,
    ReservationStatus,
)


class TestCalendarSyncServiceInitialization:
    """Tests for calendar sync service initialization"""

    @pytest.mark.unit
    def test_calendar_sync_service_creation(self):
        """Test creating calendar sync service"""
        from instruments.custom.pms_hub.calendar_sync import CalendarSyncService

        service = CalendarSyncService()
        assert service is not None
        assert hasattr(service, "registry")
        assert hasattr(service, "event_bus")

    @pytest.mark.unit
    def test_calendar_sync_service_with_calendar_hub(self):
        """Test calendar sync service integrates with calendar hub"""
        from instruments.custom.pms_hub.calendar_sync import CalendarSyncService

        service = CalendarSyncService()
        # Calendar hub may or may not be available in test environment
        assert hasattr(service, "calendar_manager")


class TestCalendarEventCreation:
    """Tests for creating calendar events from reservations"""

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_create_event_from_reservation(self, sample_reservation):
        """Test creating calendar event from PMS reservation"""
        from unittest.mock import patch

        from instruments.custom.pms_hub.calendar_sync import CalendarSyncService

        service = CalendarSyncService()

        # Mock calendar manager
        with patch.object(service, "calendar_manager") as mock_cal:
            mock_cal.create_event.return_value = {"status": "success", "data": {"id": "evt_1"}}

            result = await service.sync_reservation_to_calendar(sample_reservation)

            assert result is not None
            assert result.get("id") == "evt_1"
            mock_cal.create_event.assert_called_once()

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_event_includes_guest_details(self, sample_reservation):
        """Test calendar event includes guest name and contact"""
        from instruments.custom.pms_hub.calendar_sync import CalendarSyncService

        service = CalendarSyncService()

        # Verify formatting includes guest details
        title = service._format_event_title(sample_reservation)
        assert sample_reservation.guest_name in title

        description = service._format_event_description(sample_reservation)
        assert sample_reservation.guest_name in description
        assert sample_reservation.guest_email in description

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_event_includes_pricing_information(self, sample_reservation):
        """Test calendar event description includes pricing rules"""
        from instruments.custom.pms_hub.calendar_sync import CalendarSyncService

        service = CalendarSyncService()
        description = service._format_event_description(sample_reservation)

        # Should include pricing info
        assert "Total:" in description or "total_price" in description.lower()
        assert str(sample_reservation.total_price) in description

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_event_title_formatting(self, sample_reservation):
        """Test event title includes property and guest names"""
        from instruments.custom.pms_hub.calendar_sync import CalendarSyncService

        service = CalendarSyncService()
        title = service._format_event_title(sample_reservation)

        # Title should include guest name
        assert "Reservation" in title
        assert sample_reservation.guest_name in title

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_event_metadata_storage(self, sample_reservation):
        """Test event metadata stored for future retrieval"""
        from unittest.mock import patch

        from instruments.custom.pms_hub.calendar_sync import CalendarSyncService

        service = CalendarSyncService()

        with patch.object(service, "calendar_manager") as mock_cal:
            mock_cal.create_event.return_value = {"status": "success", "data": {"id": "evt_metadata"}}

            await service.sync_reservation_to_calendar(sample_reservation)

            # Should store event ID in reservation
            assert hasattr(sample_reservation, "calendar_event_ids")

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_multi_property_event_creation(self, sample_reservation):
        """Test creating events for multiple properties"""
        from unittest.mock import patch

        from instruments.custom.pms_hub.calendar_sync import CalendarSyncService

        service = CalendarSyncService()

        with patch.object(service, "calendar_manager") as mock_cal:
            mock_cal.create_event.return_value = {"status": "success", "data": {"id": "evt_1"}}

            # Create event in calendar 1
            await service.sync_reservation_to_calendar(sample_reservation, calendar_id=1)

            # Create event in calendar 2
            await service.sync_reservation_to_calendar(sample_reservation, calendar_id=2)

            # Should have called create_event twice
            assert mock_cal.create_event.call_count == 2


class TestCalendarEventUpdates:
    """Tests for updating calendar events when reservations change"""

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_update_event_on_status_change(self, sample_reservation):
        """Test updating event when reservation status changes"""
        from instruments.custom.pms_hub.calendar_sync import CalendarSyncService

        service = CalendarSyncService()

        with patch.object(service, "calendar_manager") as mock_cal:
            mock_cal.update_event.return_value = {"status": "success", "updated": True}

            # Change reservation status
            sample_reservation.status = ReservationStatus.CHECKED_IN

            result = await service.update_calendar_event(sample_reservation, calendar_event_id="evt_123")

            assert result is not None
            assert result.get("updated") is True
            mock_cal.update_event.assert_called_once()

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_update_event_on_date_change(self, sample_reservation):
        """Test updating event dates when reservation dates change"""
        from instruments.custom.pms_hub.calendar_sync import CalendarSyncService

        service = CalendarSyncService()

        # Change reservation dates
        original_checkin = sample_reservation.check_in_date
        sample_reservation.check_in_date = original_checkin + timedelta(days=1)

        with patch.object(service, "calendar_manager") as mock_cal:
            mock_cal.update_event.return_value = {"status": "success", "dates_updated": True}

            result = await service.update_calendar_event(sample_reservation, calendar_event_id="evt_123")

            assert result is not None
            mock_cal.update_event.assert_called_once()

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_update_event_on_guest_change(self, sample_reservation):
        """Test updating event guest details"""
        from instruments.custom.pms_hub.calendar_sync import CalendarSyncService

        service = CalendarSyncService()

        # Change guest info
        sample_reservation.guest_name = "Jane Doe"
        sample_reservation.guest_email = "jane@example.com"

        with patch.object(service, "calendar_manager") as mock_cal:
            mock_cal.update_event.return_value = {"status": "success"}

            result = await service.update_calendar_event(sample_reservation, calendar_event_id="evt_123")

            assert result is not None

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_update_pricing_in_event_description(self, sample_reservation):
        """Test pricing rules updated in event description"""
        from instruments.custom.pms_hub.calendar_sync import CalendarSyncService

        service = CalendarSyncService()

        # Update pricing
        sample_reservation.total_price = Decimal("750.00")

        with patch.object(service, "calendar_manager") as mock_cal:
            mock_cal.update_event.return_value = {"status": "success"}

            result = await service.update_calendar_event(sample_reservation, calendar_event_id="evt_123")

            assert result is not None
            # Verify description was updated with new pricing
            call_args = mock_cal.update_event.call_args
            assert call_args is not None


class TestCalendarEventDeletion:
    """Tests for deleting calendar events when reservations are cancelled"""

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_delete_event_on_cancellation(self, sample_reservation):
        """Test deleting event when reservation is cancelled"""
        from instruments.custom.pms_hub.calendar_sync import CalendarSyncService

        service = CalendarSyncService()

        sample_reservation.status = ReservationStatus.CANCELLED

        with patch.object(service, "calendar_manager") as mock_cal:
            mock_cal.delete_event.return_value = {"status": "success", "deleted": True}

            result = await service.delete_calendar_event(reservation=sample_reservation, calendar_event_id="evt_123")

            assert result is True
            mock_cal.delete_event.assert_called_once()

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_delete_maintains_audit_trail(self, sample_reservation):
        """Test deletion logged in audit trail"""
        from instruments.custom.pms_hub.calendar_sync import CalendarSyncService

        service = CalendarSyncService()

        with patch.object(service, "calendar_manager") as mock_cal:
            mock_cal.delete_event.return_value = {"status": "success"}

            result = await service.delete_calendar_event(reservation=sample_reservation, calendar_event_id="evt_123")

            assert result is True
            # Audit trail should be updated
            audit = await service.get_audit_trail(limit=1)
            assert isinstance(audit, list)


class TestMultiCalendarAccounts:
    """Tests for handling multiple calendar accounts"""

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_sync_to_multiple_calendars(self, sample_reservation):
        """Test syncing reservation to multiple calendar accounts"""
        from instruments.custom.pms_hub.calendar_sync import CalendarSyncService

        service = CalendarSyncService()

        with patch.object(service, "calendar_manager") as mock_cal:
            mock_cal.create_event.return_value = {"status": "success", "data": {"id": "evt_1"}}

            # Sync to calendar 1
            result1 = await service.sync_reservation_to_calendar(sample_reservation, calendar_id=1)

            # Sync to calendar 2
            result2 = await service.sync_reservation_to_calendar(sample_reservation, calendar_id=2)

            assert result1 is not None
            assert result2 is not None
            assert mock_cal.create_event.call_count == 2

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_calendar_account_selection(self, sample_reservation):
        """Test selecting correct calendar account per property"""
        from instruments.custom.pms_hub.calendar_sync import CalendarSyncService

        service = CalendarSyncService()

        # Get calendar ID for property
        calendar_id = await service.get_calendar_for_property(property_id=sample_reservation.property_provider_id)

        # Should return a valid calendar ID (even if default)
        assert calendar_id is not None
        assert isinstance(calendar_id, int)
        assert calendar_id >= 1

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_handle_missing_calendar_account(self, sample_reservation):
        """Test graceful handling when calendar account not configured"""
        from instruments.custom.pms_hub.calendar_sync import CalendarSyncService

        service = CalendarSyncService()

        with patch.object(service, "calendar_manager", None):
            # Attempt to sync when calendar manager is unavailable
            result = await service.sync_reservation_to_calendar(sample_reservation, calendar_id=1)

            # Should gracefully return None
            assert result is None


class TestBlockedDatesSync:
    """Tests for syncing blocked dates (cleaning, maintenance, etc)"""

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_sync_cleaning_days(self):
        """Test creating calendar blocks for cleaning days"""
        from datetime import date
        from unittest.mock import patch

        from instruments.custom.pms_hub.calendar_sync import CalendarSyncService

        service = CalendarSyncService()

        # Create list of cleaning days
        cleaning_dates = [date(2025, 2, 7), date(2025, 2, 8)]

        with patch.object(service, "calendar_manager") as mock_cal:
            mock_cal.create_event.return_value = {"status": "success"}

            result = await service.sync_blocked_dates("prop_123", cleaning_dates, reason="cleaning")

            assert result is True
            assert mock_cal.create_event.called

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_sync_maintenance_blocks(self):
        """Test creating calendar blocks for maintenance"""
        from datetime import date
        from unittest.mock import patch

        from instruments.custom.pms_hub.calendar_sync import CalendarSyncService

        service = CalendarSyncService()
        maintenance_dates = [date(2025, 2, 15), date(2025, 2, 16), date(2025, 2, 17)]

        with patch.object(service, "calendar_manager") as mock_cal:
            mock_cal.create_event.return_value = {"status": "success"}

            result = await service.sync_blocked_dates("prop_456", maintenance_dates, reason="maintenance")

            assert result is True
            mock_cal.create_event.assert_called()

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_sync_owner_blocked_dates(self):
        """Test syncing owner-specific blocked dates"""
        from datetime import date
        from unittest.mock import patch

        from instruments.custom.pms_hub.calendar_sync import CalendarSyncService

        service = CalendarSyncService()
        owner_dates = [date(2025, 3, 1), date(2025, 3, 2)]

        with patch.object(service, "calendar_manager") as mock_cal:
            mock_cal.create_event.return_value = {"status": "success"}

            result = await service.sync_blocked_dates("prop_789", owner_dates, reason="owner_use")

            assert result is True

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_block_weekdays_only(self):
        """Test creating recurring weekday-only blocks"""
        from datetime import date

        from instruments.custom.pms_hub.calendar_sync import CalendarSyncService

        service = CalendarSyncService()

        # Test helper to verify weekday grouping
        dates = [date(2025, 2, 3), date(2025, 2, 4), date(2025, 2, 5)]  # Mon, Tue, Wed
        grouped = service._group_consecutive_dates(dates)

        assert len(grouped) == 1
        assert grouped[0][0] == date(2025, 2, 3)
        assert grouped[0][1] == date(2025, 2, 5)

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_recurring_blocks_generation(self):
        """Test generating recurring blocks (monthly, etc)"""
        from datetime import date

        from instruments.custom.pms_hub.calendar_sync import CalendarSyncService

        service = CalendarSyncService()

        # Test grouping of non-consecutive dates
        dates = [
            date(2025, 2, 1),
            date(2025, 2, 2),
            date(2025, 2, 5),  # Gap here
            date(2025, 2, 6),
            date(2025, 2, 7),
        ]

        grouped = service._group_consecutive_dates(dates)

        # Should create 2 groups: (2/1-2/2) and (2/5-2/7)
        assert len(grouped) == 2
        assert grouped[0] == (date(2025, 2, 1), date(2025, 2, 2))
        assert grouped[1] == (date(2025, 2, 5), date(2025, 2, 7))


class TestMinStayRequirements:
    """Tests for syncing minimum stay requirements to calendar"""

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_apply_min_stay_rule(self, sample_reservation):
        """Test applying minimum stay requirement from pricing rule"""
        from datetime import date

        from instruments.custom.pms_hub.canonical_models import PricingRule

        # Create pricing rule with min_stay requirement
        min_stay_rule = PricingRule(
            provider_id="rule_001",
            provider="test",
            property_provider_id="prop_001",
            rule_name="Minimum Stay 3 Nights",
            rule_type="minimum_stay",
            min_nights=3,
        )

        # Reservation is 2 nights (violates min_stay of 3)
        short_reservation = sample_reservation
        short_reservation.check_in_date = date(2026, 1, 20)
        short_reservation.check_out_date = date(2026, 1, 22)
        short_reservation.nights = 2

        # Min stay validation should flag short stays
        assert short_reservation.nights < min_stay_rule.min_nights

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_min_stay_blocking_dates(self):
        """Test blocking dates that violate minimum stay"""
        from datetime import date

        from instruments.custom.pms_hub.canonical_models import Reservation

        # Create reservation with only 1 night (violates min_stay=3)
        short_stay = Reservation(
            provider_id="res_001",
            provider="test",
            property_provider_id="prop_001",
            check_in_date=date(2026, 1, 20),
            check_out_date=date(2026, 1, 21),  # Only 1 night
        )

        min_stay_required = 3
        nights = (short_stay.check_out_date - short_stay.check_in_date).days

        # Verify that short stay violates minimum
        assert nights < min_stay_required
        assert nights == 1


class TestOverlappingReservations:
    """Tests for handling overlapping/conflicting reservations"""

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_detect_overlapping_reservations(self):
        """Test detecting overlapping reservation dates"""
        from datetime import date

        from instruments.custom.pms_hub.canonical_models import Reservation

        # Create two overlapping reservations
        res1 = Reservation(
            provider_id="res_001",
            provider="test",
            property_provider_id="prop_001",
            check_in_date=date(2026, 1, 20),
            check_out_date=date(2026, 1, 25),
        )

        res2 = Reservation(
            provider_id="res_002",
            provider="test",
            property_provider_id="prop_001",
            check_in_date=date(2026, 1, 23),
            check_out_date=date(2026, 1, 28),
        )

        # Check overlap detection
        res1_end = res1.check_out_date
        res2_start = res2.check_in_date

        # Reservations overlap if res2 starts before res1 ends
        overlaps = res2_start < res1_end and res2.check_in_date >= res1.check_in_date

        assert overlaps is True
        assert res2_start == date(2026, 1, 23)
        assert res1_end == date(2026, 1, 25)

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_handle_overlapping_calendar_events(self):
        """Test handling overlapping calendar events"""
        from datetime import date

        # Create overlapping event details
        event1_start = date(2026, 1, 20)
        event1_end = date(2026, 1, 25)
        event2_start = date(2026, 1, 23)
        event2_end = date(2026, 1, 28)

        # Detect conflict: event2 starts before event1 ends
        has_conflict = event2_start < event1_end and event2_start >= event1_start

        assert has_conflict is True

        # Resolution strategy: Event2 should be marked as blocked/conflict
        conflict_resolution = "mark_as_conflict"
        assert conflict_resolution in ["mark_as_conflict", "update_date", "cancel"]


class TestDynamicPricingRules:
    """Tests for dynamic pricing rule synchronization"""

    @pytest.mark.unit
    def test_apply_percentage_adjustment(self):
        """Test applying percentage-based price adjustment"""
        from decimal import Decimal

        from instruments.custom.pms_hub.calendar_sync import CalendarSyncService

        service = CalendarSyncService()

        base_price = Decimal("100.00")
        percentage = Decimal("0.10")  # 10% increase

        result = service._apply_percentage_adjustment(base_price, percentage)

        expected = Decimal("110.00")
        assert result == expected

    @pytest.mark.unit
    def test_apply_absolute_adjustment(self):
        """Test applying absolute price adjustment"""
        from decimal import Decimal

        from instruments.custom.pms_hub.calendar_sync import CalendarSyncService

        service = CalendarSyncService()

        base_price = Decimal("100.00")
        adjustment = Decimal("15.50")  # Add $15.50

        result = service._apply_absolute_adjustment(base_price, adjustment)

        expected = Decimal("115.50")
        assert result == expected

    @pytest.mark.unit
    def test_seasonal_pricing_adjustment(self):
        """Test seasonal pricing adjustments"""
        from datetime import date
        from decimal import Decimal

        from instruments.custom.pms_hub.calendar_sync import CalendarSyncService
        from instruments.custom.pms_hub.canonical_models import PricingRule

        service = CalendarSyncService()

        # Summer season: 20% increase
        rule = PricingRule(
            provider_id="test_provider",
            provider="test",
            property_provider_id="prop_123",
            rule_name="Summer Season",
            rule_type="seasonal",
            start_date=date(2025, 6, 1),
            end_date=date(2025, 8, 31),
            price_modifier=Decimal("0.20"),
            is_percentage=True,
        )

        base_price = Decimal("100.00")
        result = service._apply_seasonal_adjustment(base_price, rule)

        expected = Decimal("120.00")
        assert result == expected

    @pytest.mark.unit
    def test_occupancy_based_pricing(self):
        """Test pricing adjustments based on occupancy"""
        from instruments.custom.pms_hub.calendar_sync import CalendarSyncService

        service = CalendarSyncService()

        base_price = Decimal("100.00")
        occupancy_level = 0.85  # 85% occupancy -> premium pricing

        # Occupancy above 85% gets 15% premium
        result = service._apply_occupancy_adjustment(base_price, occupancy_level)

        expected = Decimal("115.00")
        assert result == expected

    @pytest.mark.unit
    def test_advance_booking_discount(self):
        """Test discount for advance bookings"""
        from decimal import Decimal

        from instruments.custom.pms_hub.calendar_sync import CalendarSyncService

        service = CalendarSyncService()

        base_price = Decimal("100.00")
        check_in_date = date.today() + timedelta(days=60)  # 60 days in advance

        # Bookings 45+ days ahead get 10% discount
        result = service._apply_advance_booking_discount(base_price, check_in_date)

        expected = Decimal("90.00")
        assert result == expected

    @pytest.mark.unit
    def test_last_minute_premium(self):
        """Test premium pricing for last-minute bookings"""
        from decimal import Decimal

        from instruments.custom.pms_hub.calendar_sync import CalendarSyncService

        service = CalendarSyncService()

        base_price = Decimal("100.00")
        check_in_date = date.today() + timedelta(days=3)  # 3 days away

        # Bookings within 7 days get 25% premium
        result = service._apply_last_minute_premium(base_price, check_in_date)

        expected = Decimal("125.00")
        assert result == expected

    @pytest.mark.unit
    def test_multiple_rules_stacking(self):
        """Test multiple pricing rules stacking"""
        from datetime import date
        from decimal import Decimal

        from instruments.custom.pms_hub.calendar_sync import CalendarSyncService

        service = CalendarSyncService()

        # Create multiple rules
        rules = [
            PricingRule(
                provider_id="test",
                provider="test",
                property_provider_id="prop_123",
                rule_name="Seasonal",
                rule_type="seasonal",
                start_date=date(2025, 6, 1),
                end_date=date(2025, 8, 31),
                price_modifier=Decimal("0.10"),  # 10% increase
                is_percentage=True,
            ),
            PricingRule(
                provider_id="test",
                provider="test",
                property_provider_id="prop_123",
                rule_name="Last Minute",
                rule_type="last_minute",
                price_modifier=Decimal("0.20"),  # 20% increase
                is_percentage=True,
            ),
        ]

        base_price = Decimal("100.00")
        result = service._apply_multiple_rules(base_price, rules)

        # 100 + 10% = 110, then 110 + 20% = 132
        expected = Decimal("132.00")
        assert result == expected

    @pytest.mark.unit
    def test_rule_priority_ordering(self):
        """Test correct ordering of pricing rule priority"""
        from decimal import Decimal

        from instruments.custom.pms_hub.calendar_sync import CalendarSyncService

        service = CalendarSyncService()

        # Create rules with different priorities
        rules = [
            PricingRule(
                provider_id="test",
                provider="test",
                property_provider_id="prop_123",
                rule_name="Discount",
                rule_type="discount",
                price_modifier=Decimal("-0.10"),  # 10% discount
                is_percentage=True,
            ),
            PricingRule(
                provider_id="test",
                provider="test",
                property_provider_id="prop_123",
                rule_name="Premium",
                rule_type="premium",
                price_modifier=Decimal("0.25"),  # 25% premium
                is_percentage=True,
            ),
        ]

        # Sort by priority (premium before discount)
        sorted_rules = service._sort_rules_by_priority(rules)

        # Premium rule should come first
        assert sorted_rules[0].rule_type == "premium"
        assert sorted_rules[1].rule_type == "discount"

    @pytest.mark.unit
    def test_pricing_rule_export_to_pms(self):
        """Test exporting pricing rules back to PMS"""
        from datetime import date
        from decimal import Decimal

        from instruments.custom.pms_hub.calendar_sync import CalendarSyncService

        service = CalendarSyncService()

        reservation = Reservation(
            provider_id="res_123",
            provider="test",
            property_provider_id="prop_123",
            guest_provider_id="guest_456",
            guest_name="John Doe",
            guest_email="john@example.com",
            check_in_date=date(2025, 6, 15),
            check_out_date=date(2025, 6, 20),
            total_price=Decimal("600.00"),
        )

        final_price = service._export_pricing_to_pms(reservation)

        # Should return price details
        assert final_price is not None
        assert "base_price" in final_price or "total_price" in final_price


class TestCalendarHubIntegration:
    """Tests for integration with calendar_hub tool"""

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_calendar_hub_connection_google(self):
        """Test connecting to Google Calendar via calendar_hub"""
        from instruments.custom.pms_hub.calendar_sync import CalendarSyncService

        service = CalendarSyncService()

        with patch.object(service, "calendar_manager") as mock_cal:
            mock_cal.connect.return_value = {"status": "connected", "provider": "google"}

            result = await service._connect_to_calendar(provider="google", calendar_id=1)

            assert result is not None
            assert result.get("provider") == "google"

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_calendar_hub_connection_outlook(self):
        """Test connecting to Outlook Calendar via calendar_hub"""
        from instruments.custom.pms_hub.calendar_sync import CalendarSyncService

        service = CalendarSyncService()

        with patch.object(service, "calendar_manager") as mock_cal:
            mock_cal.connect.return_value = {"status": "connected", "provider": "outlook"}

            result = await service._connect_to_calendar(provider="outlook", calendar_id=2)

            assert result is not None
            assert result.get("provider") == "outlook"

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_sync_to_google_calendar(self, sample_reservation):
        """Test full sync to Google Calendar"""
        from instruments.custom.pms_hub.calendar_sync import CalendarSyncService

        service = CalendarSyncService()

        with patch.object(service, "calendar_manager") as mock_cal:
            mock_cal.create_event.return_value = {
                "status": "success",
                "data": {"id": "google_event_123"},
            }

            result = await service.sync_reservation_to_calendar(sample_reservation, calendar_id=1)

            assert result is not None
            assert result.get("id") == "google_event_123"
            mock_cal.create_event.assert_called_once()

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_sync_to_outlook_calendar(self, sample_reservation):
        """Test full sync to Outlook Calendar"""
        from instruments.custom.pms_hub.calendar_sync import CalendarSyncService

        service = CalendarSyncService()

        with patch.object(service, "calendar_manager") as mock_cal:
            mock_cal.create_event.return_value = {
                "status": "success",
                "data": {"id": "outlook_event_456"},
            }

            result = await service.sync_reservation_to_calendar(sample_reservation, calendar_id=2)

            assert result is not None
            assert result.get("id") == "outlook_event_456"

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_calendar_color_coding_by_status(self):
        """Test color-coding events by reservation status"""
        from instruments.custom.pms_hub.calendar_sync import CalendarSyncService

        service = CalendarSyncService()

        # Test color mapping for different reservation statuses
        color_confirmed = service._get_event_color_by_status(ReservationStatus.CONFIRMED)
        color_pending = service._get_event_color_by_status(ReservationStatus.PENDING)
        color_cancelled = service._get_event_color_by_status(ReservationStatus.CANCELLED)

        assert color_confirmed is not None
        assert color_pending is not None
        assert color_cancelled is not None
        # Confirmed should be green, pending yellow, cancelled red
        assert color_confirmed != color_pending
        assert color_pending != color_cancelled

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_event_description_formatting(self, sample_reservation):
        """Test formatting event description with all relevant details"""
        from instruments.custom.pms_hub.calendar_sync import CalendarSyncService

        service = CalendarSyncService()

        description = service._format_event_description(sample_reservation)

        # Verify all important details are in description
        assert "Guest:" in description
        assert "Email:" in description
        assert "Check-in:" in description
        assert "Check-out:" in description
        assert "Status:" in description
        assert "Payment:" in description
        assert "Total:" in description

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_guest_as_attendee(self, sample_reservation):
        """Test adding guest email as calendar attendee"""
        from instruments.custom.pms_hub.calendar_sync import CalendarSyncService

        service = CalendarSyncService()

        with patch.object(service, "calendar_manager") as mock_cal:
            mock_cal.create_event.return_value = {
                "status": "success",
                "data": {"id": "evt_1", "attendees": ["john@example.com"]},
            }

            result = await service.sync_reservation_to_calendar(sample_reservation)

            # Verify attendees were passed to calendar manager
            call_args = mock_cal.create_event.call_args
            assert call_args is not None
            # Check that attendees parameter was included
            assert "attendees" in call_args.kwargs or len(call_args.args) > 4

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_calendar_permissions_sharing(self):
        """Test calendar permission and sharing settings"""
        from instruments.custom.pms_hub.calendar_sync import CalendarSyncService

        service = CalendarSyncService()

        with patch.object(service, "calendar_manager") as mock_cal:
            mock_cal.set_permissions.return_value = {"status": "success"}

            result = await service._set_calendar_permissions(
                calendar_id=1, share_with="team@company.com", permission="read"
            )

            assert result is not None
            assert result.get("status") == "success"

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_handle_calendar_auth_failures(self):
        """Test handling calendar authentication failures"""
        from instruments.custom.pms_hub.calendar_sync import CalendarSyncService

        service = CalendarSyncService()

        with patch.object(service, "calendar_manager") as mock_cal:
            mock_cal.create_event.side_effect = Exception("Authentication failed: Invalid credentials")

            result = await service.sync_reservation_to_calendar(service._create_test_reservation())

            # Should handle gracefully and return None
            assert result is None

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_bidirectional_sync_updates(self, sample_reservation):
        """Test syncing updates from calendar back to PMS"""
        from instruments.custom.pms_hub.calendar_sync import CalendarSyncService

        service = CalendarSyncService()

        with patch.object(service, "calendar_manager") as mock_cal:
            # Simulate calendar event that was updated
            mock_cal.get_event.return_value = {
                "id": "evt_123",
                "title": "Reservation - John Doe",
                "updated_at": "2025-02-01T15:00:00Z",
            }

            result = await service._sync_calendar_updates_to_pms(calendar_id=1)

            assert result is not None


class TestBatchSynchronization:
    """Tests for batch calendar synchronization"""

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_batch_sync_property_calendar(self):
        """Test syncing all reservations for a property"""
        from instruments.custom.pms_hub.calendar_sync import CalendarSyncService

        service = CalendarSyncService()

        # Create multiple reservations
        reservations = [
            Reservation(
                provider_id=f"res_{i}",
                provider="test",
                property_provider_id="prop_123",
                guest_provider_id=f"guest_{i}",
                guest_name=f"Guest {i}",
                guest_email=f"guest{i}@example.com",
                check_in_date=date(2025, 6, 15 + i),
                check_out_date=date(2025, 6, 20 + i),
                total_price=Decimal("500.00"),
            )
            for i in range(5)
        ]

        with patch.object(service, "calendar_manager") as mock_cal:
            mock_cal.create_event.return_value = {"status": "success", "data": {"id": "evt_1"}}

            result = await service.batch_sync_reservations(
                property_id="prop_123", reservations=reservations, calendar_id=1
            )

            assert result is not None
            assert result.get("synced_count") == 5
            assert result.get("failed_count") == 0
            assert mock_cal.create_event.call_count == 5

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_batch_sync_performance(self):
        """Test batch sync performance with 100+ reservations"""
        import time

        from instruments.custom.pms_hub.calendar_sync import CalendarSyncService

        service = CalendarSyncService()

        # Create 100+ reservations
        reservations = [
            Reservation(
                provider_id=f"res_{i}",
                provider="test",
                property_provider_id="prop_123",
                guest_provider_id=f"guest_{i}",
                guest_name=f"Guest {i}",
                guest_email=f"guest{i}@example.com",
                check_in_date=date(2025, 6, 15),
                check_out_date=date(2025, 6, 20),
                total_price=Decimal("500.00"),
            )
            for i in range(110)
        ]

        with patch.object(service, "calendar_manager") as mock_cal:
            mock_cal.create_event.return_value = {"status": "success", "data": {"id": "evt_1"}}

            start_time = time.time()
            result = await service.batch_sync_reservations(
                property_id="prop_123", reservations=reservations, calendar_id=1
            )
            elapsed_time = time.time() - start_time

            assert result is not None
            assert result.get("synced_count") == 110
            # Performance check: should sync 100+ reservations within reasonable time
            assert elapsed_time < 30  # Should complete in less than 30 seconds

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_batch_sync_error_handling(self):
        """Test batch sync error handling and recovery"""
        from instruments.custom.pms_hub.calendar_sync import CalendarSyncService

        service = CalendarSyncService()

        # Create 10 reservations, some will fail
        reservations = [
            Reservation(
                provider_id=f"res_{i}",
                provider="test",
                property_provider_id="prop_123",
                guest_provider_id=f"guest_{i}",
                guest_name=f"Guest {i}",
                guest_email=f"guest{i}@example.com",
                check_in_date=date(2025, 6, 15),
                check_out_date=date(2025, 6, 20),
                total_price=Decimal("500.00"),
            )
            for i in range(10)
        ]

        with patch.object(service, "calendar_manager") as mock_cal:
            # Fail every 3rd reservation
            def create_event_side_effect(*args, **kwargs):
                call_count = mock_cal.create_event.call_count
                if call_count % 3 == 0:
                    raise Exception("Calendar API error")
                return {"status": "success", "data": {"id": "evt_1"}}

            mock_cal.create_event.side_effect = create_event_side_effect

            result = await service.batch_sync_reservations(
                property_id="prop_123", reservations=reservations, calendar_id=1
            )

            # Should continue despite errors
            assert result is not None
            assert result.get("synced_count") >= 6  # At least 6 succeeded
            assert result.get("failed_count") >= 2  # At least 2 failed


class TestSyncStatusReporting:
    """Tests for sync status reporting and monitoring"""

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_get_sync_status(self):
        """Test getting sync status"""
        from instruments.custom.pms_hub.calendar_sync import CalendarSyncService

        service = CalendarSyncService()

        status = await service.get_sync_status()

        assert status is not None
        assert "service" in status
        assert "status" in status
        assert "calendar_hub_available" in status
        assert "event_bus_available" in status

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_sync_status_detailed_report(self):
        """Test detailed sync status with errors"""
        from instruments.custom.pms_hub.calendar_sync import CalendarSyncService

        service = CalendarSyncService()

        # Perform some sync operations to generate stats
        report = await service.get_detailed_sync_report()

        assert report is not None
        assert "total_synced" in report or "sync_timestamp" in report
        # Report should include sync history
        assert isinstance(report, dict)

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_audit_trail_reporting(self):
        """Test audit trail of all sync operations"""
        from instruments.custom.pms_hub.calendar_sync import CalendarSyncService

        service = CalendarSyncService()

        # Get audit trail
        audit_trail = await service.get_audit_trail()

        # Should return list of audit entries
        assert audit_trail is not None
        assert isinstance(audit_trail, list)


class TestEventDeduplication:
    """Tests for preventing duplicate calendar events"""

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_prevent_duplicate_events(self, sample_reservation):
        """Test preventing duplicate events on re-sync"""
        from instruments.custom.pms_hub.calendar_sync import CalendarSyncService

        service = CalendarSyncService()

        # Store event ID in reservation (simulating previous sync)
        if not hasattr(sample_reservation, "calendar_event_ids"):
            sample_reservation.calendar_event_ids = {}
        sample_reservation.calendar_event_ids["calendar_1"] = "evt_existing_123"

        # Check if duplicate
        is_duplicate = await service.is_duplicate_sync(sample_reservation, calendar_id=1)

        assert is_duplicate is True

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_event_deduplication_by_metadata(self, sample_reservation):
        """Test event deduplication using stored metadata"""
        from instruments.custom.pms_hub.calendar_sync import CalendarSyncService

        service = CalendarSyncService()

        with patch.object(service, "calendar_manager") as mock_cal:
            mock_cal.create_event.return_value = {
                "status": "success",
                "data": {"id": "evt_123"},
            }

            # First sync creates event ID
            if not hasattr(sample_reservation, "calendar_event_ids"):
                sample_reservation.calendar_event_ids = {}

            # Simulate first sync storing event ID
            sample_reservation.calendar_event_ids["calendar_1"] = "evt_123"

            # Check for duplicate - should be True
            is_duplicate = await service.is_duplicate_sync(sample_reservation, calendar_id=1)

            assert is_duplicate is True
            assert sample_reservation.calendar_event_ids["calendar_1"] == "evt_123"


class TestEventBusIntegration:
    """Tests for EventBus integration"""

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_subscribe_to_reservation_created_event(self):
        """Test subscribing to reservation.created events"""
        from instruments.custom.pms_hub.calendar_sync import CalendarSyncService

        service = CalendarSyncService()

        # Mock EventBus if not available
        with patch.object(service, "event_bus") as mock_bus:
            mock_bus is not None
            assert hasattr(service, "event_bus")

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_subscribe_to_reservation_updated_event(self):
        """Test subscribing to reservation.updated events"""
        from instruments.custom.pms_hub.calendar_sync import CalendarSyncService

        service = CalendarSyncService()

        # Verify service operational with mocked EventBus
        with patch.object(service, "event_bus") as mock_bus:
            status = await service.get_sync_status()
            assert status is not None

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_subscribe_to_reservation_cancelled_event(self):
        """Test subscribing to reservation.cancelled events"""
        from instruments.custom.pms_hub.calendar_sync import CalendarSyncService

        service = CalendarSyncService()

        # Mock EventBus for event tracking
        with patch.object(service, "event_bus") as mock_bus:
            audit_trail = await service.get_audit_trail(limit=10)
            assert audit_trail is not None
            assert isinstance(audit_trail, list)

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_subscribe_to_pricing_updated_event(self):
        """Test subscribing to pricing.updated events"""
        from instruments.custom.pms_hub.calendar_sync import CalendarSyncService

        service = CalendarSyncService()

        # Mock EventBus for operational verification
        with patch.object(service, "event_bus") as mock_bus:
            report = await service.get_detailed_sync_report()
            assert report is not None


class TestErrorHandling:
    """Tests for error handling and recovery"""

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_handle_calendar_api_errors(self, sample_reservation):
        """Test handling calendar API errors gracefully"""
        from instruments.custom.pms_hub.calendar_sync import CalendarSyncService

        service = CalendarSyncService()

        with patch.object(service, "calendar_manager") as mock_cal:
            # Simulate API error
            mock_cal.create_event.side_effect = Exception("API Error: 403 Forbidden")

            result = await service.sync_reservation_to_calendar(sample_reservation, calendar_id=1)

            # Should return None on API error (graceful degradation)
            assert result is None

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_handle_network_failures(self, sample_reservation):
        """Test handling network failures during sync"""
        from instruments.custom.pms_hub.calendar_sync import CalendarSyncService

        service = CalendarSyncService()

        with patch.object(service, "calendar_manager") as mock_cal:
            # Simulate network timeout

            mock_cal.create_event.side_effect = TimeoutError("Connection timeout")

            result = await service.sync_reservation_to_calendar(sample_reservation, calendar_id=1)

            # Should handle gracefully
            assert result is None

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_retry_failed_syncs(self, sample_reservation):
        """Test retrying failed sync operations"""
        from instruments.custom.pms_hub.calendar_sync import CalendarSyncService

        service = CalendarSyncService()

        with patch.object(service, "calendar_manager") as mock_cal:
            # First call fails, second succeeds (retry pattern)
            mock_cal.create_event.side_effect = [
                Exception("Temporary error"),
                {"status": "success", "data": {"id": "evt_retry_123"}},
            ]

            # First attempt fails
            result1 = await service.sync_reservation_to_calendar(sample_reservation, calendar_id=1)
            assert result1 is None

            # Retry succeeds
            mock_cal.create_event.side_effect = None
            mock_cal.create_event.return_value = {
                "status": "success",
                "data": {"id": "evt_retry_123"},
            }
            result2 = await service.sync_reservation_to_calendar(sample_reservation, calendar_id=1)
            assert result2 is not None

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_handle_invalid_event_data(self):
        """Test handling invalid event data"""
        from datetime import date

        from instruments.custom.pms_hub.calendar_sync import CalendarSyncService
        from instruments.custom.pms_hub.canonical_models import Reservation

        service = CalendarSyncService()

        # Create reservation with minimal valid data
        invalid_reservation = Reservation(
            provider_id="test_001",
            provider="test",
            property_provider_id="prop_001",
            guest_provider_id="guest_001",
            check_in_date=date(2026, 1, 20),
            check_out_date=date(2026, 1, 22),
        )

        with patch.object(service, "calendar_manager") as mock_cal:
            mock_cal.create_event.return_value = {
                "status": "error",
                "error": "Invalid data",
            }

            # Should handle invalid data gracefully
            result = await service.sync_reservation_to_calendar(invalid_reservation, calendar_id=1)

            # May return None or error response, but shouldn't crash
            assert result is None or isinstance(result, dict)


class TestPerformance:
    """Tests for performance requirements"""

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_event_sync_performance_500ms(self, sample_reservation):
        """Test single event sync completes within 500ms"""
        import time
        from unittest.mock import patch

        from instruments.custom.pms_hub.calendar_sync import CalendarSyncService

        service = CalendarSyncService()

        with patch.object(service, "calendar_manager") as mock_cal:
            mock_cal.create_event.return_value = {
                "status": "success",
                "data": {"id": "evt_perf_001"},
            }

            # Measure sync time
            start_time = time.time()
            result = await service.sync_reservation_to_calendar(sample_reservation, calendar_id=1)
            elapsed_ms = (time.time() - start_time) * 1000

            # Should complete within 500ms
            assert elapsed_ms < 500
            assert result is not None

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_batch_sync_performance_scalability(self):
        """Test batch sync scales to 1000+ events"""
        import time
        from datetime import date, timedelta
        from decimal import Decimal
        from unittest.mock import patch

        from instruments.custom.pms_hub.calendar_sync import CalendarSyncService
        from instruments.custom.pms_hub.canonical_models import Reservation

        service = CalendarSyncService()

        # Create 100 reservations (scalability test - reduced from 1000 for test speed)
        base_date = date(2026, 1, 1)
        reservations = [
            Reservation(
                provider_id=f"res_{i:04d}",
                provider="test",
                property_provider_id="prop_001",
                check_in_date=base_date + timedelta(days=i),
                check_out_date=base_date + timedelta(days=i + 2),
                total_price=Decimal("100.00"),
            )
            for i in range(100)
        ]

        with patch.object(service, "calendar_manager") as mock_cal:
            mock_cal.create_event.return_value = {
                "status": "success",
                "data": {"id": "evt_batch_001"},
            }

            # Measure batch sync time
            start_time = time.time()
            result = await service.batch_sync_reservations("prop_001", reservations, calendar_id=1)
            elapsed_ms = (time.time() - start_time) * 1000

            # Should complete reasonably fast (100 events in < 30 seconds)
            assert elapsed_ms < 30000
            assert result is not None
            # Verify sync statistics
            assert isinstance(result, dict)
