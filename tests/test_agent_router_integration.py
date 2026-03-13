"""
Tests for agent.py LLM Router integration.

Validates:
1. get_chat_model() uses router when llm_router_enabled=True
2. get_utility_model() uses router when llm_router_enabled=True
3. call_chat_model() failover path sets loop_data.model_used
4. call_chat_model() falls back to default on router failure
5. Settings toggle controls router activation
"""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from agent import LoopData
from python.helpers.llm_router import (
    FailoverResult,
    ModelInfo,
    RoutingPriority,
)

# ── Helpers ──────────────────────────────────────────────────────────────────


def _make_model_info(provider="ollama", name="qwen2.5-coder:3b", **kw):
    return ModelInfo(
        provider=provider,
        name=name,
        display_name=kw.get("display_name", name),
        capabilities=kw.get("capabilities", ["chat", "code"]),
        is_local=kw.get("is_local", True),
        is_available=True,
        size_gb=kw.get("size_gb", 1.9),
        context_length=kw.get("context_length", 32768),
        cost_per_1k_input=0.0,
        cost_per_1k_output=0.0,
        metadata={},
    )


def _make_agent_mock():
    """Create a minimal mock agent with the required attributes."""
    agent = MagicMock()
    agent.config = MagicMock()
    agent.config.chat_model = MagicMock()
    agent.config.chat_model.provider = "openai"
    agent.config.chat_model.name = "gpt-4o"
    agent.config.chat_model.build_kwargs.return_value = {"temperature": 0.7}
    agent.config.utility_model = MagicMock()
    agent.config.utility_model.provider = "openai"
    agent.config.utility_model.name = "gpt-4o-mini"
    agent.config.utility_model.build_kwargs.return_value = {"temperature": 0.3}
    agent.config.browser_model = MagicMock()
    agent.config.browser_model.provider = "openai"
    agent.config.browser_model.name = "gpt-4o"
    agent.config.browser_model.build_kwargs.return_value = {"temperature": 0.0}
    agent.config.embeddings_model = MagicMock()
    agent.config.embeddings_model.provider = "openai"
    agent.config.embeddings_model.name = "text-embedding-3-small"
    agent.config.embeddings_model.build_kwargs.return_value = {}
    agent.loop_data = LoopData()
    return agent


@pytest.fixture(autouse=True)
def reset_router():
    import python.helpers.llm_router as lr

    lr._router_instance = None
    yield
    lr._router_instance = None


# ── 1. LoopData foundation ──────────────────────────────────────────────────


class TestLoopDataModelUsed:
    """Verify LoopData.model_used field behavior."""

    def test_default_is_empty_string(self):
        ld = LoopData()
        assert ld.model_used == ""

    def test_set_via_direct_assignment(self):
        ld = LoopData()
        ld.model_used = "anthropic/claude-sonnet-4-20250514"
        assert ld.model_used == "anthropic/claude-sonnet-4-20250514"

    def test_set_via_kwargs(self):
        ld = LoopData(model_used="ollama/qwen2.5-coder:3b")
        assert ld.model_used == "ollama/qwen2.5-coder:3b"

    def test_other_fields_unaffected(self):
        ld = LoopData(model_used="test/model")
        assert ld.iteration == -1
        assert ld.last_response == ""
        assert ld.system == []


# ── 2. get_chat_model() router integration ──────────────────────────────────


