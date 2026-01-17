"""
Email Integration Test Suite
Tests email functionality with customer lifecycle and virtual team integration
"""

import os
import sys
from pathlib import Path

import pytest

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from instruments.custom.customer_lifecycle.lifecycle_manager import CustomerLifecycleManager
from instruments.custom.virtual_team.team_orchestrator import VirtualTeamOrchestrator
from python.helpers.email_sender import EmailSender
from python.tools.email import Email


class MockResponse:
    """Mock response for testing"""
    def __init__(self, message: str, break_loop: bool = False):
        self.message = message
        self.break_loop = break_loop


class MockEmailTool:
    """Mock email tool for testing without actual SMTP"""

    def __init__(self):
        self.sent_emails = []

    async def execute(self, **kwargs):
        """Mock execute that records email instead of sending"""
        self.sent_emails.append(kwargs)

        if kwargs.get("action") == "send":
            return MockResponse(
                message=f"✅ Mock email sent to {kwargs.get('to')}",
                break_loop=False
            )
        elif kwargs.get("action") == "read":
            return MockResponse(
                message="📧 Found 0 message(s) (mock)",
                break_loop=False
            )
        else:
            return MockResponse(
                message=f"Mock executed: {kwargs.get('action')}",
                break_loop=False
            )

    def get_sent_count(self):
        """Get number of emails sent"""
        return len(self.sent_emails)

    def get_last_email(self):
        """Get last sent email details"""
        return self.sent_emails[-1] if self.sent_emails else None


class TestEmailSender:
    """Test EmailSender helper class"""

    def test_email_validation(self):
        """Test email address validation"""
        assert EmailSender.validate_email("user@example.com")
        assert EmailSender.validate_email("test.user+tag@domain.co.uk")
        assert not EmailSender.validate_email("invalid@")
        assert not EmailSender.validate_email("@example.com")
        assert not EmailSender.validate_email("notanemail")
        assert not EmailSender.validate_email("")

    def test_filename_sanitization(self):
        """Test attachment filename sanitization"""
        assert EmailSender.sanitize_filename("normal.pdf") == "normal.pdf"
        assert EmailSender.sanitize_filename("../../../etc/passwd") == "etc_passwd"
        assert EmailSender.sanitize_filename("file with spaces.txt") == "file with spaces.txt"
        assert EmailSender.sanitize_filename("special!@#$%.doc") == "special.doc"

    @pytest.mark.asyncio
    async def test_email_sender_initialization(self):
        """Test EmailSender initialization"""
        sender = EmailSender(
            server="smtp.gmail.com",
            port=587,
            username="test@example.com",
            password="test_password",
            use_tls=True
        )

        assert sender.server == "smtp.gmail.com"
        assert sender.port == 587
        assert sender.username == "test@example.com"


class TestEmailTool:
    """Test Email tool wrapper"""

    @pytest.mark.asyncio
    async def test_email_tool_send_validation(self):
        """Test email tool send validation (without actual sending)"""
        # This test validates the tool structure without requiring credentials
        tool = Email(
            agent=None,
            name="email",
            method=None,
            args={
                "action": "send",
                "to": "test@example.com",
                "subject": "Test",
                "body": "Test message"
            },
            message="",
            loop_data=None
        )

        # Verify tool has expected methods
        assert hasattr(tool, 'execute')
        assert hasattr(tool, '_send_email')
        assert hasattr(tool, '_read_emails')
        assert hasattr(tool, '_search_emails')
        assert hasattr(tool, '_send_bulk_emails')


