"""
Tests for LLM Router API handlers.

Validates all 10 LLM Router API endpoints and the model_selector_quick_switch
endpoint return correct response shapes with proper keys, edge-case handling,
and error paths.

Uses the DummyRequest + SimpleNamespace pattern established in test_calendar_api.py.
"""

import json
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from python.helpers.llm_router import (
    ModelInfo,
    RoutingPriority,
    RoutingRule,
)

# ── Helpers ──────────────────────────────────────────────────────────────────


def _make_model(provider="ollama", name="qwen2.5-coder:3b", is_local=True, **kw):
    return ModelInfo(
        provider=provider,
        name=name,
        display_name=kw.get("display_name", name),
        capabilities=kw.get("capabilities", ["chat", "code"]),
        is_local=is_local,
        is_available=True,
        size_gb=kw.get("size_gb", 1.9),
        context_length=kw.get("context_length", 32768),
        cost_per_1k_input=kw.get("cost_per_1k_input", 0.0),
        cost_per_1k_output=kw.get("cost_per_1k_output", 0.0),
        metadata=kw.get("metadata", {}),
    )


SAMPLE_MODELS = [
    _make_model(
        "ollama", "qwen2.5-coder:3b", True, display_name="Qwen 2.5 Coder 3B", capabilities=["chat", "code", "baseline"]
    ),
    _make_model(
        "openai",
        "gpt-4o",
        False,
        display_name="GPT-4o",
        capabilities=["chat", "code", "reasoning"],
        context_length=128000,
        cost_per_1k_input=2.5,
        cost_per_1k_output=10.0,
    ),
    _make_model(
        "anthropic",
        "claude-sonnet-4-20250514",
        False,
        display_name="Claude Sonnet 4",
        capabilities=["chat", "code", "reasoning"],
        context_length=200000,
        cost_per_1k_input=3.0,
        cost_per_1k_output=15.0,
    ),
]


class DummyRequest:
    """Minimal request mock for API handler tests."""

    def __init__(self, payload=None):
        self._payload = payload or {}
        self.is_json = True
        self.data = json.dumps(self._payload).encode("utf-8")

    def get_json(self):
        return self._payload


@pytest.fixture(autouse=True)
def reset_router_singleton():
    """Reset the router singleton between tests."""
    import python.helpers.llm_router as lr

    lr._router_instance = None
    yield
    lr._router_instance = None


def _mock_router(models=None, defaults=None, usage=None, rules=None):
    """Create a mock router with configurable returns."""
    router = MagicMock()
    router.db.get_models.return_value = models or []
    router.get_default_model.side_effect = lambda role: defaults.get(role) if defaults else None
    router.get_usage_stats.return_value = usage or {"totalCalls": 0, "totalCost": 0.0, "byModel": []}
    router.get_routing_rules.return_value = rules or []
    router.db.get_routing_rules.return_value = rules or []
    router.db.delete_routing_rule.return_value = True
    router.db.toggle_routing_rule.return_value = True
    router.select_model.return_value = (models or [None])[0]
    router.get_fallback_chain.return_value = (models or [])[1:] if models and len(models) > 1 else []
    router.discover_models = AsyncMock(return_value=models or [])
    router.set_default_model.return_value = None
    router.add_routing_rule.return_value = None
    router.record_call.return_value = None
    return router


# ── 1. llm_router_models ────────────────────────────────────────────────────


class TestLlmRouterModels:
    """Test /llm_router_models endpoint."""

    @pytest.mark.asyncio
    async def test_returns_all_models(self):
        from python.api.llm_router_models import LlmRouterModels

        handler = LlmRouterModels(SimpleNamespace(), SimpleNamespace())
        with patch("python.api.llm_router_models.get_router") as mock_gr:
            mock_gr.return_value = _mock_router(models=SAMPLE_MODELS)
            result = await handler.process({}, DummyRequest())

        assert result["success"] is True
        assert result["count"] == 3
        assert len(result["models"]) == 3
        assert result["models"][0]["provider"] == "ollama"

    @pytest.mark.asyncio
    async def test_filter_by_provider(self):
        from python.api.llm_router_models import LlmRouterModels

        handler = LlmRouterModels(SimpleNamespace(), SimpleNamespace())
        with patch("python.api.llm_router_models.get_router") as mock_gr:
            router = _mock_router()
            router.db.get_models.return_value = [SAMPLE_MODELS[1]]  # only openai
            mock_gr.return_value = router
            result = await handler.process({"provider": "openai"}, DummyRequest())

        assert result["success"] is True
        assert result["count"] == 1
        assert result["models"][0]["provider"] == "openai"

    @pytest.mark.asyncio
    async def test_empty_models(self):
        from python.api.llm_router_models import LlmRouterModels

        handler = LlmRouterModels(SimpleNamespace(), SimpleNamespace())
        with patch("python.api.llm_router_models.get_router") as mock_gr:
            mock_gr.return_value = _mock_router(models=[])
            result = await handler.process({}, DummyRequest())

        assert result["success"] is True
        assert result["count"] == 0
        assert result["models"] == []


# ── 2. llm_router_get_defaults ──────────────────────────────────────────────


class TestLlmRouterGetDefaults:
    """Test /llm_router_get_defaults endpoint."""

    @pytest.mark.asyncio
    async def test_returns_all_five_roles(self):
        from python.api.llm_router_get_defaults import LlmRouterGetDefaults

        handler = LlmRouterGetDefaults(SimpleNamespace(), SimpleNamespace())
        defaults = {
            "chat": ("anthropic", "claude-sonnet-4-20250514"),
            "utility": ("openai", "gpt-4o-mini"),
        }
        with patch("python.api.llm_router_get_defaults.get_router") as mock_gr:
            mock_gr.return_value = _mock_router(defaults=defaults)
            result = await handler.process({}, DummyRequest())

        assert result["success"] is True
        # All 5 roles must be present
        for role in ["chat", "utility", "browser", "embedding", "fallback"]:
            assert role in result["defaults"]

        # Set ones have structure
        assert result["defaults"]["chat"]["provider"] == "anthropic"
        assert result["defaults"]["chat"]["modelName"] == "claude-sonnet-4-20250514"
        assert result["defaults"]["utility"]["provider"] == "openai"

        # Unset ones are None
        assert result["defaults"]["browser"] is None
        assert result["defaults"]["embedding"] is None
        assert result["defaults"]["fallback"] is None

    @pytest.mark.asyncio
    async def test_no_defaults_set(self):
        from python.api.llm_router_get_defaults import LlmRouterGetDefaults

        handler = LlmRouterGetDefaults(SimpleNamespace(), SimpleNamespace())
        with patch("python.api.llm_router_get_defaults.get_router") as mock_gr:
            mock_gr.return_value = _mock_router(defaults={})
            result = await handler.process({}, DummyRequest())

        assert result["success"] is True
        assert all(v is None for v in result["defaults"].values())


