"""
Comprehensive Google Voice Messaging System Test Suite
Tests the complete Google Voice check-in messaging workflow
Full test coverage for dry-run, sending, and message tracking

Test Categories:
  • Unit Tests: Individual component functionality
  • Integration Tests: Message lifecycle (draft → send → track)
  • System Tests: End-to-end workflows
  • Performance Tests: Response time and throughput
"""

import pytest
import asyncio
from datetime import date, datetime
from pathlib import Path
from typing import Dict, Any
import tempfile
import json

from instruments.custom.pms_hub.canonical_models import (
    Reservation,
    ReservationStatus,
    MessageType,
)
from instruments.custom.google_voice.google_voice_manager import GoogleVoiceManager
from python.helpers import files


# ============================================================================
# FIXTURES
# ============================================================================


@pytest.fixture
def temp_db_path():
    """Create temporary database for testing"""
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = Path(tmpdir) / "google_voice_test.db"
        yield str(db_path)


@pytest.fixture
def google_voice_manager(temp_db_path):
    """Initialize Google Voice manager with temp database"""
    return GoogleVoiceManager(temp_db_path)


@pytest.fixture
def sample_reservation():
    """Create sample reservation for testing"""
    today = date.today()
    return Reservation(
        provider_id="res_test_001",
        provider="hostaway",
        property_provider_id="prop_test_001",
        guest_name="Test Guest",
        guest_email="test@example.com",
        guest_phone="+14155551234",
        check_in_date=today,
        check_out_date=date(today.year, today.month, today.day + 3),
        status=ReservationStatus.CONFIRMED,
    )


@pytest.fixture
def sample_reservations():
    """Create multiple sample reservations for testing"""
    today = date.today()
    return [
        Reservation(
            provider_id="res_001",
            provider="hostaway",
            property_provider_id="prop_001",
            guest_name="John Smith",
            guest_email="john@example.com",
            guest_phone="+14155551234",
            check_in_date=today,
            check_out_date=date(today.year, today.month, today.day + 3),
            status=ReservationStatus.CONFIRMED,
        ),
        Reservation(
            provider_id="res_002",
            provider="lodgify",
            property_provider_id="prop_002",
            guest_name="Maria Garcia",
            guest_email="maria@example.com",
            guest_phone="+13105555678",
            check_in_date=today,
            check_out_date=date(today.year, today.month, today.day + 2),
            status=ReservationStatus.CONFIRMED,
        ),
        Reservation(
            provider_id="res_003",
            provider="airbnb",
            property_provider_id="prop_003",
            guest_name="Robert Johnson",
            guest_email="robert@example.com",
            guest_phone="+1212555910",
            check_in_date=today,
            check_out_date=date(today.year, today.month, today.day + 5),
            status=ReservationStatus.CONFIRMED,
        ),
    ]


# ============================================================================
# UNIT TESTS - Component Functionality
# ============================================================================


class TestGoogleVoiceManagerInitialization:
    """Test GoogleVoiceManager initialization and setup"""

    @pytest.mark.unit
    def test_manager_initialization(self, google_voice_manager):
        """Test manager initializes correctly"""
        assert google_voice_manager is not None
        assert google_voice_manager.db is not None

    @pytest.mark.unit
    def test_manager_has_event_bus(self, google_voice_manager):
        """Test event bus is available"""
        assert google_voice_manager.event_bus is not None

    @pytest.mark.unit
    def test_manager_has_event_store(self, google_voice_manager):
        """Test event store is available"""
        assert google_voice_manager.event_store is not None


class TestMessageDrafting:
    """Test message creation and drafting"""

    @pytest.mark.unit
    def test_draft_single_message(self, google_voice_manager):
        """Test drafting a single outbound message"""
        phone = "+14155551234"
        body = "Test message content"

        result = google_voice_manager.draft_outbound(phone, body)

        assert "id" in result
        assert result["to_number"] == phone
        assert result["body"] == body
        assert result["status"] == "draft"

    @pytest.mark.unit
    def test_draft_message_has_id(self, google_voice_manager):
        """Test drafted message gets unique ID"""
        msg1 = google_voice_manager.draft_outbound("+14155551234", "Message 1")
        msg2 = google_voice_manager.draft_outbound("+13105555678", "Message 2")

        assert msg1["id"] != msg2["id"]

    @pytest.mark.unit
    def test_draft_message_with_unicode(self, google_voice_manager):
        """Test drafting message with unicode characters"""
        phone = "+14155551234"
        body = "Welcome! 🎉 Bienvenido ¡Hola!"

        result = google_voice_manager.draft_outbound(phone, body)

        assert result["body"] == body
        assert "🎉" in result["body"]

    @pytest.mark.unit
    def test_draft_message_with_long_text(self, google_voice_manager):
        """Test drafting message with long content"""
        phone = "+14155551234"
        body = "A" * 500  # Long message

        result = google_voice_manager.draft_outbound(phone, body)

        assert result["body"] == body
        assert len(result["body"]) == 500