class TestCustomerLifecycleEmailIntegration:
    """Test customer lifecycle email automation"""

    def setup_method(self):
        """Setup test database and manager"""
        self.db_path = "data/test_lifecycle_email.db"
        # Clean up any existing test database
        if os.path.exists(self.db_path):
            os.remove(self.db_path)

        self.manager = CustomerLifecycleManager(self.db_path)
        self.mock_email = MockEmailTool()

    def teardown_method(self):
        """Clean up test database"""
        if os.path.exists(self.db_path):
            os.remove(self.db_path)

    @pytest.mark.asyncio
    async def test_welcome_email(self):
        """Test automated welcome email"""
        # Create customer
        result = self.manager.capture_lead(
            name="John Doe",
            company="Acme Corp",
            email="john@acmecorp.com",
            source="website"
        )

        customer_id = result['customer_id']

        # Send welcome email
        await self.manager.send_welcome_email(
            customer_id=customer_id,
            email_tool=self.mock_email
        )

        # Verify email was "sent"
        assert self.mock_email.get_sent_count() == 1

        last_email = self.mock_email.get_last_email()
        assert last_email['action'] == 'send'
        assert last_email['to'] == 'john@acmecorp.com'
        assert 'Welcome' in last_email['subject']
        assert 'John Doe' in last_email['body']

    @pytest.mark.asyncio
    async def test_proposal_email(self):
        """Test proposal email automation"""
        # Create complete customer workflow
        customer = self.manager.capture_lead(
            name="Jane Smith",
            company="TechStart Inc",
            email="jane@techstart.com"
        )

        # Create requirements
        req = self.manager.conduct_requirements_interview(
            customer_id=customer['customer_id'],
            responses={"pain_points": "Manual processes", "budget": "50000"}
        )

        # Design solution
        solution = self.manager.design_solution(
            customer_id=customer['customer_id'],
            requirement_id=req['requirement_id']
        )

        # Generate proposal
        proposal = self.manager.generate_proposal(
            customer_id=customer['customer_id'],
            solution_id=solution['solution_id']
        )

        # Send proposal email
        await self.manager.send_proposal_email(
            proposal_id=proposal['proposal_id'],
            email_tool=self.mock_email,
            attachment_path="tmp/proposals/techstart_proposal.pdf"
        )

        # Verify email
        assert self.mock_email.get_sent_count() == 1

        last_email = self.mock_email.get_last_email()
        assert last_email['to'] == 'jane@techstart.com'
        assert 'Proposal' in last_email['subject']
        assert 'TechStart Inc' in last_email['body']
        assert last_email['attachments'] == ["tmp/proposals/techstart_proposal.pdf"]

    @pytest.mark.asyncio
    async def test_proposal_followup(self):
        """Test automated proposal follow-up"""
        # Create customer with proposal
        customer = self.manager.capture_lead(
            name="Bob Johnson",
            email="bob@example.com"
        )

        self.manager.conduct_requirements_interview(
            customer_id=customer['customer_id'],
            responses={"needs": "AI automation"}
        )

        self.manager.design_solution(
            customer_id=customer['customer_id']
        )

        proposal = self.manager.generate_proposal(
            customer_id=customer['customer_id']
        )

        # Mark as sent first
        self.manager.db.update_proposal_status(proposal['proposal_id'], "sent")

        # Send follow-up
        await self.manager.send_proposal_followup(
            proposal_id=proposal['proposal_id'],
            email_tool=self.mock_email
        )

        # Verify
        assert self.mock_email.get_sent_count() == 1

        last_email = self.mock_email.get_last_email()
        assert 'follow' in last_email['subject'].lower()
        assert last_email['to'] == 'bob@example.com'


class TestVirtualTeamEmailIntegration:
    """Test virtual team email notifications"""

    def setup_method(self):
        """Setup test database and orchestrator"""
        self.db_path = "data/test_virtual_team_email.db"
        if os.path.exists(self.db_path):
            os.remove(self.db_path)

        self.orchestrator = VirtualTeamOrchestrator(self.db_path)
        self.mock_email = MockEmailTool()

    def teardown_method(self):
        """Clean up test database"""
        if os.path.exists(self.db_path):
            os.remove(self.db_path)

    @pytest.mark.asyncio
    async def test_task_assignment_notification(self):
        """Test task assignment email notification"""
        # Create project and task
        project_id = self.orchestrator.create_project(
            project_name="AI Dashboard",
            description="Build analytics dashboard",
            workflow_template="full_stack_development"
        )

        # Get architect agent
        agents = self.orchestrator.db.list_agents()
        architect = next((a for a in agents if a['agent_role'] == 'architect'), None)

        # Create task
        task_id = self.orchestrator.db.create_task(
            task_name="Design system architecture",
            task_type="architecture_design",
            assigned_to=architect['agent_id'],
            priority="high",
            description="Create scalable architecture for dashboard",
            project_id=project_id['project_id']
        )

        # Send notification
        await self.orchestrator.send_task_assignment_notification(
            task_id=task_id,
            email_tool=self.mock_email,
            stakeholder_email="manager@company.com"
        )

        # Verify
        assert self.mock_email.get_sent_count() == 1

        last_email = self.mock_email.get_last_email()
        assert last_email['action'] == 'send'
        assert last_email['to'] == 'manager@company.com'
        assert 'Task Assignment' in last_email['subject']
        assert last_email['html']
        assert 'Design system architecture' in last_email['body']
        assert 'HIGH' in last_email['body']

    @pytest.mark.asyncio
    async def test_daily_digest(self):
        """Test daily digest email"""
        # Create some project activity
        self.orchestrator.create_project(
            project_name="API Service",
            workflow_template="api_development"
        )

        # Send digest
        await self.orchestrator.send_daily_digest(
            email_tool=self.mock_email,
            recipient="stakeholder@company.com"
        )

        # Verify
        assert self.mock_email.get_sent_count() == 1

        last_email = self.mock_email.get_last_email()
        assert 'Daily Digest' in last_email['subject']
        assert last_email['to'] == 'stakeholder@company.com'
        assert last_email['html']
        assert 'Active Projects' in last_email['body']

    @pytest.mark.asyncio
    async def test_project_status_update(self):
        """Test project status update email"""
        # Create project with tasks
        project = self.orchestrator.create_project(
            project_name="Mobile App",
            description="iOS and Android app",
            workflow_template="full_stack_development"
        )

        # Send status update
        await self.orchestrator.send_project_status_update(
            project_id=project['project_id'],
            email_tool=self.mock_email,
            recipients=["client@company.com", "manager@company.com"]
        )

        # Verify
        assert self.mock_email.get_sent_count() == 1

        last_email = self.mock_email.get_last_email()
        assert 'Project Update' in last_email['subject']
        assert last_email['to'] == ["client@company.com", "manager@company.com"]
        assert 'Mobile App' in last_email['body']
        assert 'Progress' in last_email['body']


