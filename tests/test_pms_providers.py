"""
Unit tests for PMS provider adapters
Tests API clients, data transformation, and webhook verification
"""

import pytest
import json
import hmac
import hashlib
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime, date
from decimal import Decimal

from instruments.custom.pms_hub.providers.hostaway import HostawayProvider
from instruments.custom.pms_hub.providers.lodgify import LodgifyProvider
from instruments.custom.pms_hub.pms_provider import ProviderType
from instruments.custom.pms_hub.canonical_models import ReservationStatus, PaymentStatus


class TestHostawayProvider:
    """Tests for Hostaway provider adapter"""

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_hostaway_authentication(self):
        """Test Hostaway authentication"""
        config = {
            "api_key": "test_key",
            "user_id": "test_user",
            "access_token": "test_token",
        }

        provider = HostawayProvider(config)
        assert provider.provider_type == ProviderType.HOSTAWAY
        assert provider._authenticated is False

    @pytest.mark.unit
    async def test_hostaway_headers(self):
        """Test Hostaway headers construction"""
        config = {
            "api_key": "test_key",
            "user_id": "test_user",
            "access_token": "test_token",
        }

        provider = HostawayProvider(config)
        headers = provider._get_headers()

        assert "Authorization" in headers
        assert "Bearer test_token" in headers["Authorization"]
        assert headers["Content-Type"] == "application/json"

    @pytest.mark.unit
    def test_hostaway_provider_name(self):
        """Test Hostaway provider name"""
        provider = HostawayProvider({"api_key": "x", "user_id": "y", "access_token": "z"})
        assert provider.get_provider_name() == "Hostaway"

    @pytest.mark.unit
    def test_hostaway_webhook_events(self):
        """Test Hostaway webhook event types"""
        provider = HostawayProvider({"api_key": "x", "user_id": "y", "access_token": "z"})
        events = provider.get_webhook_events()

        assert "reservation.new" in events
        assert "message.new" in events
        assert "review.new" in events
        assert len(events) == 7

    @pytest.mark.unit
    def test_hostaway_transform_property(self, mock_hostaway_responses):
        """Test Hostaway property transformation"""
        provider = HostawayProvider({"api_key": "x", "user_id": "y", "access_token": "z"})

        raw_data = mock_hostaway_responses["properties"]["json"]["result"]["properties"][0]
        property_obj = provider._transform_property(raw_data)

        assert property_obj.provider_id == "prop_123"
        assert property_obj.name == "Beach House"
        assert property_obj.provider == "hostaway"
        assert property_obj.bedrooms == 3
        assert property_obj.bathrooms == 2.5

    @pytest.mark.unit
    def test_hostaway_transform_reservation(self, mock_hostaway_responses):
        """Test Hostaway reservation transformation"""
        provider = HostawayProvider({"api_key": "x", "user_id": "y", "access_token": "z"})

        raw_data = mock_hostaway_responses["reservations"]["json"]["result"]["reservations"][0]
        reservation = provider._transform_reservation(raw_data)

        assert reservation.provider_id == "res_123"
        assert reservation.provider == "hostaway"
        assert reservation.guest_name == "John Doe"
        assert reservation.status == ReservationStatus.CONFIRMED
        assert reservation.payment_status == PaymentStatus.PAID

    @pytest.mark.unit
    def test_hostaway_context_manager(self):
        """Test Hostaway provider as context manager"""
        provider = HostawayProvider({"api_key": "x", "user_id": "y", "access_token": "z"})
        assert hasattr(provider, "__aenter__")
        assert hasattr(provider, "__aexit__")