# ── 3. llm_router_set_default ───────────────────────────────────────────────


class TestLlmRouterSetDefault:
    """Test /llm_router_set_default endpoint."""

    @pytest.mark.asyncio
    async def test_set_default_success(self):
        from python.api.llm_router_set_default import LlmRouterSetDefault

        handler = LlmRouterSetDefault(SimpleNamespace(), SimpleNamespace())
        with patch("python.api.llm_router_set_default.get_router") as mock_gr:
            router = _mock_router(models=SAMPLE_MODELS)
            router.db.get_models.return_value = [SAMPLE_MODELS[1]]  # openai model
            mock_gr.return_value = router

            result = await handler.process(
                {"role": "chat", "provider": "openai", "model_name": "gpt-4o"}, DummyRequest()
            )

        assert result["success"] is True
        assert result["role"] == "chat"
        assert result["provider"] == "openai"
        assert result["modelName"] == "gpt-4o"
        router.set_default_model.assert_called_once_with("chat", "openai", "gpt-4o")

    @pytest.mark.asyncio
    async def test_set_default_missing_params(self):
        from python.api.llm_router_set_default import LlmRouterSetDefault

        handler = LlmRouterSetDefault(SimpleNamespace(), SimpleNamespace())
        with patch("python.api.llm_router_set_default.get_router") as mock_gr:
            mock_gr.return_value = _mock_router()
            result = await handler.process({"role": "chat"}, DummyRequest())

        assert result["success"] is False
        assert "required" in result["error"].lower()

    @pytest.mark.asyncio
    async def test_set_default_model_not_found(self):
        from python.api.llm_router_set_default import LlmRouterSetDefault

        handler = LlmRouterSetDefault(SimpleNamespace(), SimpleNamespace())
        with patch("python.api.llm_router_set_default.get_router") as mock_gr:
            router = _mock_router(models=[])
            router.db.get_models.return_value = []
            mock_gr.return_value = router

            result = await handler.process(
                {"role": "chat", "provider": "openai", "model_name": "nonexistent"}, DummyRequest()
            )

        assert result["success"] is False
        assert "not found" in result["error"].lower()


# ── 4. llm_router_usage ─────────────────────────────────────────────────────


class TestLlmRouterUsage:
    """Test /llm_router_usage endpoint."""

    @pytest.mark.asyncio
    async def test_returns_stats(self):
        from python.api.llm_router_usage import LlmRouterUsage

        handler = LlmRouterUsage(SimpleNamespace(), SimpleNamespace())
        usage = {"totalCalls": 42, "totalCost": 1.23, "byModel": [{"model": "gpt-4o", "calls": 42}]}
        with patch("python.api.llm_router_usage.get_router") as mock_gr:
            mock_gr.return_value = _mock_router(usage=usage)
            result = await handler.process({}, DummyRequest())

        assert result["success"] is True
        assert result["stats"]["totalCalls"] == 42
        assert result["stats"]["totalCost"] == 1.23
        assert len(result["stats"]["byModel"]) == 1

    @pytest.mark.asyncio
    async def test_custom_hours(self):
        from python.api.llm_router_usage import LlmRouterUsage

        handler = LlmRouterUsage(SimpleNamespace(), SimpleNamespace())
        with patch("python.api.llm_router_usage.get_router") as mock_gr:
            router = _mock_router()
            mock_gr.return_value = router
            await handler.process({"hours": 48}, DummyRequest())

        router.get_usage_stats.assert_called_once_with(hours=48)


# ── 5. llm_router_rules ─────────────────────────────────────────────────────


