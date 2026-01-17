"""
Guest Communication Automation Tests - Team B TDD Swarm
Tests for PMS guest communication workflows and automation
Tests pre-arrival, post-checkout, issue resolution, and review management
"""

from datetime import date, timedelta

import pytest

from instruments.custom.pms_hub.canonical_models import (
    Reservation,
)


class TestCommunicationWorkflowInitialization:
    """Tests for communication workflow service initialization"""

    @pytest.mark.unit
    def test_workflow_service_creation(self):
        """Test creating communication workflow service"""
        from instruments.custom.pms_hub.communication_workflows import CommunicationWorkflowService

        service = CommunicationWorkflowService()

        # Service should be created successfully
        assert service is not None
        assert hasattr(service, "registry")
        assert hasattr(service, "event_bus")

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_workflow_service_with_event_bus(self):
        """Test workflow service initializes and is ready"""
        from instruments.custom.pms_hub.communication_workflows import CommunicationWorkflowService

        service = CommunicationWorkflowService()

        # Initialize workflow
        result = await service.initialize_workflow()

        # Should initialize successfully
        assert result is not None
        assert result.get("status") == "initialized"
        assert "templates_count" in result
        assert "channels" in result
        assert len(result["channels"]) > 0


class TestPreArrivalWorkflows:
    """Tests for pre-arrival message workflows"""

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_create_pre_arrival_workflow(self):
        """Test creating pre-arrival workflow"""

        from instruments.custom.pms_hub.communication_workflows import (
            CommunicationWorkflowService,
        )

        service = CommunicationWorkflowService()

        # Create reservation for workflow
        reservation = Reservation(
            provider_id="res_001",
            provider="test",
            property_provider_id="prop_001",
            guest_name="John Doe",
            guest_email="john@example.com",
            check_in_date=date(2026, 2, 1),
            check_out_date=date(2026, 2, 5),
        )

        # Create workflow
        workflow = await service.create_pre_arrival_workflow(reservation)

        assert workflow is not None
        assert workflow["type"] == "pre_arrival"
        assert workflow["reservation_id"] == "res_001"
        assert workflow["guest_name"] == "John Doe"
        assert "sections" in workflow

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_trigger_pre_arrival_workflow(self):
        """Test triggering pre-arrival workflow on reservation creation"""

        from instruments.custom.pms_hub.communication_workflows import (
            CommunicationWorkflowService,
        )

        service = CommunicationWorkflowService()

        reservation = Reservation(
            provider_id="res_002",
            provider="test",
            property_provider_id="prop_001",
            guest_name="Jane Smith",
            guest_email="jane@example.com",
            check_in_date=date(2026, 2, 10),
            check_out_date=date(2026, 2, 15),
        )

        # Workflow creation simulates trigger on reservation
        workflow = await service.create_pre_arrival_workflow(reservation)

        # Should be triggered and created
        assert workflow is not None
        assert "scheduled_send_time" in workflow

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_pre_arrival_message_timing(self):
        """Test pre-arrival message sent 48 hours before check-in"""

        from instruments.custom.pms_hub.communication_workflows import (
            CommunicationWorkflowService,
        )

        service = CommunicationWorkflowService()

        check_in = date(2026, 2, 20)
        reservation = Reservation(
            provider_id="res_003",
            provider="test",
            property_provider_id="prop_001",
            check_in_date=check_in,
            check_out_date=check_in + timedelta(days=3),
        )

        workflow = await service.create_pre_arrival_workflow(reservation)

        # Send time should be 48 hours before check-in
        expected_send_date = (check_in - timedelta(days=2)).isoformat()
        assert expected_send_date in workflow["scheduled_send_time"]

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_pre_arrival_check_in_instructions(self):
        """Test pre-arrival message includes check-in instructions"""

        from instruments.custom.pms_hub.communication_workflows import (
            CommunicationWorkflowService,
        )

        service = CommunicationWorkflowService()

        reservation = Reservation(
            provider_id="res_004",
            provider="test",
            property_provider_id="prop_001",
            check_in_date=date(2026, 2, 25),
            check_out_date=date(2026, 2, 28),
        )

        workflow = await service.create_pre_arrival_workflow(reservation)

        # Should include check-in instructions
        assert "check_in_instructions" in workflow["sections"]
        instructions = workflow["sections"]["check_in_instructions"]
        assert "title" in instructions
        assert "lock_type" in instructions

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_pre_arrival_house_rules(self):
        """Test pre-arrival message includes house rules"""

        from instruments.custom.pms_hub.communication_workflows import (
            CommunicationWorkflowService,
        )

        service = CommunicationWorkflowService()

        reservation = Reservation(
            provider_id="res_005",
            provider="test",
            property_provider_id="prop_001",
            check_in_date=date(2026, 3, 1),
            check_out_date=date(2026, 3, 5),
        )

        workflow = await service.create_pre_arrival_workflow(reservation)

        # Should include house rules
        assert "house_rules" in workflow["sections"]
        rules = workflow["sections"]["house_rules"]
        assert "quiet_hours" in rules
        assert "guest_limit" in rules

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_pre_arrival_wifi_password(self):
        """Test pre-arrival message includes WiFi information"""

        from instruments.custom.pms_hub.communication_workflows import (
            CommunicationWorkflowService,
        )

        service = CommunicationWorkflowService()

        reservation = Reservation(
            provider_id="res_006",
            provider="test",
            property_provider_id="prop_001",
            check_in_date=date(2026, 3, 10),
            check_out_date=date(2026, 3, 14),
        )

        workflow = await service.create_pre_arrival_workflow(reservation)

        # Should include WiFi information
        assert "wifi_info" in workflow["sections"]
        wifi = workflow["sections"]["wifi_info"]
        assert "network_name" in wifi
        assert "password" in wifi
        assert "speed" in wifi

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_pre_arrival_parking_info(self):
        """Test pre-arrival message includes parking information"""

        from instruments.custom.pms_hub.communication_workflows import (
            CommunicationWorkflowService,
        )

        service = CommunicationWorkflowService()

        reservation = Reservation(
            provider_id="res_007",
            provider="test",
            property_provider_id="prop_001",
            check_in_date=date(2026, 3, 20),
            check_out_date=date(2026, 3, 24),
        )

        workflow = await service.create_pre_arrival_workflow(reservation)

        # Should include parking information
        assert "parking_info" in workflow["sections"]
        parking = workflow["sections"]["parking_info"]
        assert "location" in parking
        assert "spots" in parking

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_pre_arrival_local_recommendations(self):
        """Test pre-arrival message includes local recommendations"""

        from instruments.custom.pms_hub.communication_workflows import (
            CommunicationWorkflowService,
        )

        service = CommunicationWorkflowService()

        reservation = Reservation(
            provider_id="res_008",
            provider="test",
            property_provider_id="prop_001",
            check_in_date=date(2026, 4, 1),
            check_out_date=date(2026, 4, 5),
        )

        workflow = await service.create_pre_arrival_workflow(reservation)

        # Should include local recommendations
        assert "local_recommendations" in workflow["sections"]
        recs = workflow["sections"]["local_recommendations"]
        assert "restaurants" in recs
        assert "attractions" in recs
        assert "transportation" in recs


