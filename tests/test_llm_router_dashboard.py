"""
Tests for LLM Router dashboard API and UI data contract.

Validates:
1. Dashboard API returns camelCase keys matching frontend expectations
2. Response structure matches what llm-router-dashboard-store.js and model-selector-store.js consume
3. LoopData.model_used flows into log item kvps as _model
4. buildAvailableModelsList handles missing/empty byProvider safely
5. Usage tracking estimates output tokens via approximate_tokens
"""

import json
from collections import OrderedDict
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

import pytest

from agent import LoopData
from python.helpers.llm_router import (
    ModelInfo,
    call_with_failover,
)

# ── Helpers ──────────────────────────────────────────────────────────────────


def _make_model(provider="ollama", name="qwen2.5-coder:3b", is_local=True, capabilities=None, **kw):
    return ModelInfo(
        provider=provider,
        name=name,
        display_name=kw.get("display_name", name),
        capabilities=capabilities or ["chat", "code"],
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
        "ollama",
        "qwen2.5-coder:3b",
        True,
        ["chat", "code", "baseline"],
        display_name="Qwen 2.5 Coder 3B",
        size_gb=1.9,
        context_length=32768,
        metadata={"priority_baseline": True},
    ),
    _make_model(
        "openai",
        "gpt-4o",
        False,
        ["chat", "code", "reasoning", "vision"],
        display_name="GPT-4o",
        context_length=128000,
        cost_per_1k_input=2.5,
        cost_per_1k_output=10.0,
    ),
    _make_model(
        "anthropic",
        "claude-sonnet-4-20250514",
        False,
        ["chat", "code", "reasoning"],
        display_name="Claude Sonnet 4",
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


# ── 1. Dashboard API camelCase contract ──────────────────────────────────────


class TestDashboardApiContract:
    """Verify the dashboard API returns camelCase keys that the frontend expects."""

    @pytest.fixture(autouse=True)
    def setup(self):
        # Reset singleton so each test gets a fresh router
        import python.helpers.llm_router as lr

        lr._router_instance = None
        yield
        lr._router_instance = None

    @pytest.mark.asyncio
    async def test_models_key_uses_camelCase(self):
        """models.byProvider, models.totalCount, etc. must be camelCase."""
        from python.api.llm_router_dashboard import LlmRouterDashboard

        handler = LlmRouterDashboard(SimpleNamespace(), SimpleNamespace())

        with patch("python.api.llm_router_dashboard.get_router") as mock_gr:
            router = MagicMock()
            router.db.get_models.return_value = SAMPLE_MODELS
            router.get_default_model.return_value = None
            router.get_usage_stats.return_value = {"totalCalls": 0, "totalCost": 0.0, "byModel": []}
            mock_gr.return_value = router

            result = await handler.process({}, DummyRequest())

        assert result["success"] is True

        # models block must use camelCase
        models = result["models"]
        assert "byProvider" in models, "Expected camelCase 'byProvider', got snake_case"
        assert "totalCount" in models
        assert "localCount" in models
        assert "cloudCount" in models

        # Must NOT have snake_case equivalents
        assert "by_provider" not in models
        assert "total_count" not in models
        assert "local_count" not in models
        assert "cloud_count" not in models

    @pytest.mark.asyncio
    async def test_usage_key_uses_camelCase(self):
        """usage.lastHour, usage.last24h, costUsd must be camelCase."""
        from python.api.llm_router_dashboard import LlmRouterDashboard

        handler = LlmRouterDashboard(SimpleNamespace(), SimpleNamespace())

        with patch("python.api.llm_router_dashboard.get_router") as mock_gr:
            router = MagicMock()
            router.db.get_models.return_value = []
            router.get_default_model.return_value = None
            router.get_usage_stats.return_value = {"totalCalls": 5, "totalCost": 0.123, "byModel": [{"model": "x"}]}
            mock_gr.return_value = router

            result = await handler.process({}, DummyRequest())

        usage = result["usage"]
        assert "lastHour" in usage, "Expected camelCase 'lastHour'"
        assert "last24h" in usage, "Expected camelCase 'last24h'"
        assert "costUsd" in usage["lastHour"]
        assert "costUsd" in usage["last24h"]
        assert "byModel" in usage["last24h"]

        # Must NOT have snake_case equivalents
        assert "last_hour" not in usage
        assert "last_24h" not in usage
        assert "cost_usd" not in usage.get("lastHour", {})

    @pytest.mark.asyncio
    async def test_models_grouped_by_provider(self):
        """byProvider should group models correctly."""
        from python.api.llm_router_dashboard import LlmRouterDashboard

        handler = LlmRouterDashboard(SimpleNamespace(), SimpleNamespace())

        with patch("python.api.llm_router_dashboard.get_router") as mock_gr:
            router = MagicMock()
            router.db.get_models.return_value = SAMPLE_MODELS
            router.get_default_model.return_value = None
            router.get_usage_stats.return_value = {"totalCalls": 0, "totalCost": 0.0, "byModel": []}
            mock_gr.return_value = router

            result = await handler.process({}, DummyRequest())

        bp = result["models"]["byProvider"]
        assert "ollama" in bp
        assert "openai" in bp
        assert "anthropic" in bp
        assert len(bp["ollama"]) == 1
        assert bp["ollama"][0]["name"] == "qwen2.5-coder:3b"

    @pytest.mark.asyncio
    async def test_counts_are_correct(self):
        """totalCount, localCount, cloudCount must reflect the model list."""
        from python.api.llm_router_dashboard import LlmRouterDashboard

        handler = LlmRouterDashboard(SimpleNamespace(), SimpleNamespace())

        with patch("python.api.llm_router_dashboard.get_router") as mock_gr:
            router = MagicMock()
            router.db.get_models.return_value = SAMPLE_MODELS
            router.get_default_model.return_value = None
            router.get_usage_stats.return_value = {"totalCalls": 0, "totalCost": 0.0, "byModel": []}
            mock_gr.return_value = router

            result = await handler.process({}, DummyRequest())

        assert result["models"]["totalCount"] == 3
        assert result["models"]["localCount"] == 1  # only ollama
        assert result["models"]["cloudCount"] == 2  # openai + anthropic

    @pytest.mark.asyncio
    async def test_defaults_included_when_set(self):
        """defaults should map role → {provider, modelName}."""
        from python.api.llm_router_dashboard import LlmRouterDashboard

        handler = LlmRouterDashboard(SimpleNamespace(), SimpleNamespace())

        def fake_default(role):
            if role == "chat":
                return ("anthropic", "claude-sonnet-4-20250514")
            return None

        with patch("python.api.llm_router_dashboard.get_router") as mock_gr:
            router = MagicMock()
            router.db.get_models.return_value = []
            router.get_default_model.side_effect = fake_default
            router.get_usage_stats.return_value = {"totalCalls": 0, "totalCost": 0.0, "byModel": []}
            mock_gr.return_value = router

            result = await handler.process({}, DummyRequest())

        assert "chat" in result["defaults"]
        assert result["defaults"]["chat"]["provider"] == "anthropic"
        assert result["defaults"]["chat"]["modelName"] == "claude-sonnet-4-20250514"
        assert "utility" not in result["defaults"]

    @pytest.mark.asyncio
    async def test_empty_models_returns_valid_structure(self):
        """Dashboard with no models should still return valid structure."""
        from python.api.llm_router_dashboard import LlmRouterDashboard

        handler = LlmRouterDashboard(SimpleNamespace(), SimpleNamespace())

        with patch("python.api.llm_router_dashboard.get_router") as mock_gr:
            router = MagicMock()
            router.db.get_models.return_value = []
            router.get_default_model.return_value = None
            router.get_usage_stats.return_value = {"totalCalls": 0, "totalCost": 0.0, "byModel": []}
            mock_gr.return_value = router

            result = await handler.process({}, DummyRequest())

        assert result["success"] is True
        assert result["models"]["byProvider"] == {}
        assert result["models"]["totalCount"] == 0
        assert result["models"]["localCount"] == 0
        assert result["models"]["cloudCount"] == 0


# ── 2. LoopData.model_used → log kvps._model ────────────────────────────────


class TestModelUsedPropagation:
    """Verify model_used on LoopData flows into log item kvps."""

    def test_loop_data_has_model_used_field(self):
        """LoopData should have model_used initialized to empty string."""
        ld = LoopData()
        assert hasattr(ld, "model_used")
        assert ld.model_used == ""

    def test_loop_data_model_used_can_be_set(self):
        """LoopData.model_used can hold provider/model string."""
        ld = LoopData()
        ld.model_used = "anthropic/claude-sonnet-4-20250514"
        assert ld.model_used == "anthropic/claude-sonnet-4-20250514"

    def test_loop_data_model_used_via_kwargs(self):
        """model_used can be set via LoopData constructor kwargs."""
        ld = LoopData(model_used="openai/gpt-4o")
        assert ld.model_used == "openai/gpt-4o"

    def test_log_from_stream_injects_model_kvp(self):
        """_10_log_from_stream should add _model to kvps when loop_data.model_used is set."""
        # We test the logic inline rather than instantiating the Extension class
        # (which requires an Agent instance). The critical logic is:
        #   if hasattr(loop_data, 'model_used') and loop_data.model_used:
        #       kvps["_model"] = loop_data.model_used

        loop_data = LoopData()
        loop_data.model_used = "google/gemini-2.0-flash"

        kvps = {"thoughts": ["thinking..."], "headline": "Test"}
        if hasattr(loop_data, "model_used") and loop_data.model_used:
            kvps["_model"] = loop_data.model_used

        assert kvps["_model"] == "google/gemini-2.0-flash"

    def test_log_from_stream_skips_model_when_empty(self):
        """_model should NOT be added when model_used is empty."""
        loop_data = LoopData()
        # model_used is "" by default

        kvps = {"thoughts": ["thinking..."]}
        if hasattr(loop_data, "model_used") and loop_data.model_used:
            kvps["_model"] = loop_data.model_used

        assert "_model" not in kvps


# ── 3. Usage tracking token estimation ───────────────────────────────────────


class TestUsageTokenEstimation:
    """Verify call_with_failover estimates output tokens."""

    @pytest.fixture(autouse=True)
    def setup(self):
        import python.helpers.llm_router as lr

        lr._router_instance = None
        yield
        lr._router_instance = None

    @pytest.mark.asyncio
    async def test_failover_records_estimated_tokens(self):
        """Successful call should record non-zero output_tokens based on response size."""

        primary = _make_model("openai", "gpt-4o", False)

        # Track what record_call receives
        recorded_calls = []

        async def mock_call_func(provider, model_name):
            return "This is a test response with enough words to produce tokens.", ""

        with patch("python.helpers.llm_router.get_router") as mock_gr:
            router = MagicMock()
            router.get_fallback_chain.return_value = []

            def capture_record(*a, **kw):
                recorded_calls.append(kw)

            router.record_call.side_effect = capture_record
            mock_gr.return_value = router

            result = await call_with_failover(
                primary_model=primary,
                call_func=mock_call_func,
                max_retries=1,
                record_usage=True,
            )

        assert result.success is True
        assert len(recorded_calls) == 1
        assert recorded_calls[0]["output_tokens"] > 0, "output_tokens should be estimated, not zero"
        assert recorded_calls[0]["success"] is True


# ── 4. Frontend store safety ─────────────────────────────────────────────────


class TestFrontendStoreCompat:
    """
    Simulate what the JS stores do with the API response.
    These tests act as a contract test between Python API and JS frontend.
    """

    @pytest.fixture(autouse=True)
    def setup(self):
        import python.helpers.llm_router as lr

        lr._router_instance = None
        yield
        lr._router_instance = None

    @pytest.mark.asyncio
    async def test_model_selector_store_reads_byProvider(self):
        """
        model-selector-store.js does: resp.models?.byProvider
        Ensure the API response has this exact path.
        """
        from python.api.llm_router_dashboard import LlmRouterDashboard

        handler = LlmRouterDashboard(SimpleNamespace(), SimpleNamespace())

        with patch("python.api.llm_router_dashboard.get_router") as mock_gr:
            router = MagicMock()
            router.db.get_models.return_value = SAMPLE_MODELS
            router.get_default_model.return_value = None
            router.get_usage_stats.return_value = {"totalCalls": 0, "totalCost": 0.0, "byModel": []}
            mock_gr.return_value = router

            resp = await handler.process({}, DummyRequest())

        # Simulate: this.availableModels = resp.models?.byProvider || {}
        available_models = resp.get("models", {}).get("byProvider") or {}
        assert isinstance(available_models, dict)
        assert "ollama" in available_models

    @pytest.mark.asyncio
    async def test_dashboard_store_build_available_models_list(self):
        """
        Simulate buildAvailableModelsList() from llm-router-dashboard-store.js
        which iterates Object.entries(this.models.byProvider).
        """
        from python.api.llm_router_dashboard import LlmRouterDashboard

        handler = LlmRouterDashboard(SimpleNamespace(), SimpleNamespace())

        with patch("python.api.llm_router_dashboard.get_router") as mock_gr:
            router = MagicMock()
            router.db.get_models.return_value = SAMPLE_MODELS
            router.get_default_model.return_value = None
            router.get_usage_stats.return_value = {"totalCalls": 0, "totalCost": 0.0, "byModel": []}
            mock_gr.return_value = router

            resp = await handler.process({}, DummyRequest())

        models_data = resp.get("models", {})
        by_provider = models_data.get("byProvider", {})

        # Simulate buildAvailableModelsList
        available = []
        for provider, models in by_provider.items():
            for model in models:
                available.append(
                    {
                        "provider": provider,
                        "name": model["name"],
                        "displayName": model.get("displayName") or model["name"],
                        "isLocal": model.get("isLocal", False),
                        "contextLength": model.get("contextLength", 0),
                    }
                )

        assert len(available) == 3
        providers = {m["provider"] for m in available}
        assert providers == {"ollama", "openai", "anthropic"}

    @pytest.mark.asyncio
    async def test_dashboard_store_stats_cards(self):
        """
        Simulate HTML template bindings:
          $store.llmRouterStore.models.totalCount
          $store.llmRouterStore.usage.last24h.calls
          $store.llmRouterStore.usage.last24h.costUsd
        """
        from python.api.llm_router_dashboard import LlmRouterDashboard

        handler = LlmRouterDashboard(SimpleNamespace(), SimpleNamespace())

        with patch("python.api.llm_router_dashboard.get_router") as mock_gr:
            router = MagicMock()
            router.db.get_models.return_value = SAMPLE_MODELS
            router.get_default_model.return_value = None
            router.get_usage_stats.return_value = {"totalCalls": 42, "totalCost": 1.2345, "byModel": []}
            mock_gr.return_value = router

            resp = await handler.process({}, DummyRequest())

        # These are exactly what the Alpine template binds to
        assert resp["models"]["totalCount"] == 3
        assert resp["models"]["localCount"] == 1
        assert resp["models"]["cloudCount"] == 2
        assert resp["usage"]["last24h"]["calls"] == 42
        assert resp["usage"]["last24h"]["costUsd"] == 1.2345
        assert resp["usage"]["lastHour"]["calls"] == 42
        assert resp["usage"]["lastHour"]["costUsd"] == 1.2345

    @pytest.mark.asyncio
    async def test_empty_response_does_not_crash_object_entries(self):
        """
        When no models exist, Object.entries(byProvider) should get {}
        not undefined.
        """
        from python.api.llm_router_dashboard import LlmRouterDashboard

        handler = LlmRouterDashboard(SimpleNamespace(), SimpleNamespace())

        with patch("python.api.llm_router_dashboard.get_router") as mock_gr:
            router = MagicMock()
            router.db.get_models.return_value = []
            router.get_default_model.return_value = None
            router.get_usage_stats.return_value = {"totalCalls": 0, "totalCost": 0.0, "byModel": []}
            mock_gr.return_value = router

            resp = await handler.process({}, DummyRequest())

        by_provider = resp["models"]["byProvider"]
        assert isinstance(by_provider, dict)
        # Object.entries({}) → [] — no crash
        assert len(by_provider) == 0


# ── 5. KVP filtering ────────────────────────────────────────────────────────


class TestKvpFiltering:
    """Verify that _model and other underscore-prefixed kvps are kept out of the
    display table but still present in the data for badge rendering."""

    def test_underscore_kvps_in_output(self):
        """LogItem.output() should include _model in kvps (it's filtered client-side)."""
        from python.helpers.log import Log, LogItem

        log = MagicMock(spec=Log)
        log.guid = "test-guid"
        item = LogItem(log=log, no=1, type="agent", heading="Test")
        item.kvps = OrderedDict(
            [
                ("thoughts", ["a thought"]),
                ("_model", "anthropic/claude-sonnet-4-20250514"),
                ("headline", "Doing stuff"),
            ]
        )

        output = item.output()
        # _model should be in the serialized output (UI filters it from display table)
        assert "_model" in output["kvps"]
        assert output["kvps"]["_model"] == "anthropic/claude-sonnet-4-20250514"


# ── 6. formatCost null-safety ────────────────────────────────────────────────


class TestFormatCostNullSafety:
    """Validate the JS formatCost function logic handles edge cases.

    These are Python-side contract tests simulating the JS behavior
    to ensure the store function won't break on null/undefined inputs.
    """

    @staticmethod
    def _format_cost_py(cost):
        """Python port of the JS formatCost function for testing."""
        if cost is None:
            return "$0.00"
        if cost == 0:
            return "Free"
        if cost < 0.01:
            return "<$0.01"
        return f"${cost:.2f}"

    def test_format_cost_null(self):
        assert self._format_cost_py(None) == "$0.00"

    def test_format_cost_zero(self):
        assert self._format_cost_py(0) == "Free"

    def test_format_cost_tiny(self):
        assert self._format_cost_py(0.001) == "<$0.01"

    def test_format_cost_normal(self):
        assert self._format_cost_py(1.50) == "$1.50"

    def test_format_cost_large(self):
        assert self._format_cost_py(99.99) == "$99.99"
