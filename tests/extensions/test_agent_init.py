"""Tests for agent_init extensions: initial message and load profile settings."""

import sys
from pathlib import Path
from unittest.mock import MagicMock, AsyncMock, patch

import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


class TestInitialMessage:
    """Tests for _10_initial_message.py."""

    @pytest.mark.asyncio
    async def test_skips_for_subordinate_agent(self, mock_agent):
        mock_agent.number = 1
        mock_agent.context.log.logs = []
        mock_agent.read_prompt.return_value = '{"tool_args":{"text":"Hi"}}'

        from python.extensions.agent_init._10_initial_message import InitialMessage

        ext = InitialMessage(agent=mock_agent)
        await ext.execute()
        mock_agent.hist_add_ai_response.assert_not_called()

    @pytest.mark.asyncio
    async def test_skips_when_logs_exist(self, mock_agent):
        mock_agent.number = 0
        mock_agent.context.log.logs = [MagicMock()]

        from python.extensions.agent_init._10_initial_message import InitialMessage

        ext = InitialMessage(agent=mock_agent)
        await ext.execute()
        mock_agent.hist_add_ai_response.assert_not_called()

    @pytest.mark.asyncio
    async def test_adds_initial_message_for_main_agent(self, mock_agent):
        mock_agent.number = 0
        mock_agent.context.log.logs = []
        mock_agent.read_prompt.return_value = '{"tool_args":{"text":"Hello! How can I help?"}}'

        from python.extensions.agent_init._10_initial_message import InitialMessage

        ext = InitialMessage(agent=mock_agent)
        await ext.execute()

        mock_agent.hist_add_ai_response.assert_called_once()
        mock_agent.context.log.log.assert_called_with(
            type="response",
            content="Hello! How can I help?",
            finished=True,
            update_progress="none",
        )


class TestLoadProfileSettings:
    """Tests for _15_load_profile_settings.py."""

    @pytest.mark.asyncio
    async def test_returns_early_without_agent(self):
        from python.extensions.agent_init._15_load_profile_settings import LoadProfileSettings

        ext = LoadProfileSettings(agent=None)
        await ext.execute()

    @pytest.mark.asyncio
    async def test_returns_early_without_profile(self, mock_agent):
        mock_agent.config.profile = None

        from python.extensions.agent_init._15_load_profile_settings import LoadProfileSettings

        ext = LoadProfileSettings(agent=mock_agent)
        await ext.execute()

    @pytest.mark.asyncio
    async def test_loads_settings_from_profile(self, mock_agent):
        mock_agent.config.profile = "test_profile"
        mock_agent.config.memory_subdir = "mem"
        mock_agent.config.mcp_servers = []
        mock_agent.config.browser_http_headers = {}

        with patch(
            "python.extensions.agent_init._15_load_profile_settings.subagents.get_paths",
            return_value=[],
        ):
            from python.extensions.agent_init._15_load_profile_settings import LoadProfileSettings

            ext = LoadProfileSettings(agent=mock_agent)
            await ext.execute()
