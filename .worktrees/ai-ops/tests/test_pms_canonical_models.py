"""
Unit tests for PMS Hub Canonical Data Models
Tests data model validation, serialization, and transformations
"""

import pytest
from datetime import datetime, date
from decimal import Decimal

from instruments.custom.pms_hub.canonical_models import (
    Property,
    Unit,
    Guest,
    Reservation,
    Message,
    Review,
    Calendar,
    PricingRule,
    ReservationStatus,
    PaymentStatus,
    MessageType,
)


class TestPropertyModel:
    """Tests for Property canonical model"""

    @pytest.mark.unit
    def test_property_creation_with_defaults(self):
        """Test creating property with minimal fields"""
        prop = Property(
            provider_id="prop_1",
            provider="hostaway",
            external_id="airbnb_1",
            name="Test Property",
            address="123 Main St",
            city="Boston",
            state="MA",
        )

        assert prop.provider_id == "prop_1"
        assert prop.provider == "hostaway"
        assert prop.bedrooms == 1
        assert prop.bathrooms == 1.0
        assert prop.base_price == Decimal("0")

    @pytest.mark.unit
    def test_property_with_full_details(self, sample_property):
        """Test creating property with all details"""
        assert sample_property.name == "Beach House Paradise"
        assert sample_property.bedrooms == 3
        assert sample_property.bathrooms == 2.5
        assert sample_property.max_guests == 6
        assert sample_property.latitude == 34.0195
        assert len(sample_property.amenities) == 4

    @pytest.mark.unit
    def test_property_sync_metadata(self):
        """Test property sync metadata"""
        prop = Property(
            provider_id="p1",
            provider="test",
            external_id="e1",
            name="Test",
            address="123",
            city="City",
            state="ST",
        )

        assert prop.synced_at is not None
        assert isinstance(prop.synced_at, datetime)
        assert prop.sync_hash is None

    @pytest.mark.unit
    def test_property_coordinates(self):
        """Test property geographic coordinates"""
        prop = Property(
            provider_id="p1",
            provider="test",
            external_id="e1",
            name="Test",
            address="123",
            city="City",
            state="ST",
            latitude=40.7128,
            longitude=-74.0060,
        )

        assert prop.latitude == 40.7128
        assert prop.longitude == -74.0060


class TestReservationModel:
    """Tests for Reservation canonical model"""

    @pytest.mark.unit
    def test_reservation_dates_calculation(self, sample_reservation):
        """Test reservation calculates nights correctly"""
        assert sample_reservation.nights == 6
        assert sample_reservation.check_in_date == date(2025, 2, 1)
        assert sample_reservation.check_out_date == date(2025, 2, 7)

    @pytest.mark.unit
    def test_reservation_pricing_breakdown(self, sample_reservation):
        """Test reservation pricing components"""
        assert sample_reservation.base_price == Decimal("1200.00")
        assert sample_reservation.discount == Decimal("100.00")
        assert sample_reservation.service_fee == Decimal("180.00")
        assert sample_reservation.cleaning_fee == Decimal("150.00")
        assert sample_reservation.taxes == Decimal("200.00")
        assert sample_reservation.total_price == Decimal("1730.00")

    @pytest.mark.unit
    def test_reservation_status_transitions(self):
        """Test valid reservation status values"""
        statuses = [
            ReservationStatus.INQUIRY,
            ReservationStatus.PENDING,
            ReservationStatus.CONFIRMED,
            ReservationStatus.CHECKED_IN,
            ReservationStatus.CHECKED_OUT,
            ReservationStatus.CANCELLED,
            ReservationStatus.DECLINED,
        ]

        for status in statuses:
            res = Reservation(
                provider_id="r1",
                provider="test",
                property_provider_id="p1",
                status=status,
                check_in_date=date(2025, 2, 1),
                check_out_date=date(2025, 2, 7),
            )
            assert res.status == status

    @pytest.mark.unit
    def test_reservation_payment_status(self):
        """Test reservation payment status"""
        res = Reservation(
            provider_id="r1",
            provider="test",
            property_provider_id="p1",
            payment_status=PaymentStatus.PAID,
            check_in_date=date(2025, 2, 1),
            check_out_date=date(2025, 2, 7),
        )

        assert res.payment_status == PaymentStatus.PAID

    @pytest.mark.unit
    def test_reservation_guest_info(self, sample_reservation):
        """Test reservation guest information"""
        assert sample_reservation.guest_name == "John Doe"
        assert sample_reservation.guest_email == "john@example.com"
        assert sample_reservation.guest_phone == "+1-555-0123"

    @pytest.mark.unit
    def test_reservation_property_manager_mapping(self):
        """Test reservation mapping to property manager IDs"""
        res = Reservation(
            provider_id="r1",
            provider="test",
            property_provider_id="p1",
            check_in_date=date(2025, 2, 1),
            check_out_date=date(2025, 2, 7),
        )

        # Initially None
        assert res.property_manager_id is None
        assert res.lease_manager_id is None

        # Set after sync
        res.property_manager_id = 100
        res.lease_manager_id = 200

        assert res.property_manager_id == 100
        assert res.lease_manager_id == 200