class TestGetChatModelRouter:
    """Test Agent.get_chat_model() with LLM router enabled/disabled."""

    def test_router_disabled_uses_config_model(self):
        """When llm_router_enabled is False, use configured chat model."""
        from agent import Agent

        settings_data = {"llm_router_enabled": False}

        with (
            patch("python.helpers.settings.get_settings", return_value=settings_data),
            patch("models.get_chat_model") as mock_gcm,
        ):
            mock_gcm.return_value = MagicMock(name="configured_model")
            agent = _make_agent_mock()
            # Call the actual method (unbound)
            result = Agent.get_chat_model(agent)

        # Should have called with full config kwargs
        mock_gcm.assert_called_once_with(
            "openai",
            "gpt-4o",
            model_config=agent.config.chat_model,
            temperature=0.7,
        )

    def test_router_enabled_selects_model(self):
        """When llm_router_enabled is True and router finds a model, use it."""
        from agent import Agent

        settings_data = {"llm_router_enabled": True}
        selected_model = _make_model_info("anthropic", "claude-sonnet-4-20250514")

        with (
            patch("python.helpers.settings.get_settings", return_value=settings_data),
            patch("python.helpers.llm_router.get_router") as mock_gr,
            patch("models.get_chat_model") as mock_gcm,
        ):
            router = MagicMock()
            router.select_model.return_value = selected_model
            mock_gr.return_value = router
            mock_gcm.return_value = MagicMock(name="router_model")

            agent = _make_agent_mock()
            result = Agent.get_chat_model(agent)

        # Router should select with chat role and QUALITY priority
        router.select_model.assert_called_once_with(
            role="chat",
            context_type="USER",
            priority=RoutingPriority.QUALITY,
            required_capabilities=["chat"],
        )
        # Should call get_chat_model with router-selected provider/name AND config kwargs
        mock_gcm.assert_called_once_with(
            "anthropic",
            "claude-sonnet-4-20250514",
            model_config=agent.config.chat_model,
            temperature=0.7,
        )

    def test_router_enabled_but_no_model_found_falls_back(self):
        """When router returns None, fall back to default config model."""
        from agent import Agent

        settings_data = {"llm_router_enabled": True}

        with (
            patch("python.helpers.settings.get_settings", return_value=settings_data),
            patch("python.helpers.llm_router.get_router") as mock_gr,
            patch("models.get_chat_model") as mock_gcm,
        ):
            router = MagicMock()
            router.select_model.return_value = None
            mock_gr.return_value = router
            mock_gcm.return_value = MagicMock()

            agent = _make_agent_mock()
            result = Agent.get_chat_model(agent)

        # Should fall through to default with full config
        mock_gcm.assert_called_once_with(
            "openai",
            "gpt-4o",
            model_config=agent.config.chat_model,
            temperature=0.7,
        )

    def test_router_enabled_but_exception_falls_back(self):
        """When router throws exception, fall back to default config model."""
        from agent import Agent

        settings_data = {"llm_router_enabled": True}

        with (
            patch("python.helpers.settings.get_settings", return_value=settings_data),
            patch("python.helpers.llm_router.get_router") as mock_gr,
            patch("models.get_chat_model") as mock_gcm,
        ):
            mock_gr.side_effect = RuntimeError("Router init failed")
            mock_gcm.return_value = MagicMock()

            agent = _make_agent_mock()
            result = Agent.get_chat_model(agent)

        # Should gracefully fall back
        mock_gcm.assert_called_once_with(
            "openai",
            "gpt-4o",
            model_config=agent.config.chat_model,
            temperature=0.7,
        )


# ── 3. get_utility_model() router integration ──────────────────────────────


class TestGetUtilityModelRouter:
    """Test Agent.get_utility_model() with LLM router."""

    def test_router_selects_utility_model_with_speed_priority(self):
        """Router should use SPEED priority for utility model."""
        from agent import Agent

        settings_data = {"llm_router_enabled": True}
        selected_model = _make_model_info("openai", "gpt-4o-mini")

        with (
            patch("python.helpers.settings.get_settings", return_value=settings_data),
            patch("python.helpers.llm_router.get_router") as mock_gr,
            patch("models.get_chat_model") as mock_gcm,
        ):
            router = MagicMock()
            router.select_model.return_value = selected_model
            mock_gr.return_value = router
            mock_gcm.return_value = MagicMock()

            agent = _make_agent_mock()
            result = Agent.get_utility_model(agent)

        router.select_model.assert_called_once_with(
            role="utility",
            context_type="TASK",
            priority=RoutingPriority.SPEED,
            required_capabilities=["chat"],
        )
        mock_gcm.assert_called_once_with(
            "openai",
            "gpt-4o-mini",
            model_config=agent.config.utility_model,
            temperature=0.3,
        )


# ── 4. call_chat_model() failover path ─────────────────────────────────────