class TestEndToEndWorkflow:
    """Test complete email-enabled workflows"""

    def setup_method(self):
        """Setup databases"""
        self.lifecycle_db = "data/test_e2e_lifecycle.db"
        self.team_db = "data/test_e2e_team.db"

        for db_path in [self.lifecycle_db, self.team_db]:
            if os.path.exists(db_path):
                os.remove(db_path)

        self.lifecycle = CustomerLifecycleManager(self.lifecycle_db)
        self.team = VirtualTeamOrchestrator(self.team_db)
        self.mock_email = MockEmailTool()

    def teardown_method(self):
        """Cleanup"""
        for db_path in [self.lifecycle_db, self.team_db]:
            if os.path.exists(db_path):
                os.remove(db_path)

    @pytest.mark.asyncio
    async def test_complete_customer_journey_with_emails(self):
        """Test complete customer journey with email automation"""
        # 1. Capture lead and send welcome email
        customer = self.lifecycle.capture_lead(
            name="Sarah Williams",
            company="DataCo",
            email="sarah@dataco.com",
            industry="finance"
        )

        await self.lifecycle.send_welcome_email(
            customer_id=customer['customer_id'],
            email_tool=self.mock_email
        )

        assert self.mock_email.get_sent_count() == 1

        # 2. Conduct interview
        self.lifecycle.conduct_requirements_interview(
            customer_id=customer['customer_id'],
            responses={
                "pain_points": "Manual data processing",
                "budget": "100000",
                "timeline": "3 months"
            }
        )

        # 3. Design solution
        self.lifecycle.design_solution(
            customer_id=customer['customer_id']
        )

        # 4. Generate and send proposal
        proposal = self.lifecycle.generate_proposal(
            customer_id=customer['customer_id']
        )

        await self.lifecycle.send_proposal_email(
            proposal_id=proposal['proposal_id'],
            email_tool=self.mock_email
        )

        assert self.mock_email.get_sent_count() == 2

        # 5. Create virtual team project for delivery
        project = self.team.create_project(
            project_name="DataCo AI Platform",
            description="Automated data processing system",
            workflow_template="full_stack_development"
        )

        # 6. Send project kickoff notification
        await self.team.send_project_status_update(
            project_id=project['project_id'],
            email_tool=self.mock_email,
            recipients=["sarah@dataco.com"]
        )

        assert self.mock_email.get_sent_count() == 3

        # Verify all emails
        emails = self.mock_email.sent_emails

        # Email 1: Welcome
        assert 'Welcome' in emails[0]['subject']

        # Email 2: Proposal
        assert 'Proposal' in emails[1]['subject']
        assert emails[1]['to'] == 'sarah@dataco.com'

        # Email 3: Project kickoff
        assert 'Project Update' in emails[2]['subject']


if __name__ == "__main__":
    # Run tests
    pytest.main([__file__, "-v", "--tb=short"])
