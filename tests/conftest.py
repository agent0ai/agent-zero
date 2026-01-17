"""
Pytest configuration and fixtures for PMS Hub tests
Shared fixtures across all test modules
"""

import asyncio

# Add project root to path
import sys
import tempfile
from datetime import date, datetime
from decimal import Decimal
from pathlib import Path
from unittest.mock import AsyncMock

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent))

from instruments.custom.pms_hub.canonical_models import (
    Calendar,
    Guest,
    Message,
    MessageType,
    PaymentStatus,
    Property,
    Reservation,
    ReservationStatus,
    Review,
)
from instruments.custom.pms_hub.pms_provider import ProviderType

# ============================================================================
# Event Loop Fixture
# ============================================================================


@pytest.fixture(scope="session")
def event_loop():
    """Create event loop for async tests"""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


# ============================================================================
# Canonical Models Fixtures
# ============================================================================


@pytest.fixture
def sample_property():
    """Sample property for testing"""
    return Property(
        provider_id="prop_123",
        provider="hostaway",
        external_id="airbnb_456",
        name="Beach House Paradise",
        description="Beautiful beachfront property",
        property_type="vacation_rental",
        address="123 Ocean Lane",
        city="Malibu",
        state="CA",
        zip_code="90265",
        country="USA",
        latitude=34.0195,
        longitude=-118.6813,
        bedrooms=3,
        bathrooms=2.5,
        max_guests=6,
        square_feet=2500,
        amenities=["WiFi", "Pool", "Hot Tub", "Parking"],
        images=["img1.jpg", "img2.jpg"],
        base_price=Decimal("250.00"),
        currency="USD",
    )


@pytest.fixture
def sample_guest():
    """Sample guest for testing"""
    return Guest(
        provider_id="guest_123",
        provider="hostaway",
        first_name="John",
        last_name="Doe",
        email="john@example.com",
        phone="+1-555-0123",
        identity_verified=True,
        superhost_reviewed=True,
        review_count=15,
        review_rating=4.9,
        preferred_contact_method="email",
    )


@pytest.fixture
def sample_reservation(sample_property, sample_guest):
    """Sample reservation for testing"""
    return Reservation(
        provider_id="res_123",
        provider="hostaway",
        property_provider_id=sample_property.provider_id,
        guest_provider_id=sample_guest.provider_id,
        confirmation_code="CONF123ABC",
        check_in_date=date(2025, 2, 1),
        check_out_date=date(2025, 2, 7),
        nights=6,
        guests_count=4,
        base_price=Decimal("1200.00"),
        discount=Decimal("100.00"),
        service_fee=Decimal("180.00"),
        cleaning_fee=Decimal("150.00"),
        taxes=Decimal("200.00"),
        total_price=Decimal("1730.00"),
        currency="USD",
        status=ReservationStatus.CONFIRMED,
        payment_status=PaymentStatus.PAID,
        guest_name="John Doe",
        guest_email="john@example.com",
        guest_phone="+1-555-0123",
        special_requests="Late check-in appreciated",
        source="pms",
    )


@pytest.fixture
def sample_message():
    """Sample message for testing"""
    return Message(
        provider_id="msg_123",
        provider="hostaway",
        guest_provider_id="guest_123",
        reservation_provider_id="res_123",
        sender="guest",
        message_type=MessageType.INQUIRY,
        subject="Question about amenities",
        body="Is there parking available?",
        is_read=False,
        requires_response=True,
    )


@pytest.fixture
def sample_review():
    """Sample review for testing"""
    return Review(
        provider_id="rev_123",
        provider="hostaway",
        reservation_provider_id="res_123",
        guest_provider_id="guest_123",
        rating=4.5,
        title="Wonderful stay!",
        comment="Great property, responsive host",
        categories={
            "cleanliness": 5.0,
            "communication": 4.0,
            "location": 5.0,
            "value": 4.0,
        },
    )


@pytest.fixture
def sample_calendar():
    """Sample calendar entry for testing"""
    return Calendar(
        provider_id="cal_123",
        provider="hostaway",
        property_provider_id="prop_123",
        date=date(2025, 2, 1),
        status="booked",
        price=Decimal("250.00"),
        min_nights=1,
    )


# ============================================================================
# Provider Registry Fixtures
# ============================================================================


@pytest.fixture
def temp_config_dir():
    """Create temporary directory for config storage"""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