class TestCallChatModelFailover:
    """Test Agent.call_chat_model() with LLM router failover."""

    @pytest.mark.asyncio
    async def test_failover_success_sets_model_used(self):
        """Successful failover should set loop_data.model_used."""
        from agent import Agent

        settings_data = {"llm_router_enabled": True}
        selected = _make_model_info("anthropic", "claude-sonnet-4-20250514")
        failover_result = FailoverResult(
            success=True,
            response="Hello from Claude!",
            reasoning="",
            error=None,
            model_used=selected,
            attempts=1,
        )

        agent = _make_agent_mock()
        agent.get_thinking_kwargs = MagicMock(return_value={})
        agent.rate_limiter_callback = AsyncMock()

        with (
            patch("python.helpers.settings.get_settings", return_value=settings_data),
            patch("python.helpers.llm_router.get_router") as mock_gr,
            patch("python.helpers.llm_router.call_with_failover", new_callable=AsyncMock) as mock_cwf,
        ):
            router = MagicMock()
            router.select_model.return_value = selected
            mock_gr.return_value = router
            mock_cwf.return_value = failover_result

            response, reasoning = await Agent.call_chat_model(agent, messages=[])

        assert response == "Hello from Claude!"
        assert agent.loop_data.model_used == "anthropic/claude-sonnet-4-20250514"

    @pytest.mark.asyncio
    async def test_failover_all_fail_falls_back_to_default(self):
        """When all failover attempts fail, fall back to default model."""
        from agent import Agent

        settings_data = {"llm_router_enabled": True}
        selected = _make_model_info("openai", "gpt-4o")
        failover_result = FailoverResult(
            success=False,
            response="",
            reasoning="",
            error="All models failed",
            model_used=selected,
            attempts=3,
        )

        agent = _make_agent_mock()
        agent.get_thinking_kwargs = MagicMock(return_value={})
        agent.get_chat_model = MagicMock()
        agent.rate_limiter_callback = AsyncMock()

        mock_model = MagicMock()
        mock_model.unified_call = AsyncMock(return_value=("Default response", ""))
        agent.get_chat_model.return_value = mock_model

        with (
            patch("python.helpers.settings.get_settings", return_value=settings_data),
            patch("python.helpers.llm_router.get_router") as mock_gr,
            patch("python.helpers.llm_router.call_with_failover", new_callable=AsyncMock) as mock_cwf,
        ):
            router = MagicMock()
            router.select_model.return_value = selected
            mock_gr.return_value = router
            mock_cwf.return_value = failover_result

            response, reasoning = await Agent.call_chat_model(agent, messages=[])

        assert response == "Default response"
        # model_used should show the default model
        assert agent.loop_data.model_used == "openai/gpt-4o"

    @pytest.mark.asyncio
    async def test_router_exception_falls_back_to_default(self):
        """Router system error should gracefully fall back to default model."""
        from agent import Agent

        settings_data = {"llm_router_enabled": True}

        agent = _make_agent_mock()
        agent.get_thinking_kwargs = MagicMock(return_value={})
        agent.get_chat_model = MagicMock()
        agent.rate_limiter_callback = AsyncMock()

        mock_model = MagicMock()
        mock_model.unified_call = AsyncMock(return_value=("Fallback response", ""))
        agent.get_chat_model.return_value = mock_model

        with (
            patch("python.helpers.settings.get_settings", return_value=settings_data),
            patch("python.helpers.llm_router.get_router") as mock_gr,
        ):
            mock_gr.side_effect = RuntimeError("Router DB corrupted")

            response, reasoning = await Agent.call_chat_model(agent, messages=[])

        assert response == "Fallback response"
        # Default model info should still be recorded
        assert agent.loop_data.model_used == "openai/gpt-4o"

    @pytest.mark.asyncio
    async def test_router_disabled_uses_default_directly(self):
        """When router disabled, call default model directly and set model_used."""
        from agent import Agent

        settings_data = {"llm_router_enabled": False}

        agent = _make_agent_mock()
        agent.get_thinking_kwargs = MagicMock(return_value={})
        agent.get_chat_model = MagicMock()
        agent.rate_limiter_callback = AsyncMock()

        mock_model = MagicMock()
        mock_model.unified_call = AsyncMock(return_value=("Direct response", "thinking..."))
        agent.get_chat_model.return_value = mock_model

        with patch("python.helpers.settings.get_settings", return_value=settings_data):
            response, reasoning = await Agent.call_chat_model(agent, messages=[])

        assert response == "Direct response"
        assert reasoning == "thinking..."
        assert agent.loop_data.model_used == "openai/gpt-4o"


# ── 5. Settings integration ────────────────────────────────────────────────