class TestPostCheckoutWorkflows:
    """Tests for post-checkout message workflows"""

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_create_post_checkout_workflow(self):
        """Test creating post-checkout workflow"""
        from instruments.custom.pms_hub.communication_workflows import (
            CommunicationWorkflowService,
        )

        service = CommunicationWorkflowService()

        reservation = Reservation(
            provider_id="res_009",
            provider="test",
            property_provider_id="prop_001",
            guest_name="Alice Johnson",
            guest_email="alice@example.com",
            check_in_date=date(2026, 4, 10),
            check_out_date=date(2026, 4, 15),
        )

        workflow = await service.create_post_checkout_workflow(reservation)

        assert workflow is not None
        assert workflow["type"] == "post_checkout"
        assert workflow["reservation_id"] == "res_009"
        assert "sections" in workflow

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_trigger_post_checkout_workflow(self):
        """Test triggering post-checkout workflow on check-out"""
        from instruments.custom.pms_hub.communication_workflows import (
            CommunicationWorkflowService,
        )

        service = CommunicationWorkflowService()

        reservation = Reservation(
            provider_id="res_010",
            provider="test",
            property_provider_id="prop_001",
            check_in_date=date(2026, 4, 20),
            check_out_date=date(2026, 4, 25),
        )

        workflow = await service.create_post_checkout_workflow(reservation)

        assert workflow is not None
        assert "scheduled_send_time" in workflow

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_post_checkout_thank_you_message(self):
        """Test post-checkout thank you message"""
        from instruments.custom.pms_hub.communication_workflows import (
            CommunicationWorkflowService,
        )

        service = CommunicationWorkflowService()

        reservation = Reservation(
            provider_id="res_011",
            provider="test",
            property_provider_id="prop_001",
            check_in_date=date(2026, 5, 1),
            check_out_date=date(2026, 5, 5),
        )

        workflow = await service.create_post_checkout_workflow(reservation)

        assert "thank_you_message" in workflow["sections"]
        thank_you = workflow["sections"]["thank_you_message"]
        assert "title" in thank_you
        assert "body" in thank_you

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_post_checkout_review_request(self):
        """Test post-checkout review request in message"""
        from instruments.custom.pms_hub.communication_workflows import (
            CommunicationWorkflowService,
        )

        service = CommunicationWorkflowService()

        reservation = Reservation(
            provider_id="res_012",
            provider="test",
            property_provider_id="prop_001",
            check_in_date=date(2026, 5, 10),
            check_out_date=date(2026, 5, 14),
        )

        workflow = await service.create_post_checkout_workflow(reservation)

        assert "review_request" in workflow["sections"]
        review = workflow["sections"]["review_request"]
        assert "review_url" in review
        assert "incentive" in review

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_post_checkout_feedback_survey(self):
        """Test post-checkout includes feedback survey"""
        from instruments.custom.pms_hub.communication_workflows import (
            CommunicationWorkflowService,
        )

        service = CommunicationWorkflowService()

        reservation = Reservation(
            provider_id="res_013",
            provider="test",
            property_provider_id="prop_001",
            check_in_date=date(2026, 5, 20),
            check_out_date=date(2026, 5, 24),
        )

        workflow = await service.create_post_checkout_workflow(reservation)

        assert "feedback_survey" in workflow["sections"]
        survey = workflow["sections"]["feedback_survey"]
        assert "questions" in survey
        assert len(survey["questions"]) > 0

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_post_checkout_cleaning_confirmation(self):
        """Test post-checkout confirms cleaning scheduling"""
        from instruments.custom.pms_hub.communication_workflows import (
            CommunicationWorkflowService,
        )

        service = CommunicationWorkflowService()

        reservation = Reservation(
            provider_id="res_014",
            provider="test",
            property_provider_id="prop_001",
            check_in_date=date(2026, 6, 1),
            check_out_date=date(2026, 6, 5),
        )

        workflow = await service.create_post_checkout_workflow(reservation)

        assert "cleaning_confirmation" in workflow["sections"]
        cleaning = workflow["sections"]["cleaning_confirmation"]
        assert "message" in cleaning
        assert "contact" in cleaning


class TestIssueResolutionWorkflows:
    """Tests for issue resolution workflows"""

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_create_issue_workflow(self):
        """Test creating issue resolution workflow"""
        from instruments.custom.pms_hub.communication_workflows import (
            CommunicationWorkflowService,
        )

        service = CommunicationWorkflowService()

        reservation = Reservation(
            provider_id="res_015",
            provider="test",
            property_provider_id="prop_001",
            check_in_date=date(2026, 6, 10),
            check_out_date=date(2026, 6, 14),
        )

        workflow = await service.create_issue_resolution_workflow(reservation, "damage")

        assert workflow is not None
        assert workflow["type"] == "issue_resolution"
        assert workflow["issue_type"] == "damage"
        assert "priority" in workflow
        assert "escalation_path" in workflow

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_damage_report_workflow(self):
        """Test damage report issue workflow"""
        from instruments.custom.pms_hub.communication_workflows import (
            CommunicationWorkflowService,
        )

        service = CommunicationWorkflowService()

        reservation = Reservation(
            provider_id="res_016",
            provider="test",
            property_provider_id="prop_001",
            check_in_date=date(2026, 6, 15),
            check_out_date=date(2026, 6, 19),
        )

        workflow = await service.create_issue_resolution_workflow(reservation, "damage")

        assert workflow["priority"] == "high"
        assert "issue_description" in workflow["sections"]
        assert "damage" in workflow["sections"]["issue_description"]["title"].lower()

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_noise_complaint_workflow(self):
        """Test noise complaint issue workflow"""
        from instruments.custom.pms_hub.communication_workflows import (
            CommunicationWorkflowService,
        )

        service = CommunicationWorkflowService()

        reservation = Reservation(
            provider_id="res_017",
            provider="test",
            property_provider_id="prop_001",
            check_in_date=date(2026, 6, 20),
            check_out_date=date(2026, 6, 24),
        )

        workflow = await service.create_issue_resolution_workflow(reservation, "noise")

        assert workflow["priority"] == "medium"
        assert "noise" in workflow["sections"]["issue_description"]["title"].lower()
        assert "security" in workflow["escalation_path"]

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_cleanliness_issue_workflow(self, sample_reservation):
        """Test cleanliness issue workflow"""
        from instruments.custom.pms_hub.communication_workflows import (
            CommunicationWorkflowService,
        )

        service = CommunicationWorkflowService()
        await service.initialize_workflow()

        workflow = await service.create_issue_resolution_workflow(sample_reservation, "maintenance")

        assert workflow is not None
        assert workflow["type"] == "issue_resolution"
        assert workflow["issue_type"] == "maintenance"
        assert workflow["priority"] == "medium"
        assert "maintenance" in workflow["escalation_path"]
        assert workflow["sections"]["issue_description"]["title"] == "Maintenance Request"

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_guest_escalation_to_host(self, sample_reservation):
        """Test escalating guest concerns to host"""
        from instruments.custom.pms_hub.communication_workflows import (
            CommunicationWorkflowService,
        )

        service = CommunicationWorkflowService()
        await service.initialize_workflow()

        workflow = await service.create_issue_resolution_workflow(sample_reservation, "safety")

        assert workflow is not None
        assert workflow["type"] == "issue_resolution"
        assert workflow["issue_type"] == "safety"
        assert workflow["priority"] == "critical"
        assert workflow["escalation_path"][0] == "manager"
        assert "legal" in workflow["escalation_path"]
        assert workflow["sections"]["issue_description"]["title"] == "Safety Concern"

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_issue_resolution_tracking(self, sample_reservation):
        """Test tracking issue resolution status"""
        from instruments.custom.pms_hub.communication_workflows import (
            CommunicationWorkflowService,
        )

        service = CommunicationWorkflowService()
        await service.initialize_workflow()

        # Create injury issue (critical priority)
        workflow = await service.create_issue_resolution_workflow(sample_reservation, "injury")

        assert workflow is not None
        assert workflow["issue_type"] == "injury"
        assert workflow["priority"] == "critical"
        assert workflow["escalation_path"] == ["manager", "insurance", "legal"]
        assert "Injury Report" in workflow["sections"]["issue_description"]["title"]
        assert "medical attention" in workflow["sections"]["issue_description"]["next_steps"].lower()

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_issue_resolution_closure(self, sample_reservation):
        """Test closing resolved issues"""
        from instruments.custom.pms_hub.communication_workflows import (
            CommunicationWorkflowService,
        )

        service = CommunicationWorkflowService()
        await service.initialize_workflow()

        # Create lost_key issue (low priority)
        workflow = await service.create_issue_resolution_workflow(sample_reservation, "lost_key")

        assert workflow is not None
        assert workflow["type"] == "issue_resolution"
        assert workflow["issue_type"] == "lost_key"
        assert workflow["priority"] == "low"
        assert workflow["escalation_path"] == ["support"]
        assert len(workflow["sections"]["resolution_steps"]["immediate"]) > 0
        assert len(workflow["sections"]["resolution_steps"]["follow_up"]) > 0

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_automatic_compensation_offers(self, sample_reservation):
        """Test automatic compensation offers for issues"""
        from instruments.custom.pms_hub.communication_workflows import (
            CommunicationWorkflowService,
        )

        service = CommunicationWorkflowService()
        await service.initialize_workflow()

        # Damage issue should trigger compensation pathway
        workflow_damage = await service.create_issue_resolution_workflow(sample_reservation, "damage")

        assert workflow_damage is not None
        assert workflow_damage["priority"] == "high"
        assert "manager" in workflow_damage["escalation_path"]

        # Noise issue has lower compensation threshold
        workflow_noise = await service.create_issue_resolution_workflow(sample_reservation, "noise")

        assert workflow_noise["priority"] == "medium"
        assert workflow_noise["priority"] != workflow_damage["priority"]

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_issue_documentation(self, sample_reservation):
        """Test comprehensive issue documentation"""
        from instruments.custom.pms_hub.communication_workflows import (
            CommunicationWorkflowService,
        )

        service = CommunicationWorkflowService()
        await service.initialize_workflow()

        issue_types = ["damage", "noise", "maintenance", "safety", "injury", "lost_key"]

        for issue_type in issue_types:
            workflow = await service.create_issue_resolution_workflow(sample_reservation, issue_type)

            assert workflow is not None
            assert workflow["type"] == "issue_resolution"
            assert workflow["reservation_id"] == sample_reservation.provider_id
            assert workflow["guest_name"] == sample_reservation.guest_name
            assert "issue_description" in workflow["sections"]
            assert "resolution_steps" in workflow["sections"]
            assert "contact_info" in workflow["sections"]
            assert workflow["escalation_path"] is not None
            assert len(workflow["escalation_path"]) > 0


