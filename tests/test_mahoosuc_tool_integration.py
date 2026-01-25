"""
Integration tests for all converted Mahoosuc tools

Validates that all 5 converted tools work together and follow consistent patterns
"""

from unittest.mock import MagicMock

import pytest

from python.helpers.tool import Response


@pytest.fixture
def mock_agent():
    """Create mock agent for all tests"""
    agent = MagicMock()
    agent.agent_name = "integration-test-agent"
    agent.context = MagicMock()
    agent.context.log = MagicMock()
    agent.context.log.log = MagicMock(return_value=MagicMock())
    agent.hist_add_tool_result = MagicMock()
    return agent


@pytest.mark.asyncio
async def test_all_tools_importable():
    """Test that all 5 converted tools can be imported"""
    from python.tools.analytics_roi_calculator import AnalyticsROICalculator
    from python.tools.api_design import APIDesign
    from python.tools.auth_test import AuthTest
    from python.tools.code_review import CodeReview
    from python.tools.devops_deploy import DevOpsDeploy

    # All imports successful
    assert DevOpsDeploy is not None
    assert AuthTest is not None
    assert APIDesign is not None
    assert AnalyticsROICalculator is not None
    assert CodeReview is not None


@pytest.mark.asyncio
async def test_all_tools_instantiable(mock_agent):
    """Test that all tools can be instantiated with minimal args"""
    from python.tools.analytics_roi_calculator import AnalyticsROICalculator
    from python.tools.api_design import APIDesign
    from python.tools.auth_test import AuthTest
    from python.tools.code_review import CodeReview
    from python.tools.devops_deploy import DevOpsDeploy

    tools = [
        DevOpsDeploy(mock_agent, "devops_deploy", None, {}, "", None),
        AuthTest(mock_agent, "auth_test", None, {}, "", None),
        APIDesign(mock_agent, "api_design", None, {}, "", None),
        AnalyticsROICalculator(mock_agent, "analytics_roi_calculator", None, {}, "", None),
        CodeReview(mock_agent, "code_review", None, {}, "", None),
    ]

    for tool in tools:
        assert tool is not None
        assert hasattr(tool, "execute")


@pytest.mark.asyncio
async def test_all_tools_return_response_objects(mock_agent):
    """Test that all tools return Response objects"""
    from python.tools.analytics_roi_calculator import AnalyticsROICalculator
    from python.tools.api_design import APIDesign
    from python.tools.auth_test import AuthTest
    from python.tools.code_review import CodeReview
    from python.tools.devops_deploy import DevOpsDeploy

    # Create tool instances with valid minimal args
    deploy = DevOpsDeploy(mock_agent, "devops_deploy", None, {"environment": "staging"}, "", None)
    auth = AuthTest(mock_agent, "auth_test", None, {"endpoint": "login"}, "", None)
    api = APIDesign(mock_agent, "api_design", None, {"resource": "users"}, "", None)
    roi = AnalyticsROICalculator(mock_agent, "roi", None, {"investment": "1000", "revenue": "1500"}, "", None)
    review = CodeReview(mock_agent, "code_review", None, {"file": "test.py"}, "", None)

    # Execute all tools
    responses = [
        await deploy.execute(),
        await auth.execute(),
        await api.execute(),
        await roi.execute(),
        await review.execute(),
    ]

    # All should return Response objects
    for response in responses:
        assert isinstance(response, Response)
        assert hasattr(response, "message")
        assert hasattr(response, "break_loop")


@pytest.mark.asyncio
async def test_workflow_devops_to_testing(mock_agent):
    """Test workflow: deploy → auth test → code review"""
    from python.tools.auth_test import AuthTest
    from python.tools.code_review import CodeReview
    from python.tools.devops_deploy import DevOpsDeploy

    # Step 1: Deploy to staging
    deploy = DevOpsDeploy(mock_agent, "devops_deploy", None, {"environment": "staging"}, "", None)
    deploy_result = await deploy.execute()
    assert "staging" in deploy_result.message.lower()

    # Step 2: Test authentication
    auth = AuthTest(mock_agent, "auth_test", None, {"endpoint": "all"}, "", None)
    auth_result = await auth.execute()
    assert "test" in auth_result.message.lower()

    # Step 3: Review deployment code
    review = CodeReview(mock_agent, "code_review", None, {"file": "deploy.py", "focus": "security"}, "", None)
    review_result = await review.execute()
    assert "security" in review_result.message.lower()


@pytest.mark.asyncio
async def test_workflow_api_design_to_roi(mock_agent):
    """Test workflow: design API → calculate ROI"""
    from python.tools.analytics_roi_calculator import AnalyticsROICalculator
    from python.tools.api_design import APIDesign

    # Step 1: Design API
    api = APIDesign(mock_agent, "api_design", None, {"resource": "subscriptions", "format": "rest"}, "", None)
    api_result = await api.execute()
    assert "subscription" in api_result.message.lower()

    # Step 2: Calculate ROI for API project
    roi = AnalyticsROICalculator(
        mock_agent, "roi", None, {"investment": "100000", "revenue": "250000", "period": "12"}, "", None
    )
    roi_result = await roi.execute()
    assert "150" in roi_result.message  # 150% ROI