class TestLlmRouterRules:
    """Test /llm_router_rules endpoint."""

    @pytest.mark.asyncio
    async def test_list_rules(self):
        from python.api.llm_router_rules import LlmRouterRules

        handler = LlmRouterRules(SimpleNamespace(), SimpleNamespace())
        sample_rules = [
            RoutingRule(
                name="prefer-local",
                priority=10,
                condition="is_coding=true",
                preferred_models=["ollama/qwen2.5-coder:3b"],
                enabled=True,
            ),
        ]
        with patch("python.api.llm_router_rules.get_router") as mock_gr:
            mock_gr.return_value = _mock_router(rules=sample_rules)
            result = await handler.process({"action": "list"}, DummyRequest())

        assert result["success"] is True
        assert len(result["rules"]) == 1
        assert result["rules"][0]["name"] == "prefer-local"
        assert result["rules"][0]["enabled"] is True
        # Verify camelCase serialization
        assert result["rules"][0]["preferredModels"] == ["ollama/qwen2.5-coder:3b"]
        assert "preferred_models" not in result["rules"][0]

    @pytest.mark.asyncio
    async def test_add_rule_success(self):
        from python.api.llm_router_rules import LlmRouterRules

        handler = LlmRouterRules(SimpleNamespace(), SimpleNamespace())
        with patch("python.api.llm_router_rules.get_router") as mock_gr:
            router = _mock_router()
            mock_gr.return_value = router
            result = await handler.process(
                {"action": "add", "rule": {"name": "cost-limit", "priority": 5, "max_cost_per_1k": 0.5}}, DummyRequest()
            )

        assert result["success"] is True
        assert "cost-limit" in result["message"]
        router.add_routing_rule.assert_called_once()
        added_rule = router.add_routing_rule.call_args[0][0]
        assert added_rule.name == "cost-limit"
        assert added_rule.max_cost_per_1k == 0.5

    @pytest.mark.asyncio
    async def test_add_rule_missing_name(self):
        from python.api.llm_router_rules import LlmRouterRules

        handler = LlmRouterRules(SimpleNamespace(), SimpleNamespace())
        with patch("python.api.llm_router_rules.get_router") as mock_gr:
            mock_gr.return_value = _mock_router()
            result = await handler.process({"action": "add", "rule": {"priority": 5}}, DummyRequest())

        assert result["success"] is False
        assert "name" in result["error"].lower()

    @pytest.mark.asyncio
    async def test_unknown_action(self):
        from python.api.llm_router_rules import LlmRouterRules

        handler = LlmRouterRules(SimpleNamespace(), SimpleNamespace())
        with patch("python.api.llm_router_rules.get_router") as mock_gr:
            mock_gr.return_value = _mock_router()
            result = await handler.process({"action": "purge"}, DummyRequest())

        assert result["success"] is False
        assert "unknown" in result["error"].lower()

    @pytest.mark.asyncio
    async def test_delete_rule_success(self):
        from python.api.llm_router_rules import LlmRouterRules

        handler = LlmRouterRules(SimpleNamespace(), SimpleNamespace())
        with patch("python.api.llm_router_rules.get_router") as mock_gr:
            router = _mock_router()
            mock_gr.return_value = router
            result = await handler.process({"action": "delete", "name": "old-rule"}, DummyRequest())

        assert result["success"] is True
        assert "old-rule" in result["message"]
        router.db.delete_routing_rule.assert_called_once_with("old-rule")

    @pytest.mark.asyncio
    async def test_delete_rule_not_found(self):
        from python.api.llm_router_rules import LlmRouterRules

        handler = LlmRouterRules(SimpleNamespace(), SimpleNamespace())
        with patch("python.api.llm_router_rules.get_router") as mock_gr:
            router = _mock_router()
            router.db.delete_routing_rule.return_value = False
            mock_gr.return_value = router
            result = await handler.process({"action": "delete", "name": "nonexistent"}, DummyRequest())

        assert result["success"] is False
        assert "not found" in result["error"].lower()

    @pytest.mark.asyncio
    async def test_delete_rule_missing_name(self):
        from python.api.llm_router_rules import LlmRouterRules

        handler = LlmRouterRules(SimpleNamespace(), SimpleNamespace())
        with patch("python.api.llm_router_rules.get_router") as mock_gr:
            mock_gr.return_value = _mock_router()
            result = await handler.process({"action": "delete"}, DummyRequest())

        assert result["success"] is False
        assert "name" in result["error"].lower()

    @pytest.mark.asyncio
    async def test_toggle_rule_enable(self):
        from python.api.llm_router_rules import LlmRouterRules

        handler = LlmRouterRules(SimpleNamespace(), SimpleNamespace())
        with patch("python.api.llm_router_rules.get_router") as mock_gr:
            router = _mock_router()
            mock_gr.return_value = router
            result = await handler.process({"action": "toggle", "name": "my-rule", "enabled": True}, DummyRequest())

        assert result["success"] is True
        assert "enabled" in result["message"]
        router.db.toggle_routing_rule.assert_called_once_with("my-rule", True)

    @pytest.mark.asyncio
    async def test_toggle_rule_disable(self):
        from python.api.llm_router_rules import LlmRouterRules

        handler = LlmRouterRules(SimpleNamespace(), SimpleNamespace())
        with patch("python.api.llm_router_rules.get_router") as mock_gr:
            router = _mock_router()
            mock_gr.return_value = router
            result = await handler.process({"action": "toggle", "name": "my-rule", "enabled": False}, DummyRequest())

        assert result["success"] is True
        assert "disabled" in result["message"]
        router.db.toggle_routing_rule.assert_called_once_with("my-rule", False)

    @pytest.mark.asyncio
    async def test_toggle_rule_not_found(self):
        from python.api.llm_router_rules import LlmRouterRules

        handler = LlmRouterRules(SimpleNamespace(), SimpleNamespace())
        with patch("python.api.llm_router_rules.get_router") as mock_gr:
            router = _mock_router()
            router.db.toggle_routing_rule.return_value = False
            mock_gr.return_value = router
            result = await handler.process({"action": "toggle", "name": "gone", "enabled": True}, DummyRequest())

        assert result["success"] is False
        assert "not found" in result["error"].lower()

    @pytest.mark.asyncio
    async def test_toggle_rule_missing_enabled(self):
        from python.api.llm_router_rules import LlmRouterRules

        handler = LlmRouterRules(SimpleNamespace(), SimpleNamespace())
        with patch("python.api.llm_router_rules.get_router") as mock_gr:
            mock_gr.return_value = _mock_router()
            result = await handler.process({"action": "toggle", "name": "my-rule"}, DummyRequest())

        assert result["success"] is False
        assert "enabled" in result["error"].lower()

    @pytest.mark.asyncio
    async def test_update_rule_success(self):
        from python.api.llm_router_rules import LlmRouterRules

        handler = LlmRouterRules(SimpleNamespace(), SimpleNamespace())
        with patch("python.api.llm_router_rules.get_router") as mock_gr:
            router = _mock_router()
            mock_gr.return_value = router
            result = await handler.process(
                {"action": "update", "rule": {"name": "my-rule", "priority": 10, "maxCostPer1k": 1.0}},
                DummyRequest(),
            )

        assert result["success"] is True
        assert "updated" in result["message"].lower()
        router.add_routing_rule.assert_called_once()
        updated_rule = router.add_routing_rule.call_args[0][0]
        assert updated_rule.name == "my-rule"
        assert updated_rule.priority == 10
        assert updated_rule.max_cost_per_1k == 1.0

    @pytest.mark.asyncio
    async def test_update_rule_missing_name(self):
        from python.api.llm_router_rules import LlmRouterRules

        handler = LlmRouterRules(SimpleNamespace(), SimpleNamespace())
        with patch("python.api.llm_router_rules.get_router") as mock_gr:
            mock_gr.return_value = _mock_router()
            result = await handler.process({"action": "update", "rule": {"priority": 5}}, DummyRequest())

        assert result["success"] is False
        assert "name" in result["error"].lower()

    @pytest.mark.asyncio
    async def test_add_rule_camelcase_input(self):
        """Verify add action accepts camelCase input (primary) alongside snake_case (compat)."""
        from python.api.llm_router_rules import LlmRouterRules

        handler = LlmRouterRules(SimpleNamespace(), SimpleNamespace())
        with patch("python.api.llm_router_rules.get_router") as mock_gr:
            router = _mock_router()
            mock_gr.return_value = router
            result = await handler.process(
                {
                    "action": "add",
                    "rule": {
                        "name": "camel-test",
                        "priority": 3,
                        "preferredModels": ["ollama/llama3"],
                        "minContextLength": 8192,
                    },
                },
                DummyRequest(),
            )

        assert result["success"] is True
        added_rule = router.add_routing_rule.call_args[0][0]
        assert added_rule.preferred_models == ["ollama/llama3"]
        assert added_rule.min_context_length == 8192


