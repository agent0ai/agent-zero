"""Tests for python/helpers/tool.py — Tool base class, Response, set_progress, nice_key."""

import sys
from pathlib import Path
from unittest.mock import MagicMock, AsyncMock, patch

import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

try:
    from python.helpers.tool import Tool, Response
except ImportError:
    pytest.skip("Cannot import tool module (heavy deps)", allow_module_level=True)


class ConcreteTool(Tool):
    async def execute(self, **kwargs):
        return Response(message="done", break_loop=False)


class TestResponse:
    def test_response_dataclass(self):
        r = Response(message="ok", break_loop=True, additional={"key": "val"})
        assert r.message == "ok"
        assert r.break_loop is True
        assert r.additional == {"key": "val"}

    def test_response_additional_default_none(self):
        r = Response(message="x", break_loop=False)
        assert r.additional is None


class TestToolBase:
    @pytest.fixture
    def mock_agent(self):
        a = MagicMock()
        a.agent_name = "TestAgent"
        a.context = MagicMock()
        a.context.log = MagicMock()
        a.context.log.log = MagicMock(return_value=MagicMock(update=MagicMock()))
        a.hist_add_tool_result = MagicMock()
        return a

    def test_init_stores_args(self, mock_agent):
        t = ConcreteTool(
            agent=mock_agent,
            name="my_tool",
            method="run",
            args={"a": "1"},
            message="msg",
            loop_data=None,
        )
        assert t.name == "my_tool"
        assert t.method == "run"
        assert t.args == {"a": "1"}
        assert t.message == "msg"
        assert t.progress == ""

    def test_set_progress(self, mock_agent):
        t = ConcreteTool(mock_agent, "t", None, {}, "m", None)
        t.set_progress("50%")
        assert t.progress == "50%"
        t.set_progress(None)
        assert t.progress == ""

    def test_add_progress_appends(self, mock_agent):
        t = ConcreteTool(mock_agent, "t", None, {}, "m", None)
        t.add_progress("a")
        t.add_progress("b")
        assert t.progress == "ab"
        t.add_progress(None)
        assert t.progress == "ab"

    def test_nice_key(self, mock_agent):
        t = ConcreteTool(mock_agent, "t", None, {}, "m", None)
        assert t.nice_key("file_name") == "File name"
        assert t.nice_key("some_key") == "Some key"

    def test_get_log_object_with_method(self, mock_agent):
        t = ConcreteTool(mock_agent, "t", "run", {}, "m", None)
        log = t.get_log_object()
        if hasattr(log, "update"):
            mock_agent.context.log.log.assert_called_once()
        call_kw = mock_agent.context.log.log.call_args[1]
        assert "t:run" in str(call_kw.get("heading", ""))

    def test_get_log_object_without_method(self, mock_agent):
        t = ConcreteTool(mock_agent, "t", None, {}, "m", None)
        t.get_log_object()
        call_kw = mock_agent.context.log.log.call_args[1]
        assert "t" in str(call_kw.get("heading", ""))
