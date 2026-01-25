"""
Research Organize Tool Tests - TDD Implementation
Tests for organizing research materials into structured knowledge base
Converted from Mahoosuc /research:organize command
"""

from unittest.mock import MagicMock

import pytest

from python.tools.research_organize import ResearchOrganize


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
    """Helper to create ResearchOrganize tool with proper initialization"""
    return ResearchOrganize(
        agent=mock_agent, name="research_organize", method=None, args=args, message="", loop_data=None
    )


class TestResearchOrganizeValidation:
    """Tests for input validation"""

    @pytest.mark.unit
    async def test_tool_can_be_instantiated(self, mock_agent):
        """Test that tool can be created"""
        tool = create_tool(mock_agent, {})
        assert tool is not None
        assert tool.name == "research_organize"

    @pytest.mark.unit
    async def test_valid_structure_types_accepted(self, mock_agent):
        """Test that valid structure types are accepted"""
        valid_structures = ["topic", "chronological", "source", "methodology"]

        for structure in valid_structures:
            tool = create_tool(mock_agent, {"structure": structure})
            response = await tool.execute()
            assert "ERROR" not in response.message or "Invalid structure" not in response.message

    @pytest.mark.unit
    async def test_invalid_structure_type_fails(self, mock_agent):
        """Test that invalid structure type fails validation"""
        tool = create_tool(mock_agent, {"structure": "invalid"})
        response = await tool.execute()

        assert "ERROR" in response.message or "invalid" in response.message.lower()

    @pytest.mark.unit
    async def test_valid_export_formats_accepted(self, mock_agent):
        """Test that valid export formats are accepted"""
        valid_formats = ["obsidian", "notion", "roam", "markdown"]

        for export_format in valid_formats:
            tool = create_tool(mock_agent, {"export": export_format})
            response = await tool.execute()
            assert "ERROR" not in response.message or "Invalid export" not in response.message


class TestResearchOrganizeExecution:
    """Tests for organization execution"""

    @pytest.mark.unit
    async def test_default_execution_generates_report(self, mock_agent):
        """Test that default execution generates organization report"""
        tool = create_tool(mock_agent, {})
        response = await tool.execute()

        # Should mention research organization
        assert "research" in response.message.lower() or "organization" in response.message.lower()
        assert response.message  # Non-empty response

    @pytest.mark.unit
    async def test_topic_structure_generates_hierarchy(self, mock_agent):
        """Test that topic structure generates hierarchical organization"""
        tool = create_tool(mock_agent, {"structure": "topic"})
        response = await tool.execute()

        # Should mention topic-based organization
        assert "topic" in response.message.lower()

    @pytest.mark.unit
    async def test_tags_option_generates_tagging_system(self, mock_agent):
        """Test that tags option generates tagging system"""
        tool = create_tool(mock_agent, {"tags": "true"})
        response = await tool.execute()

        # Should mention tagging
        assert "tag" in response.message.lower()


class TestResearchOrganizePOC:
    """Tests for POC implementation that returns simulated organization"""

    @pytest.mark.unit
    async def test_poc_returns_success_status(self, mock_agent):
        """Test POC returns success organization status"""
        tool = create_tool(mock_agent, {"structure": "topic"})
        response = await tool.execute()

        # POC should indicate successful organization
        assert response.message  # Non-empty response
        assert response.break_loop is False

    @pytest.mark.unit
    async def test_poc_includes_structure_info(self, mock_agent):
        """Test POC includes organization structure information"""
        tool = create_tool(mock_agent, {"structure": "chronological"})
        response = await tool.execute()

        # Should mention the structure type
        assert "chronological" in response.message.lower() or "structure" in response.message.lower()

    @pytest.mark.unit
    async def test_export_format_included_in_output(self, mock_agent):
        """Test that export format is mentioned in output"""
        tool = create_tool(mock_agent, {"export": "obsidian"})
        response = await tool.execute()

        # Should mention export format
        assert "obsidian" in response.message.lower() or "export" in response.message.lower()

    @pytest.mark.unit
    async def test_combined_options_work_together(self, mock_agent):
        """Test that multiple options work together"""
        tool = create_tool(mock_agent, {"structure": "topic", "tags": "true", "export": "notion"})
        response = await tool.execute()

        # Should include all options
        assert response.message  # Non-empty response
        assert response.break_loop is False