class TestSettingsIntegration:
    """Verify settings correctly control router behavior."""

    def test_setting_defaults_to_false_when_missing(self):
        """set.get('llm_router_enabled', False) returns False when key absent."""
        from agent import Agent

        settings_data = {}  # no llm_router_enabled key

        with (
            patch("python.helpers.settings.get_settings", return_value=settings_data),
            patch("models.get_chat_model") as mock_gcm,
        ):
            mock_gcm.return_value = MagicMock()
            agent = _make_agent_mock()
            result = Agent.get_chat_model(agent)

        # Should use default model (router not activated)
        mock_gcm.assert_called_once_with(
            "openai",
            "gpt-4o",
            model_config=agent.config.chat_model,
            temperature=0.7,
        )

    def test_setting_explicitly_false_disables_router(self):
        from agent import Agent

        settings_data = {"llm_router_enabled": False}

        with (
            patch("python.helpers.settings.get_settings", return_value=settings_data),
            patch("models.get_chat_model") as mock_gcm,
        ):
            mock_gcm.return_value = MagicMock()
            agent = _make_agent_mock()
            result = Agent.get_chat_model(agent)

        mock_gcm.assert_called_once_with(
            "openai",
            "gpt-4o",
            model_config=agent.config.chat_model,
            temperature=0.7,
        )


# ── 6. Model label format ──────────────────────────────────────────────────


class TestModelLabelFormat:
    """Verify the model_used label format is 'provider/name'."""

    @pytest.mark.asyncio
    async def test_label_format_router_path(self):
        from agent import Agent

        settings_data = {"llm_router_enabled": True}
        selected = _make_model_info("google", "gemini-2.0-flash")
        failover_result = FailoverResult(
            success=True,
            response="Hi!",
            reasoning="",
            error=None,
            model_used=selected,
            attempts=1,
        )

        agent = _make_agent_mock()
        agent.get_thinking_kwargs = MagicMock(return_value={})
        agent.rate_limiter_callback = AsyncMock()

        with (
            patch("python.helpers.settings.get_settings", return_value=settings_data),
            patch("python.helpers.llm_router.get_router") as mock_gr,
            patch("python.helpers.llm_router.call_with_failover", new_callable=AsyncMock) as mock_cwf,
        ):
            router = MagicMock()
            router.select_model.return_value = selected
            mock_gr.return_value = router
            mock_cwf.return_value = failover_result

            await Agent.call_chat_model(agent, messages=[])

        # Format must be "provider/name"
        assert agent.loop_data.model_used == "google/gemini-2.0-flash"
        assert "/" in agent.loop_data.model_used
        parts = agent.loop_data.model_used.split("/")
        assert len(parts) == 2
        assert parts[0] == "google"
        assert parts[1] == "gemini-2.0-flash"

    @pytest.mark.asyncio
    async def test_label_format_default_path(self):
        from agent import Agent

        settings_data = {"llm_router_enabled": False}

        agent = _make_agent_mock()
        agent.config.chat_model.provider = "anthropic"
        agent.config.chat_model.name = "claude-sonnet-4-20250514"
        agent.get_thinking_kwargs = MagicMock(return_value={})
        agent.get_chat_model = MagicMock()
        agent.rate_limiter_callback = AsyncMock()

        mock_model = MagicMock()
        mock_model.unified_call = AsyncMock(return_value=("response", ""))
        agent.get_chat_model.return_value = mock_model

        with patch("python.helpers.settings.get_settings", return_value=settings_data):
            await Agent.call_chat_model(agent, messages=[])

        assert agent.loop_data.model_used == "anthropic/claude-sonnet-4-20250514"


# ── 7. get_browser_model() router integration ──────────────────────────────