# ── 6. llm_router_select ────────────────────────────────────────────────────


class TestLlmRouterSelect:
    """Test /llm_router_select endpoint."""

    @pytest.mark.asyncio
    async def test_select_model_success(self):
        from python.api.llm_router_select import LlmRouterSelect

        handler = LlmRouterSelect(SimpleNamespace(), SimpleNamespace())
        with patch("python.api.llm_router_select.get_router") as mock_gr:
            router = _mock_router(models=SAMPLE_MODELS)
            router.select_model.return_value = SAMPLE_MODELS[0]
            mock_gr.return_value = router
            result = await handler.process({"role": "chat", "priority": "quality"}, DummyRequest())

        assert result["success"] is True
        assert result["model"]["provider"] == "ollama"
        assert result["selectionCriteria"]["role"] == "chat"
        assert result["selectionCriteria"]["priority"] == "quality"

    @pytest.mark.asyncio
    async def test_select_model_no_match(self):
        from python.api.llm_router_select import LlmRouterSelect

        handler = LlmRouterSelect(SimpleNamespace(), SimpleNamespace())
        with patch("python.api.llm_router_select.get_router") as mock_gr:
            router = _mock_router()
            router.select_model.return_value = None
            mock_gr.return_value = router
            result = await handler.process({"role": "chat", "required_capabilities": ["vision"]}, DummyRequest())

        assert result["success"] is False
        assert "no matching model" in result["error"].lower()

    @pytest.mark.asyncio
    async def test_priority_map_defaults_to_balanced(self):
        from python.api.llm_router_select import LlmRouterSelect

        handler = LlmRouterSelect(SimpleNamespace(), SimpleNamespace())
        with patch("python.api.llm_router_select.get_router") as mock_gr:
            router = _mock_router(models=SAMPLE_MODELS)
            router.select_model.return_value = SAMPLE_MODELS[0]
            mock_gr.return_value = router
            await handler.process({"priority": "unknown_value"}, DummyRequest())

        # Should have fallen back to BALANCED
        call_kwargs = router.select_model.call_args
        assert (
            call_kwargs.kwargs.get("priority") == RoutingPriority.BALANCED
            or call_kwargs[1].get("priority") == RoutingPriority.BALANCED
        )


# ── 7. llm_router_fallback ──────────────────────────────────────────────────


class TestLlmRouterFallback:
    """Test /llm_router_fallback endpoint."""

    @pytest.mark.asyncio
    async def test_fallback_by_role(self):
        from python.api.llm_router_fallback import LlmRouterFallback

        handler = LlmRouterFallback(SimpleNamespace(), SimpleNamespace())
        with patch("python.api.llm_router_fallback.get_router") as mock_gr:
            router = _mock_router(models=SAMPLE_MODELS)
            router.select_model.return_value = SAMPLE_MODELS[0]
            router.get_fallback_chain.return_value = SAMPLE_MODELS[1:]
            mock_gr.return_value = router
            result = await handler.process({"role": "chat"}, DummyRequest())

        assert result["success"] is True
        assert result["role"] == "chat"
        assert result["primary"]["provider"] == "ollama"
        assert len(result["fallbacks"]) == 2

    @pytest.mark.asyncio
    async def test_fallback_by_model(self):
        from python.api.llm_router_fallback import LlmRouterFallback

        handler = LlmRouterFallback(SimpleNamespace(), SimpleNamespace())
        with patch("python.api.llm_router_fallback.get_router") as mock_gr:
            router = _mock_router(models=SAMPLE_MODELS)
            router.db.get_models.return_value = [SAMPLE_MODELS[1]]
            router.get_fallback_chain.return_value = [SAMPLE_MODELS[2]]
            mock_gr.return_value = router
            result = await handler.process({"provider": "openai", "model_name": "gpt-4o"}, DummyRequest())

        assert result["success"] is True
        assert result["primary"]["provider"] == "openai"
        assert len(result["fallbacks"]) >= 1

    @pytest.mark.asyncio
    async def test_fallback_no_model_for_role(self):
        from python.api.llm_router_fallback import LlmRouterFallback

        handler = LlmRouterFallback(SimpleNamespace(), SimpleNamespace())
        with patch("python.api.llm_router_fallback.get_router") as mock_gr:
            router = _mock_router()
            router.select_model.return_value = None
            mock_gr.return_value = router
            result = await handler.process({"role": "chat"}, DummyRequest())

        assert result["success"] is False
        assert "no model available" in result["error"].lower()

    @pytest.mark.asyncio
    async def test_fallback_missing_params(self):
        from python.api.llm_router_fallback import LlmRouterFallback

        handler = LlmRouterFallback(SimpleNamespace(), SimpleNamespace())
        with patch("python.api.llm_router_fallback.get_router") as mock_gr:
            mock_gr.return_value = _mock_router()
            result = await handler.process({}, DummyRequest())

        assert result["success"] is False
        assert "required" in result["error"].lower()

    @pytest.mark.asyncio
    async def test_fallback_invalid_priority_uses_balanced(self):
        """Unknown priority string should fall back to BALANCED, not crash."""
        from python.api.llm_router_fallback import LlmRouterFallback

        handler = LlmRouterFallback(SimpleNamespace(), SimpleNamespace())
        with patch("python.api.llm_router_fallback.get_router") as mock_gr:
            router = _mock_router(models=SAMPLE_MODELS)
            router.select_model.return_value = SAMPLE_MODELS[0]
            router.get_fallback_chain.return_value = SAMPLE_MODELS[1:]
            mock_gr.return_value = router
            result = await handler.process({"role": "chat", "priority": "INVALID_JUNK"}, DummyRequest())

        assert result["success"] is True
        # Should have used BALANCED (the default fallback)
        router.select_model.assert_called_once()
        call_kwargs = router.select_model.call_args
        assert call_kwargs.kwargs.get("priority") == RoutingPriority.BALANCED

    @pytest.mark.asyncio
    async def test_fallback_model_not_found_by_name(self):
        from python.api.llm_router_fallback import LlmRouterFallback

        handler = LlmRouterFallback(SimpleNamespace(), SimpleNamespace())
        with patch("python.api.llm_router_fallback.get_router") as mock_gr:
            router = _mock_router()
            router.db.get_models.return_value = []  # no models
            mock_gr.return_value = router
            result = await handler.process({"provider": "openai", "model_name": "nonexistent"}, DummyRequest())

        assert result["success"] is False
        assert "not found" in result["error"].lower()