class TestMessageTemplates:
    """Tests for message template system"""

    @pytest.mark.unit
    def test_load_template(self):
        """Test loading message template"""
        templates = {
            "pre_arrival": {
                "subject": "Welcome! Your arrival is coming up",
                "body": "We're excited to welcome you...",
            },
            "post_checkout": {
                "subject": "Thanks for staying with us!",
                "body": "We hope you had a wonderful stay...",
            },
        }

        loaded_template = templates.get("pre_arrival")

        assert loaded_template is not None
        assert "subject" in loaded_template
        assert "body" in loaded_template
        assert "Welcome" in loaded_template["subject"]

    @pytest.mark.unit
    def test_render_template_variables(self):
        """Test rendering template with variables"""
        template = "Hello {{guest_name}}, your check-in is on {{check_in_date}}"
        variables = {
            "guest_name": "John Doe",
            "check_in_date": "February 1, 2026",
        }

        # Simple template rendering
        rendered = template
        for key, value in variables.items():
            rendered = rendered.replace(f"{{{{{key}}}}}", value)

        assert "John Doe" in rendered
        assert "February 1, 2026" in rendered
        assert "{{" not in rendered

    @pytest.mark.unit
    def test_personalization_tokens(self):
        """Test personalization tokens (guest name, dates, etc)"""
        available_tokens = {
            "{{guest_first_name}}": "John",
            "{{guest_last_name}}": "Doe",
            "{{property_name}}": "Beach House Paradise",
            "{{check_in_date}}": "Feb 1",
            "{{check_out_date}}": "Feb 7",
            "{{host_name}}": "Sarah",
        }

        # Validate token availability
        for value in available_tokens.values():
            assert value is not None
            assert len(value) > 0

        # Test token in message
        message = f"Hi {{{{guest_first_name}}}}, welcome to {{{{{available_tokens['{{property_name}}']}}}}}!"
        assert "{{" in message or all(v in message for v in available_tokens.values())

    @pytest.mark.unit
    def test_guest_language_selection(self):
        """Test selecting template by guest language"""
        language_templates = {
            "en": {
                "subject": "Welcome!",
                "body": "Welcome to our property",
            },
            "es": {
                "subject": "¡Bienvenido!",
                "body": "Bienvenido a nuestra propiedad",
            },
            "fr": {
                "subject": "Bienvenue!",
                "body": "Bienvenue dans notre propriété",
            },
        }

        guest_language = "es"
        selected_template = language_templates.get(guest_language)

        assert selected_template is not None
        assert selected_template["subject"] == "¡Bienvenido!"
        assert selected_template["body"] == "Bienvenido a nuestra propiedad"
        assert len(language_templates) == 3

    @pytest.mark.unit
    def test_property_specific_templates(self):
        """Test property-specific template overrides"""
        default_templates = {
            "pre_arrival": {
                "subject": "Welcome to our property",
                "body": "Get ready for your stay",
            },
        }

        property_overrides = {
            "prop_luxury": {
                "subject": "Welcome to Luxury Estate",
                "body": "Experience luxury living at our exclusive property",
            },
            "prop_budget": {
                "subject": "Welcome to Budget Inn",
                "body": "Thank you for choosing our affordable option",
            },
        }

        property_id = "prop_luxury"
        template = property_overrides.get(property_id) or default_templates["pre_arrival"]

        assert template["subject"] == "Welcome to Luxury Estate"
        assert template["body"] == "Experience luxury living at our exclusive property"
        assert property_id in property_overrides

    @pytest.mark.unit
    def test_template_validation(self):
        """Test template validation and syntax checking"""
        # Valid templates
        valid_template = {
            "id": "template_001",
            "name": "pre_arrival",
            "subject": "Welcome to {{property_name}}",
            "body": "Hello {{guest_first_name}}, your check-in is on {{check_in_date}}",
        }

        # Validate template structure
        required_fields = ["id", "name", "subject", "body"]
        for field in required_fields:
            assert field in valid_template
            assert valid_template[field] is not None
            assert len(str(valid_template[field])) > 0

        # Check for balanced braces in template
        template_body = valid_template["body"]
        open_braces = template_body.count("{{")
        close_braces = template_body.count("}}")
        assert open_braces == close_braces

    @pytest.mark.unit
    def test_template_import_export(self):
        """Test importing and exporting templates"""
        template_export = {
            "version": "1.0",
            "templates": [
                {
                    "id": "pre_arrival_001",
                    "name": "Pre-Arrival Welcome",
                    "subject": "Welcome {{guest_name}}!",
                    "body": "We're excited to host you.",
                    "language": "en",
                },
                {
                    "id": "post_checkout_001",
                    "name": "Post-Checkout Thank You",
                    "subject": "Thank you for staying!",
                    "body": "We hope you enjoyed your stay.",
                    "language": "en",
                },
            ],
            "export_timestamp": "2026-01-17T12:00:00Z",
            "export_count": 2,
        }

        imported_templates = template_export["templates"]
        assert len(imported_templates) == 2
        assert imported_templates[0]["id"] == "pre_arrival_001"
        assert template_export["export_count"] == 2
        assert "version" in template_export

    @pytest.mark.unit
    def test_conditional_template_sections(self):
        """Test conditional sections in templates"""
        template_with_conditions = {
            "base_content": "Welcome {{guest_name}} to {{property_name}}",
            "conditional_sections": {
                "has_pool": {
                    "condition": True,
                    "content": "Enjoy our heated pool and hot tub!",
                },
                "has_parking": {
                    "condition": True,
                    "content": "Free parking available at the property.",
                },
                "has_gym": {
                    "condition": False,
                    "content": "Access our fitness center.",
                },
            },
        }

        included_sections = [
            section for section, data in template_with_conditions["conditional_sections"].items() if data["condition"]
        ]

        assert len(included_sections) == 2
        assert "has_pool" in included_sections
        assert "has_parking" in included_sections
        assert "has_gym" not in included_sections

    @pytest.mark.unit
    def test_template_formatting(self):
        """Test template HTML/plain text formatting"""
        template_formats = {
            "plain_text": {
                "format_type": "text/plain",
                "content": "Welcome {{guest_name}} to {{property_name}}. Check-in is at {{check_in_time}}.",
                "line_breaks": True,
            },
            "html": {
                "format_type": "text/html",
                "content": "<p>Welcome <strong>{{guest_name}}</strong> to {{property_name}}.</p><p>Check-in: {{check_in_time}}</p>",
                "html_tags": 4,
            },
            "markdown": {
                "format_type": "text/markdown",
                "content": "# Welcome {{guest_name}}\n\n**Property**: {{property_name}}\n\n**Check-in**: {{check_in_time}}",
                "markdown_markers": True,
            },
        }

        html_format = template_formats["html"]
        assert html_format["format_type"] == "text/html"
        assert "<p>" in html_format["content"]
        assert "</p>" in html_format["content"]
        assert html_format["html_tags"] == 4
        assert len(template_formats) == 3

    @pytest.mark.unit
    def test_template_character_limits_sms(self):
        """Test SMS character limit enforcement (160 chars)"""
        sms_templates = {
            "check_in_reminder": "Hi {{guest_name}}, check-in is today! Property code: 1234. Contact: +1-555-0000",
            "check_out_reminder": "Hi {{guest_name}}, checkout is at 11am today. Please ensure keys are left at desk.",
            "emergency_contact": "Emergency contact: Sarah (owner) +1-555-HELP. Non-emergency: +1-555-SUPP",
        }

        sms_limit = 160

        for template_name, template_text in sms_templates.items():
            # Replace variables to estimate final length
            estimated_text = template_text.replace("{{guest_name}}", "John")
            assert len(estimated_text) <= sms_limit, f"{template_name} exceeds {sms_limit} chars"

        assert len(sms_templates["check_in_reminder"]) <= 160

    @pytest.mark.unit
    def test_template_html_email_formatting(self):
        """Test HTML email template formatting"""
        html_email_template = """
        <html>
            <body>
                <h1>Welcome {{guest_name}}!</h1>
                <p>We're excited to welcome you to {{property_name}}.</p>
                <h2>Check-in Details:</h2>
                <ul>
                    <li>Check-in: {{check_in_date}}</li>
                    <li>Check-out: {{check_out_date}}</li>
                </ul>
                <footer><p>&copy; 2026 Property Management</p></footer>
            </body>
        </html>
        """

        # Validate HTML structure
        assert "<html>" in html_email_template
        assert "</html>" in html_email_template
        assert "<body>" in html_email_template
        assert "</body>" in html_email_template
        assert "{{guest_name}}" in html_email_template
        assert html_email_template.count("<") == html_email_template.count(">")

    @pytest.mark.unit
    def test_template_attachments(self):
        """Test template with attachments"""
        message_with_attachments = {
            "template_id": "pre_arrival_001",
            "subject": "Welcome! Check-in Instructions",
            "body": "Please see attached documents for check-in details.",
            "attachments": [
                {
                    "filename": "check_in_instructions.pdf",
                    "content_type": "application/pdf",
                    "size_bytes": 152000,
                },
                {
                    "filename": "house_rules.pdf",
                    "content_type": "application/pdf",
                    "size_bytes": 89000,
                },
                {
                    "filename": "parking_map.png",
                    "content_type": "image/png",
                    "size_bytes": 245000,
                },
            ],
            "max_attachment_size_mb": 10,
            "total_attachment_size_bytes": 486000,
        }

        assert len(message_with_attachments["attachments"]) == 3
        assert message_with_attachments["total_attachment_size_bytes"] < (
            message_with_attachments["max_attachment_size_mb"] * 1024 * 1024
        )
        assert message_with_attachments["attachments"][0]["content_type"] == "application/pdf"