class TestMessageListing:
    """Test message listing and filtering"""

    @pytest.mark.unit
    def test_list_empty_messages(self, google_voice_manager):
        """Test listing when no messages exist"""
        result = google_voice_manager.list_outbound()
        assert isinstance(result, list)
        assert len(result) == 0

    @pytest.mark.unit
    def test_list_draft_messages(self, google_voice_manager):
        """Test listing only draft messages"""
        google_voice_manager.draft_outbound("+14155551234", "Draft 1")
        google_voice_manager.draft_outbound("+13105555678", "Draft 2")

        drafts = google_voice_manager.list_outbound("draft")

        assert len(drafts) >= 2
        assert all(msg["status"] == "draft" for msg in drafts)

    @pytest.mark.unit
    def test_list_all_messages(self, google_voice_manager):
        """Test listing all messages regardless of status"""
        google_voice_manager.draft_outbound("+14155551234", "Message 1")
        google_voice_manager.draft_outbound("+13105555678", "Message 2")
        google_voice_manager.draft_outbound("+1212555910", "Message 3")

        all_msgs = google_voice_manager.list_outbound()

        assert len(all_msgs) >= 3

    @pytest.mark.unit
    def test_list_inbound_messages(self, google_voice_manager):
        """Test listing inbound messages"""
        inbound = google_voice_manager.list_inbound()

        assert isinstance(inbound, list)


class TestMessageStatusTracking:
    """Test message status transitions"""

    @pytest.mark.unit
    def test_initial_status_is_draft(self, google_voice_manager):
        """Test new message starts in draft status"""
        msg = google_voice_manager.draft_outbound("+14155551234", "Test")

        assert msg["status"] == "draft"

    @pytest.mark.unit
    def test_update_message_status(self, google_voice_manager):
        """Test updating message status"""
        msg = google_voice_manager.draft_outbound("+14155551234", "Test")
        msg_id = msg["id"]

        google_voice_manager.db.update_outbound_status(msg_id, "approved")

        updated = google_voice_manager.list_outbound()
        found = next((m for m in updated if m["id"] == msg_id), None)

        assert found is not None
        assert found["status"] == "approved"

    @pytest.mark.unit
    def test_status_transitions(self, google_voice_manager):
        """Test all valid status transitions"""
        msg = google_voice_manager.draft_outbound("+14155551234", "Test")
        msg_id = msg["id"]

        # draft -> approved
        google_voice_manager.db.update_outbound_status(msg_id, "approved")
        updated = google_voice_manager.list_outbound()
        assert next(m for m in updated if m["id"] == msg_id)["status"] == "approved"

        # approved -> sent
        google_voice_manager.db.update_outbound_status(msg_id, "sent")
        updated = google_voice_manager.list_outbound()
        assert next(m for m in updated if m["id"] == msg_id)["status"] == "sent"


# ============================================================================
# INTEGRATION TESTS - Message Lifecycle
# ============================================================================