# ── 8. llm_router_discover ──────────────────────────────────────────────────


class TestLlmRouterDiscover:
    """Test /llm_router_discover endpoint."""

    @pytest.mark.asyncio
    async def test_discover_returns_models(self):
        from python.api.llm_router_discover import LlmRouterDiscover

        handler = LlmRouterDiscover(SimpleNamespace(), SimpleNamespace())
        with patch("python.api.llm_router_discover.get_router") as mock_gr:
            router = _mock_router(models=SAMPLE_MODELS)
            mock_gr.return_value = router
            result = await handler.process({}, DummyRequest())

        assert result["success"] is True
        assert result["count"] == 3
        assert set(result["providers"]) == {"ollama", "openai", "anthropic"}
        assert len(result["models"]) == 3

    @pytest.mark.asyncio
    async def test_discover_with_force(self):
        from python.api.llm_router_discover import LlmRouterDiscover

        handler = LlmRouterDiscover(SimpleNamespace(), SimpleNamespace())
        with patch("python.api.llm_router_discover.get_router") as mock_gr:
            router = _mock_router(models=[])
            mock_gr.return_value = router
            await handler.process({"force": True}, DummyRequest())

        router.discover_models.assert_called_once_with(force=True)

    @pytest.mark.asyncio
    async def test_discover_empty(self):
        from python.api.llm_router_discover import LlmRouterDiscover

        handler = LlmRouterDiscover(SimpleNamespace(), SimpleNamespace())
        with patch("python.api.llm_router_discover.get_router") as mock_gr:
            mock_gr.return_value = _mock_router(models=[])
            result = await handler.process({}, DummyRequest())

        assert result["success"] is True
        assert result["count"] == 0
        assert result["providers"] == []


# ── 9. llm_router_auto_configure ────────────────────────────────────────────


class TestLlmRouterAutoConfigure:
    """Test /llm_router_auto_configure endpoint."""

    @pytest.mark.asyncio
    async def test_auto_configure_success(self):
        from python.api.llm_router_auto_configure import LlmRouterAutoConfigure

        handler = LlmRouterAutoConfigure(SimpleNamespace(), SimpleNamespace())
        defaults = {
            "chat": ("ollama", "qwen2.5-coder:3b"),
            "utility": ("openai", "gpt-4o-mini"),
            "browser": ("openai", "gpt-4o"),
            "embedding": ("openai", "text-embedding-3-small"),
        }

        with (
            patch("python.api.llm_router_auto_configure.auto_configure_models", new_callable=AsyncMock) as mock_ac,
            patch("python.api.llm_router_auto_configure.get_router") as mock_gr,
        ):
            mock_ac.return_value = SAMPLE_MODELS
            mock_gr.return_value = _mock_router(defaults=defaults)
            result = await handler.process({}, DummyRequest())

        assert result["success"] is True
        assert result["discoveredModels"] == 3
        assert "chat" in result["configuredDefaults"]
        assert "utility" in result["configuredDefaults"]
        assert "browser" in result["configuredDefaults"]
        assert "embedding" in result["configuredDefaults"]

    @pytest.mark.asyncio
    async def test_auto_configure_reads_all_five_roles(self):
        """auto_configure must read back defaults for all 5 roles."""
        from python.api.llm_router_auto_configure import LlmRouterAutoConfigure

        handler = LlmRouterAutoConfigure(SimpleNamespace(), SimpleNamespace())

        with (
            patch("python.api.llm_router_auto_configure.auto_configure_models", new_callable=AsyncMock) as mock_ac,
            patch("python.api.llm_router_auto_configure.get_router") as mock_gr,
        ):
            mock_ac.return_value = SAMPLE_MODELS
            router = _mock_router()
            mock_gr.return_value = router
            await handler.process({}, DummyRequest())

        # Verify get_default_model was called for all 5 roles
        called_roles = [call.args[0] for call in router.get_default_model.call_args_list]
        assert set(called_roles) == {"chat", "utility", "browser", "embedding", "fallback"}

    @pytest.mark.asyncio
    async def test_auto_configure_error(self):
        from python.api.llm_router_auto_configure import LlmRouterAutoConfigure

        handler = LlmRouterAutoConfigure(SimpleNamespace(), SimpleNamespace())
        with patch("python.api.llm_router_auto_configure.auto_configure_models", new_callable=AsyncMock) as mock_ac:
            mock_ac.side_effect = RuntimeError("Ollama not reachable")
            result = await handler.process({}, DummyRequest())

        assert result["success"] is False
        assert "not reachable" in result["error"]

    @pytest.mark.asyncio
    async def test_auto_configure_no_defaults_returns_empty(self):
        """When no defaults are set, configuredDefaults should be empty."""
        from python.api.llm_router_auto_configure import LlmRouterAutoConfigure

        handler = LlmRouterAutoConfigure(SimpleNamespace(), SimpleNamespace())
        with (
            patch("python.api.llm_router_auto_configure.auto_configure_models", new_callable=AsyncMock) as mock_ac,
            patch("python.api.llm_router_auto_configure.get_router") as mock_gr,
        ):
            mock_ac.return_value = SAMPLE_MODELS
            mock_gr.return_value = _mock_router()  # no defaults
            result = await handler.process({}, DummyRequest())

        assert result["success"] is True
        assert result["configuredDefaults"] == {}

    @pytest.mark.asyncio
    async def test_auto_configure_response_has_camel_keys(self):
        """Verify response uses discoveredModels and configuredDefaults (camelCase)."""
        from python.api.llm_router_auto_configure import LlmRouterAutoConfigure

        handler = LlmRouterAutoConfigure(SimpleNamespace(), SimpleNamespace())
        with (
            patch("python.api.llm_router_auto_configure.auto_configure_models", new_callable=AsyncMock) as mock_ac,
            patch("python.api.llm_router_auto_configure.get_router") as mock_gr,
        ):
            mock_ac.return_value = SAMPLE_MODELS
            mock_gr.return_value = _mock_router()
            result = await handler.process({}, DummyRequest())

        # camelCase keys present
        assert "discoveredModels" in result
        assert "configuredDefaults" in result
        # snake_case keys absent
        assert "discovered_models" not in result
        assert "configured_defaults" not in result


