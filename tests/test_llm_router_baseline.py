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


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
