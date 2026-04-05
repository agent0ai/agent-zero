import sys
import threading
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from flask import Flask

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from agent import AgentContext
from initialize import initialize_agent
from api.stop import Stop


@pytest.fixture
def ctx():
    ctxid = "ctx-stop-test"
    context = AgentContext(config=initialize_agent(), id=ctxid, set_current=False)
    yield context
    AgentContext.remove(ctxid)


class TestAgentContextStop:
    """Unit tests for AgentContext.stop() method."""

    def test_stop_clears_paused_state(self, ctx):
        ctx.paused = True
        ctx.stop()
        assert ctx.paused is False

    def test_stop_clears_streaming_agent(self, ctx):
        ctx.streaming_agent = MagicMock()
        ctx.stop()
        assert ctx.streaming_agent is None

    def test_stop_calls_kill_process(self, ctx):
        with patch.object(ctx, "kill_process") as mock_kill:
            ctx.stop()
            mock_kill.assert_called_once()

    def test_stop_logs_info_message(self, ctx):
        initial_log_count = len(ctx.log.logs)
        ctx.stop()
        assert len(ctx.log.logs) > initial_log_count
        last_log = ctx.log.logs[-1]
        assert last_log.type == "info"
        assert "stopped" in last_log.content.lower()

    def test_stop_preserves_conversation_history(self, ctx):
        ctx.log.log(type="user", heading="test", content="hello world")
        log_count_before = len(ctx.log.logs)
        ctx.stop()
        # Should have original logs + the "stopped" info log
        assert len(ctx.log.logs) == log_count_before + 1

    def test_stop_does_not_reset_agent(self, ctx):
        original_agent = ctx.agent0
        ctx.stop()
        assert ctx.agent0 is original_agent

    def test_stop_when_not_running_is_safe(self, ctx):
        """Calling stop when nothing is running should not raise."""
        ctx.task = None
        ctx.paused = False
        ctx.streaming_agent = None
        ctx.stop()  # should not raise
        assert ctx.paused is False

    def test_stop_differs_from_nudge(self, ctx):
        """Stop should NOT restart the agent (unlike nudge)."""
        ctx.stop()
        # After stop, task should be None (no new task started)
        # nudge() would set self.task to a new communicate() call
        assert ctx.task is None

    def test_stop_differs_from_reset(self, ctx):
        """Stop should NOT clear the log (unlike reset)."""
        ctx.log.log(type="user", heading="test", content="preserved")
        ctx.stop()
        # reset() calls log.reset() which clears everything
        assert len(ctx.log.logs) >= 2  # original + stopped message


class TestStopApiHandler:
    """Tests for the api/stop.py endpoint."""

    @pytest.mark.asyncio
    async def test_stop_api_returns_success(self, ctx):
        app = Flask("stop-api-test")
        app.secret_key = "test-secret"
        lock = threading.RLock()

        handler = Stop(app, lock)
        result = await handler.process({"context": ctx.id}, None)

        assert result["message"] == "Agent stopped."
        assert result["context"] == ctx.id

    @pytest.mark.asyncio
    async def test_stop_api_raises_without_context_id(self):
        app = Flask("stop-api-test")
        app.secret_key = "test-secret"
        lock = threading.RLock()

        handler = Stop(app, lock)
        with pytest.raises(Exception, match="No context id provided"):
            await handler.process({"context": ""}, None)

    @pytest.mark.asyncio
    async def test_stop_api_actually_stops_agent(self, ctx):
        ctx.paused = True
        ctx.streaming_agent = MagicMock()

        app = Flask("stop-api-test")
        app.secret_key = "test-secret"
        lock = threading.RLock()

        handler = Stop(app, lock)
        await handler.process({"context": ctx.id}, None)

        assert ctx.paused is False
        assert ctx.streaming_agent is None
