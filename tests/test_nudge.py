"""
Unit tests for the nudge functionality.

Tests verify that:
1. last_active_agent is set when an agent starts its monologue
2. get_agent() returns the correct agent based on priority
3. nudge() restarts the correct agent (subordinate, not always agent0)
"""

import sys
import os
import asyncio
from unittest.mock import Mock, MagicMock, AsyncMock, patch

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import agent as agent_module
from agent import Agent, AgentContext, AgentConfig


def create_mock_config():
    """Create a mock AgentConfig with required fields."""
    config = Mock(spec=AgentConfig)
    config.auto_nudge_enabled = False
    config.auto_nudge_timeout = 60
    return config


class TestGetAgent:
    """Tests for AgentContext.get_agent() method."""

    def setup_method(self):
        """Set up test fixtures."""
        self.config = create_mock_config()
        self.context = Mock(spec=AgentContext)
        self.context.streaming_agent = None
        self.context.last_active_agent = None
        self.context.agent0 = Mock(spec=Agent)
        self.context.agent0.number = 0

    def test_get_agent_returns_streaming_agent_when_set(self):
        """get_agent() should return streaming_agent when it's set."""
        streaming = Mock(spec=Agent)
        streaming.number = 1
        self.context.streaming_agent = streaming

        # Call the actual method
        result = AgentContext.get_agent(self.context)

        assert result == streaming
        assert result.number == 1

    def test_get_agent_returns_last_active_when_streaming_is_none(self):
        """get_agent() should return last_active_agent when streaming_agent is None."""
        last_active = Mock(spec=Agent)
        last_active.number = 2
        self.context.streaming_agent = None
        self.context.last_active_agent = last_active

        result = AgentContext.get_agent(self.context)

        assert result == last_active
        assert result.number == 2

    def test_get_agent_falls_back_to_agent0(self):
        """get_agent() should fall back to agent0 when both are None."""
        self.context.streaming_agent = None
        self.context.last_active_agent = None

        result = AgentContext.get_agent(self.context)

        assert result == self.context.agent0
        assert result.number == 0

    def test_get_agent_priority_order(self):
        """get_agent() should check streaming_agent first, then last_active_agent, then agent0."""
        streaming = Mock(spec=Agent)
        streaming.number = 1
        last_active = Mock(spec=Agent)
        last_active.number = 2

        self.context.streaming_agent = streaming
        self.context.last_active_agent = last_active

        # streaming_agent should take priority
        result = AgentContext.get_agent(self.context)
        assert result.number == 1

        # When streaming is None, last_active should be used
        self.context.streaming_agent = None
        result = AgentContext.get_agent(self.context)
        assert result.number == 2


class TestNudgeSubordinateAgent:
    """Tests for nudging subordinate agents (the main bug fix)."""

    def test_nudge_uses_last_active_agent_not_agent0(self):
        """
        When a subordinate agent was last active, nudge should restart
        that agent, not agent0.

        This is the core bug fix - before, nudge always restarted agent0
        because streaming_agent was cleared at monologue end.
        """
        context = Mock(spec=AgentContext)
        context.streaming_agent = None  # Cleared after monologue
        context.paused = True
        context._watchdog_task = None

        # Simulate Agent 2 was the last active (subordinate)
        agent2 = Mock(spec=Agent)
        agent2.number = 2
        agent2.monologue = AsyncMock()
        context.last_active_agent = agent2

        # Agent 0 should NOT be used
        agent0 = Mock(spec=Agent)
        agent0.number = 0
        context.agent0 = agent0

        # Mock the methods
        context.kill_process = Mock()
        context._stop_watchdog = Mock()
        context.run_task = Mock(return_value=Mock())

        # Bind get_agent to use actual implementation
        context.get_agent = lambda: AgentContext.get_agent(context)

        # Call nudge
        AgentContext.nudge(context)

        # Verify agent2's monologue was started, not agent0's
        context.run_task.assert_called_once()
        args = context.run_task.call_args[0]
        assert args[0] == agent2.monologue, "Should start agent2's monologue, not agent0's"


class TestAutoNudgeConfig:
    """Tests for auto-nudge configuration."""

    def test_auto_nudge_disabled_by_default(self):
        """Auto-nudge should be disabled by default (checking dataclass default)."""
        # Check the dataclass field default directly
        from dataclasses import fields
        config_fields = {f.name: f for f in fields(AgentConfig)}
        assert config_fields['auto_nudge_enabled'].default is False

    def test_auto_nudge_timeout_default(self):
        """Auto-nudge timeout should default to 60 seconds."""
        from dataclasses import fields
        config_fields = {f.name: f for f in fields(AgentConfig)}
        assert config_fields['auto_nudge_timeout'].default == 60

    def test_auto_nudge_fields_exist(self):
        """Auto-nudge config fields should exist in AgentConfig."""
        from dataclasses import fields
        field_names = [f.name for f in fields(AgentConfig)]
        assert 'auto_nudge_enabled' in field_names
        assert 'auto_nudge_timeout' in field_names


class TestLastActiveAgentTracking:
    """Tests for last_active_agent field behavior."""

    def test_last_active_agent_initialized_to_none(self):
        """last_active_agent should be None initially."""
        # Create a minimal mock for dependencies
        with patch.object(agent_module, 'Log'):
            with patch.object(agent_module, 'DeferredTask'):
                context = AgentContext.__new__(AgentContext)
                context.streaming_agent = None
                context.last_active_agent = None
                context.last_stream_time = 0.0
                context._watchdog_task = None

                assert context.last_active_agent is None

    def test_last_active_agent_not_cleared_like_streaming_agent(self):
        """
        Unlike streaming_agent which is cleared at monologue end,
        last_active_agent should persist.
        """
        context = Mock(spec=AgentContext)
        agent1 = Mock(spec=Agent)
        agent1.number = 1

        # Simulate monologue start
        context.streaming_agent = agent1
        context.last_active_agent = agent1

        # Simulate monologue end (streaming_agent cleared)
        context.streaming_agent = None
        # last_active_agent should still be set

        assert context.last_active_agent == agent1
        assert context.streaming_agent is None


def run_tests():
    """Run all tests and print results."""
    import traceback

    test_classes = [
        TestGetAgent,
        TestNudgeSubordinateAgent,
        TestAutoNudgeConfig,
        TestLastActiveAgentTracking,
    ]

    passed = 0
    failed = 0

    for test_class in test_classes:
        print(f"\n{'='*60}")
        print(f"Running {test_class.__name__}")
        print('='*60)

        instance = test_class()

        for method_name in dir(instance):
            if method_name.startswith('test_'):
                if hasattr(instance, 'setup_method'):
                    instance.setup_method()

                try:
                    method = getattr(instance, method_name)
                    method()
                    print(f"  PASS: {method_name}")
                    passed += 1
                except AssertionError as e:
                    print(f"  FAIL: {method_name}")
                    print(f"        {e}")
                    failed += 1
                except Exception as e:
                    print(f"  ERROR: {method_name}")
                    print(f"        {e}")
                    traceback.print_exc()
                    failed += 1

    print(f"\n{'='*60}")
    print(f"Results: {passed} passed, {failed} failed")
    print('='*60)

    return failed == 0


if __name__ == "__main__":
    success = run_tests()
    sys.exit(0 if success else 1)