@pytest.fixture
def provider_config_data():
    """Sample provider configuration"""
    return {
        "hostaway_main": {
            "provider_type": "hostaway",
            "name": "Hostaway Main",
            "enabled": True,
            "credentials": {
                "api_key": "test_api_key",  # pragma: allowlist secret
                "user_id": "test_user_id",  # pragma: allowlist secret
                "access_token": "test_access_token",  # pragma: allowlist secret
            },
            "options": {},
        },
        "lodgify_backup": {
            "provider_type": "lodgify",
            "name": "Lodgify Backup",
            "enabled": True,
            "credentials": {
                "api_key": "test_lodgify_key",  # pragma: allowlist secret
                "api_secret": "test_secret",  # pragma: allowlist secret
                "account_id": "test_account",
            },
            "options": {},
        },
    }


# ============================================================================
# Mock Provider Fixtures
# ============================================================================


@pytest.fixture
def mock_provider():
    """Mock PMS provider for testing"""
    provider = AsyncMock()
    provider.provider_type = ProviderType.HOSTAWAY
    provider.is_authenticated.return_value = True
    provider.get_provider_name.return_value = "Mock Provider"
    provider.get_webhook_events.return_value = [
        "reservation.created",
        "reservation.updated",
    ]
    return provider


@pytest.fixture
def mock_httpx_client():
    """Mock httpx async client"""
    client = AsyncMock()
    client.get = AsyncMock()
    client.post = AsyncMock()
    client.put = AsyncMock()
    client.aclose = AsyncMock()
    return client


@pytest.fixture
def mock_hostaway_responses():
    """Mock responses for Hostaway API"""
    return {
        "properties": {
            "status_code": 200,
            "json": {
                "result": {
                    "properties": [
                        {
                            "id": "prop_123",
                            "title": "Beach House",
                            "description": "Nice beach property",
                            "address1": "123 Ocean Lane",
                            "city": "Malibu",
                            "state": "CA",
                            "zipCode": "90265",
                            "country": "USA",
                            "bedrooms": 3,
                            "bathrooms": 2.5,
                            "maximumOccupancy": 6,
                            "basePrice": 250.0,
                            "currency": "USD",
                        }
                    ]
                }
            },
        },
        "reservations": {
            "status_code": 200,
            "json": {
                "result": {
                    "reservations": [
                        {
                            "id": "res_123",
                            "propertyId": "prop_123",
                            "confirmationCode": "CONF123",
                            "checkinDate": "2025-02-01T00:00:00Z",
                            "checkoutDate": "2025-02-07T00:00:00Z",
                            "numberOfGuests": 4,
                            "basePrice": 1200.0,
                            "discount": 100.0,
                            "serviceFee": 180.0,
                            "cleaningFee": 150.0,
                            "taxes": 200.0,
                            "totalPrice": 1730.0,
                            "currency": "USD",
                            "status": "confirmed",
                            "isPaid": True,
                            "guestFirstName": "John",
                            "guestLastName": "Doe",
                            "guestEmail": "john@example.com",
                            "guestPhone": "+1-555-0123",
                        }
                    ]
                }
            },
        },
    }


@pytest.fixture
def mock_webhook_payload():
    """Mock webhook payload"""
    return {
        "id": "event_123",
        "type": "reservation.confirmed",
        "data": {
            "reservationId": "res_123",
            "guestName": "John Doe",
            "checkInDate": "2025-02-01",
            "checkOutDate": "2025-02-07",
        },
        "timestamp": datetime.utcnow().isoformat(),
    }


# ============================================================================
# Event Bus Fixtures
# ============================================================================


@pytest.fixture
def event_store_temp():
    """Temporary event store database"""
    from python.helpers.event_bus import EventStore

    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        db_path = f.name

    store = EventStore(db_path)
    yield store

    # Cleanup
    Path(db_path).unlink(missing_ok=True)


@pytest.fixture
def event_bus(event_store_temp):
    """Event bus with temporary storage"""
    from python.helpers.event_bus import EventBus

    return EventBus(event_store_temp)


# ============================================================================
# Database Fixtures (PropertyManager mocks)
# ============================================================================


@pytest.fixture
def mock_property_manager():
    """Mock PropertyManager for sync testing"""
    pm = AsyncMock()
    pm.add_property = AsyncMock(return_value={"status": "success", "data": {"id": 1}})
    pm.add_units = AsyncMock(return_value={"status": "success", "data": [{"id": 1}]})
    pm.add_tenant = AsyncMock(return_value={"status": "success", "data": {"id": 1}})
    pm.create_lease = AsyncMock(return_value={"status": "success", "data": {"id": 1}})
    pm.record_payment = AsyncMock(return_value={"status": "success"})
    return pm


# ============================================================================
# Markers for Test Organization
# ============================================================================


def pytest_configure(config):
    """Register custom markers"""
    config.addinivalue_line("markers", "unit: Unit tests")
    config.addinivalue_line("markers", "integration: Integration tests")
    config.addinivalue_line("markers", "async: Async tests")
    config.addinivalue_line("markers", "slow: Slow tests")
    config.addinivalue_line("markers", "mock: Tests using mocks")
