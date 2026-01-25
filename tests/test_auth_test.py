"""Tests for Auth Test tool"""

from unittest.mock import MagicMock

import pytest

from python.helpers.tool import Response
from python.tools.auth_test import AuthTest


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
async def test_auth_test_tool_exists():
    """Test that AuthTest tool can be instantiated"""
    agent = MagicMock()
    tool = AuthTest(agent=agent, name="auth_test", method=None, args={}, message="Test authentication", loop_data=None)
    assert tool is not None


@pytest.mark.asyncio
async def test_auth_test_validates_endpoints(mock_agent):
    """Test that auth test validates endpoint parameter"""
    tool = AuthTest(
        agent=mock_agent,
        name="auth_test",
        method=None,
        args={"endpoint": "invalid-endpoint"},
        message="Test auth",
        loop_data=None,
    )

    response = await tool.execute()

    assert isinstance(response, Response)
    assert response.break_loop is False
    assert "Invalid endpoint" in response.message


@pytest.mark.asyncio
async def test_auth_test_accepts_valid_endpoints(mock_agent):
    """Test that auth test accepts all valid endpoints"""
    valid_endpoints = ["login", "logout", "refresh", "protected", "all"]

    for endpoint in valid_endpoints:
        tool = AuthTest(
            agent=mock_agent,
            name="auth_test",
            method=None,
            args={"endpoint": endpoint},
            message=f"Test {endpoint}",
            loop_data=None,
        )

        response = await tool.execute()

        assert isinstance(response, Response)
        assert "Invalid endpoint" not in response.message


@pytest.mark.asyncio
async def test_auth_test_includes_security_checks(mock_agent):
    """Test that auth test includes security vulnerability checks"""
    tool = AuthTest(
        agent=mock_agent,
        name="auth_test",
        method=None,
        args={"endpoint": "all"},
        message="Full auth test",
        loop_data=None,
    )

    response = await tool.execute()

    # Should include security testing
    message_lower = response.message.lower()
    security_keywords = ["security", "xss", "csrf", "injection", "vulnerability"]
    assert any(keyword in message_lower for keyword in security_keywords)


@pytest.mark.asyncio
async def test_auth_test_coverage_mode(mock_agent):
    """Test that --coverage flag generates coverage report"""
    tool = AuthTest(
        agent=mock_agent,
        name="auth_test",
        method=None,
        args={"coverage": "true"},
        message="Test with coverage",
        loop_data=None,
    )

    response = await tool.execute()

    assert "coverage" in response.message.lower()