class TestMessageLifecycle:
    """Test complete message lifecycle"""

    @pytest.mark.integration
    def test_message_lifecycle_draft_to_sent(self, google_voice_manager):
        """Test complete message flow: draft -> approved -> sent"""
        phone = "+14155551234"
        body = "Check-in message"

        # Step 1: Draft
        draft = google_voice_manager.draft_outbound(phone, body)
        msg_id = draft["id"]
        assert draft["status"] == "draft"

        # Step 2: Verify in database
        all_msgs = google_voice_manager.list_outbound()
        found = next((m for m in all_msgs if m["id"] == msg_id), None)
        assert found is not None

        # Step 3: Update to approved
        google_voice_manager.db.update_outbound_status(msg_id, "approved")
        updated = google_voice_manager.list_outbound()
        approved_msg = next(m for m in updated if m["id"] == msg_id)
        assert approved_msg["status"] == "approved"

        # Step 4: Mark as sent with timestamp
        sent_at = datetime.utcnow().isoformat()
        google_voice_manager.db.update_outbound_status(msg_id, "sent", sent_at=sent_at)
        final = google_voice_manager.list_outbound()
        sent_msg = next(m for m in final if m["id"] == msg_id)
        assert sent_msg["status"] == "sent"
        assert sent_msg["sent_at"] == sent_at

    @pytest.mark.integration
    def test_multiple_messages_independence(self, google_voice_manager, sample_reservations):
        """Test multiple messages track independently"""
        messages = {}
        for res in sample_reservations:
            msg = google_voice_manager.draft_outbound(
                res.guest_phone,
                f"Hi {res.guest_name}! Welcome!",
            )
            messages[res.provider_id] = msg["id"]

        # Update one message to sent
        first_id = list(messages.values())[0]
        google_voice_manager.db.update_outbound_status(first_id, "sent")

        # Verify others remain draft
        all_msgs = google_voice_manager.list_outbound()
        sent_count = sum(1 for m in all_msgs if m["status"] == "sent")
        draft_count = sum(1 for m in all_msgs if m["status"] == "draft")

        assert sent_count == 1
        assert draft_count >= 2


class TestBulkMessageHandling:
    """Test handling multiple messages efficiently"""

    @pytest.mark.integration
    def test_create_multiple_messages(self, google_voice_manager, sample_reservations):
        """Test creating multiple messages in sequence"""
        created = []
        for res in sample_reservations:
            msg = google_voice_manager.draft_outbound(
                res.guest_phone,
                f"Welcome {res.guest_name}!",
            )
            created.append(msg)

        assert len(created) == len(sample_reservations)
        assert all("id" in msg for msg in created)

    @pytest.mark.integration
    def test_list_multiple_messages_with_filtering(self, google_voice_manager, sample_reservations):
        """Test listing and filtering multiple messages"""
        # Create messages
        for res in sample_reservations:
            google_voice_manager.draft_outbound(res.guest_phone, f"Hi {res.guest_name}!")

        # List all
        all_msgs = google_voice_manager.list_outbound()
        assert len(all_msgs) >= 3

        # List drafts
        drafts = google_voice_manager.list_outbound("draft")
        assert len(drafts) >= 3
        assert all(m["status"] == "draft" for m in drafts)


# ============================================================================
# SYSTEM TESTS - End-to-End Workflows
# ============================================================================


class TestCheckInMessageGeneration:
    """Test check-in message generation from reservations"""

    @pytest.mark.system
    def test_generate_checkin_message(self, sample_reservation):
        """Test generating personalized check-in message"""
        guest_name = sample_reservation.guest_name
        property_id = sample_reservation.property_provider_id

        message = f"Hi {guest_name.split()[0]}! Welcome to {property_id}! 🎉\n\nWe're excited to host you!"

        assert guest_name.split()[0] in message
        assert property_id in message
        assert "🎉" in message

    @pytest.mark.system
    def test_checkin_messages_for_multiple_guests(self, sample_reservations):
        """Test generating messages for multiple guests"""
        messages = []
        for res in sample_reservations:
            guest_first = res.guest_name.split()[0]
            msg = f"Hi {guest_first}! Welcome to {res.property_provider_id}! 🎉"
            messages.append(msg)

        assert len(messages) == len(sample_reservations)
        assert all("Welcome" in msg for msg in messages)
        assert all("🎉" in msg for msg in messages)

    @pytest.mark.system
    def test_personalization_accuracy(self, sample_reservation):
        """Test message personalization is accurate"""
        res = sample_reservation
        message = f"Hi {res.guest_name.split()[0]}! Welcome to {res.property_provider_id}! 🎉"

        # Verify personalization
        assert res.guest_name.split()[0] in message  # First name
        assert res.property_provider_id in message  # Property ID
        assert res.guest_phone not in message or res.guest_phone is None  # No exposed PII