# ── 9b. llm_router_select camelCase ─────────────────────────────────────────


class TestLlmRouterSelectCamelCase:
    """Test that select endpoint accepts camelCase params and returns camelCase response."""

    @pytest.mark.asyncio
    async def test_select_accepts_camel_case_params(self):
        from python.api.llm_router_select import LlmRouterSelect

        handler = LlmRouterSelect(SimpleNamespace(), SimpleNamespace())
        with patch("python.api.llm_router_select.get_router") as mock_gr:
            router = _mock_router(models=SAMPLE_MODELS)
            mock_gr.return_value = router
            result = await handler.process(
                {
                    "role": "chat",
                    "contextType": "user",
                    "requiredCapabilities": ["chat"],
                    "priority": "quality",
                    "minContextLength": 8000,
                    "maxCostPer1k": 5.0,
                    "preferredProvider": "openai",
                },
                DummyRequest(),
            )

        # Verify router was called with the right args
        call_kwargs = router.select_model.call_args[1]
        assert call_kwargs["context_type"] == "user"
        assert call_kwargs["min_context_length"] == 8000

    @pytest.mark.asyncio
    async def test_select_response_uses_camel_case(self):
        from python.api.llm_router_select import LlmRouterSelect

        handler = LlmRouterSelect(SimpleNamespace(), SimpleNamespace())
        with patch("python.api.llm_router_select.get_router") as mock_gr:
            router = _mock_router(models=SAMPLE_MODELS)
            mock_gr.return_value = router
            result = await handler.process({"role": "chat"}, DummyRequest())

        assert "selectionCriteria" in result
        assert "selection_criteria" not in result


# ── 9c. Rule Name Validation ────────────────────────────────────────────────


class TestRuleNameValidation:
    """Test rule name validation in the rules endpoint."""

    @pytest.mark.asyncio
    async def test_empty_name_rejected(self):
        from python.api.llm_router_rules import LlmRouterRules

        handler = LlmRouterRules(SimpleNamespace(), SimpleNamespace())
        with patch("python.api.llm_router_rules.get_router") as mock_gr:
            mock_gr.return_value = _mock_router()
            result = await handler.process({"action": "add", "rule": {"name": ""}}, DummyRequest())

        assert result["success"] is False
        assert "required" in result["error"].lower()

    @pytest.mark.asyncio
    async def test_too_long_name_rejected(self):
        from python.api.llm_router_rules import LlmRouterRules

        handler = LlmRouterRules(SimpleNamespace(), SimpleNamespace())
        with patch("python.api.llm_router_rules.get_router") as mock_gr:
            mock_gr.return_value = _mock_router()
            result = await handler.process({"action": "add", "rule": {"name": "x" * 100}}, DummyRequest())

        assert result["success"] is False
        assert "64" in result["error"]

    @pytest.mark.asyncio
    async def test_special_chars_rejected(self):
        from python.api.llm_router_rules import LlmRouterRules

        handler = LlmRouterRules(SimpleNamespace(), SimpleNamespace())
        with patch("python.api.llm_router_rules.get_router") as mock_gr:
            mock_gr.return_value = _mock_router()
            result = await handler.process({"action": "add", "rule": {"name": "rule<script>"}}, DummyRequest())

        assert result["success"] is False
        assert "letters" in result["error"].lower() or "may only" in result["error"].lower()

    @pytest.mark.asyncio
    async def test_valid_name_accepted(self):
        from python.api.llm_router_rules import LlmRouterRules

        handler = LlmRouterRules(SimpleNamespace(), SimpleNamespace())
        with patch("python.api.llm_router_rules.get_router") as mock_gr:
            mock_gr.return_value = _mock_router()
            result = await handler.process(
                {"action": "add", "rule": {"name": "My Rule - v2.1", "priority": 5}}, DummyRequest()
            )

        assert result["success"] is True


# ── 10. model_selector_quick_switch ─────────────────────────────────────────