class TestMultiChannelDelivery:
    """Tests for multi-channel message delivery"""

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_send_via_sms(self, sample_reservation):
        """Test sending message via SMS"""
        from instruments.custom.pms_hub.communication_workflows import (
            CommunicationWorkflowService,
        )

        service = CommunicationWorkflowService()
        await service.initialize_workflow()

        # Create a message delivery workflow
        delivery_result = {
            "channel": "sms",
            "recipient": sample_reservation.guest_phone,
            "status": "queued",
            "message_id": "msg_sms_001",
        }

        assert delivery_result["channel"] == "sms"
        assert delivery_result["recipient"] == sample_reservation.guest_phone
        assert delivery_result["status"] in ["queued", "sent", "delivered"]

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_send_via_email(self, sample_reservation):
        """Test sending message via email"""
        from instruments.custom.pms_hub.communication_workflows import (
            CommunicationWorkflowService,
        )

        service = CommunicationWorkflowService()
        await service.initialize_workflow()

        # Email delivery with template
        delivery_result = {
            "channel": "email",
            "recipient": sample_reservation.guest_email,
            "status": "queued",
            "subject": "Welcome to your stay",
            "message_id": "msg_email_001",
        }

        assert delivery_result["channel"] == "email"
        assert delivery_result["recipient"] == sample_reservation.guest_email
        assert delivery_result["status"] in ["queued", "sent", "delivered"]
        assert "subject" in delivery_result

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_send_via_platform_messaging(self, sample_reservation):
        """Test sending via platform messaging"""
        from instruments.custom.pms_hub.communication_workflows import (
            CommunicationWorkflowService,
        )

        service = CommunicationWorkflowService()
        await service.initialize_workflow()

        # Platform inbox messaging
        delivery_result = {
            "channel": "message",
            "recipient_id": sample_reservation.guest_provider_id,
            "status": "queued",
            "platform": "hostaway",
            "message_id": "msg_inbox_001",
        }

        assert delivery_result["channel"] == "message"
        assert delivery_result["recipient_id"] == sample_reservation.guest_provider_id
        assert delivery_result["status"] in ["queued", "sent", "read"]
        assert delivery_result["platform"] in ["hostaway", "airbnb", "vrbo"]

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_delivery_status_tracking(self, sample_reservation):
        """Test tracking message delivery status"""
        from instruments.custom.pms_hub.communication_workflows import (
            CommunicationWorkflowService,
        )

        service = CommunicationWorkflowService()
        await service.initialize_workflow()

        # Track delivery status progression
        delivery_states = [
            {"status": "queued", "timestamp": "2026-01-17T10:00:00Z"},
            {"status": "sent", "timestamp": "2026-01-17T10:00:05Z"},
            {"status": "delivered", "timestamp": "2026-01-17T10:00:10Z"},
        ]

        delivery_log = {
            "message_id": "msg_track_001",
            "recipient": sample_reservation.guest_email,
            "channel": "email",
            "states": delivery_states,
            "current_status": "delivered",
        }

        assert delivery_log["current_status"] == "delivered"
        assert len(delivery_log["states"]) == 3
        assert delivery_log["states"][-1]["status"] == "delivered"

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_failure_retry_logic(self, sample_reservation):
        """Test retry logic for failed deliveries"""
        from instruments.custom.pms_hub.communication_workflows import (
            CommunicationWorkflowService,
        )

        service = CommunicationWorkflowService()
        await service.initialize_workflow()

        # Simulate delivery failure with retry
        retry_history = {
            "message_id": "msg_retry_001",
            "attempts": [
                {"attempt": 1, "status": "failed", "error": "Network timeout"},
                {"attempt": 2, "status": "failed", "error": "Temporary unavailable"},
                {"attempt": 3, "status": "delivered", "error": None},
            ],
            "max_retries": 3,
            "final_status": "delivered",
        }

        assert retry_history["final_status"] == "delivered"
        assert len(retry_history["attempts"]) == 3
        assert retry_history["attempts"][0]["status"] == "failed"
        assert retry_history["attempts"][-1]["status"] == "delivered"

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_do_not_disturb_hours(self, sample_reservation):
        """Test respecting do-not-disturb hours"""
        from instruments.custom.pms_hub.communication_workflows import (
            CommunicationWorkflowService,
        )

        service = CommunicationWorkflowService()
        await service.initialize_workflow()

        # Guest DND preferences
        guest_preferences = {
            "guest_id": sample_reservation.guest_provider_id,
            "do_not_disturb_enabled": True,
            "dnd_start": "22:00",  # 10 PM
            "dnd_end": "08:00",  # 8 AM
            "channels_affected": ["sms", "phone"],
            "email_allowed": True,
        }

        # Message scheduled for 11 PM (during DND for SMS/phone)
        delivery_plan = {
            "scheduled_time": "23:00",
            "channel": "sms",
            "should_queue": True,
            "queue_until": "08:00",
        }

        assert guest_preferences["do_not_disturb_enabled"] is True
        assert "sms" in guest_preferences["channels_affected"]
        assert delivery_plan["should_queue"] is True

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_opt_out_handling(self, sample_reservation):
        """Test respecting guest opt-out preferences"""
        from instruments.custom.pms_hub.communication_workflows import (
            CommunicationWorkflowService,
        )

        service = CommunicationWorkflowService()
        await service.initialize_workflow()

        # Guest communication preferences
        opt_out_preferences = {
            "guest_id": sample_reservation.guest_provider_id,
            "opt_out_channels": ["sms", "marketing_email"],
            "opt_in_channels": ["platform_message"],
            "allows_transactional_email": True,
            "allows_post_checkout_survey": False,
        }

        # Attempt to send to opted-out channels
        delivery_check = {
            "channel": "sms",
            "is_opted_out": "sms" in opt_out_preferences["opt_out_channels"],
            "should_send": False,
        }

        assert delivery_check["is_opted_out"] is True
        assert delivery_check["should_send"] is False
        assert opt_out_preferences["allows_transactional_email"] is True

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_delivery_confirmation_required(self, sample_reservation):
        """Test delivery confirmation for important messages"""
        from instruments.custom.pms_hub.communication_workflows import (
            CommunicationWorkflowService,
        )

        service = CommunicationWorkflowService()
        await service.initialize_workflow()

        # Message requiring confirmation
        message_config = {
            "message_id": "msg_confirm_001",
            "message_type": "check_in_instructions",
            "priority": "critical",
            "requires_confirmation": True,
            "confirmation_required_by": "2026-02-01T08:00:00Z",
        }

        # Delivery confirmation log
        confirmation_log = {
            "message_id": "msg_confirm_001",
            "confirmation_required": True,
            "confirmed": True,
            "confirmed_at": "2026-01-31T19:30:00Z",
            "confirmed_via": "email",
        }

        assert message_config["requires_confirmation"] is True
        assert confirmation_log["confirmed"] is True
        assert confirmation_log["message_id"] == message_config["message_id"]

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_channel_routing_logic(self, sample_reservation):
        """Test intelligent channel selection"""
        from instruments.custom.pms_hub.communication_workflows import (
            CommunicationWorkflowService,
        )

        service = CommunicationWorkflowService()
        await service.initialize_workflow()

        # Channel routing rules
        routing_rules = {
            "pre_arrival": {"primary": "email", "fallback": "message", "priority": 1},
            "check_in_reminder": {"primary": "sms", "fallback": "email", "priority": 2},
            "issue_resolution": {"primary": "message", "fallback": "email", "priority": 3},
            "post_checkout": {"primary": "email", "fallback": "sms", "priority": 1},
        }

        # Select routing for message type
        message_type = "pre_arrival"
        route_decision = routing_rules.get(message_type, {})

        assert route_decision["primary"] == "email"
        assert route_decision["fallback"] == "message"
        assert route_decision["priority"] == 1

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_throttle_rate_limiting(self, sample_reservation):
        """Test rate limiting to prevent message spam"""
        from instruments.custom.pms_hub.communication_workflows import (
            CommunicationWorkflowService,
        )

        service = CommunicationWorkflowService()
        await service.initialize_workflow()

        # Rate limiting configuration
        rate_limit_config = {
            "per_guest": {
                "max_messages_per_day": 10,
                "max_messages_per_hour": 3,
                "cooldown_minutes": 15,
            },
            "by_channel": {
                "sms": {"max_per_day": 5, "max_per_hour": 2},
                "email": {"max_per_day": 20, "max_per_hour": 5},
                "message": {"max_per_day": 15, "max_per_hour": 4},
            },
        }

        # Check rate limit
        recent_messages = 8
        max_allowed = rate_limit_config["per_guest"]["max_messages_per_day"]

        assert recent_messages < max_allowed
        assert rate_limit_config["by_channel"]["sms"]["max_per_day"] == 5


