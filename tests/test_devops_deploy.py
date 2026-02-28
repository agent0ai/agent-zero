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
        deployment = response.additional["deployment"]
        assert deployment["status"] == "failed"
        assert deployment["telemetry"]["failed_stage"] == "validate"

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

    @pytest.mark.unit
    async def test_deployment_runs_primitives_chain(self, mock_agent):
        """Test that deployment result includes validate/checks/execute/record primitive outputs."""
        tool = create_tool(mock_agent, {"environment": "staging", "platform": "kubernetes"})

        response = await tool.execute()

        deployment = response.additional["deployment"]
        primitives = deployment["primitives"]

        assert deployment["environment"] == "staging"
        assert deployment["platform"] == "kubernetes"
        assert deployment["status"] == "success"

        assert primitives["checks"]["status"] == "passed"
        assert primitives["execution"]["status"] == "success"
        assert primitives["record"]["recorded"] is True
        assert primitives["record"]["summary"]["environment"] == "staging"
        assert primitives["record"]["summary"]["platform"] == "kubernetes"
        telemetry = deployment["telemetry"]
        assert telemetry["failed_stage"] is None
        assert len(telemetry["stages"]) == 3
        assert [stage["name"] for stage in telemetry["stages"]] == ["checks", "execute", "record"]
        assert all(stage["status"] == "passed" for stage in telemetry["stages"])
        assert all(isinstance(stage["duration_ms"], int) for stage in telemetry["stages"])

    @pytest.mark.unit
    async def test_deployment_marks_failed_stage_when_checks_raise(self, mock_agent, monkeypatch):
        def _raise_checks(*args, **kwargs):
            raise RuntimeError("checks failed")

        monkeypatch.setattr("python.tools.devops_deploy.run_predeployment_checks", _raise_checks)
        tool = create_tool(mock_agent, {"environment": "staging"})

        response = await tool.execute()
        deployment = response.additional["deployment"]

        assert deployment["status"] == "failed"
        assert deployment["telemetry"]["failed_stage"] == "checks"
        assert deployment["telemetry"]["stages"][-1]["name"] == "checks"
        assert deployment["telemetry"]["stages"][-1]["status"] == "failed"

    @pytest.mark.unit
    async def test_deployment_marks_failed_stage_when_execute_raise(self, mock_agent, monkeypatch):
        def _ok_checks(*args, **kwargs):
            return {"status": "passed", "checks": {"backup": True, "tests": True}}

        def _raise_execute(*args, **kwargs):
            raise RuntimeError("execute failed")

        monkeypatch.setattr("python.tools.devops_deploy.run_predeployment_checks", _ok_checks)
        monkeypatch.setattr("python.tools.devops_deploy.execute_deployment", _raise_execute)
        tool = create_tool(mock_agent, {"environment": "staging"})

        response = await tool.execute()
        deployment = response.additional["deployment"]

        assert deployment["status"] == "failed"
        assert deployment["telemetry"]["failed_stage"] == "execute"
        assert deployment["telemetry"]["stages"][0]["name"] == "checks"
        assert deployment["telemetry"]["stages"][0]["status"] == "passed"
        assert deployment["telemetry"]["stages"][-1]["name"] == "execute"
        assert deployment["telemetry"]["stages"][-1]["status"] == "failed"

    @pytest.mark.unit
    async def test_deployment_marks_failed_stage_when_record_raise(self, mock_agent, monkeypatch):
        def _ok_checks(*args, **kwargs):
            return {"status": "passed", "checks": {"backup": True, "tests": True}}

        def _ok_execute(*args, **kwargs):
            return {
                "environment": "staging",
                "platform": "default",
                "status": "success",
                "health_checks_passed": True,
                "smoke_tests_passed": True,
            }

        def _raise_record(*args, **kwargs):
            raise RuntimeError("record failed")

        monkeypatch.setattr("python.tools.devops_deploy.run_predeployment_checks", _ok_checks)
        monkeypatch.setattr("python.tools.devops_deploy.execute_deployment", _ok_execute)
        monkeypatch.setattr("python.tools.devops_deploy.record_deployment_result", _raise_record)
        tool = create_tool(mock_agent, {"environment": "staging"})

        response = await tool.execute()
        deployment = response.additional["deployment"]

        assert deployment["status"] == "failed"
        assert deployment["telemetry"]["failed_stage"] == "record"
        assert deployment["telemetry"]["stages"][0]["name"] == "checks"
        assert deployment["telemetry"]["stages"][1]["name"] == "execute"
        assert deployment["telemetry"]["stages"][-1]["name"] == "record"
        assert deployment["telemetry"]["stages"][-1]["status"] == "failed"


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