class TestModelSelectorQuickSwitch:
    """Test /model_selector_quick_switch endpoint."""

    @pytest.mark.asyncio
    async def test_switch_chat_model(self):
        from python.api.model_selector_quick_switch import ModelSelectorQuickSwitch

        handler = ModelSelectorQuickSwitch(SimpleNamespace(), SimpleNamespace())

        mock_settings = {"chat_model_provider": "ollama", "chat_model_name": "old-model"}

        with (
            patch("python.helpers.settings.get_settings", return_value=mock_settings),
            patch("python.helpers.settings.set_settings") as mock_set,
            patch("python.helpers.llm_router.get_router") as mock_gr,
        ):
            mock_gr.return_value = _mock_router()
            result = await handler.process({"provider": "openai", "model_name": "gpt-4o"}, DummyRequest())

        assert result["success"] is True
        assert result["model"]["provider"] == "openai"
        assert result["model"]["name"] == "gpt-4o"
        assert result["model"]["role"] == "chat"
        # Settings should have been updated
        assert mock_settings["chat_model_provider"] == "openai"
        assert mock_settings["chat_model_name"] == "gpt-4o"

    @pytest.mark.asyncio
    async def test_switch_utility_model(self):
        from python.api.model_selector_quick_switch import ModelSelectorQuickSwitch

        handler = ModelSelectorQuickSwitch(SimpleNamespace(), SimpleNamespace())
        mock_settings = {}

        with (
            patch("python.helpers.settings.get_settings", return_value=mock_settings),
            patch("python.helpers.settings.set_settings"),
            patch("python.helpers.llm_router.get_router") as mock_gr,
        ):
            mock_gr.return_value = _mock_router()
            result = await handler.process(
                {"provider": "anthropic", "model_name": "claude-sonnet-4-20250514", "role": "utility"}, DummyRequest()
            )

        assert result["success"] is True
        assert result["model"]["role"] == "utility"
        assert mock_settings["util_model_provider"] == "anthropic"
        assert mock_settings["util_model_name"] == "claude-sonnet-4-20250514"

    @pytest.mark.asyncio
    async def test_switch_browser_model(self):
        from python.api.model_selector_quick_switch import ModelSelectorQuickSwitch

        handler = ModelSelectorQuickSwitch(SimpleNamespace(), SimpleNamespace())
        mock_settings = {}

        with (
            patch("python.helpers.settings.get_settings", return_value=mock_settings),
            patch("python.helpers.settings.set_settings"),
            patch("python.helpers.llm_router.get_router") as mock_gr,
        ):
            mock_gr.return_value = _mock_router()
            result = await handler.process(
                {"provider": "openai", "model_name": "gpt-4o", "role": "browser"}, DummyRequest()
            )

        assert result["success"] is True
        assert mock_settings["browser_model_provider"] == "openai"

    @pytest.mark.asyncio
    async def test_switch_embedding_model(self):
        from python.api.model_selector_quick_switch import ModelSelectorQuickSwitch

        handler = ModelSelectorQuickSwitch(SimpleNamespace(), SimpleNamespace())
        mock_settings = {}

        with (
            patch("python.helpers.settings.get_settings", return_value=mock_settings),
            patch("python.helpers.settings.set_settings"),
            patch("python.helpers.llm_router.get_router") as mock_gr,
        ):
            mock_gr.return_value = _mock_router()
            result = await handler.process(
                {"provider": "openai", "model_name": "text-embedding-3-small", "role": "embedding"}, DummyRequest()
            )

        assert result["success"] is True
        assert mock_settings["embed_model_provider"] == "openai"

    @pytest.mark.asyncio
    async def test_switch_unknown_role_skips_settings(self):
        """Fallback role has no settings key map entry — settings not updated but router is."""
        from python.api.model_selector_quick_switch import ModelSelectorQuickSwitch

        handler = ModelSelectorQuickSwitch(SimpleNamespace(), SimpleNamespace())
        mock_settings = {}

        with (
            patch("python.helpers.settings.get_settings", return_value=mock_settings),
            patch("python.helpers.settings.set_settings") as mock_set,
            patch("python.helpers.llm_router.get_router") as mock_gr,
        ):
            router = _mock_router()
            mock_gr.return_value = router
            result = await handler.process(
                {"provider": "ollama", "model_name": "qwen2.5-coder:3b", "role": "fallback"}, DummyRequest()
            )

        assert result["success"] is True
        # Settings should NOT have been updated for unknown role
        assert "fallback_model_provider" not in mock_settings
        # But router should have been called
        router.set_default_model.assert_called_once_with("fallback", "ollama", "qwen2.5-coder:3b")

    @pytest.mark.asyncio
    async def test_switch_missing_provider(self):
        from python.api.model_selector_quick_switch import ModelSelectorQuickSwitch

        handler = ModelSelectorQuickSwitch(SimpleNamespace(), SimpleNamespace())
        result = await handler.process({"model_name": "gpt-4o"}, DummyRequest())

        assert result["success"] is False
        assert "required" in result["error"].lower()

    @pytest.mark.asyncio
    async def test_switch_missing_model_name(self):
        from python.api.model_selector_quick_switch import ModelSelectorQuickSwitch

        handler = ModelSelectorQuickSwitch(SimpleNamespace(), SimpleNamespace())
        result = await handler.process({"provider": "openai"}, DummyRequest())

        assert result["success"] is False
        assert "required" in result["error"].lower()

    @pytest.mark.asyncio
    async def test_router_failure_non_fatal(self):
        """Router update failure should not fail the whole request."""
        from python.api.model_selector_quick_switch import ModelSelectorQuickSwitch

        handler = ModelSelectorQuickSwitch(SimpleNamespace(), SimpleNamespace())
        mock_settings = {}

        with (
            patch("python.helpers.settings.get_settings", return_value=mock_settings),
            patch("python.helpers.settings.set_settings"),
            patch("python.helpers.llm_router.get_router") as mock_gr,
        ):
            router = _mock_router()
            router.set_default_model.side_effect = RuntimeError("DB locked")
            mock_gr.return_value = router
            result = await handler.process({"provider": "openai", "model_name": "gpt-4o"}, DummyRequest())

        # Should still succeed even though router update failed
        assert result["success"] is True
        assert mock_settings["chat_model_provider"] == "openai"


# ── 11. Routing Rule Condition Evaluator ────────────────────────────────────