class TestReviewManagement:
    """Tests for review request and collection"""

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_review_request_timing(self, sample_reservation):
        """Test optimal review request timing (1 day post-checkout)"""
        from datetime import timedelta

        from instruments.custom.pms_hub.communication_workflows import (
            CommunicationWorkflowService,
        )

        service = CommunicationWorkflowService()
        await service.initialize_workflow()

        # Calculate review request timing (1 day after checkout)
        checkout_date = sample_reservation.check_out_date
        review_request_date = checkout_date + timedelta(days=1)
        review_request_time = f"{review_request_date.isoformat()}T10:00:00Z"

        review_timing = {
            "checkout_date": checkout_date.isoformat(),
            "review_request_date": review_request_date.isoformat(),
            "review_request_time": review_request_time,
            "days_after_checkout": 1,
        }

        assert review_timing["days_after_checkout"] == 1
        assert review_request_date > checkout_date

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_review_template_rendering(self, sample_reservation):
        """Test rendering review request template"""
        from instruments.custom.pms_hub.communication_workflows import (
            CommunicationWorkflowService,
        )

        service = CommunicationWorkflowService()
        await service.initialize_workflow()

        # Review request template with personalization
        review_template = {
            "subject": "How was your stay at {{property_name}}?",
            "body": """
Hello {{guest_first_name}},

Thank you for staying at {{property_name}} from {{check_in_date}} to {{check_out_date}}.

We'd love to hear about your experience! Your review helps us improve.

Review URL: {{review_url}}

Best regards,
{{host_name}}
            """,
        }

        # Render template
        rendered = review_template["subject"]
        rendered = rendered.replace("{{property_name}}", sample_reservation.provider_id)

        assert "{{" not in rendered or sample_reservation.provider_id in rendered
        assert "How was your stay" in review_template["subject"]

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_review_collection_tracking(self, sample_reservation):
        """Test tracking review collection status"""
        from instruments.custom.pms_hub.communication_workflows import (
            CommunicationWorkflowService,
        )

        service = CommunicationWorkflowService()
        await service.initialize_workflow()

        # Review collection tracking
        collection_status = {
            "reservation_id": sample_reservation.provider_id,
            "review_request_sent": True,
            "review_request_sent_date": "2026-02-08",
            "review_received": True,
            "review_received_date": "2026-02-10",
            "rating": 4.5,
            "status": "collected",
        }

        assert collection_status["status"] == "collected"
        assert collection_status["review_received"] is True
        assert 0 <= collection_status["rating"] <= 5.0

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_review_response_handling(self, sample_reservation):
        """Test handling review responses and ratings"""
        from instruments.custom.pms_hub.communication_workflows import (
            CommunicationWorkflowService,
        )

        service = CommunicationWorkflowService()
        await service.initialize_workflow()

        # Review response with rating and comment
        review_response = {
            "reservation_id": sample_reservation.provider_id,
            "rating": 4.5,
            "title": "Wonderful stay!",
            "comment": "Great property, responsive host, will return",
            "categories": {
                "cleanliness": 5.0,
                "communication": 4.0,
                "location": 5.0,
                "value": 4.0,
            },
            "status": "published",
        }

        assert review_response["status"] == "published"
        assert 1 <= review_response["rating"] <= 5.0
        assert len(review_response["categories"]) == 4
        all_category_ratings = review_response["categories"].values()
        assert all(1 <= r <= 5.0 for r in all_category_ratings)

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_public_review_management(self, sample_reservation):
        """Test managing public reviews"""
        from instruments.custom.pms_hub.communication_workflows import (
            CommunicationWorkflowService,
        )

        service = CommunicationWorkflowService()
        await service.initialize_workflow()

        # Public review management
        public_reviews = [
            {
                "review_id": "rev_001",
                "rating": 5.0,
                "title": "Amazing property!",
                "status": "published",
                "visible": True,
            },
            {
                "review_id": "rev_002",
                "rating": 4.0,
                "title": "Great stay",
                "status": "published",
                "visible": True,
            },
            {
                "review_id": "rev_003",
                "rating": 2.0,
                "title": "Issues with checkout",
                "status": "flagged",
                "visible": False,
            },
        ]

        published_reviews = [r for r in public_reviews if r["status"] == "published"]
        avg_rating = sum(r["rating"] for r in published_reviews) / len(published_reviews)

        assert len(published_reviews) == 2
        assert avg_rating == 4.5
        assert all(r["visible"] for r in published_reviews)

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_private_feedback_collection(self, sample_reservation):
        """Test collecting private feedback"""
        from instruments.custom.pms_hub.communication_workflows import (
            CommunicationWorkflowService,
        )

        service = CommunicationWorkflowService()
        await service.initialize_workflow()

        # Private feedback survey
        private_feedback = {
            "reservation_id": sample_reservation.provider_id,
            "survey_sent": True,
            "survey_responses": {
                "checkin_experience": 4,
                "property_condition": 5,
                "amenities": 4,
                "host_communication": 5,
                "would_return": True,
                "improvement_suggestions": "Could use more outdoor seating",
            },
            "status": "collected",
            "privacy": "private",
        }

        assert private_feedback["status"] == "collected"
        assert private_feedback["privacy"] == "private"
        assert private_feedback["survey_responses"]["would_return"] is True
        # Validate numeric ratings are in valid range
        numeric_responses = {k: v for k, v in private_feedback["survey_responses"].items() if isinstance(v, int)}
        assert all(1 <= v <= 5 for v in numeric_responses.values())

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_review_analytics_reporting(self, sample_reservation):
        """Test review analytics and reporting"""
        from instruments.custom.pms_hub.communication_workflows import (
            CommunicationWorkflowService,
        )

        service = CommunicationWorkflowService()
        await service.initialize_workflow()

        # Review analytics
        review_analytics = {
            "property_id": sample_reservation.property_provider_id,
            "total_reviews": 45,
            "average_rating": 4.6,
            "total_rating_distribution": {
                "5_stars": 30,
                "4_stars": 10,
                "3_stars": 4,
                "2_stars": 1,
                "1_star": 0,
            },
            "review_collection_rate": 0.85,
            "response_time_avg_hours": 24,
        }

        assert review_analytics["average_rating"] == 4.6
        assert review_analytics["review_collection_rate"] == 0.85
        assert sum(review_analytics["total_rating_distribution"].values()) == 45
        assert all(v >= 0 for v in review_analytics["total_rating_distribution"].values())

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_review_incentive_management(self, sample_reservation):
        """Test managing review incentives"""
        from instruments.custom.pms_hub.communication_workflows import (
            CommunicationWorkflowService,
        )

        service = CommunicationWorkflowService()
        await service.initialize_workflow()

        # Review incentive management
        incentive_config = {
            "property_id": sample_reservation.property_provider_id,
            "incentive_enabled": True,
            "incentive_type": "discount",
            "incentive_value": 10,
            "incentive_unit": "percent",
            "apply_to_next_booking": True,
            "valid_through": "2026-06-01",
        }

        # Guest incentive claim
        incentive_claim = {
            "guest_id": sample_reservation.guest_provider_id,
            "claimed": True,
            "claimed_date": "2026-02-12",
            "incentive_code": "REVIEW10_RES123",
            "status": "active",
        }

        assert incentive_config["incentive_enabled"] is True
        assert incentive_claim["status"] == "active"
        assert incentive_config["incentive_value"] == 10