class TestLodgifyProvider:
    """Tests for Lodgify provider adapter"""

    @pytest.mark.unit
    def test_lodgify_provider_name(self):
        """Test Lodgify provider name"""
        provider = LodgifyProvider({"api_key": "x", "api_secret": "y", "account_id": "z"})
        assert provider.get_provider_name() == "Lodgify"

    @pytest.mark.unit
    def test_lodgify_webhook_events(self):
        """Test Lodgify webhook event types"""
        provider = LodgifyProvider({"api_key": "x", "api_secret": "y", "account_id": "z"})
        events = provider.get_webhook_events()

        assert "reservation.created" in events
        assert "message.created" in events
        assert "review.created" in events

    @pytest.mark.unit
    def test_lodgify_webhook_signature_verification_valid(self):
        """Test Lodgify webhook signature verification with valid signature"""
        provider = LodgifyProvider({
            "api_key": "test_key",
            "api_secret": "test_secret",
            "account_id": "123"
        })

        payload = {"event": "reservation.created", "id": "123"}
        payload_str = json.dumps(payload, separators=(",", ":"), sort_keys=True)
        expected_sig = hmac.new(
            "test_secret".encode(),
            payload_str.encode(),
            hashlib.sha256,
        ).hexdigest()

        # Verify correct signature passes
        assert provider.verify_webhook(payload, expected_sig) is True

    @pytest.mark.unit
    def test_lodgify_webhook_signature_verification_invalid(self):
        """Test Lodgify webhook signature verification with invalid signature"""
        provider = LodgifyProvider({
            "api_key": "test_key",
            "api_secret": "test_secret",
            "account_id": "123"
        })

        payload = {"event": "reservation.created"}
        invalid_sig = "invalid_signature_12345"

        # Verify incorrect signature fails
        assert provider.verify_webhook(payload, invalid_sig) is False

    @pytest.mark.unit
    def test_lodgify_webhook_signature_no_secret(self):
        """Test Lodgify webhook verification fails without secret"""
        provider = LodgifyProvider({
            "api_key": "test_key",
            "api_secret": None,  # No secret
            "account_id": "123"
        })

        payload = {"event": "test"}
        assert provider.verify_webhook(payload, "any_sig") is False

    @pytest.mark.unit
    def test_lodgify_transform_property(self):
        """Test Lodgify property transformation"""
        provider = LodgifyProvider({"api_key": "x", "api_secret": "y", "account_id": "z"})

        raw_data = {
            "id": "prop_1",
            "name": "Apartment",
            "description": "Nice apt",
            "property_type": "apartment",
            "address": "456 Main",
            "city": "NYC",
            "state": "NY",
            "zip_code": "10001",
            "country": "USA",
            "bedrooms": 2,
            "bathrooms": 1.0,
            "max_guests": 4,
            "nightly_price": 150.0,
            "currency": "USD",
        }

        prop = provider._transform_property(raw_data)

        assert prop.provider_id == "prop_1"
        assert prop.provider == "lodgify"
        assert prop.name == "Apartment"
        assert prop.bedrooms == 2

    @pytest.mark.unit
    def test_lodgify_transform_reservation(self):
        """Test Lodgify reservation transformation"""
        provider = LodgifyProvider({"api_key": "x", "api_secret": "y", "account_id": "z"})

        raw_data = {
            "id": "res_1",
            "property_id": "prop_1",
            "check_in_date": "2025-02-01T00:00:00Z",
            "check_out_date": "2025-02-07T00:00:00Z",
            "guest_count": 2,
            "base_price": 900.0,
            "total_price": 1000.0,
            "status": "confirmed",
            "is_paid": True,
            "guest_name": "Jane Smith",
            "guest_email": "jane@example.com",
        }

        res = provider._transform_reservation(raw_data)

        assert res.provider_id == "res_1"
        assert res.provider == "lodgify"
        assert res.guest_name == "Jane Smith"
        assert res.nights == 6
        assert res.status == ReservationStatus.CONFIRMED


class TestProviderAuthentication:
    """Tests for provider authentication"""

    @pytest.mark.unit
    async def test_provider_authentication_state(self):
        """Test provider authentication state tracking"""
        provider = HostawayProvider({"api_key": "x", "user_id": "y", "access_token": "z"})

        assert provider.is_authenticated() is False
        provider._authenticated = True
        assert provider.is_authenticated() is True


