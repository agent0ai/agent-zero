"""
DevOps Monitor Tool Tests - TDD Implementation
Tests for comprehensive infrastructure monitoring with dashboards and alerts
Converted from Mahoosuc /devops:monitor command
"""

from unittest.mock import MagicMock

import pytest

from python.helpers.tool import Response
from python.tools.devops_monitor import DevOpsMonitor


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
    """Helper to create DevOpsMonitor tool with proper initialization"""
    return DevOpsMonitor(
        agent=mock_agent,
        name="devops_monitor",
        method=None,
        args=args,
        message="",
        loop_data=None
    )


class TestDevOpsMonitorInstantiation:
    """Tests for tool instantiation"""

    @pytest.mark.unit
    def test_tool_can_be_instantiated(self, mock_agent):
        """Test that DevOpsMonitor tool can be instantiated"""
        tool = create_tool(mock_agent, {})
        assert tool is not None
        assert isinstance(tool, DevOpsMonitor)


class TestDevOpsMonitorValidation:
    """Tests for input validation"""

    @pytest.mark.unit
    async def test_default_environment_is_production(self, mock_agent):
        """Test that default environment is production when not specified"""
        tool = create_tool(mock_agent, {})
        response = await tool.execute()

        # Should use production as default
        assert isinstance(response, Response)
        assert "production" in response.message.lower()

    @pytest.mark.unit
    async def test_valid_environments_accepted(self, mock_agent):
        """Test that valid environment values are accepted"""
        valid_envs = ["production", "staging", "development", "all"]

        for env in valid_envs:
            tool = create_tool(mock_agent, {"environment": env})
            response = await tool.execute()

            assert isinstance(response, Response)
            assert "ERROR" not in response.message

    @pytest.mark.unit
    async def test_invalid_environment_fails(self, mock_agent):
        """Test that invalid environment value fails validation"""
        tool = create_tool(mock_agent, {"environment": "invalid"})
        response = await tool.execute()

        assert isinstance(response, Response)
        assert "ERROR" in response.message or "error" in response.message.lower()

    @pytest.mark.unit
    async def test_valid_platforms_accepted(self, mock_agent):
        """Test that valid platform values are accepted"""
        valid_platforms = ["grafana", "datadog", "cloudwatch"]

        for platform in valid_platforms:
            tool = create_tool(mock_agent, {"platform": platform})
            response = await tool.execute()

            assert isinstance(response, Response)
            assert platform in response.message.lower()

    @pytest.mark.unit
    async def test_invalid_platform_fails(self, mock_agent):
        """Test that invalid platform value fails validation"""
        tool = create_tool(mock_agent, {"platform": "invalid"})
        response = await tool.execute()

        assert isinstance(response, Response)
        assert "ERROR" in response.message or "error" in response.message.lower()


class TestDevOpsMonitorExecution:
    """Tests for monitoring setup execution"""

    @pytest.mark.unit
    async def test_monitor_generates_report(self, mock_agent):
        """Test that monitoring setup generates comprehensive report"""
        tool = create_tool(mock_agent, {"environment": "production", "platform": "grafana"})
        response = await tool.execute()

        assert isinstance(response, Response)
        assert "monitoring" in response.message.lower()
        assert response.break_loop is False

    @pytest.mark.unit
    async def test_monitor_includes_environment_info(self, mock_agent):
        """Test that report includes environment information"""
        tool = create_tool(mock_agent, {"environment": "staging", "platform": "datadog"})
        response = await tool.execute()

        assert isinstance(response, Response)
        assert "staging" in response.message.lower()
        assert "datadog" in response.message.lower()

    @pytest.mark.unit
    async def test_monitor_includes_metrics_info(self, mock_agent):
        """Test that report includes metrics collection info"""
        tool = create_tool(mock_agent, {"environment": "production", "platform": "grafana"})
        response = await tool.execute()

        assert isinstance(response, Response)
        # Should mention metrics collection
        assert any(word in response.message.lower() for word in ["metrics", "cpu", "memory", "monitoring"])

    @pytest.mark.unit
    async def test_monitor_includes_dashboard_info(self, mock_agent):
        """Test that report includes dashboard information"""
        tool = create_tool(mock_agent, {"environment": "production", "platform": "grafana"})
        response = await tool.execute()

        assert isinstance(response, Response)
        assert "dashboard" in response.message.lower()

    @pytest.mark.unit
    async def test_monitor_includes_alert_info(self, mock_agent):
        """Test that report includes alert configuration info"""
        tool = create_tool(mock_agent, {"environment": "production", "platform": "grafana"})
        response = await tool.execute()

        assert isinstance(response, Response)
        assert "alert" in response.message.lower()


class TestDevOpsMonitorPlatforms:
    """Tests for platform-specific monitoring setup"""

    @pytest.mark.unit
    async def test_grafana_setup_details(self, mock_agent):
        """Test that Grafana setup includes platform-specific details"""
        tool = create_tool(mock_agent, {"environment": "production", "platform": "grafana"})
        response = await tool.execute()

        assert isinstance(response, Response)
        assert "grafana" in response.message.lower()
        # Should mention Prometheus or dashboards
        assert any(word in response.message.lower() for word in ["prometheus", "dashboard"])

    @pytest.mark.unit
    async def test_datadog_setup_details(self, mock_agent):
        """Test that Datadog setup includes platform-specific details"""
        tool = create_tool(mock_agent, {"environment": "production", "platform": "datadog"})
        response = await tool.execute()

        assert isinstance(response, Response)
        assert "datadog" in response.message.lower()
        # Should mention agent installation or configuration
        assert any(word in response.message.lower() for word in ["agent", "dashboard", "monitoring"])

    @pytest.mark.unit
    async def test_cloudwatch_setup_details(self, mock_agent):
        """Test that CloudWatch setup includes platform-specific details"""
        tool = create_tool(mock_agent, {"environment": "production", "platform": "cloudwatch"})
        response = await tool.execute()

        assert isinstance(response, Response)
        assert "cloudwatch" in response.message.lower()
        # Should mention AWS-specific features
        assert any(word in response.message.lower() for word in ["aws", "alarm", "dashboard"])
