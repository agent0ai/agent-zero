"""
Tests for baseline model configuration and fallback logic
"""

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

        router.db.get_models = lambda available_only=False: mock_models

        baseline = router.get_baseline_model()

        assert baseline is not None
        assert baseline.name == "qwen2.5-coder:3b"
        assert baseline.metadata.get("priority_baseline") is True

    def test_get_baseline_model_when_unavailable(self):
        """Should return None when no baseline model available"""
        router = LLMRouter()

        router.db.get_models = lambda available_only=False: []

        baseline = router.get_baseline_model()

        assert baseline is None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