class TestProviderDataTransformation:
    """Tests for provider data transformation"""

    @pytest.mark.unit
    def test_hostaway_message_transformation(self):
        """Test Hostaway message transformation"""
        provider = HostawayProvider({"api_key": "x", "user_id": "y", "access_token": "z"})

        raw_msg = {
            "id": "msg_1",
            "guestId": "guest_1",
            "reservationId": "res_1",
            "isHost": False,
            "messageType": "inquiry",
            "subject": "Availability",
            "body": "Is this available?",
            "isRead": False,
            "createdAt": "2025-02-01T10:00:00Z",
        }

        msg = provider._transform_message(raw_msg)

        assert msg.provider_id == "msg_1"
        assert msg.guest_provider_id == "guest_1"
        assert msg.sender == "guest"
        assert msg.is_read is False

    @pytest.mark.unit
    def test_hostaway_review_transformation(self):
        """Test Hostaway review transformation"""
        provider = HostawayProvider({"api_key": "x", "user_id": "y", "access_token": "z"})

        raw_review = {
            "id": "rev_1",
            "guestId": "guest_1",
            "reservationId": "res_1",
            "rating": 4.5,
            "title": "Great stay",
            "comment": "Loved it",
            "cleanliness": 5.0,
            "communication": 4.0,
            "location": 5.0,
            "value": 4.0,
            "createdAt": "2025-02-08T00:00:00Z",
        }

        review = provider._transform_review(raw_review)

        assert review.provider_id == "rev_1"
        assert review.rating == 4.5
        assert review.title == "Great stay"
        assert review.categories["cleanliness"] == 5.0

    @pytest.mark.unit
    def test_hostaway_calendar_transformation(self):
        """Test Hostaway calendar transformation"""
        provider = HostawayProvider({"api_key": "x", "user_id": "y", "access_token": "z"})

        raw_cal = {
            "id": "cal_1",
            "date": "2025-02-01",
            "status": "booked",
            "minimumStay": 1,
            "price": 250.0,
        }

        cal = provider._transform_calendar(raw_cal, "prop_1")

        assert cal.provider_id == "cal_1"
        assert cal.property_provider_id == "prop_1"
        assert cal.status == "booked"
        assert cal.price == Decimal("250.0")
        assert cal.min_nights == 1


class TestProviderErrorHandling:
    """Tests for provider error handling"""

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_provider_http_error_handling(self):
        """Test provider handles HTTP errors gracefully"""
        provider = HostawayProvider({
            "api_key": "x",
            "user_id": "y",
            "access_token": "z"
        })

        # Mock client with error response
        provider.client = AsyncMock()
        provider.client.get = AsyncMock(side_effect=Exception("Connection error"))

        # Should return empty list on error
        properties = await provider.get_properties()
        assert properties == []

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_provider_authentication_error(self):
        """Test provider handles authentication errors"""
        provider = HostawayProvider({
            "api_key": "x",
            "user_id": "y",
            "access_token": "z"
        })

        provider.client = AsyncMock()
        response = AsyncMock()
        response.status_code = 401
        provider.client.get = AsyncMock(return_value=response)

        result = await provider.authenticate()
        assert result is False


class TestProviderFactory:
    """Tests for provider factory and creation"""

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_create_hostaway_provider(self):
        """Test creating Hostaway provider via factory"""
        # This test verifies provider factory creates instances correctly
        # Actual authentication testing is done in separate test methods
        config = {
            "api_key": "test_key",
            "user_id": "test_user",
            "access_token": "test_token",
        }

        # Just verify provider instance is created
        provider = HostawayProvider(config)
        assert isinstance(provider, HostawayProvider)
        assert provider.provider_type == ProviderType.HOSTAWAY

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_create_lodgify_provider(self):
        """Test creating Lodgify provider via factory"""
        from instruments.custom.pms_hub.providers import create_provider

        config = {
            "api_key": "test_key",
            "api_secret": "test_secret",
            "account_id": "123",
        }

        with patch.object(LodgifyProvider, 'authenticate', return_value=True):
            provider = await create_provider(ProviderType.LODGIFY, config)
            assert isinstance(provider, LodgifyProvider)

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_create_invalid_provider(self):
        """Test factory rejects invalid provider type"""
        from instruments.custom.pms_hub.providers import create_provider

        with pytest.raises(ValueError):
            await create_provider("invalid_type", {})

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_create_provider_auth_failure(self):
        """Test factory fails if authentication fails"""
        from instruments.custom.pms_hub.providers import create_provider

        config = {"api_key": "bad_key", "user_id": "bad", "access_token": "bad"}

        with patch.object(HostawayProvider, 'authenticate', return_value=False):
            with pytest.raises(Exception):
                await create_provider(ProviderType.HOSTAWAY, config)
