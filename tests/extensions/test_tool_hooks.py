"""Tests for tool_execute extensions: mask_secrets (after), replace_last_tool_output, unmask_secrets (before)."""

import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


class TestMaskToolSecretsAfter:
    """Tests for tool_execute_after/_10_mask_secrets.py."""

    @pytest.mark.asyncio
    async def test_returns_early_without_response(self, mock_agent):
        from python.extensions.tool_execute_after._10_mask_secrets import MaskToolSecrets

        ext = MaskToolSecrets(agent=mock_agent)
        await ext.execute(response=None)

    @pytest.mark.asyncio
    async def test_masks_response_message(self, mock_agent):
        from python.helpers.tool import Response

        response = Response(message="secret_key_123", break_loop=False)

        with patch(
            "python.extensions.tool_execute_after._10_mask_secrets.get_secrets_manager"
        ) as mock_mgr:
            mock_mgr.return_value.mask_values.return_value = "***"

            from python.extensions.tool_execute_after._10_mask_secrets import (
                MaskToolSecrets,
            )

            ext = MaskToolSecrets(agent=mock_agent)
            await ext.execute(response=response)

        assert response.message == "***"


class TestReplaceLastToolOutput:
    """Tests for tool_execute_before/_10_replace_last_tool_output.py."""

    @pytest.mark.asyncio
    async def test_returns_early_without_tool_args(self, mock_agent):
        from python.extensions.tool_execute_before._10_replace_last_tool_output import (
            ReplaceLastToolOutput,
        )

        ext = ReplaceLastToolOutput(agent=mock_agent)
        await ext.execute(tool_args=None)

    @pytest.mark.asyncio
    async def test_replaces_last_tool_output_placeholder(self, mock_agent):
        tool_args = {"prompt": "Use output: {last_tool_output}"}
        mock_agent.get_data.return_value = {
            "last_tool_output": "actual output",
        }

        from python.extensions.tool_execute_before._10_replace_last_tool_output import (
            ReplaceLastToolOutput,
        )

        ext = ReplaceLastToolOutput(agent=mock_agent)
        await ext.execute(tool_args=tool_args, tool_name="test")

        assert tool_args["prompt"] == "Use output: actual output"


class TestUnmaskToolSecrets:
    """Tests for tool_execute_before/_10_unmask_secrets.py."""

    @pytest.mark.asyncio
    async def test_returns_early_without_tool_args(self, mock_agent):
        from python.extensions.tool_execute_before._10_unmask_secrets import (
            UnmaskToolSecrets,
        )

        ext = UnmaskToolSecrets(agent=mock_agent)
        await ext.execute(tool_args=None)

    @pytest.mark.asyncio
    async def test_unmasks_placeholders_in_tool_args(self, mock_agent):
        tool_args = {"api_key": "SECRET_PLACEHOLDER_1"}

        with patch(
            "python.extensions.tool_execute_before._10_unmask_secrets.get_secrets_manager"
        ) as mock_mgr:
            mock_mgr.return_value.replace_placeholders.return_value = "real_key"

            from python.extensions.tool_execute_before._10_unmask_secrets import (
                UnmaskToolSecrets,
            )

            ext = UnmaskToolSecrets(agent=mock_agent)
            await ext.execute(tool_args=tool_args)

        assert tool_args["api_key"] == "real_key"
