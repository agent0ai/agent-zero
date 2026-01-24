"""
Tests for baseline model configuration and fallback logic
"""

from unittest.mock import patch

import pytest

from python.helpers.llm_router import LLMRouter, ModelInfo


class TestBaselineModel:
    """Test baseline model functionality"""

    def test_qwen_3b_marked_as_baseline(self):
        """Verify Qwen 2.5 3B is configured as baseline model"""
        router = LLMRouter()

        # Check MODEL_CATALOG entry
        qwen_3b_key = "ollama/qwen2.5-coder:3b"
        assert qwen_3b_key in router.MODEL_CATALOG

        config = router.MODEL_CATALOG[qwen_3b_key]
        assert "baseline" in config["capabilities"]
        assert config.get("priority_baseline") is True

    def test_get_baseline_model_returns_qwen_3b(self):
        """get_baseline_model() should return Qwen 2.5 3B when available"""
        router = LLMRouter()

        # Mock available models including qwen 3b
        mock_models = [
            ModelInfo(
                provider="ollama",
                name="qwen2.5-coder:3b",
                display_name="Qwen 2.5 Coder 3B",
                capabilities=["chat", "code", "fast", "baseline"],
                is_local=True,
                is_available=True,
                size_gb=1.9,
                context_length=32768,
                metadata={"priority_baseline": True},
            )
        ]

        with patch.object(router.db, "get_models", return_value=mock_models):
            baseline = router.get_baseline_model()

            assert baseline is not None
            assert baseline.name == "qwen2.5-coder:3b"
            assert baseline.metadata.get("priority_baseline") is True

    def test_get_baseline_model_falls_back_to_capability(self):
        """Should select smallest local model with baseline capability when no priority_baseline"""
        router = LLMRouter()

        # Mock models with baseline capability but no priority_baseline flag
        mock_models = [
            ModelInfo(
                provider="ollama",
                name="llama3.2:3b",
                display_name="Llama 3.2 3B",
                capabilities=["chat", "baseline"],
                is_local=True,
                is_available=True,
                size_gb=2.0,
                context_length=8192,
                metadata={},
            ),
            ModelInfo(
                provider="ollama",
                name="phi3:mini",
                display_name="Phi-3 Mini",
                capabilities=["chat", "baseline"],
                is_local=True,
                is_available=True,
                size_gb=2.3,
                context_length=4096,
                metadata={},
            ),
            ModelInfo(
                provider="ollama",
                name="gemma:2b",
                display_name="Gemma 2B",
                capabilities=["chat", "baseline"],
                is_local=True,
                is_available=True,
                size_gb=1.4,
                context_length=8192,
                metadata={},
            ),
        ]

        with patch.object(router.db, "get_models", return_value=mock_models):
            baseline = router.get_baseline_model()

            assert baseline is not None
            assert baseline.name == "gemma:2b"  # Smallest by size_gb
            assert baseline.size_gb == 1.4

    def test_get_baseline_model_when_unavailable(self):
        """Should return None when no baseline model available"""
        router = LLMRouter()

        with patch.object(router.db, "get_models", return_value=[]):
            baseline = router.get_baseline_model()

            assert baseline is None


class TestFallbackChain:
    """Test fallback chain includes baseline"""

    def test_fallback_chain_includes_baseline_as_last(self):
        """Fallback chain should always include baseline as final fallback"""
        router = LLMRouter()

        # Mock models
        mock_models = [
            ModelInfo(
                provider="ollama",
                name="qwen2.5-coder:3b",
                display_name="Qwen 2.5 Coder 3B",
                capabilities=["chat", "code", "baseline"],
                is_local=True,
                is_available=True,
                size_gb=1.9,
                context_length=32768,
                metadata={"priority_baseline": True},
            ),
            ModelInfo(
                provider="ollama",
                name="qwen2.5-coder:7b",
                display_name="Qwen 2.5 Coder 7B",
                capabilities=["chat", "code"],
                is_local=True,
                is_available=True,
                size_gb=4.7,
                context_length=32768,
                metadata={},
            ),
            ModelInfo(
                provider="openai",
                name="gpt-4o-mini",
                display_name="GPT-4o Mini",
                capabilities=["chat", "code", "fast"],
                is_local=False,
                is_available=True,
                size_gb=0,
                context_length=128000,
                metadata={},
            ),
        ]

        with patch.object(router.db, "get_models", return_value=mock_models):
            primary = mock_models[1]  # Use 7b as primary
            fallback_chain = router.get_fallback_chain(primary, max_fallbacks=3)

            # Baseline should be last in chain
            assert len(fallback_chain) > 0
            assert fallback_chain[-1].name == "qwen2.5-coder:3b"
            assert fallback_chain[-1].metadata.get("priority_baseline") is True

    def test_fallback_chain_respects_capabilities(self):
        """Fallback chain should only include models with required capabilities"""
        router = LLMRouter()

        mock_models = [
            ModelInfo(
                provider="ollama",
                name="qwen2.5-coder:3b",
                display_name="Qwen 2.5 Coder 3B",
                capabilities=["chat", "code", "baseline"],
                is_local=True,
                is_available=True,
                size_gb=1.9,
                context_length=32768,
                metadata={"priority_baseline": True},
            ),
            ModelInfo(
                provider="ollama",
                name="phi3:mini",
                display_name="Phi-3 Mini",
                capabilities=["chat", "fast"],  # No "code" capability
                is_local=True,
                is_available=True,
                size_gb=2.2,
                context_length=4096,
                metadata={},
            ),
        ]

        with patch.object(router.db, "get_models", return_value=mock_models):
            primary = mock_models[0]
            fallback_chain = router.get_fallback_chain(primary, required_capabilities=["code"], max_fallbacks=3)

            # Only models with "code" capability should be included
            for model in fallback_chain:
                assert "code" in model.capabilities


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
