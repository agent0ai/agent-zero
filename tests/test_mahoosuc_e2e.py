"""End-to-end integration tests for Mahoosuc OS"""

from pathlib import Path

import pytest


class TestMahoosucEndToEnd:
    """End-to-end integration tests"""

    def test_complete_workflow_reference_mode(self):
        """Should complete full workflow in reference mode"""
        from python.helpers.mahoosuc_config import get_integration_mode, validate_config
        from python.helpers.mahoosuc_reference import (
            get_command_spec,
            list_command_categories,
            search_commands,
        )

        # 1. Validate configuration
        config = validate_config()
        assert config["valid"] is True

        # 2. Verify mode
        mode = get_integration_mode()
        assert mode in ["reference", "mcp-bridge", "native-tools"]

        # 3. List categories
        categories = list_command_categories()
        assert len(categories) >= 90

        # 4. Get specific command
        deploy_spec = get_command_spec("devops", "deploy")
        assert deploy_spec is not None
        assert len(deploy_spec) > 100

        # 5. Search for commands
        results = search_commands("deployment")
        assert len(results) > 0

    @pytest.mark.asyncio
    async def test_native_tool_conversion_workflow(self):
        """Should demonstrate native tool conversion workflow"""
        from python.helpers.mahoosuc_reference import get_command_spec
        from python.tools.mahoosuc_finance_report import FinanceReport

        # 1. Reference original command
        original_spec = get_command_spec("finance", "report")
        assert original_spec is not None
        assert "report" in original_spec.lower()

        # 2. Use converted native tool
        tool = FinanceReport(
            agent=None,
            name="mahoosuc_finance_report",
            method="",
            args={"type": "income", "period": "month"},
            message="",
            loop_data=None,
        )

        response = await tool.execute()
        assert response.message is not None
        assert "income" in response.message.lower()

    def test_documentation_completeness(self):
        """Should have complete documentation for all components"""
        docs_dir = Path(".claude/docs")

        required_docs = [
            "COMMANDS_INDEX.md",
            "AGENTS_MIGRATION.md",
            "SKILLS_ADAPTATION.md",
            "IMPORT_SUMMARY.md",
            "USING_MAHOOSUC_COMMANDS.md",
            "AGENT_ZERO_INTEGRATION.md",
            "CONFIGURATION.md",
        ]

        for doc in required_docs:
            doc_path = docs_dir / doc
            assert doc_path.exists(), f"Missing documentation: {doc}"
            assert doc_path.stat().st_size > 1000, f"Documentation too small: {doc}"

    def test_all_integration_modes_documented(self):
        """Should document all 3 integration modes"""
        config_doc = Path(".claude/docs/CONFIGURATION.md").read_text()

        # All modes should be documented
        assert "reference" in config_doc.lower()
        assert "mcp-bridge" in config_doc.lower()
        assert "native-tools" in config_doc.lower()

        # Should have examples for each
        assert "reference mode" in config_doc.lower()
        assert "mcp bridge" in config_doc.lower()
        assert "native tool" in config_doc.lower()
