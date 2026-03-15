"""Tests for reasoning_stream extensions: log_from_stream, mask_stream, mask_end."""

import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


class TestReasoningLogFromStream:
    """Tests for reasoning_stream/_10_log_from_stream.py."""

    @pytest.mark.asyncio
    async def test_creates_log_item_for_reasoning(self, mock_agent, mock_loop_data):
        mock_loop_data.params_temporary = {}
        mock_log_item = MagicMock()
        mock_agent.context.log.log.return_value = mock_log_item

        from python.extensions.reasoning_stream._10_log_from_stream import LogFromStream

        ext = LogFromStream(agent=mock_agent)
        await ext.execute(loop_data=mock_loop_data, text="thinking...")

        assert "log_item_generating" in mock_loop_data.params_temporary
        mock_log_item.update.assert_called()


class TestMaskReasoningStreamChunk:
    """Tests for reasoning_stream_chunk/_10_mask_stream.py."""

    @pytest.mark.asyncio
    async def test_returns_early_without_agent(self, mock_agent):
        from python.extensions.reasoning_stream_chunk._10_mask_stream import (
            MaskReasoningStreamChunk,
        )

        ext = MaskReasoningStreamChunk(agent=mock_agent)
        await ext.execute(stream_data=None, agent=None)

    @pytest.mark.asyncio
    async def test_masks_reasoning_chunk(self, mock_agent):
        stream_data = {"chunk": "secret", "full": "secret"}
        filter_mock = MagicMock()
        filter_mock.process_chunk.return_value = "***"

        with patch(
            "python.extensions.reasoning_stream_chunk._10_mask_stream.get_secrets_manager"
        ) as mock_mgr:
            mock_mgr.return_value.create_streaming_filter.return_value = filter_mock
            mock_mgr.return_value.mask_values.return_value = "***"

            from python.extensions.reasoning_stream_chunk._10_mask_stream import (
                MaskReasoningStreamChunk,
            )

            ext = MaskReasoningStreamChunk(agent=mock_agent)
            await ext.execute(stream_data=stream_data, agent=mock_agent)

        assert stream_data["chunk"] == "***"


class TestMaskReasoningStreamEnd:
    """Tests for reasoning_stream_end/_10_mask_end.py."""

    @pytest.mark.asyncio
    async def test_returns_early_without_agent(self, mock_agent):
        from python.extensions.reasoning_stream_end._10_mask_end import (
            MaskReasoningStreamEnd,
        )

        ext = MaskReasoningStreamEnd(agent=mock_agent)
        await ext.execute(agent=None)

    @pytest.mark.asyncio
    async def test_finalizes_reasoning_filter(self, mock_agent):
        filter_mock = MagicMock()
        filter_mock.finalize.return_value = ""
        mock_agent.get_data.return_value = filter_mock

        from python.extensions.reasoning_stream_end._10_mask_end import (
            MaskReasoningStreamEnd,
        )

        ext = MaskReasoningStreamEnd(agent=mock_agent)
        await ext.execute(agent=mock_agent)

        mock_agent.set_data.assert_called_with("_reason_stream_filter", None)
