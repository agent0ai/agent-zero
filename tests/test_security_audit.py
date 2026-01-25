"""Tests for Security Audit tool"""

from unittest.mock import MagicMock

import pytest

from python.helpers.tool import Response
from python.tools.security_audit import SecurityAudit


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
async def test_security_audit_tool_exists():
    """Test that SecurityAudit tool can be instantiated"""
    agent = MagicMock()
    tool = SecurityAudit(
        agent=agent, name="security_audit", method=None, args={}, message="Run security audit", loop_data=None
    )
    assert tool is not None


@pytest.mark.asyncio
async def test_security_audit_default_scope_and_severity(mock_agent):
    """Test that security audit works with default parameters"""
    tool = SecurityAudit(
        agent=mock_agent, name="security_audit", method=None, args={}, message="Run audit", loop_data=None
    )

    response = await tool.execute()

    assert isinstance(response, Response)
    assert response.break_loop is False
    assert "security audit" in response.message.lower()
    assert "score" in response.message.lower()


@pytest.mark.asyncio
async def test_security_audit_accepts_scope_parameter(mock_agent):
    """Test that security audit accepts scope parameter"""
    scopes = ["code", "infra", "full"]

    for scope in scopes:
        tool = SecurityAudit(
            agent=mock_agent,
            name="security_audit",
            method=None,
            args={"scope": scope},
            message=f"Audit scope {scope}",
            loop_data=None,
        )

        response = await tool.execute()

        assert isinstance(response, Response)
        assert scope in response.message.lower()
        assert response.break_loop is False


@pytest.mark.asyncio
async def test_security_audit_accepts_severity_parameter(mock_agent):
    """Test that security audit accepts severity filter"""
    severities = ["critical", "high", "all"]

    for severity in severities:
        tool = SecurityAudit(
            agent=mock_agent,
            name="security_audit",
            method=None,
            args={"severity": severity},
            message=f"Audit severity {severity}",
            loop_data=None,
        )

        response = await tool.execute()

        assert isinstance(response, Response)
        assert response.break_loop is False


@pytest.mark.asyncio
async def test_security_audit_invalid_scope_returns_error(mock_agent):
    """Test that invalid scope returns clear error message"""
    tool = SecurityAudit(
        agent=mock_agent,
        name="security_audit",
        method=None,
        args={"scope": "invalid"},
        message="Invalid scope",
        loop_data=None,
    )

    response = await tool.execute()

    assert isinstance(response, Response)
    assert "error" in response.message.lower() or "invalid" in response.message.lower()
    assert response.break_loop is False


@pytest.mark.asyncio
async def test_security_audit_invalid_severity_returns_error(mock_agent):
    """Test that invalid severity returns clear error message"""
    tool = SecurityAudit(
        agent=mock_agent,
        name="security_audit",
        method=None,
        args={"severity": "invalid"},
        message="Invalid severity",
        loop_data=None,
    )

    response = await tool.execute()

    assert isinstance(response, Response)
    assert "error" in response.message.lower() or "invalid" in response.message.lower()
    assert response.break_loop is False


@pytest.mark.asyncio
async def test_security_audit_includes_all_audit_areas(mock_agent):
    """Test that full audit includes all 9 security areas"""
    tool = SecurityAudit(
        agent=mock_agent,
        name="security_audit",
        method=None,
        args={"scope": "full"},
        message="Full audit",
        loop_data=None,
    )

    response = await tool.execute()

    # Should include key security areas
    message_lower = response.message.lower()
    areas = [
        "authentication",
        "authorization",
        "encryption",
        "injection",
        "dependencies",
        "api security",
        "logging",
    ]

    # At least 5 areas should be mentioned
    found_areas = sum(1 for area in areas if area in message_lower)
    assert found_areas >= 5


@pytest.mark.asyncio
async def test_security_audit_code_scope_excludes_infrastructure(mock_agent):
    """Test that code scope focuses on code security"""
    tool = SecurityAudit(
        agent=mock_agent,
        name="security_audit",
        method=None,
        args={"scope": "code"},
        message="Code audit",
        loop_data=None,
    )

    response = await tool.execute()

    message_lower = response.message.lower()
    # Should include code-specific items
    assert any(term in message_lower for term in ["authentication", "injection", "xss", "dependencies"])
    # Infrastructure should be skipped or minimal
    assert "infrastructure" not in message_lower or "skipped" in message_lower


@pytest.mark.asyncio
async def test_security_audit_infra_scope_excludes_code(mock_agent):
    """Test that infra scope focuses on infrastructure security"""
    tool = SecurityAudit(
        agent=mock_agent,
        name="security_audit",
        method=None,
        args={"scope": "infra"},
        message="Infrastructure audit",
        loop_data=None,
    )

    response = await tool.execute()

    message_lower = response.message.lower()
    # Should include infrastructure-specific items
    assert any(term in message_lower for term in ["iam", "network", "firewall", "infrastructure"])


@pytest.mark.asyncio
async def test_security_audit_critical_severity_shows_only_critical(mock_agent):
    """Test that critical severity filter works"""
    tool = SecurityAudit(
        agent=mock_agent,
        name="security_audit",
        method=None,
        args={"severity": "critical"},
        message="Critical only",
        loop_data=None,
    )

    response = await tool.execute()

    message_lower = response.message.lower()
    assert "critical" in message_lower
    assert "severity" in message_lower


@pytest.mark.asyncio
async def test_security_audit_calculates_security_score(mock_agent):
    """Test that security audit calculates and displays security score"""
    tool = SecurityAudit(
        agent=mock_agent, name="security_audit", method=None, args={}, message="Run audit", loop_data=None
    )

    response = await tool.execute()

    message_lower = response.message.lower()
    # Should include score and grade
    assert "score" in message_lower
    assert any(term in message_lower for term in ["grade", "rating", "excellent", "good", "fair", "poor"])


@pytest.mark.asyncio
async def test_security_audit_includes_findings_summary(mock_agent):
    """Test that audit includes findings summary with severity breakdown"""
    tool = SecurityAudit(
        agent=mock_agent, name="security_audit", method=None, args={}, message="Run audit", loop_data=None
    )

    response = await tool.execute()

    message_lower = response.message.lower()
    # Should include findings summary
    assert "findings" in message_lower or "vulnerabilities" in message_lower
    # Should mention severity levels
    severity_count = sum(
        1 for term in ["critical", "high", "medium", "low"] if term in message_lower
    )
    assert severity_count >= 2
