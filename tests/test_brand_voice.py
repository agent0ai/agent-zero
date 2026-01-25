"""Tests for Brand Voice tool"""

from unittest.mock import MagicMock

import pytest

from python.helpers.tool import Response
from python.tools.brand_voice import BrandVoice


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
async def test_brand_voice_tool_exists():
    """Test that BrandVoice tool can be instantiated"""
    agent = MagicMock()
    tool = BrandVoice(
        agent=agent,
        name="brand_voice",
        method=None,
        args={"mode": "define"},
        message="Define brand voice",
        loop_data=None,
    )
    assert tool is not None


@pytest.mark.asyncio
async def test_brand_voice_requires_mode(mock_agent):
    """Test that brand voice requires mode parameter"""
    tool = BrandVoice(
        agent=mock_agent,
        name="brand_voice",
        method=None,
        args={},
        message="Brand voice check",
        loop_data=None,
    )

    response = await tool.execute()

    assert isinstance(response, Response)
    assert "mode" in response.message.lower() and "required" in response.message.lower()


@pytest.mark.asyncio
async def test_brand_voice_validates_mode(mock_agent):
    """Test that brand voice validates mode parameter"""
    tool = BrandVoice(
        agent=mock_agent,
        name="brand_voice",
        method=None,
        args={"mode": "invalid-mode"},
        message="Brand voice check",
        loop_data=None,
    )

    response = await tool.execute()

    assert isinstance(response, Response)
    assert "invalid" in response.message.lower() or "mode" in response.message.lower()


@pytest.mark.asyncio
async def test_brand_voice_define_mode(mock_agent):
    """Test brand voice define mode"""
    tool = BrandVoice(
        agent=mock_agent,
        name="brand_voice",
        method=None,
        args={"mode": "define"},
        message="Define brand voice",
        loop_data=None,
    )

    response = await tool.execute()

    assert isinstance(response, Response)
    assert "brand voice" in response.message.lower()
    assert "guideline" in response.message.lower() or "define" in response.message.lower()
    assert response.break_loop is False


@pytest.mark.asyncio
async def test_brand_voice_analyze_mode(mock_agent):
    """Test brand voice analyze mode"""
    tool = BrandVoice(
        agent=mock_agent,
        name="brand_voice",
        method=None,
        args={"mode": "analyze", "content": "This is sample content to analyze."},
        message="Analyze content",
        loop_data=None,
    )

    response = await tool.execute()

    assert isinstance(response, Response)
    assert "analyz" in response.message.lower() or "analysis" in response.message.lower()
    assert response.break_loop is False


@pytest.mark.asyncio
async def test_brand_voice_analyze_requires_content(mock_agent):
    """Test that analyze mode requires content parameter"""
    tool = BrandVoice(
        agent=mock_agent,
        name="brand_voice",
        method=None,
        args={"mode": "analyze"},
        message="Analyze without content",
        loop_data=None,
    )

    response = await tool.execute()

    assert isinstance(response, Response)
    assert "content" in response.message.lower() and "required" in response.message.lower()


@pytest.mark.asyncio
async def test_brand_voice_check_mode(mock_agent):
    """Test brand voice check mode"""
    tool = BrandVoice(
        agent=mock_agent,
        name="brand_voice",
        method=None,
        args={"mode": "check", "file": "/path/to/content.md"},
        message="Check file",
        loop_data=None,
    )

    response = await tool.execute()

    assert isinstance(response, Response)
    assert "check" in response.message.lower() or "consistency" in response.message.lower()
    assert response.break_loop is False


@pytest.mark.asyncio
async def test_brand_voice_train_mode(mock_agent):
    """Test brand voice train mode"""
    tool = BrandVoice(
        agent=mock_agent,
        name="brand_voice",
        method=None,
        args={"mode": "train"},
        message="Train brand voice",
        loop_data=None,
    )

    response = await tool.execute()

    assert isinstance(response, Response)
    assert "train" in response.message.lower() or "learning" in response.message.lower()
    assert response.break_loop is False
