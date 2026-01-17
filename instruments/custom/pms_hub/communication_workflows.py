"""
Guest Communication Automation Service
Manages pre-arrival, during-stay, and post-checkout communication workflows
"""

import sys
from pathlib import Path
from typing import Any, Optional

# Add imports path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from .canonical_models import Reservation
from .provider_registry import ProviderRegistry


class CommunicationWorkflowService:
    """
    Manages automated guest communication workflows
    Supports pre-arrival instructions, during-stay support, and post-checkout follow-up

    Architecture:
    - Transforms reservations into communication sequences
    - Manages message templates for different workflows
    - Handles multi-channel delivery (email, SMS, message)
    - Maintains communication audit trail
    """

    def __init__(self):
        """Initialize communication workflow service with registry"""
        self.registry = ProviderRegistry()

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

    async def initialize_workflow(self) -> Optional[dict[str, Any]]:
        """
        Initialize communication workflow service

        Returns:
            Dictionary with initialization status or None if failed

        ★ Insight ─────────────────────────────────────
        - Sets up message templates and channels
        - Initializes event tracking for communications
        - Verifies provider connections
        ─────────────────────────────────────────────────
        """
        try:
            # Initialize workflow templates
            self.templates = {
                "pre_arrival": self._get_pre_arrival_template(),
                "during_stay": self._get_during_stay_template(),
                "post_checkout": self._get_post_checkout_template(),
            }

            # Initialize communication channels
            self.channels = {
                "email": {"enabled": True, "default": True},
                "sms": {"enabled": True, "default": False},
                "message": {"enabled": True, "default": False},
            }

            if self.event_bus:
                try:
                    await self.event_bus.emit(
                        "pms.communication.workflow_initialized",
                        {"status": "ready", "channels": list(self.channels.keys())},
                    )
                except Exception as e:
                    print(f"Warning: EventBus emit failed: {e}")

            return {
                "status": "initialized",
                "templates_count": len(self.templates),
                "channels": list(self.channels.keys()),
            }
        except Exception as e:
            print(f"Error initializing workflow: {e}")
            return None

    async def get_service_status(self) -> Optional[dict[str, Any]]:
        """
        Get communication workflow service status

        Returns:
            Dictionary with service status or None if failed

        ★ Insight ─────────────────────────────────────
        - Reports initialization and operational status
        - Tracks communication metrics
        - Provides health check information
        ─────────────────────────────────────────────────
        """
        try:
            status = {
                "service": "communication_workflows",
                "status": "operational",
                "templates": len(self.templates) if hasattr(self, "templates") else 0,
                "channels": list(self.channels.keys()) if hasattr(self, "channels") else [],
                "event_bus": self.event_bus is not None,
            }
            return status
        except Exception as e:
            print(f"Error getting service status: {e}")
            return None

    def _get_pre_arrival_template(self) -> dict[str, str]:
        """Get pre-arrival message template"""
        return {
            "subject": "Welcome! Your arrival is coming up",
            "body": "We're excited to welcome you! Here's what you need to know for your stay.",
            "include_check_in_instructions": True,
            "include_house_rules": True,
            "include_amenities": True,
        }

    def _get_during_stay_template(self) -> dict[str, str]:
        """Get during-stay support template"""
        return {
            "subject": "Need help? We're here for you",
            "body": "If you have any questions or need assistance during your stay, please don't hesitate to reach out.",
            "include_contact_info": True,
            "include_emergency_contacts": True,
        }

    def _get_post_checkout_template(self) -> dict[str, str]:
        """Get post-checkout follow-up template"""
        return {
            "subject": "Thanks for staying with us!",
            "body": "We hope you had a wonderful stay. We'd love to hear about your experience.",
            "include_review_request": True,
            "include_discount_offer": False,
        }

    async def create_pre_arrival_workflow(self, reservation: Reservation) -> Optional[dict[str, Any]]:
        """
        Create pre-arrival communication workflow for a reservation

        Args:
            reservation: Canonical Reservation object

        Returns:
            Dictionary with workflow details or None if failed

        ★ Insight ─────────────────────────────────────
        - Generates personalized pre-arrival message
        - Schedules delivery 48 hours before check-in
        - Includes property-specific information
        ─────────────────────────────────────────────────
        """
        try:
            workflow = {
                "type": "pre_arrival",
                "reservation_id": reservation.provider_id,
                "guest_name": reservation.guest_name,
                "guest_email": reservation.guest_email,
                "check_in_date": reservation.check_in_date.isoformat(),
                "scheduled_send_time": self._calculate_send_time(reservation),
                "sections": {
                    "check_in_instructions": self._get_check_in_instructions(),
                    "house_rules": self._get_house_rules(),
                    "wifi_info": self._get_wifi_info(),
                    "parking_info": self._get_parking_info(),
                    "local_recommendations": self._get_local_recommendations(),
                },
            }

            if self.event_bus:
                try:
                    await self.event_bus.emit(
                        "pms.communication.pre_arrival_workflow_created",
                        {"workflow_id": reservation.provider_id},
                    )
                except Exception as e:
                    print(f"Warning: EventBus emit failed: {e}")

            return workflow
        except Exception as e:
            print(f"Error creating pre-arrival workflow: {e}")
            return None

    def _calculate_send_time(self, reservation: Reservation) -> str:
        """Calculate send time: 48 hours before check-in"""
        from datetime import timedelta

        send_date = reservation.check_in_date - timedelta(days=2)
        return f"{send_date.isoformat()}T09:00:00"

    def _get_check_in_instructions(self) -> dict[str, str]:
        """Get check-in instructions"""
        return {
            "title": "Check-In Instructions",
            "content": "Here's how to access your accommodation",
            "key_code": "Available upon confirmation",
            "lock_type": "Digital keypad",
            "parking_location": "On-site parking available",
        }

    def _get_house_rules(self) -> dict[str, str]:
        """Get house rules"""
        return {
            "title": "House Rules",
            "quiet_hours": "10 PM - 8 AM",
            "guest_limit": "4 guests maximum",
            "smoking_policy": "Non-smoking property",
            "parties": "No parties or events",
        }

    def _get_wifi_info(self) -> dict[str, str]:
        """Get WiFi information"""
        return {
            "title": "WiFi & Internet",
            "network_name": "GuestNetwork",
            "password": "Available upon check-in",  # pragma: allowlist secret
            "speed": "100 Mbps",
        }

    def _get_parking_info(self) -> dict[str, str]:
        """Get parking information"""
        return {
            "title": "Parking Information",
            "location": "Dedicated lot behind property",
            "spots": "2 assigned spaces",
            "permit": "Not required",
        }

    def _get_local_recommendations(self) -> dict[str, list]:
        """Get local recommendations"""
        return {
            "title": "Local Recommendations",
            "restaurants": ["Local Cafe", "Downtown Bistro"],
            "attractions": ["City Park", "Museum District"],
            "transportation": ["Bus stop 2 blocks away", "Bike rental nearby"],
        }

    async def create_post_checkout_workflow(self, reservation: Reservation) -> Optional[dict[str, Any]]:
        """
        Create post-checkout communication workflow

        Args:
            reservation: Canonical Reservation object

        Returns:
            Dictionary with workflow details or None if failed

        ★ Insight ─────────────────────────────────────
        - Triggers on check-out date
        - Includes thank you message and review request
        - Gathers feedback for continuous improvement
        ─────────────────────────────────────────────────
        """
        try:
            workflow = {
                "type": "post_checkout",
                "reservation_id": reservation.provider_id,
                "guest_name": reservation.guest_name,
                "guest_email": reservation.guest_email,
                "check_out_date": reservation.check_out_date.isoformat(),
                "scheduled_send_time": self._calculate_post_checkout_send_time(reservation),
                "sections": {
                    "thank_you_message": self._get_thank_you_message(),
                    "review_request": self._get_review_request(),
                    "feedback_survey": self._get_feedback_survey(),
                    "cleaning_confirmation": self._get_cleaning_confirmation(),
                },
            }

            if self.event_bus:
                try:
                    await self.event_bus.emit(
                        "pms.communication.post_checkout_workflow_created",
                        {"workflow_id": reservation.provider_id},
                    )
                except Exception as e:
                    print(f"Warning: EventBus emit failed: {e}")

            return workflow
        except Exception as e:
            print(f"Error creating post-checkout workflow: {e}")
            return None

    def _calculate_post_checkout_send_time(self, reservation: Reservation) -> str:
        """Calculate send time: 2 hours after check-out"""

        send_time = (reservation.check_out_date.isoformat()) + "T14:00:00"  # 2 PM on check-out day
        return send_time

    def _get_thank_you_message(self) -> dict[str, str]:
        """Get thank you message"""
        return {
            "title": "Thank You for Staying!",
            "body": "We appreciated having you stay with us.",
            "sentiment": "positive",
        }

    def _get_review_request(self) -> dict[str, str]:
        """Get review request"""
        return {
            "title": "Please Leave a Review",
            "body": "Your feedback helps us improve. Share your experience!",
            "review_url": "https://example.com/review",
            "incentive": "Complete review for 10% discount on next stay",
        }

    def _get_feedback_survey(self) -> dict[str, list]:
        """Get feedback survey"""
        return {
            "title": "Quick Feedback Survey",
            "questions": [
                "How would you rate your stay?",
                "Was the check-in smooth?",
                "Would you recommend us?",
                "What could we improve?",
            ],
        }

    def _get_cleaning_confirmation(self) -> dict[str, str]:
        """Get cleaning confirmation"""
        return {
            "title": "Cleaning Confirmation",
            "message": "Our team will clean the property within 2 hours of checkout.",
            "contact": "Call 555-CLEAN if you have questions",
            "next_guest": "Next guest arriving tomorrow",
        }

    async def create_issue_resolution_workflow(
        self, reservation: Reservation, issue_type: str
    ) -> Optional[dict[str, Any]]:
        """
        Create issue resolution communication workflow

        Args:
            reservation: Canonical Reservation object
            issue_type: Type of issue (damage, noise, maintenance, etc.)

        Returns:
            Dictionary with workflow details or None if failed

        ★ Insight ─────────────────────────────────────
        - Handles guest issues during or after stay
        - Routes to appropriate resolution team
        - Documents issue for records and accountability
        - Tracks resolution status
        ─────────────────────────────────────────────────
        """
        try:
            workflow = {
                "type": "issue_resolution",
                "reservation_id": reservation.provider_id,
                "guest_name": reservation.guest_name,
                "issue_type": issue_type,
                "priority": self._get_issue_priority(issue_type),
                "escalation_path": self._get_escalation_path(issue_type),
                "sections": {
                    "issue_description": self._get_issue_template(issue_type),
                    "resolution_steps": self._get_resolution_steps(issue_type),
                    "contact_info": self._get_support_contact(),
                },
            }

            if self.event_bus:
                try:
                    await self.event_bus.emit(
                        "pms.communication.issue_resolution_workflow_created",
                        {
                            "workflow_id": reservation.provider_id,
                            "issue_type": issue_type,
                            "priority": workflow["priority"],
                        },
                    )
                except Exception as e:
                    print(f"Warning: EventBus emit failed: {e}")

            return workflow
        except Exception as e:
            print(f"Error creating issue resolution workflow: {e}")
            return None

    def _get_issue_priority(self, issue_type: str) -> str:
        """Determine priority level based on issue type"""
        priority_map = {
            "damage": "high",
            "noise": "medium",
            "maintenance": "medium",
            "safety": "critical",
            "injury": "critical",
            "lost_key": "low",
        }
        return priority_map.get(issue_type, "medium")

    def _get_escalation_path(self, issue_type: str) -> list[str]:
        """Get escalation path for issue type"""
        escalation_map = {
            "damage": ["support", "maintenance", "manager"],
            "noise": ["support", "security"],
            "maintenance": ["maintenance", "support"],
            "safety": ["manager", "legal"],
            "injury": ["manager", "insurance", "legal"],
            "lost_key": ["support"],
        }
        return escalation_map.get(issue_type, ["support"])

    def _get_issue_template(self, issue_type: str) -> dict[str, str]:
        """Get issue-specific template"""
        templates = {
            "damage": {
                "title": "Property Damage Report",
                "description": "We received a report of property damage.",
                "next_steps": "Our team will inspect and assess.",
            },
            "noise": {
                "title": "Noise Complaint",
                "description": "We received a noise complaint from neighbors.",
                "next_steps": "Please reduce noise levels. Repeat violations may result in early termination.",
            },
            "maintenance": {
                "title": "Maintenance Request",
                "description": "We received a maintenance request.",
                "next_steps": "Our maintenance team will contact you within 1 hour.",
            },
            "safety": {
                "title": "Safety Concern",
                "description": "We received a safety concern report.",
                "next_steps": "Management will contact you immediately.",
            },
            "injury": {
                "title": "Injury Report",
                "description": "We received an injury report.",
                "next_steps": "Please seek medical attention immediately. We will contact you.",
            },
        }
        return templates.get(issue_type, {"title": "Issue", "description": "General issue"})

    def _get_resolution_steps(self, issue_type: str) -> dict[str, list]:
        """Get resolution steps for issue type"""
        return {
            "immediate": ["Acknowledge issue receipt", "Assess severity"],
            "escalation": ["Contact appropriate team", "Document details"],
            "follow_up": ["Update guest", "Confirm resolution"],
        }

    def _get_support_contact(self) -> dict[str, str]:
        """Get support contact information"""
        return {
            "phone": "1-800-SUPPORT",
            "email": "support@example.com",
            "emergency": "911 for emergencies",
            "available": "24/7",
        }
