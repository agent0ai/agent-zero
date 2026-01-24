"""Test Mahoosuc OS configuration validation"""

import os
from unittest.mock import patch

import pytest


class TestMahoosucConfiguration:
    """Test configuration loading and validation"""

    def test_commands_dir_path_resolution(self):
        """Should resolve MAHOOSUC_COMMANDS_DIR to absolute path"""
        with patch.dict(os.environ, {"MAHOOSUC_COMMANDS_DIR": ".claude/commands"}):
            from python.helpers.mahoosuc_config import get_commands_dir

            commands_dir = get_commands_dir()
            assert commands_dir.is_absolute()
            assert commands_dir.name == "commands"
            assert commands_dir.exists()

    def test_integration_mode_validation(self):
        """Should validate integration mode is valid"""
        from python.helpers.mahoosuc_config import validate_integration_mode

        # Valid modes
        assert validate_integration_mode("reference") is True
        assert validate_integration_mode("mcp-bridge") is True
        assert validate_integration_mode("native-tools") is True

        # Invalid modes
        with pytest.raises(ValueError, match="Invalid integration mode"):
            validate_integration_mode("invalid-mode")

    def test_default_integration_mode(self):
        """Should default to 'reference' mode when not configured"""
        with patch.dict(os.environ, {}, clear=True):
            from python.helpers.mahoosuc_config import get_integration_mode

            mode = get_integration_mode()
            assert mode == "reference"

    def test_config_validation_missing_directories(self):
        """Should detect when required directories are missing"""
        from python.helpers.mahoosuc_config import validate_config

        with patch.dict(
            os.environ, {"MAHOOSUC_COMMANDS_DIR": "/nonexistent/path", "MAHOOSUC_INTEGRATION_MODE": "reference"}
        ):
            result = validate_config()
            assert result["valid"] is False
            assert "commands directory not found" in result["errors"][0].lower()

    def test_mcp_bridge_requires_claude_code(self):
        """MCP bridge mode should require CLAUDE_CODE_ENABLED"""
        from python.helpers.mahoosuc_config import validate_config

        with patch.dict(os.environ, {"MAHOOSUC_INTEGRATION_MODE": "mcp-bridge", "CLAUDE_CODE_ENABLED": "false"}):
            result = validate_config()
            assert result["valid"] is False
            assert "claude_code_enabled" in result["errors"][0].lower()