class TestMessageModel:
    """Tests for Message canonical model"""

    @pytest.mark.unit
    def test_message_types(self):
        """Test all message types"""
        types = [
            MessageType.INQUIRY,
            MessageType.BOOKING,
            MessageType.PRE_ARRIVAL,
            MessageType.DURING_STAY,
            MessageType.POST_CHECKOUT,
            MessageType.ISSUE,
            MessageType.SYSTEM,
        ]

        for msg_type in types:
            msg = Message(
                provider_id="m1",
                provider="test",
                guest_provider_id="g1",
                message_type=msg_type,
                body="Test",
            )
            assert msg.message_type == msg_type

    @pytest.mark.unit
    def test_message_sender_types(self):
        """Test message from guest vs host"""
        msg_guest = Message(
            provider_id="m1",
            provider="test",
            guest_provider_id="g1",
            sender="guest",
            body="Question",
        )

        msg_host = Message(
            provider_id="m2",
            provider="test",
            guest_provider_id="g1",
            sender="host",
            body="Response",
        )

        assert msg_guest.sender == "guest"
        assert msg_host.sender == "host"

    @pytest.mark.unit
    def test_message_requires_response(self, sample_message):
        """Test message response requirement flag"""
        assert sample_message.requires_response is True
        assert sample_message.is_read is False


class TestReviewModel:
    """Tests for Review canonical model"""

    @pytest.mark.unit
    def test_review_rating_range(self):
        """Test review rating validation"""
        for rating in [1.0, 2.5, 3.0, 4.5, 5.0]:
            review = Review(
                provider_id="rev1",
                provider="test",
                reservation_provider_id="res1",
                guest_provider_id="g1",
                rating=rating,
            )
            assert review.rating == rating

    @pytest.mark.unit
    def test_review_categories(self, sample_review):
        """Test review category breakdown"""
        assert sample_review.categories["cleanliness"] == 5.0
        assert sample_review.categories["communication"] == 4.0
        assert sample_review.categories["location"] == 5.0
        assert sample_review.categories["value"] == 4.0

    @pytest.mark.unit
    def test_review_text_content(self, sample_review):
        """Test review text content"""
        assert sample_review.title == "Wonderful stay!"
        assert sample_review.comment == "Great property, responsive host"


class TestCalendarModel:
    """Tests for Calendar canonical model"""

    @pytest.mark.unit
    def test_calendar_statuses(self):
        """Test calendar availability statuses"""
        statuses = ["available", "booked", "blocked", "not_available"]

        for status in statuses:
            cal = Calendar(
                provider_id="cal1",
                provider="test",
                property_provider_id="p1",
                date=date(2025, 2, 1),
                status=status,
            )
            assert cal.status == status

    @pytest.mark.unit
    def test_calendar_pricing(self, sample_calendar):
        """Test calendar price tracking"""
        assert sample_calendar.price == Decimal("250.00")
        assert sample_calendar.min_nights == 1

    @pytest.mark.unit
    def test_calendar_blocked_reason(self):
        """Test calendar blocking reasons"""
        reasons = ["cleaning", "maintenance", "owner_block", "custom"]

        for reason in reasons:
            cal = Calendar(
                provider_id="cal1",
                provider="test",
                property_provider_id="p1",
                date=date(2025, 2, 1),
                status="blocked",
                blocked_reason=reason,
            )
            assert cal.blocked_reason == reason


