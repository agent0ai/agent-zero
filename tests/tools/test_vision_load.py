"""Tests for python/tools/vision_load.py — VisionLoad tool."""

import sys
from pathlib import Path
from unittest.mock import MagicMock, AsyncMock, patch

import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


@pytest.fixture
def mock_agent():
    agent = MagicMock()
    agent.context = MagicMock()
    agent.context.log = MagicMock()
    agent.context.log.log = MagicMock(return_value=MagicMock())
    agent.hist_add_message = MagicMock()
    agent.hist_add_tool_result = MagicMock()
    return agent


@pytest.fixture
def tool(mock_agent):
    from python.tools.vision_load import VisionLoad
    t = VisionLoad(
        agent=mock_agent,
        name="vision_load",
        method=None,
        args={},
        message="",
        loop_data=None,
    )
    t.log = MagicMock(update=MagicMock())
    return t


class TestVisionLoadExecute:
    @pytest.mark.asyncio
    async def test_empty_paths_returns_dummy(self, tool):
        resp = await tool.execute(paths=[])
        assert resp.message == "dummy"
        assert resp.break_loop is False

    @pytest.mark.asyncio
    async def test_skips_nonexistent_paths(self, tool):
        with patch("python.tools.vision_load.runtime.call_development_function", new_callable=AsyncMock) as mock_exists:
            mock_exists.return_value = False
            resp = await tool.execute(paths=["/nonexistent/image.png"])
        assert tool.images_dict == {}
        assert resp.message == "dummy"

    @pytest.mark.asyncio
    async def test_processes_existing_image_path(self, tool):
        import base64
        fake_b64 = base64.b64encode(b"\xff\xd8\xff\xe0\x00\x10JFIF" + b"\x00" * 500).decode("utf-8")

        async def mock_dev(fn, *args):
            if fn.__name__ == "exists":
                return True
            return fake_b64

        with patch("python.tools.vision_load.runtime.call_development_function", new_callable=AsyncMock, side_effect=mock_dev):
            with patch("python.tools.vision_load.images.compress_image", return_value=b"\xff\xd8\xff"):
                resp = await tool.execute(paths=["/tmp/real.png"])
        assert resp.message == "dummy"
        assert "/tmp/real.png" in tool.images_dict
        assert tool.images_dict["/tmp/real.png"] is not None

    @pytest.mark.asyncio
    async def test_handles_image_processing_error(self, tool):
        with patch("python.tools.vision_load.runtime.call_development_function", new_callable=AsyncMock) as mock_dev:
            async def mock_dev_impl(fn, *args):
                if fn.__name__ == "exists":
                    return True
                raise ValueError("Invalid image")
            mock_dev.side_effect = mock_dev_impl
            with patch("python.tools.vision_load.PrintStyle") as mock_ps:
                mock_ps.return_value.error = MagicMock()
                resp = await tool.execute(paths=["/tmp/bad.png"])
        assert "/tmp/bad.png" in tool.images_dict
        assert tool.images_dict["/tmp/bad.png"] is None


class TestVisionLoadAfterExecution:
    @pytest.mark.asyncio
    async def test_after_execution_adds_images_to_history(self, tool):
        from python.helpers.tool import Response
        tool.images_dict = {"/img.png": "base64data"}
        resp = Response(message="dummy", break_loop=False)
        await tool.after_execution(resp)
        tool.agent.hist_add_message.assert_called_once()
        call_args = tool.agent.hist_add_message.call_args
        assert call_args[0][0] is False  # is_user
        assert "content" in call_args[1]

    @pytest.mark.asyncio
    async def test_after_execution_adds_error_for_failed_image(self, tool):
        from python.helpers.tool import Response
        tool.images_dict = {"/bad.png": None}
        resp = Response(message="dummy", break_loop=False)
        await tool.after_execution(resp)
        tool.agent.hist_add_message.assert_called_once()
        msg = tool.agent.hist_add_message.call_args[1]["content"]
        raw = msg["raw_content"] if isinstance(msg, dict) else getattr(msg, "raw_content", msg)
        assert any("Error processing" in str(item.get("text", "")) for item in raw if isinstance(item, dict))

    @pytest.mark.asyncio
    async def test_after_execution_adds_tool_result_when_no_images(self, tool):
        from python.helpers.tool import Response
        tool.images_dict = {}
        resp = Response(message="dummy", break_loop=False)
        await tool.after_execution(resp)
        tool.agent.hist_add_tool_result.assert_called_once_with("vision_load", "No images processed")
