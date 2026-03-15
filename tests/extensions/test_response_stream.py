"""Tests for response_stream extensions: log_from_stream, replace_include_alias, live_response, mask_stream, mask_end, log_from_stream_end."""

import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


class TestLogFromStream:
    """Tests for response_stream/_10_log_from_stream.py."""

    @pytest.mark.asyncio
    async def test_creates_and_updates_log_item(self, mock_agent, mock_loop_data):
        mock_loop_data.params_temporary = {}
        mock_log_item = MagicMock()
        mock_log_item.kvps = {}
        mock_agent.context.log.log.return_value = mock_log_item

        from python.extensions.response_stream._10_log_from_stream import LogFromStream

        ext = LogFromStream(agent=mock_agent)
        await ext.execute(loop_data=mock_loop_data, text="hello", parsed={})

        assert "log_item_generating" in mock_loop_data.params_temporary
        mock_log_item.update.assert_called()


class TestReplaceIncludeAlias:
    """Tests for response_stream/_15_replace_include_alias.py."""

    @pytest.mark.asyncio
    async def test_returns_early_without_parsed(self):
        from python.extensions.response_stream._15_replace_include_alias import (
            ReplaceIncludeAlias,
        )

        ext = ReplaceIncludeAlias(agent=MagicMock())
        await ext.execute(parsed=None)
        await ext.execute(parsed={})

    @pytest.mark.asyncio
    async def test_replaces_include_in_tool_args(self, mock_agent):
        parsed = {"tool_name": "read_file", "tool_args": {"path": "§§include(/x/y)"}}

        def mock_replace(text, pattern=None):
            return "file content" if "§§include" in text else text

        with patch(
            "python.extensions.response_stream._15_replace_include_alias.replace_file_includes",
            side_effect=mock_replace,
        ):
            from python.extensions.response_stream._15_replace_include_alias import (
                ReplaceIncludeAlias,
            )

            ext = ReplaceIncludeAlias(agent=mock_agent)
            await ext.execute(parsed=parsed)

        assert parsed["tool_args"]["path"] == "file content"


class TestLiveResponse:
    """Tests for response_stream/_20_live_response.py."""

    @pytest.mark.asyncio
    async def test_returns_early_when_not_response(self, mock_agent, mock_loop_data):
        mock_loop_data.params_temporary = {}
        parsed = {"tool_name": "other_tool"}

        from python.extensions.response_stream._20_live_response import LiveResponse

        ext = LiveResponse(agent=mock_agent)
        await ext.execute(loop_data=mock_loop_data, parsed=parsed)

        mock_agent.context.log.log.assert_not_called()

    @pytest.mark.asyncio
    async def test_updates_log_for_response_tool(self, mock_agent, mock_loop_data):
        mock_loop_data.params_temporary = {}
        mock_log_item = MagicMock()
        mock_agent.context.log.log.return_value = mock_log_item
        parsed = {
            "tool_name": "response",
            "tool_args": {"text": "Hello user"},
        }

        from python.extensions.response_stream._20_live_response import LiveResponse

        ext = LiveResponse(agent=mock_agent)
        await ext.execute(loop_data=mock_loop_data, parsed=parsed)

        mock_log_item.update.assert_called_with(content="Hello user")


class TestMaskResponseStreamChunk:
    """Tests for response_stream_chunk/_10_mask_stream.py."""

    @pytest.mark.asyncio
    async def test_returns_early_without_agent(self, mock_agent):
        from python.extensions.response_stream_chunk._10_mask_stream import (
            MaskResponseStreamChunk,
        )

        ext = MaskResponseStreamChunk(agent=mock_agent)
        await ext.execute(stream_data=None, agent=None)

    @pytest.mark.asyncio
    async def test_masks_chunk(self, mock_agent):
        stream_data = {"chunk": "secret123", "full": "secret123"}
        filter_mock = MagicMock()
        filter_mock.process_chunk.return_value = "***"

        with patch(
            "python.extensions.response_stream_chunk._10_mask_stream.get_secrets_manager"
        ) as mock_mgr:
            mock_mgr.return_value.create_streaming_filter.return_value = filter_mock
            mock_mgr.return_value.mask_values.return_value = "***"

            from python.extensions.response_stream_chunk._10_mask_stream import (
                MaskResponseStreamChunk,
            )

            ext = MaskResponseStreamChunk(agent=mock_agent)
            await ext.execute(stream_data=stream_data, agent=mock_agent)

        assert stream_data["chunk"] == "***"


class TestMaskResponseStreamEnd:
    """Tests for response_stream_end/_10_mask_end.py."""

    @pytest.mark.asyncio
    async def test_returns_early_without_agent(self, mock_agent):
        from python.extensions.response_stream_end._10_mask_end import (
            MaskResponseStreamEnd,
        )

        ext = MaskResponseStreamEnd(agent=mock_agent)
        await ext.execute(agent=None)

    @pytest.mark.asyncio
    async def test_finalizes_filter(self, mock_agent):
        filter_mock = MagicMock()
        filter_mock.finalize.return_value = ""
        mock_agent.get_data.return_value = filter_mock

        from python.extensions.response_stream_end._10_mask_end import (
            MaskResponseStreamEnd,
        )

        ext = MaskResponseStreamEnd(agent=mock_agent)
        await ext.execute(agent=mock_agent)

        mock_agent.set_data.assert_called_with("_resp_stream_filter", None)


class TestLogFromStreamEnd:
    """Tests for response_stream_end/_15_log_from_stream_end.py."""

    @pytest.mark.asyncio
    async def test_returns_early_without_log_item(self, mock_agent, mock_loop_data):
        mock_loop_data.params_temporary = {"log_item_generating": None}

        from python.extensions.response_stream_end._15_log_from_stream_end import (
            LogFromStream,
        )

        ext = LogFromStream(agent=mock_agent)
        await ext.execute(loop_data=mock_loop_data)

    @pytest.mark.asyncio
    async def test_removes_step_from_kvps(self, mock_agent, mock_loop_data):
        mock_log_item = MagicMock()
        mock_log_item.kvps = {"step": "Using tool...", "other": "val"}
        mock_loop_data.params_temporary = {"log_item_generating": mock_log_item}

        from python.extensions.response_stream_end._15_log_from_stream_end import (
            LogFromStream,
        )

        ext = LogFromStream(agent=mock_agent)
        await ext.execute(loop_data=mock_loop_data)

        assert "step" not in mock_log_item.kvps
