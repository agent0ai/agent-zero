"""Tests for Code Review tool"""

from unittest.mock import MagicMock

import pytest

from python.helpers.tool import Response
from python.tools.code_review import CodeReview


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
async def test_code_review_tool_exists():
    """Test that CodeReview tool can be instantiated"""
    agent = MagicMock()
    tool = CodeReview(
        agent=agent, name="code_review", method=None, args={"file": "example.py"}, message="Review code", loop_data=None
    )
    assert tool is not None


@pytest.mark.asyncio
async def test_code_review_requires_file_or_diff(mock_agent):
    """Test that code review requires file or diff parameter"""
    tool = CodeReview(agent=mock_agent, name="code_review", method=None, args={}, message="Review code", loop_data=None)

    response = await tool.execute()

    assert isinstance(response, Response)
    assert "file" in response.message.lower() or "diff" in response.message.lower()
    assert "required" in response.message.lower()


@pytest.mark.asyncio
async def test_code_review_accepts_file_parameter(mock_agent):
    """Test that code review accepts file parameter"""
    tool = CodeReview(
        agent=mock_agent,
        name="code_review",
        method=None,
        args={"file": "test.py"},
        message="Review file",
        loop_data=None,
    )

    response = await tool.execute()

    assert isinstance(response, Response)
    assert "test.py" in response.message


@pytest.mark.asyncio
async def test_code_review_accepts_diff_parameter(mock_agent):
    """Test that code review accepts git diff"""
    tool = CodeReview(
        agent=mock_agent,
        name="code_review",
        method=None,
        args={"diff": "git diff main...feature"},
        message="Review diff",
        loop_data=None,
    )

    response = await tool.execute()

    assert isinstance(response, Response)
    assert response.break_loop is False


@pytest.mark.asyncio
async def test_code_review_includes_analysis_categories(mock_agent):
    """Test that code review includes standard analysis categories"""
    tool = CodeReview(
        agent=mock_agent,
        name="code_review",
        method=None,
        args={"file": "example.py"},
        message="Review code",
        loop_data=None,
    )

    response = await tool.execute()

    # Should include standard review categories
    message_lower = response.message.lower()
    categories = ["code quality", "security", "performance", "maintainability", "best practices"]

    # At least 3 categories should be mentioned
    found_categories = sum(1 for cat in categories if cat in message_lower)
    assert found_categories >= 3


@pytest.mark.asyncio
async def test_code_review_supports_focus_parameter(mock_agent):
    """Test that code review supports focus parameter"""
    focuses = ["security", "performance", "style"]

    for focus in focuses:
        tool = CodeReview(
            agent=mock_agent,
            name="code_review",
            method=None,
            args={"file": "test.py", "focus": focus},
            message=f"Review with focus on {focus}",
            loop_data=None,
        )

        response = await tool.execute()

        assert isinstance(response, Response)
        assert focus in response.message.lower()
