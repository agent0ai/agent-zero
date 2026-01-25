"""Tests for API Design tool"""

from unittest.mock import MagicMock

import pytest

from python.helpers.tool import Response
from python.tools.api_design import APIDesign


@pytest.fixture
def mock_agent():
    """Create mock agent"""
    agent = MagicMock()
    agent.agent_name = "test-agent"
    agent.context = MagicMock()
    agent.context.log = MagicMock()
    agent.context.log.log = MagicMock(return_value=MagicMock())
    agent.hist_add_tool_result = MagicMock()
    return agent


@pytest.mark.asyncio
async def test_api_design_tool_exists():
    """Test that APIDesign tool can be instantiated"""
    agent = MagicMock()
    tool = APIDesign(
        agent=agent,
        name="api_design",
        method=None,
        args={"resource": "users"},
        message="Design users API",
        loop_data=None,
    )
    assert tool is not None


@pytest.mark.asyncio
async def test_api_design_requires_resource(mock_agent):
    """Test that API design requires resource parameter"""
    tool = APIDesign(agent=mock_agent, name="api_design", method=None, args={}, message="Design API", loop_data=None)

    response = await tool.execute()

    assert isinstance(response, Response)
    assert "resource parameter is required" in response.message.lower()


@pytest.mark.asyncio
async def test_api_design_generates_rest_endpoints(mock_agent):
    """Test that API design generates RESTful endpoints"""
    tool = APIDesign(
        agent=mock_agent,
        name="api_design",
        method=None,
        args={"resource": "products"},
        message="Design products API",
        loop_data=None,
    )

    response = await tool.execute()

    # Should include REST methods
    message_upper = response.message.upper()
    assert "GET" in message_upper
    assert "POST" in message_upper
    assert "PUT" in message_upper or "PATCH" in message_upper
    assert "DELETE" in message_upper


@pytest.mark.asyncio
async def test_api_design_includes_documentation(mock_agent):
    """Test that API design includes documentation"""
    tool = APIDesign(
        agent=mock_agent,
        name="api_design",
        method=None,
        args={"resource": "orders"},
        message="Design orders API",
        loop_data=None,
    )

    response = await tool.execute()

    # Should include documentation elements
    message_lower = response.message.lower()
    assert "endpoint" in message_lower or "route" in message_lower
    assert "response" in message_lower or "example" in message_lower


@pytest.mark.asyncio
async def test_api_design_supports_format_option(mock_agent):
    """Test that API design supports format option (openapi/graphql)"""
    for fmt in ["openapi", "graphql", "rest"]:
        tool = APIDesign(
            agent=mock_agent,
            name="api_design",
            method=None,
            args={"resource": "users", "format": fmt},
            message=f"Design API in {fmt}",
            loop_data=None,
        )

        response = await tool.execute()

        assert isinstance(response, Response)
        assert response.break_loop is False