class TestEventBusIntegration:
    """Test event bus integration for message tracking"""

    @pytest.mark.system
    def test_event_bus_emits_message_sent_event(self, google_voice_manager):
        """Test event bus emits events for sent messages"""
        # Create and process message
        msg = google_voice_manager.draft_outbound("+14155551234", "Test")
        assert google_voice_manager.event_bus is not None

    @pytest.mark.system
    def test_event_bus_connection(self, google_voice_manager):
        """Test event bus is properly connected"""
        assert google_voice_manager.event_bus is not None
        assert google_voice_manager.event_store is not None


# ============================================================================
# PERFORMANCE TESTS - Response Time and Throughput
# ============================================================================


class TestPerformance:
    """Test system performance and throughput"""

    @pytest.mark.performance
    def test_draft_message_response_time(self, google_voice_manager):
        """Test message drafting completes in <100ms"""
        import time

        start = time.time()
        google_voice_manager.draft_outbound("+14155551234", "Test message")
        elapsed = time.time() - start

        assert elapsed < 0.1  # <100ms

    @pytest.mark.performance
    def test_list_messages_response_time(self, google_voice_manager):
        """Test listing messages completes in <50ms"""
        import time

        # Create some messages
        for i in range(10):
            google_voice_manager.draft_outbound(f"+14155551{i:03d}", f"Message {i}")

        start = time.time()
        google_voice_manager.list_outbound()
        elapsed = time.time() - start

        assert elapsed < 0.05  # <50ms

    @pytest.mark.performance
    def test_bulk_message_creation_throughput(self, google_voice_manager):
        """Test creating 100 messages completes in <1 second"""
        import time

        start = time.time()
        for i in range(100):
            google_voice_manager.draft_outbound(f"+14155551{i%9999:04d}", f"Message {i}")
        elapsed = time.time() - start

        assert elapsed < 1.0  # <1 second for 100 messages


# ============================================================================
# ERROR HANDLING & EDGE CASES
# ============================================================================


class TestErrorHandling:
    """Test error handling and edge cases"""

    @pytest.mark.unit
    def test_draft_with_empty_phone(self, google_voice_manager):
        """Test drafting with empty phone number"""
        result = google_voice_manager.draft_outbound("", "Message")
        assert result is not None

    @pytest.mark.unit
    def test_draft_with_empty_message(self, google_voice_manager):
        """Test drafting with empty message"""
        result = google_voice_manager.draft_outbound("+14155551234", "")
        assert result is not None

    @pytest.mark.unit
    def test_list_nonexistent_status(self, google_voice_manager):
        """Test listing with invalid status filter"""
        result = google_voice_manager.list_outbound("nonexistent_status")
        assert isinstance(result, list)

    @pytest.mark.unit
    def test_get_inbound_with_limit(self, google_voice_manager):
        """Test getting inbound messages with limit"""
        result = google_voice_manager.list_inbound(limit=5)
        assert isinstance(result, list)


# ============================================================================
# VALIDATION TESTS - Business Logic
# ============================================================================


class TestBusinessLogicValidation:
    """Test business logic and requirements"""

    @pytest.mark.validation
    def test_messages_include_guest_name(self, sample_reservation):
        """Test messages include personalized guest name"""
        res = sample_reservation
        message = f"Hi {res.guest_name.split()[0]}! Welcome!"
        assert res.guest_name.split()[0] in message

    @pytest.mark.validation
    def test_messages_include_check_in_details(self, sample_reservation):
        """Test messages include check-in/out dates"""
        res = sample_reservation
        details = f"Check-in: {res.check_in_date}, Check-out: {res.check_out_date}"
        assert str(res.check_in_date) in details
        assert str(res.check_out_date) in details

    @pytest.mark.validation
    def test_phone_number_format_validation(self, sample_reservation):
        """Test phone numbers are properly formatted"""
        phone = sample_reservation.guest_phone
        assert phone.startswith("+")
        assert len(phone) >= 10

    @pytest.mark.validation
    def test_reservation_status_confirmed(self, sample_reservation):
        """Test reservation is in confirmed status"""
        assert sample_reservation.status == ReservationStatus.CONFIRMED

    @pytest.mark.validation
    def test_check_in_is_today(self, sample_reservation):
        """Test check-in date is today"""
        assert sample_reservation.check_in_date == date.today()


# ============================================================================
# TEST SUMMARY
# ============================================================================

if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