class TestRuleConditionEvaluator:
    """Test the safe condition evaluator (no eval)."""

    def test_empty_condition_always_matches(self):
        from python.helpers.llm_router import LLMRouter

        assert LLMRouter.evaluate_rule_condition("", {"role": "chat"}) is True
        assert LLMRouter.evaluate_rule_condition("   ", {}) is True
        assert LLMRouter.evaluate_rule_condition(None, {}) is True

    def test_simple_equality(self):
        from python.helpers.llm_router import LLMRouter

        ctx = {"role": "chat", "context_type": "user"}
        assert LLMRouter.evaluate_rule_condition("role=chat", ctx) is True
        assert LLMRouter.evaluate_rule_condition("role=utility", ctx) is False

    def test_case_insensitive(self):
        from python.helpers.llm_router import LLMRouter

        ctx = {"role": "CHAT", "context_type": "USER"}
        assert LLMRouter.evaluate_rule_condition("role=chat", ctx) is True
        assert LLMRouter.evaluate_rule_condition("ROLE=CHAT", ctx) is True

    def test_not_equals(self):
        from python.helpers.llm_router import LLMRouter

        ctx = {"role": "chat", "context_type": "user"}
        assert LLMRouter.evaluate_rule_condition("role!=utility", ctx) is True
        assert LLMRouter.evaluate_rule_condition("role!=chat", ctx) is False

    def test_and_operator(self):
        from python.helpers.llm_router import LLMRouter

        ctx = {"role": "chat", "context_type": "user"}
        assert LLMRouter.evaluate_rule_condition("role=chat AND context_type=user", ctx) is True
        assert LLMRouter.evaluate_rule_condition("role=chat AND context_type=background", ctx) is False

    def test_or_operator(self):
        from python.helpers.llm_router import LLMRouter

        ctx = {"role": "chat", "context_type": "user"}
        assert LLMRouter.evaluate_rule_condition("role=chat OR role=utility", ctx) is True
        assert LLMRouter.evaluate_rule_condition("role=utility OR role=browser", ctx) is False

    def test_mixed_and_or(self):
        from python.helpers.llm_router import LLMRouter

        ctx = {"role": "chat", "context_type": "user"}
        # OR branches: (role=utility AND context_type=user) OR (role=chat)
        assert LLMRouter.evaluate_rule_condition("role=utility AND context_type=user OR role=chat", ctx) is True

    def test_missing_key_returns_false(self):
        from python.helpers.llm_router import LLMRouter

        assert LLMRouter.evaluate_rule_condition("missing_key=value", {}) is False

    def test_bare_key_truthy(self):
        from python.helpers.llm_router import LLMRouter

        assert LLMRouter.evaluate_rule_condition("role", {"role": "chat"}) is True
        assert LLMRouter.evaluate_rule_condition("missing", {"role": "chat"}) is False


# ── 12. Routing Rules Applied in select_model ───────────────────────────────


class TestRoutingRulesApplied:
    """Test that routing rules actually influence model selection."""

    def _make_router_with_models(self, tmp_path, rules=None):
        """Create a real router with in-memory DB and sample models."""
        from python.helpers.llm_router import LLMRouter, LLMRouterDatabase

        db_path = str(tmp_path / "test_router.db")
        db = LLMRouterDatabase(db_path)
        router = LLMRouter.__new__(LLMRouter)
        router.db = db
        router.MODEL_CATALOG = {}

        # Register sample models
        for m in SAMPLE_MODELS:
            db.save_model(m)

        # Also add a fast cheap model
        fast_model = _make_model(
            "groq",
            "llama-3-8b",
            False,
            display_name="Llama 3 8B",
            capabilities=["chat", "fast", "cheap"],
            context_length=8192,
            cost_per_1k_input=0.05,
            cost_per_1k_output=0.08,
        )
        db.save_model(fast_model)

        # Add rules
        if rules:
            for rule in rules:
                db.save_routing_rule(rule)

        return router

    def test_rule_excludes_model(self, tmp_path):
        """A rule excluding a model should remove it from candidates."""
        rule = RoutingRule(
            name="no-gpt4o",
            priority=10,
            excluded_models=["openai/gpt-4o"],
            enabled=True,
        )
        router = self._make_router_with_models(tmp_path, rules=[rule])
        result = router.select_model(role="chat", priority=RoutingPriority.QUALITY)
        assert result is not None
        assert result.name != "gpt-4o"

    def test_rule_prefers_model(self, tmp_path):
        """A rule preferring a model should boost its score."""
        rule = RoutingRule(
            name="prefer-groq",
            priority=10,
            preferred_models=["groq/llama-3-8b"],
            enabled=True,
        )
        router = self._make_router_with_models(tmp_path, rules=[rule])
        result = router.select_model(role="chat", priority=RoutingPriority.BALANCED)
        assert result is not None
        # Groq gets +50 rule boost on top of its base score
        assert result.provider == "groq"

    def test_rule_with_condition_matches(self, tmp_path):
        """A rule with role=chat condition should only apply to chat role."""
        rule = RoutingRule(
            name="chat-only-exclude-anthropic",
            priority=10,
            condition="role=chat",
            excluded_models=["anthropic/claude-sonnet-4-20250514"],
            enabled=True,
        )
        router = self._make_router_with_models(tmp_path, rules=[rule])

        # Chat role: anthropic excluded
        chat_result = router.select_model(role="chat", priority=RoutingPriority.QUALITY)
        assert chat_result is not None
        assert chat_result.provider != "anthropic"

        # Utility role: anthropic NOT excluded (condition doesn't match)
        util_result = router.select_model(role="utility", priority=RoutingPriority.QUALITY)
        assert util_result is not None
        # Anthropic could be selected for utility

    def test_disabled_rule_ignored(self, tmp_path):
        """Disabled rules should have no effect."""
        rule = RoutingRule(
            name="disabled-rule",
            priority=10,
            excluded_models=["openai/gpt-4o", "anthropic/claude-sonnet-4-20250514", "groq/llama-3-8b"],
            enabled=False,
        )
        router = self._make_router_with_models(tmp_path, rules=[rule])
        result = router.select_model(role="chat", priority=RoutingPriority.QUALITY)
        assert result is not None
        # All models should still be available

    def test_rule_max_cost_constraint(self, tmp_path):
        """A rule with max_cost_per_1k should filter expensive models."""
        rule = RoutingRule(
            name="budget-cap",
            priority=10,
            max_cost_per_1k=0.1,
            enabled=True,
        )
        router = self._make_router_with_models(tmp_path, rules=[rule])
        result = router.select_model(role="chat", priority=RoutingPriority.QUALITY)
        assert result is not None
        # Only local (free) and groq (0.08) should survive
        assert max(result.cost_per_1k_input, result.cost_per_1k_output) <= 0.1

    def test_multiple_rules_merge(self, tmp_path):
        """Multiple matching rules should merge their constraints."""
        rules = [
            RoutingRule(
                name="no-anthropic", priority=10, excluded_models=["anthropic/claude-sonnet-4-20250514"], enabled=True
            ),
            RoutingRule(name="no-openai", priority=5, excluded_models=["openai/gpt-4o"], enabled=True),
        ]
        router = self._make_router_with_models(tmp_path, rules=rules)
        result = router.select_model(role="chat", priority=RoutingPriority.QUALITY)
        assert result is not None
        assert result.provider not in ("openai", "anthropic")