class TestPricingRuleModel:
    """Tests for PricingRule canonical model"""

    @pytest.mark.unit
    def test_pricing_rule_types(self):
        """Test different pricing rule types"""
        rules = [
            "minimum_stay",
            "seasonal",
            "weekly_discount",
            "monthly_discount",
            "holiday_premium",
        ]

        for rule_type in rules:
            rule = PricingRule(
                provider_id="rule1",
                provider="test",
                property_provider_id="p1",
                rule_name=f"Rule: {rule_type}",
                rule_type=rule_type,
            )
            assert rule.rule_type == rule_type

    @pytest.mark.unit
    def test_pricing_rule_percentage_vs_absolute(self):
        """Test absolute vs percentage pricing modifiers"""
        # Absolute price
        abs_rule = PricingRule(
            provider_id="rule1",
            provider="test",
            property_provider_id="p1",
            rule_name="$50 discount",
            rule_type="discount",
            price_modifier=Decimal("-50.00"),
            is_percentage=False,
        )

        # Percentage
        pct_rule = PricingRule(
            provider_id="rule2",
            provider="test",
            property_provider_id="p1",
            rule_name="10% discount",
            rule_type="discount",
            price_modifier=Decimal("10.00"),
            is_percentage=True,
        )

        assert abs_rule.is_percentage is False
        assert pct_rule.is_percentage is True

    @pytest.mark.unit
    def test_pricing_rule_date_ranges(self):
        """Test pricing rule date ranges"""
        rule = PricingRule(
            provider_id="rule1",
            provider="test",
            property_provider_id="p1",
            rule_name="Summer premium",
            rule_type="seasonal",
            start_date=date(2025, 6, 1),
            end_date=date(2025, 8, 31),
            price_modifier=Decimal("50.00"),
        )

        assert rule.start_date == date(2025, 6, 1)
        assert rule.end_date == date(2025, 8, 31)


class TestUnitModel:
    """Tests for Unit canonical model"""

    @pytest.mark.unit
    def test_unit_creation(self):
        """Test unit creation for multi-unit properties"""
        unit = Unit(
            provider_id="unit_101",
            property_provider_id="prop_1",
            unit_number="101",
            unit_type="room",
            bedrooms=1,
            bathrooms=1.0,
            max_guests=2,
            base_price=Decimal("150.00"),
        )

        assert unit.unit_number == "101"
        assert unit.unit_type == "room"
        assert unit.bedrooms == 1


class TestGuestModel:
    """Tests for Guest canonical model"""

    @pytest.mark.unit
    def test_guest_creation(self, sample_guest):
        """Test guest model creation"""
        assert sample_guest.first_name == "John"
        assert sample_guest.last_name == "Doe"
        assert sample_guest.email == "john@example.com"

    @pytest.mark.unit
    def test_guest_verification_status(self, sample_guest):
        """Test guest verification tracking"""
        assert sample_guest.identity_verified is True
        assert sample_guest.superhost_reviewed is True
        assert sample_guest.review_count == 15
        assert sample_guest.review_rating == 4.9


# ============================================================================
# Integration Tests for Model Relationships
# ============================================================================

class TestModelRelationships:
    """Tests for relationships between models"""

    @pytest.mark.unit
    def test_reservation_references_property_and_guest(self, sample_reservation):
        """Test reservation references correct property and guest"""
        assert sample_reservation.property_provider_id == "prop_123"
        assert sample_reservation.guest_provider_id == "guest_123"

    @pytest.mark.unit
    def test_message_linked_to_reservation(self, sample_message):
        """Test message linked to reservation"""
        assert sample_message.reservation_provider_id == "res_123"
        assert sample_message.guest_provider_id == "guest_123"

    @pytest.mark.unit
    def test_review_references_reservation_and_guest(self, sample_review):
        """Test review references correct entities"""
        assert sample_review.reservation_provider_id == "res_123"
        assert sample_review.guest_provider_id == "guest_123"


# ============================================================================
# Serialization Tests
# ============================================================================

class TestModelSerialization:
    """Tests for model serialization and deserialization"""

    @pytest.mark.unit
    def test_property_to_dict(self, sample_property):
        """Test property can be converted to dict"""
        # Properties are dataclasses, should have __dict__
        import dataclasses
        prop_dict = dataclasses.asdict(sample_property)

        assert prop_dict["provider_id"] == "prop_123"
        assert prop_dict["name"] == "Beach House Paradise"
        assert prop_dict["bedrooms"] == 3

    @pytest.mark.unit
    def test_reservation_decimal_precision(self, sample_reservation):
        """Test decimal precision for pricing"""
        assert str(sample_reservation.total_price) == "1730.00"
        assert isinstance(sample_reservation.base_price, Decimal)

    @pytest.mark.unit
    def test_date_fields_are_dates(self, sample_reservation):
        """Test date fields are proper date objects"""
        from datetime import date
        assert isinstance(sample_reservation.check_in_date, date)
        assert isinstance(sample_reservation.check_out_date, date)
