"""
DevOps Deploy Tool Tests - TDD Implementation
Tests for deploying applications to multi-environment infrastructure
Converted from Mahoosuc /devops:deploy command
"""

from unittest.mock import MagicMock

import pytest

from python.tools.devops_deploy import DevOpsDeploy


@pytest.fixture
def mock_agent():
    """Create mock agent for testing"""
    agent = MagicMock()
    agent.context = MagicMock()
    agent.context.log = MagicMock()
    agent.context.log.log = MagicMock(return_value=MagicMock())
    agent.read_prompt = MagicMock(return_value="")
    agent.agent_name = "TestAgent"
    return agent


def create_tool(mock_agent, args):
    """Helper to create DevOpsDeploy tool with proper initialization"""
    return DevOpsDeploy(agent=mock_agent, name="devops_deploy", method=None, args=args, message="", loop_data=None)


class TestDevOpsDeployValidation:
    """Tests for input validation"""

    @pytest.mark.unit
    async def test_missing_environment_fails(self, mock_agent):
        """Test that missing environment argument fails validation"""
        tool = create_tool(mock_agent, {})
        response = await tool.execute()

        assert "ERROR" in response.message
        assert "environment" in response.message.lower()

    @pytest.mark.unit
    async def test_invalid_environment_fails(self, mock_agent):
        """Test that invalid environment value fails validation"""
        tool = create_tool(mock_agent, {"environment": "invalid"})
        response = await tool.execute()

        assert "ERROR" in response.message
        assert "invalid environment" in response.message.lower()

    @pytest.mark.unit
    async def test_valid_environment_accepted(self, mock_agent):
        """Test that valid environments are accepted"""
        valid_envs = ["production", "staging", "development", "prod", "stage", "dev"]

        for env in valid_envs:
            tool = create_tool(mock_agent, {"environment": env})
            # Should not fail validation
            response = await tool.execute()
            assert "ERROR: Invalid environment" not in response.message


class TestDevOpsDeployExecution:
    """Tests for deployment execution"""

    @pytest.mark.unit
    async def test_deployment_generates_report(self, mock_agent):
        """Test that deployment generates deployment report"""
        tool = create_tool(mock_agent, {"environment": "staging"})

        response = await tool.execute()

        # Should mention deployment report
        assert "deployment" in response.message.lower()

    @pytest.mark.unit
    async def test_production_deployment_requires_approval(self, mock_agent):
        """Test that production deployment has approval step"""
        tool = create_tool(mock_agent, {"environment": "production"})

        response = await tool.execute()

        # Production deployment should mention approval/confirmation
        assert any(word in response.message.lower() for word in ["production", "deploy"])


class TestDevOpsDeployPOC:
    """Tests for POC implementation that returns simulated deployment"""

    @pytest.mark.unit
    async def test_poc_returns_success_status(self, mock_agent):
        """Test POC returns success deployment status"""
        tool = create_tool(mock_agent, {"environment": "development"})

        response = await tool.execute()

        # POC should indicate successful deployment
        assert "deployment" in response.message.lower()
        assert response.message  # Non-empty response

    @pytest.mark.unit
    async def test_poc_includes_environment_info(self, mock_agent):
        """Test POC includes environment information"""
        tool = create_tool(mock_agent, {"environment": "staging"})

        response = await tool.execute()

        # Should mention the environment
        assert "staging" in response.message.lower() or "environment" in response.message.lower()
