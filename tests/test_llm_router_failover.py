"""
Tests for LLM Router failover functionality

Tests automatic failover when primary models fail, including:
- Failover to next model in chain
- Permanent vs transient failure detection
- Provider unavailability marking
- Baseline model as last resort
"""

from unittest.mock import MagicMock, patch

import pytest

from python.helpers.llm_router import (
    FailoverResult,
    LLMRouter,
    ModelInfo,
    _is_permanent_failure,
    call_with_failover,
    get_available_providers,
    mark_provider_unavailable,
)


class TestFailoverResult:
    """Test FailoverResult data class"""

    def test_success_result(self):
        """Test creating a successful result"""
        model = ModelInfo(
            provider="google",
            name="gemini-2.0-flash",
            display_name="Gemini Flash",
            capabilities=["chat"],
            is_available=True,
            is_local=False,
        )
        result = FailoverResult(
            success=True,
            response="Hello!",
            reasoning="",
            model_used=model,
            attempts=[{"provider": "google", "model_name": "gemini-2.0-flash", "success": True}],
        )

        assert result.success is True
        assert result.response == "Hello!"
        assert result.model_used.provider == "google"
        assert len(result.attempts) == 1

    def test_failure_result(self):
        """Test creating a failure result"""
        result = FailoverResult(
            success=False,
            error="All models failed",
            attempts=[
                {"provider": "anthropic", "model_name": "claude-3", "success": False, "error": "blocked"},
                {"provider": "google", "model_name": "gemini", "success": False, "error": "rate limited"},
            ],
        )

        assert result.success is False
        assert "All models failed" in result.error
        assert len(result.attempts) == 2


class TestPermanentFailureDetection:
    """Test _is_permanent_failure function"""

    def test_auth_failure_is_permanent(self):
        """Authentication errors should be permanent"""
        exc = Exception("Invalid API key provided")
        assert _is_permanent_failure(exc) is True

        exc = Exception("Unauthorized: authentication required")
        assert _is_permanent_failure(exc) is True

    def test_billing_failure_is_permanent(self):
        """Billing/quota errors should be permanent"""
        exc = Exception("Billing quota exceeded for this account")
        assert _is_permanent_failure(exc) is True

        exc = Exception("Account suspended due to non-payment")
        assert _is_permanent_failure(exc) is True

    def test_blocked_failure_is_permanent(self):
        """Blocked/forbidden errors should be permanent"""
        exc = Exception("Access denied: API blocked for your organization")
        assert _is_permanent_failure(exc) is True

        exc = Exception("Forbidden: this model is disabled")
        assert _is_permanent_failure(exc) is True

    def test_status_code_401_is_permanent(self):
        """401 status code should be permanent"""
        exc = MagicMock()
        exc.status_code = 401
        exc.__str__ = lambda self: "Unauthorized"
        assert _is_permanent_failure(exc) is True

    def test_status_code_403_is_permanent(self):
        """403 status code should be permanent"""
        exc = MagicMock()
        exc.status_code = 403
        exc.__str__ = lambda self: "Forbidden"
        assert _is_permanent_failure(exc) is True

    def test_rate_limit_is_not_permanent(self):
        """Rate limit errors should NOT be permanent (transient)"""
        exc = Exception("Rate limit exceeded, please retry")
        assert _is_permanent_failure(exc) is False

    def test_timeout_is_not_permanent(self):
        """Timeout errors should NOT be permanent (transient)"""
        exc = Exception("Request timed out")
        assert _is_permanent_failure(exc) is False

    def test_server_error_is_not_permanent(self):
        """Server errors should NOT be permanent (transient)"""
        exc = Exception("Internal server error")
        assert _is_permanent_failure(exc) is False