@pytest.mark.asyncio
async def test_all_tools_handle_errors_gracefully(mock_agent):
    """Test that all tools handle invalid inputs gracefully"""
    from python.tools.analytics_roi_calculator import AnalyticsROICalculator
    from python.tools.api_design import APIDesign
    from python.tools.auth_test import AuthTest
    from python.tools.code_review import CodeReview
    from python.tools.devops_deploy import DevOpsDeploy

    # All with intentionally invalid args
    tools_with_invalid_args = [
        DevOpsDeploy(mock_agent, "deploy", None, {"environment": "invalid"}, "", None),
        AuthTest(mock_agent, "auth", None, {"endpoint": "invalid"}, "", None),
        APIDesign(mock_agent, "api", None, {}, "", None),  # Missing required resource
        AnalyticsROICalculator(mock_agent, "roi", None, {}, "", None),  # Missing required params
        CodeReview(mock_agent, "review", None, {}, "", None),  # Missing required file/diff
    ]

    for tool in tools_with_invalid_args:
        response = await tool.execute()
        # Should return error message, not raise exception
        assert isinstance(response, Response)
        assert response.break_loop is False
        # Error message should contain helpful text
        assert len(response.message) > 0


@pytest.mark.asyncio
async def test_all_tools_have_correct_signatures(mock_agent):
    """Test that all tools have the correct method signatures"""
    import inspect

    from python.tools.analytics_roi_calculator import AnalyticsROICalculator
    from python.tools.api_design import APIDesign
    from python.tools.auth_test import AuthTest
    from python.tools.code_review import CodeReview
    from python.tools.devops_deploy import DevOpsDeploy

    tools = [
        DevOpsDeploy(mock_agent, "devops_deploy", None, {}, "", None),
        AuthTest(mock_agent, "auth_test", None, {}, "", None),
        APIDesign(mock_agent, "api_design", None, {}, "", None),
        AnalyticsROICalculator(mock_agent, "analytics_roi_calculator", None, {}, "", None),
        CodeReview(mock_agent, "code_review", None, {}, "", None),
    ]

    for tool in tools:
        # Check execute method exists and is async
        assert hasattr(tool, "execute")
        assert inspect.iscoroutinefunction(tool.execute)


@pytest.mark.asyncio
async def test_tools_interoperability_shared_context(mock_agent):
    """Test that tools can share context through the agent"""
    from python.tools.code_review import CodeReview
    from python.tools.devops_deploy import DevOpsDeploy

    # Simulate deployment creating context
    deploy = DevOpsDeploy(mock_agent, "devops_deploy", None, {"environment": "production"}, "", None)
    deploy_result = await deploy.execute()
    assert deploy_result is not None

    # Code review can access same agent context
    review = CodeReview(mock_agent, "code_review", None, {"file": "deploy.py"}, "", None)
    review_result = await review.execute()
    assert review_result is not None

    # Both tools used same mock agent
    assert deploy.agent == review.agent


@pytest.mark.asyncio
async def test_error_handling_consistency(mock_agent):
    """Test that all tools handle errors consistently"""
    from python.tools.analytics_roi_calculator import AnalyticsROICalculator
    from python.tools.api_design import APIDesign
    from python.tools.auth_test import AuthTest
    from python.tools.code_review import CodeReview
    from python.tools.devops_deploy import DevOpsDeploy

    # Create tools with missing required parameters
    tools = [
        DevOpsDeploy(mock_agent, "deploy", None, {}, "", None),
        AuthTest(mock_agent, "auth", None, {}, "", None),
        APIDesign(mock_agent, "api", None, {}, "", None),
        AnalyticsROICalculator(mock_agent, "roi", None, {}, "", None),
        CodeReview(mock_agent, "review", None, {}, "", None),
    ]

    for tool in tools:
        response = await tool.execute()
        # All should return Response objects
        assert isinstance(response, Response)
        # All should not break the loop on error
        assert response.break_loop is False
        # All should have non-empty error messages
        assert len(response.message) > 0
        # Error messages should be helpful
        assert (
            "error" in response.message.lower()
            or "required" in response.message.lower()
            or "missing" in response.message.lower()
        )


@pytest.mark.asyncio
async def test_all_tools_non_terminal(mock_agent):
    """Test that all tools are non-terminal (break_loop=False)"""
    from python.tools.analytics_roi_calculator import AnalyticsROICalculator
    from python.tools.api_design import APIDesign
    from python.tools.auth_test import AuthTest
    from python.tools.code_review import CodeReview
    from python.tools.devops_deploy import DevOpsDeploy

    # Create tools with valid args
    deploy = DevOpsDeploy(mock_agent, "deploy", None, {"environment": "staging"}, "", None)
    auth = AuthTest(mock_agent, "auth", None, {"endpoint": "login"}, "", None)
    api = APIDesign(mock_agent, "api", None, {"resource": "users"}, "", None)
    roi = AnalyticsROICalculator(mock_agent, "roi", None, {"investment": "1000", "revenue": "1500"}, "", None)
    review = CodeReview(mock_agent, "review", None, {"file": "test.py"}, "", None)

    # Execute all tools
    responses = [
        await deploy.execute(),
        await auth.execute(),
        await api.execute(),
        await roi.execute(),
        await review.execute(),
    ]

    # All should be non-terminal
    for response in responses:
        assert response.break_loop is False