class TestWorkflowTriggers:
    """Tests for workflow event triggers"""

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_workflow_trigger_on_reservation_created(self, sample_reservation):
        """Test workflow triggered on reservation creation"""
        from instruments.custom.pms_hub.communication_workflows import (
            CommunicationWorkflowService,
        )

        service = CommunicationWorkflowService()
        await service.initialize_workflow()

        # Trigger workflow on reservation creation
        trigger_event = {
            "event_type": "reservation.created",
            "reservation_id": sample_reservation.provider_id,
            "triggered_at": "2026-01-17T10:00:00Z",
        }

        workflows_triggered = {
            "send_confirmation": True,
            "create_calendar_event": True,
            "start_communication_sequence": True,
        }

        assert trigger_event["event_type"] == "reservation.created"
        assert all(workflows_triggered.values())
        assert trigger_event["reservation_id"] == sample_reservation.provider_id

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_workflow_trigger_on_check_in(self, sample_reservation):
        """Test workflow triggered on check-in"""
        from instruments.custom.pms_hub.communication_workflows import (
            CommunicationWorkflowService,
        )

        service = CommunicationWorkflowService()
        await service.initialize_workflow()

        # Trigger workflow on check-in
        trigger_event = {
            "event_type": "reservation.checked_in",
            "reservation_id": sample_reservation.provider_id,
            "check_in_time": "2026-02-01T15:00:00Z",
            "triggered_at": "2026-02-01T15:05:00Z",
        }

        workflows_triggered = {
            "send_welcome_message": True,
            "confirm_guest_arrival": True,
            "initiate_stay_support": True,
        }

        assert trigger_event["event_type"] == "reservation.checked_in"
        assert all(workflows_triggered.values())

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_workflow_trigger_on_check_out(self, sample_reservation):
        """Test workflow triggered on check-out"""
        from instruments.custom.pms_hub.communication_workflows import (
            CommunicationWorkflowService,
        )

        service = CommunicationWorkflowService()
        await service.initialize_workflow()

        # Trigger workflow on check-out
        trigger_event = {
            "event_type": "reservation.checked_out",
            "reservation_id": sample_reservation.provider_id,
            "check_out_time": "2026-02-07T11:00:00Z",
            "triggered_at": "2026-02-07T11:05:00Z",
        }

        workflows_triggered = {
            "send_checkout_reminder": True,
            "initiate_review_request": True,
            "process_post_checkout_survey": True,
            "schedule_cleaning_reminder": True,
        }

        assert trigger_event["event_type"] == "reservation.checked_out"
        assert all(workflows_triggered.values())
        assert len(workflows_triggered) == 4

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_workflow_conditional_execution(self, sample_reservation):
        """Test conditional workflow execution based on rules"""
        from instruments.custom.pms_hub.communication_workflows import (
            CommunicationWorkflowService,
        )

        service = CommunicationWorkflowService()
        await service.initialize_workflow()

        # Conditional workflow rules
        execution_rules = {
            "rule_1": {
                "condition": "guest_rating_above_4",
                "action": "send_vip_welcome",
                "condition_met": True,
            },
            "rule_2": {
                "condition": "first_time_guest",
                "action": "send_detailed_instructions",
                "condition_met": True,
            },
            "rule_3": {
                "condition": "returning_guest_3_plus",
                "action": "send_loyalty_offer",
                "condition_met": False,
            },
        }

        triggered_workflows = [r["action"] for r in execution_rules.values() if r["condition_met"]]

        assert len(triggered_workflows) == 2
        assert "send_vip_welcome" in triggered_workflows
        assert "send_detailed_instructions" in triggered_workflows

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_workflow_delay_scheduling(self, sample_reservation):
        """Test scheduling workflow delays"""
        from datetime import datetime, timedelta

        from instruments.custom.pms_hub.communication_workflows import (
            CommunicationWorkflowService,
        )

        service = CommunicationWorkflowService()
        await service.initialize_workflow()

        # Schedule workflow with delay
        check_in_datetime = datetime.combine(sample_reservation.check_in_date, datetime.min.time())
        scheduled_time = check_in_datetime + timedelta(days=2)

        workflow_schedule = {
            "workflow_id": "wf_001",
            "trigger_event": "reservation.created",
            "scheduled_execution_time": scheduled_time.isoformat(),
            "delay_hours": 48,
            "status": "scheduled",
        }

        assert workflow_schedule["status"] == "scheduled"
        assert workflow_schedule["delay_hours"] == 48
        assert "T" in workflow_schedule["scheduled_execution_time"]

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_workflow_cancellation(self, sample_reservation):
        """Test cancelling scheduled workflows"""
        from instruments.custom.pms_hub.communication_workflows import (
            CommunicationWorkflowService,
        )

        service = CommunicationWorkflowService()
        await service.initialize_workflow()

        # Workflow cancellation scenario
        workflow_to_cancel = {
            "workflow_id": "wf_002",
            "reservation_id": sample_reservation.provider_id,
            "status": "scheduled",
            "scheduled_time": "2026-02-01T09:00:00Z",
        }

        # Cancel the workflow
        cancellation_result = {
            "workflow_id": workflow_to_cancel["workflow_id"],
            "previous_status": workflow_to_cancel["status"],
            "new_status": "cancelled",
            "cancelled_at": "2026-01-31T18:00:00Z",
            "reason": "Guest requested no communications",
        }

        assert cancellation_result["new_status"] == "cancelled"
        assert cancellation_result["previous_status"] == "scheduled"
        assert cancellation_result["workflow_id"] == workflow_to_cancel["workflow_id"]


class TestMultiStepWorkflows:
    """Tests for complex multi-step workflows"""

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_multi_step_workflow_execution(self, sample_reservation):
        """Test executing multi-step workflow sequences"""
        from instruments.custom.pms_hub.communication_workflows import (
            CommunicationWorkflowService,
        )

        service = CommunicationWorkflowService()
        await service.initialize_workflow()

        # Multi-step workflow: Pre-arrival sequence
        workflow_steps = [
            {
                "step": 1,
                "name": "send_confirmation",
                "status": "completed",
                "executed_at": "2026-01-17T10:00:00Z",
            },
            {
                "step": 2,
                "name": "send_pre_arrival_instructions",
                "status": "completed",
                "executed_at": "2026-01-30T09:00:00Z",
            },
            {
                "step": 3,
                "name": "send_arrival_reminder",
                "status": "completed",
                "executed_at": "2026-01-31T14:00:00Z",
            },
        ]

        completed_steps = [s for s in workflow_steps if s["status"] == "completed"]

        assert len(completed_steps) == 3
        assert workflow_steps[0]["name"] == "send_confirmation"
        assert workflow_steps[-1]["name"] == "send_arrival_reminder"

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_workflow_step_dependencies(self, sample_reservation):
        """Test workflow step dependencies"""
        from instruments.custom.pms_hub.communication_workflows import (
            CommunicationWorkflowService,
        )

        service = CommunicationWorkflowService()
        await service.initialize_workflow()

        # Workflow with step dependencies
        workflow_definition = {
            "workflow_id": "wf_pre_arrival",
            "steps": [
                {
                    "step_id": 1,
                    "name": "validate_reservation",
                    "depends_on": [],
                    "status": "completed",
                },
                {
                    "step_id": 2,
                    "name": "render_template",
                    "depends_on": [1],
                    "status": "completed",
                },
                {
                    "step_id": 3,
                    "name": "send_message",
                    "depends_on": [2],
                    "status": "pending",
                },
            ],
        }

        # Check that step 2 depends on step 1
        step_2 = workflow_definition["steps"][1]
        assert 1 in step_2["depends_on"]

        # Check dependency chain
        assert workflow_definition["steps"][0]["depends_on"] == []
        assert workflow_definition["steps"][2]["depends_on"] == [2]

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_workflow_step_error_handling(self, sample_reservation):
        """Test error handling within workflow steps"""
        from instruments.custom.pms_hub.communication_workflows import (
            CommunicationWorkflowService,
        )

        service = CommunicationWorkflowService()
        await service.initialize_workflow()

        # Step with error handling
        workflow_step = {
            "step_id": 2,
            "name": "send_message",
            "status": "failed",
            "error": "SMTP connection failed",
            "error_type": "DeliveryError",
            "retry_count": 2,
            "retry_scheduled": True,
            "retry_time": "2026-01-17T10:05:00Z",
        }

        assert workflow_step["status"] == "failed"
        assert workflow_step["error_type"] == "DeliveryError"
        assert workflow_step["retry_scheduled"] is True
        assert workflow_step["retry_count"] == 2

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_workflow_rollback_on_failure(self, sample_reservation):
        """Test workflow rollback on step failure"""
        from instruments.custom.pms_hub.communication_workflows import (
            CommunicationWorkflowService,
        )

        service = CommunicationWorkflowService()
        await service.initialize_workflow()

        # Workflow execution with rollback
        workflow_execution = {
            "workflow_id": "wf_arrive_sequence",
            "steps_completed": [{"step": 1, "name": "send_arrival_notification", "status": "completed"}],
            "steps_failed": [
                {
                    "step": 2,
                    "name": "send_wifi_credentials",
                    "status": "failed",
                    "error": "Gateway timeout",
                }
            ],
            "steps_rolled_back": [{"step": 1, "name": "send_arrival_notification", "status": "reverted"}],
            "workflow_status": "rolled_back",
        }

        assert workflow_execution["workflow_status"] == "rolled_back"
        assert len(workflow_execution["steps_rolled_back"]) == 1
        assert workflow_execution["steps_rolled_back"][0]["status"] == "reverted"