class TestCallWithFailover:
    """Test call_with_failover async function"""

    @pytest.fixture
    def primary_model(self):
        return ModelInfo(
            provider="anthropic",
            name="claude-3-sonnet",
            display_name="Claude 3 Sonnet",
            capabilities=["chat", "code"],
            is_available=True,
            is_local=False,
        )

    @pytest.fixture
    def fallback_models(self):
        return [
            ModelInfo(
                provider="google",
                name="gemini-2.0-flash",
                display_name="Gemini Flash",
                capabilities=["chat"],
                is_available=True,
                is_local=False,
            ),
            ModelInfo(
                provider="ollama",
                name="qwen2.5-coder:3b",
                display_name="Qwen Baseline",
                capabilities=["chat", "baseline"],
                is_available=True,
                is_local=True,
            ),
        ]

    @pytest.mark.asyncio
    async def test_success_on_first_try(self, primary_model, fallback_models):
        """Should succeed with primary model on first try"""

        async def mock_call(provider, model_name):
            return ("Success response", "")

        with patch("python.helpers.llm_router.get_router") as mock_get_router:
            mock_router = MagicMock()
            mock_router.get_fallback_chain.return_value = fallback_models
            mock_router.record_call = MagicMock()
            mock_get_router.return_value = mock_router

            result = await call_with_failover(primary_model=primary_model, call_func=mock_call, max_retries=3)

            assert result.success is True
            assert result.response == "Success response"
            assert result.model_used.provider == "anthropic"
            assert len(result.attempts) == 1

    @pytest.mark.asyncio
    async def test_failover_to_second_model(self, primary_model, fallback_models):
        """Should failover to second model when first fails"""
        call_count = 0

        async def mock_call(provider, model_name):
            nonlocal call_count
            call_count += 1
            if provider == "anthropic":
                raise Exception("Claude is blocked")
            return ("Gemini response", "")

        with patch("python.helpers.llm_router.get_router") as mock_get_router:
            mock_router = MagicMock()
            mock_router.get_fallback_chain.return_value = fallback_models
            mock_router.record_call = MagicMock()
            mock_router.db = MagicMock()
            mock_get_router.return_value = mock_router

            result = await call_with_failover(primary_model=primary_model, call_func=mock_call, max_retries=3)

            assert result.success is True
            assert result.response == "Gemini response"
            assert result.model_used.provider == "google"
            assert len(result.attempts) == 2
            assert call_count == 2

    @pytest.mark.asyncio
    async def test_failover_to_baseline(self, primary_model, fallback_models):
        """Should failover to baseline when all cloud models fail"""

        async def mock_call(provider, model_name):
            if provider == "anthropic":
                raise Exception("Claude blocked")
            elif provider == "google":
                raise Exception("Gemini rate limited")
            return ("Baseline response", "")

        with patch("python.helpers.llm_router.get_router") as mock_get_router:
            mock_router = MagicMock()
            mock_router.get_fallback_chain.return_value = fallback_models
            mock_router.record_call = MagicMock()
            mock_router.db = MagicMock()
            mock_get_router.return_value = mock_router

            result = await call_with_failover(primary_model=primary_model, call_func=mock_call, max_retries=3)

            assert result.success is True
            assert result.response == "Baseline response"
            assert result.model_used.provider == "ollama"
            assert result.model_used.is_local is True
            assert len(result.attempts) == 3

    @pytest.mark.asyncio
    async def test_all_models_fail(self, primary_model, fallback_models):
        """Should return failure when all models fail"""

        async def mock_call(provider, model_name):
            raise Exception(f"{provider} failed")

        with patch("python.helpers.llm_router.get_router") as mock_get_router:
            mock_router = MagicMock()
            mock_router.get_fallback_chain.return_value = fallback_models
            mock_router.record_call = MagicMock()
            mock_router.db = MagicMock()
            mock_get_router.return_value = mock_router

            result = await call_with_failover(primary_model=primary_model, call_func=mock_call, max_retries=3)

            assert result.success is False
            assert "All 3 models failed" in result.error
            assert len(result.attempts) == 3

    @pytest.mark.asyncio
    async def test_permanent_failure_marks_provider_unavailable(self, primary_model, fallback_models):
        """Permanent failures should mark the provider as unavailable"""

        async def mock_call(provider, model_name):
            if provider == "anthropic":
                raise Exception("Unauthorized: Invalid API key")
            return ("Success", "")

        with patch("python.helpers.llm_router.get_router") as mock_get_router:
            mock_router = MagicMock()
            mock_router.get_fallback_chain.return_value = fallback_models
            mock_router.record_call = MagicMock()
            mock_router.db = MagicMock()
            mock_get_router.return_value = mock_router

            result = await call_with_failover(primary_model=primary_model, call_func=mock_call, max_retries=3)

            # Should have called mark_provider_models_unavailable for anthropic
            mock_router.db.mark_provider_models_unavailable.assert_called_once_with("anthropic")
            assert result.success is True


class TestProviderAvailability:
    """Test provider availability functions"""

    def test_mark_provider_unavailable(self):
        """Should mark all models from a provider as unavailable"""
        with patch("python.helpers.llm_router.get_router") as mock_get_router:
            mock_router = MagicMock()
            mock_router.db = MagicMock()
            mock_get_router.return_value = mock_router

            mark_provider_unavailable("anthropic")

            mock_router.db.mark_provider_models_unavailable.assert_called_once_with("anthropic")

    def test_get_available_providers(self):
        """Should return list of available providers"""
        mock_models = [
            ModelInfo(
                provider="google",
                name="gemini",
                display_name="Gemini",
                capabilities=["chat"],
                is_available=True,
                is_local=False,
            ),
            ModelInfo(
                provider="ollama",
                name="qwen",
                display_name="Qwen",
                capabilities=["chat"],
                is_available=True,
                is_local=True,
            ),
            ModelInfo(
                provider="google",
                name="gemini-pro",
                display_name="Gemini Pro",
                capabilities=["chat"],
                is_available=True,
                is_local=False,
            ),
        ]

        with patch("python.helpers.llm_router.get_router") as mock_get_router:
            mock_router = MagicMock()
            mock_router.db = MagicMock()
            mock_router.db.get_models.return_value = mock_models
            mock_get_router.return_value = mock_router

            providers = get_available_providers()

            assert set(providers) == {"google", "ollama"}


class TestQuickSwitchMethodFix:
    """Test that quick switch API uses correct method name"""

    def test_set_default_model_method_exists(self):
        """Verify set_default_model method exists on LLMRouter"""
        router = LLMRouter()

        # The method should exist
        assert hasattr(router, "set_default_model")
        assert callable(router.set_default_model)

        # The old incorrect method should NOT exist
        assert not hasattr(router, "set_default")