class TestGetBrowserModelRouter:
    """Test Agent.get_browser_model() with LLM router."""

    def test_router_selects_browser_model_with_vision(self):
        """Router should use QUALITY priority and require vision for browser."""
        from agent import Agent

        settings_data = {"llm_router_enabled": True}
        selected_model = _make_model_info("anthropic", "claude-sonnet-4-20250514")

        with (
            patch("python.helpers.settings.get_settings", return_value=settings_data),
            patch("python.helpers.llm_router.get_router") as mock_gr,
            patch("models.get_browser_model") as mock_gbm,
        ):
            router = MagicMock()
            router.select_model.return_value = selected_model
            mock_gr.return_value = router
            mock_gbm.return_value = MagicMock()

            agent = _make_agent_mock()
            result = Agent.get_browser_model(agent)

        router.select_model.assert_called_once_with(
            role="browser",
            context_type="TASK",
            priority=RoutingPriority.QUALITY,
            required_capabilities=["chat", "vision"],
        )
        mock_gbm.assert_called_once_with(
            "anthropic",
            "claude-sonnet-4-20250514",
            model_config=agent.config.browser_model,
            temperature=0.0,
        )

    def test_browser_model_disabled_uses_config(self):
        """When router disabled, use config model directly."""
        from agent import Agent

        settings_data = {"llm_router_enabled": False}

        with (
            patch("python.helpers.settings.get_settings", return_value=settings_data),
            patch("models.get_browser_model") as mock_gbm,
        ):
            mock_gbm.return_value = MagicMock()
            agent = _make_agent_mock()
            result = Agent.get_browser_model(agent)

        mock_gbm.assert_called_once_with(
            "openai",
            "gpt-4o",
            model_config=agent.config.browser_model,
            temperature=0.0,
        )

    def test_browser_model_router_exception_falls_back(self):
        """Router error should fall back to config model."""
        from agent import Agent

        settings_data = {"llm_router_enabled": True}

        with (
            patch("python.helpers.settings.get_settings", return_value=settings_data),
            patch("python.helpers.llm_router.get_router") as mock_gr,
            patch("models.get_browser_model") as mock_gbm,
        ):
            mock_gr.side_effect = RuntimeError("Router init failed")
            mock_gbm.return_value = MagicMock()

            agent = _make_agent_mock()
            result = Agent.get_browser_model(agent)

        mock_gbm.assert_called_once_with(
            "openai",
            "gpt-4o",
            model_config=agent.config.browser_model,
            temperature=0.0,
        )


# ── 8. get_embedding_model() router integration ────────────────────────────


class TestGetEmbeddingModelRouter:
    """Test Agent.get_embedding_model() with LLM router."""

    def test_router_selects_embedding_model(self):
        """Router should require embedding capability."""
        from agent import Agent

        settings_data = {"llm_router_enabled": True}
        selected_model = _make_model_info("openai", "text-embedding-3-large")

        with (
            patch("python.helpers.settings.get_settings", return_value=settings_data),
            patch("python.helpers.llm_router.get_router") as mock_gr,
            patch("models.get_embedding_model") as mock_gem,
        ):
            router = MagicMock()
            router.select_model.return_value = selected_model
            mock_gr.return_value = router
            mock_gem.return_value = MagicMock()

            agent = _make_agent_mock()
            result = Agent.get_embedding_model(agent)

        router.select_model.assert_called_once_with(
            role="embedding",
            context_type="TASK",
            required_capabilities=["embedding"],
        )
        mock_gem.assert_called_once_with(
            "openai",
            "text-embedding-3-large",
            model_config=agent.config.embeddings_model,
        )

    def test_embedding_model_disabled_uses_config(self):
        """When router disabled, use config model directly."""
        from agent import Agent

        settings_data = {"llm_router_enabled": False}

        with (
            patch("python.helpers.settings.get_settings", return_value=settings_data),
            patch("models.get_embedding_model") as mock_gem,
        ):
            mock_gem.return_value = MagicMock()
            agent = _make_agent_mock()
            result = Agent.get_embedding_model(agent)

        mock_gem.assert_called_once_with(
            "openai",
            "text-embedding-3-small",
            model_config=agent.config.embeddings_model,
        )

    def test_embedding_model_router_no_model_falls_back(self):
        """When router returns None, fall back to config model."""
        from agent import Agent

        settings_data = {"llm_router_enabled": True}

        with (
            patch("python.helpers.settings.get_settings", return_value=settings_data),
            patch("python.helpers.llm_router.get_router") as mock_gr,
            patch("models.get_embedding_model") as mock_gem,
        ):
            router = MagicMock()
            router.select_model.return_value = None
            mock_gr.return_value = router
            mock_gem.return_value = MagicMock()

            agent = _make_agent_mock()
            result = Agent.get_embedding_model(agent)

        mock_gem.assert_called_once_with(
            "openai",
            "text-embedding-3-small",
            model_config=agent.config.embeddings_model,
        )