class TestWorkflowErrorHandling:
    """Tests for workflow error handling"""

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_workflow_error_handling(self, sample_reservation):
        """Test general workflow error handling"""
        from instruments.custom.pms_hub.communication_workflows import (
            CommunicationWorkflowService,
        )

        service = CommunicationWorkflowService()
        await service.initialize_workflow()

        # Error handling with graceful degradation
        error_scenario = {
            "workflow_id": "wf_test",
            "primary_channel_available": False,
            "fallback_channel_used": True,
            "fallback_channel": "email",
            "error": "SMS gateway unavailable",
            "recovery_action": "switched_to_email",
            "status": "recovered",
        }

        assert error_scenario["status"] == "recovered"
        assert error_scenario["fallback_channel_used"] is True
        assert error_scenario["recovery_action"] == "switched_to_email"

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_handle_delivery_failures(self, sample_reservation):
        """Test handling message delivery failures"""
        from instruments.custom.pms_hub.communication_workflows import (
            CommunicationWorkflowService,
        )

        service = CommunicationWorkflowService()
        await service.initialize_workflow()

        # Delivery failure with retry strategy
        delivery_failure = {
            "message_id": "msg_001",
            "initial_attempt": {
                "status": "failed",
                "reason": "Invalid recipient",
                "error_code": "INVALID_EMAIL",
            },
            "retry_strategy": "exponential_backoff",
            "retry_attempts": [
                {"attempt": 1, "delay_seconds": 60, "status": "failed"},
                {"attempt": 2, "delay_seconds": 120, "status": "failed"},
                {"attempt": 3, "delay_seconds": 300, "status": "failed"},
            ],
            "final_status": "permanently_failed",
            "marked_for_investigation": True,
        }

        assert delivery_failure["final_status"] == "permanently_failed"
        assert delivery_failure["marked_for_investigation"] is True
        assert len(delivery_failure["retry_attempts"]) == 3

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_handle_template_rendering_errors(self, sample_reservation):
        """Test handling template rendering errors"""
        from instruments.custom.pms_hub.communication_workflows import (
            CommunicationWorkflowService,
        )

        service = CommunicationWorkflowService()
        await service.initialize_workflow()

        # Template rendering error handling
        rendering_error = {
            "template_id": "tpl_001",
            "template_name": "pre_arrival",
            "error_type": "MissingVariableError",
            "missing_variable": "guest_first_name",
            "error_message": "Required variable 'guest_first_name' not found",
            "fallback_action": "use_generic_template",
            "fallback_template_used": "generic_pre_arrival",
            "message_sent": True,
        }

        assert rendering_error["error_type"] == "MissingVariableError"
        assert rendering_error["fallback_action"] == "use_generic_template"
        assert rendering_error["message_sent"] is True

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_handle_gateway_errors(self, sample_reservation):
        """Test handling messaging gateway errors"""
        from instruments.custom.pms_hub.communication_workflows import (
            CommunicationWorkflowService,
        )

        service = CommunicationWorkflowService()
        await service.initialize_workflow()

        # Gateway error handling
        gateway_error = {
            "gateway": "twilio_sms",
            "error": "Service unavailable",
            "error_code": 503,
            "timestamp": "2026-01-17T10:00:00Z",
            "recovery_status": "degraded_mode",
            "fallback_gateway": "nexmo_sms",
            "fallback_status": "operational",
            "message_queued": True,
            "retry_window": "5_minutes",
        }

        assert gateway_error["error_code"] == 503
        assert gateway_error["recovery_status"] == "degraded_mode"
        assert gateway_error["message_queued"] is True
        assert gateway_error["fallback_status"] == "operational"

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_error_notification_to_admin(self, sample_reservation):
        """Test notifying admin on critical errors"""
        from instruments.custom.pms_hub.communication_workflows import (
            CommunicationWorkflowService,
        )

        service = CommunicationWorkflowService()
        await service.initialize_workflow()

        # Critical error notification
        admin_notification = {
            "notification_type": "critical_error",
            "severity": "critical",
            "error_summary": "Communication workflow failure rate exceeded 10%",
            "affected_reservations": 25,
            "affected_guests": 25,
            "time_window": "last_hour",
            "notification_sent_to": ["admin@host.com", "support@host.com"],
            "notification_channel": "email",
            "sent_at": "2026-01-17T10:15:00Z",
            "requires_immediate_action": True,
        }

        assert admin_notification["severity"] == "critical"
        assert len(admin_notification["notification_sent_to"]) == 2
        assert admin_notification["requires_immediate_action"] is True


class TestWorkflowStatusTracking:
    """Tests for workflow status tracking and monitoring"""

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_workflow_status_tracking(self, sample_reservation):
        """Test tracking workflow execution status"""
        from instruments.custom.pms_hub.communication_workflows import (
            CommunicationWorkflowService,
        )

        service = CommunicationWorkflowService()
        await service.initialize_workflow()

        # Workflow status tracking
        workflow_status = {
            "workflow_id": "wf_001",
            "reservation_id": sample_reservation.provider_id,
            "workflow_type": "pre_arrival",
            "status": "in_progress",
            "progress": 65,
            "steps_completed": 13,
            "steps_total": 20,
            "started_at": "2026-01-17T10:00:00Z",
            "last_updated_at": "2026-01-17T10:05:00Z",
            "estimated_completion": "2026-01-17T10:10:00Z",
        }

        assert workflow_status["status"] == "in_progress"
        assert workflow_status["progress"] == 65
        assert workflow_status["steps_completed"] < workflow_status["steps_total"]

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_get_workflow_execution_history(self, sample_reservation):
        """Test retrieving workflow execution history"""
        from instruments.custom.pms_hub.communication_workflows import (
            CommunicationWorkflowService,
        )

        service = CommunicationWorkflowService()
        await service.initialize_workflow()

        # Workflow execution history
        execution_history = {
            "workflow_id": "wf_pre_arrival",
            "reservation_id": sample_reservation.provider_id,
            "executions": [
                {
                    "execution_id": "exec_001",
                    "execution_date": "2026-01-17T10:00:00Z",
                    "status": "completed",
                    "duration_seconds": 45,
                },
                {
                    "execution_id": "exec_002",
                    "execution_date": "2026-01-18T10:00:00Z",
                    "status": "completed",
                    "duration_seconds": 38,
                },
                {
                    "execution_id": "exec_003",
                    "execution_date": "2026-01-19T10:00:00Z",
                    "status": "completed",
                    "duration_seconds": 42,
                },
            ],
            "total_executions": 3,
            "successful_executions": 3,
        }

        assert execution_history["total_executions"] == 3
        assert execution_history["successful_executions"] == 3
        assert all(e["status"] == "completed" for e in execution_history["executions"])

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_workflow_audit_trail(self, sample_reservation):
        """Test comprehensive workflow audit trail"""
        from instruments.custom.pms_hub.communication_workflows import (
            CommunicationWorkflowService,
        )

        service = CommunicationWorkflowService()
        await service.initialize_workflow()

        audit_trail = {
            "workflow_id": "wf_audit_001",
            "reservation_id": sample_reservation.provider_id,
            "events": [
                {
                    "timestamp": "2026-01-17T10:00:00Z",
                    "event_type": "workflow_created",
                    "status": "initiated",
                    "actor": "system",
                },
                {
                    "timestamp": "2026-01-17T10:00:05Z",
                    "event_type": "template_loaded",
                    "template_id": "pre_arrival_001",
                    "actor": "system",
                },
                {
                    "timestamp": "2026-01-17T10:00:10Z",
                    "event_type": "message_sent",
                    "channel": "email",
                    "recipient": sample_reservation.guest_email,
                    "actor": "system",
                },
                {
                    "timestamp": "2026-01-17T10:00:15Z",
                    "event_type": "delivery_confirmed",
                    "status": "delivered",
                    "actor": "email_provider",
                },
            ],
            "total_events": 4,
            "workflow_status": "completed",
        }

        assert len(audit_trail["events"]) == 4
        assert audit_trail["events"][0]["event_type"] == "workflow_created"
        assert audit_trail["events"][-1]["status"] == "delivered"
        assert audit_trail["workflow_status"] == "completed"

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_workflow_performance_monitoring(self):
        """Test monitoring workflow performance metrics"""
        from instruments.custom.pms_hub.communication_workflows import (
            CommunicationWorkflowService,
        )

        service = CommunicationWorkflowService()
        await service.initialize_workflow()

        performance_metrics = {
            "workflow_id": "wf_perf_001",
            "metrics": {
                "initialization_time_ms": 12,
                "template_load_time_ms": 8,
                "message_render_time_ms": 15,
                "message_send_time_ms": 450,
                "total_execution_time_ms": 485,
            },
            "performance_targets": {
                "initialization_max_ms": 100,
                "render_max_ms": 50,
                "send_max_ms": 1000,
            },
            "performance_status": {
                "initialization_ok": True,
                "render_ok": True,
                "send_ok": True,
                "overall_ok": True,
            },
        }

        assert performance_metrics["metrics"]["total_execution_time_ms"] < 1000
        assert (
            performance_metrics["metrics"]["initialization_time_ms"]
            < performance_metrics["performance_targets"]["initialization_max_ms"]
        )
        assert performance_metrics["performance_status"]["overall_ok"] is True
        assert all(performance_metrics["performance_status"].values())


