"""Tests for Analytics ROI Calculator tool"""

from unittest.mock import MagicMock

import pytest

from python.helpers.tool import Response
from python.tools.analytics_roi_calculator import AnalyticsROICalculator


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
async def test_roi_calculator_tool_exists():
    """Test that AnalyticsROICalculator tool can be instantiated"""
    agent = MagicMock()
    tool = AnalyticsROICalculator(
        agent=agent,
        name="analytics_roi_calculator",
        method=None,
        args={"investment": "50000", "revenue": "75000"},
        message="Calculate ROI",
        loop_data=None,
    )
    assert tool is not None


@pytest.mark.asyncio
async def test_roi_calculator_requires_investment(mock_agent):
    """Test that ROI calculator requires investment parameter"""
    tool = AnalyticsROICalculator(
        agent=mock_agent,
        name="analytics_roi_calculator",
        method=None,
        args={"revenue": "100000"},
        message="Calculate ROI",
        loop_data=None,
    )

    response = await tool.execute()

    assert isinstance(response, Response)
    assert "investment" in response.message.lower() and "required" in response.message.lower()


@pytest.mark.asyncio
async def test_roi_calculator_requires_revenue(mock_agent):
    """Test that ROI calculator requires revenue parameter"""
    tool = AnalyticsROICalculator(
        agent=mock_agent,
        name="analytics_roi_calculator",
        method=None,
        args={"investment": "50000"},
        message="Calculate ROI",
        loop_data=None,
    )

    response = await tool.execute()

    assert isinstance(response, Response)
    assert "revenue" in response.message.lower() and "required" in response.message.lower()


@pytest.mark.asyncio
async def test_roi_calculator_validates_numeric_inputs(mock_agent):
    """Test that ROI calculator validates numeric inputs"""
    tool = AnalyticsROICalculator(
        agent=mock_agent,
        name="analytics_roi_calculator",
        method=None,
        args={"investment": "not-a-number", "revenue": "100000"},
        message="Calculate ROI",
        loop_data=None,
    )

    response = await tool.execute()

    assert isinstance(response, Response)
    assert "invalid" in response.message.lower() or "numeric" in response.message.lower()


@pytest.mark.asyncio
async def test_roi_calculator_computes_roi(mock_agent):
    """Test that ROI calculator computes ROI percentage"""
    tool = AnalyticsROICalculator(
        agent=mock_agent,
        name="analytics_roi_calculator",
        method=None,
        args={"investment": "50000", "revenue": "75000"},
        message="Calculate ROI",
        loop_data=None,
    )

    response = await tool.execute()

    # ROI = ((Revenue - Investment) / Investment) * 100 = ((75000 - 50000) / 50000) * 100 = 50%
    assert isinstance(response, Response)
    assert "50" in response.message or "50%" in response.message


@pytest.mark.asyncio
async def test_roi_calculator_supports_costs_parameter(mock_agent):
    """Test that ROI calculator supports optional costs parameter"""
    tool = AnalyticsROICalculator(
        agent=mock_agent,
        name="analytics_roi_calculator",
        method=None,
        args={"investment": "50000", "revenue": "100000", "costs": "10000"},
        message="Calculate ROI with costs",
        loop_data=None,
    )

    response = await tool.execute()

    assert isinstance(response, Response)
    assert response.break_loop is False