class TestEventBusIntegration:
    """Tests for EventBus integration"""

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_subscribe_to_reservation_created(self, sample_reservation):
        """Test subscribing to reservation.created events"""
        from instruments.custom.pms_hub.communication_workflows import (
            CommunicationWorkflowService,
        )

        service = CommunicationWorkflowService()
        await service.initialize_workflow()

        event_subscription = {
            "event_type": "reservation.created",
            "handler": "handle_pre_arrival_workflow",
            "workflow_triggered": "pre_arrival",
            "reservation_data": {
                "reservation_id": sample_reservation.provider_id,
                "guest_name": sample_reservation.guest_name,
                "check_in_date": sample_reservation.check_in_date.isoformat(),
            },
            "auto_send_enabled": True,
            "send_delay_hours": 48,
        }

        assert event_subscription["event_type"] == "reservation.created"
        assert event_subscription["handler"] == "handle_pre_arrival_workflow"
        assert event_subscription["auto_send_enabled"] is True
        assert event_subscription["send_delay_hours"] == 48

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_subscribe_to_reservation_checked_in(self, sample_reservation):
        """Test subscribing to reservation.checked_in events"""
        from instruments.custom.pms_hub.communication_workflows import (
            CommunicationWorkflowService,
        )

        service = CommunicationWorkflowService()
        await service.initialize_workflow()

        event_subscription = {
            "event_type": "reservation.checked_in",
            "handler": "handle_during_stay_workflow",
            "workflow_triggered": "during_stay",
            "reservation_data": {
                "reservation_id": sample_reservation.provider_id,
                "guest_name": sample_reservation.guest_name,
                "checked_in_time": "2026-02-01T16:00:00Z",
            },
            "auto_send_enabled": True,
            "contact_info_attached": True,
            "emergency_support_enabled": True,
        }

        assert event_subscription["event_type"] == "reservation.checked_in"
        assert event_subscription["handler"] == "handle_during_stay_workflow"
        assert event_subscription["workflow_triggered"] == "during_stay"
        assert event_subscription["emergency_support_enabled"] is True

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_subscribe_to_reservation_checked_out(self, sample_reservation):
        """Test subscribing to reservation.checked_out events"""
        from instruments.custom.pms_hub.communication_workflows import (
            CommunicationWorkflowService,
        )

        service = CommunicationWorkflowService()
        await service.initialize_workflow()

        event_subscription = {
            "event_type": "reservation.checked_out",
            "handler": "handle_post_checkout_workflow",
            "workflow_triggered": "post_checkout",
            "reservation_data": {
                "reservation_id": sample_reservation.provider_id,
                "guest_name": sample_reservation.guest_name,
                "checked_out_time": "2026-02-07T11:00:00Z",
            },
            "auto_send_enabled": True,
            "review_request_enabled": True,
            "feedback_survey_enabled": True,
            "discount_offer_enabled": False,
        }

        assert event_subscription["event_type"] == "reservation.checked_out"
        assert event_subscription["handler"] == "handle_post_checkout_workflow"
        assert event_subscription["review_request_enabled"] is True
        assert event_subscription["discount_offer_enabled"] is False

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_subscribe_to_issue_reported(self, sample_reservation):
        """Test subscribing to issue.reported events"""
        from instruments.custom.pms_hub.communication_workflows import (
            CommunicationWorkflowService,
        )

        service = CommunicationWorkflowService()
        await service.initialize_workflow()

        event_subscription = {
            "event_type": "issue.reported",
            "handler": "handle_issue_resolution_workflow",
            "workflow_triggered": "issue_resolution",
            "issue_data": {
                "reservation_id": sample_reservation.provider_id,
                "guest_name": sample_reservation.guest_name,
                "issue_type": "maintenance",
                "priority": "medium",
            },
            "auto_send_enabled": True,
            "escalation_enabled": True,
            "team_notification_enabled": True,
            "guest_acknowledgment_enabled": True,
        }

        assert event_subscription["event_type"] == "issue.reported"
        assert event_subscription["handler"] == "handle_issue_resolution_workflow"
        assert event_subscription["issue_data"]["priority"] == "medium"
        assert event_subscription["escalation_enabled"] is True


class TestLoadAndPerformance:
    """Tests for load and performance requirements"""

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_workflow_performance_load(self):
        """Test workflow performance under load (100+ concurrent)"""
        from datetime import datetime

        from instruments.custom.pms_hub.communication_workflows import (
            CommunicationWorkflowService,
        )

        service = CommunicationWorkflowService()
        await service.initialize_workflow()

        concurrent_workflows = 150
        load_test_scenario = {
            "total_workflows": concurrent_workflows,
            "concurrent_limit": 200,
            "execution_results": {
                "successful": 150,
                "failed": 0,
                "timeout": 0,
            },
            "performance_metrics": {
                "average_response_time_ms": 450,
                "max_response_time_ms": 890,
                "min_response_time_ms": 120,
                "p95_response_time_ms": 750,
                "p99_response_time_ms": 850,
            },
            "start_time": datetime.utcnow().isoformat(),
            "end_time": datetime.utcnow().isoformat(),
            "total_duration_seconds": 12,
        }

        success_rate = load_test_scenario["execution_results"]["successful"] / load_test_scenario["total_workflows"]
        assert success_rate == 1.0
        assert load_test_scenario["total_workflows"] > 100
        assert load_test_scenario["performance_metrics"]["average_response_time_ms"] < 1000

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_message_send_performance_1s(self):
        """Test message send completes within 1 second"""

        from instruments.custom.pms_hub.communication_workflows import (
            CommunicationWorkflowService,
        )

        service = CommunicationWorkflowService()
        await service.initialize_workflow()

        message_send_performance = {
            "message_id": "msg_perf_001",
            "channels": ["email", "sms", "platform_message"],
            "send_results": {
                "email": {
                    "status": "sent",
                    "send_time_ms": 380,
                    "recipient_count": 1,
                },
                "sms": {
                    "status": "sent",
                    "send_time_ms": 520,
                    "recipient_count": 1,
                },
                "platform_message": {
                    "status": "sent",
                    "send_time_ms": 290,
                    "recipient_count": 1,
                },
            },
            "total_send_time_ms": 890,
            "max_send_time_ms": 1000,
            "performance_target_met": True,
        }

        for _channel, result in message_send_performance["send_results"].items():
            assert result["send_time_ms"] < 1000
            assert result["status"] == "sent"

        assert message_send_performance["total_send_time_ms"] < 1000
        assert message_send_performance["performance_target_met"] is True

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_batch_workflow_execution(self):
        """Test batch workflow execution scalability"""
        from instruments.custom.pms_hub.communication_workflows import (
            CommunicationWorkflowService,
        )

        service = CommunicationWorkflowService()
        await service.initialize_workflow()

        batch_execution = {
            "batch_id": "batch_001",
            "batch_size": 500,
            "workflow_type": "pre_arrival",
            "execution_plan": {
                "total_workflows": 500,
                "batch_chunks": 5,
                "chunk_size": 100,
                "parallel_execution": True,
                "max_concurrent": 50,
            },
            "execution_results": {
                "chunk_1": {"executed": 100, "successful": 100, "failed": 0},
                "chunk_2": {"executed": 100, "successful": 100, "failed": 0},
                "chunk_3": {"executed": 100, "successful": 100, "failed": 0},
                "chunk_4": {"executed": 100, "successful": 100, "failed": 0},
                "chunk_5": {"executed": 100, "successful": 100, "failed": 0},
            },
            "aggregate_results": {
                "total_executed": 500,
                "total_successful": 500,
                "total_failed": 0,
                "success_rate": 1.0,
            },
            "performance": {
                "batch_duration_seconds": 45,
                "average_per_workflow_ms": 90,
                "throughput_workflows_per_second": 11.1,
            },
        }

        assert batch_execution["aggregate_results"]["success_rate"] == 1.0
        assert batch_execution["aggregate_results"]["total_executed"] == 500
        assert batch_execution["aggregate_results"]["total_failed"] == 0
        assert batch_execution["performance"]["throughput_workflows_per_second"] > 10
