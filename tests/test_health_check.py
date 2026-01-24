"""
Tests for model health check system
"""

from unittest.mock import Mock, patch

import pytest

from python.helpers.llm_router import LLMRouter


class TestHealthCheck:
    """Test health check functionality"""

    @pytest.mark.asyncio
    async def test_health_check_ollama_available(self):
        """Should report Ollama as healthy when running"""
        router = LLMRouter()

        # Mock urllib response for Ollama
        mock_response = Mock()
        mock_response.read.return_value = b'{"models": [{"name": "qwen2.5-coder:3b"}]}'
        mock_response.__enter__ = Mock(return_value=mock_response)
        mock_response.__exit__ = Mock(return_value=False)

        with patch("urllib.request.urlopen", return_value=mock_response):
            status = await router.health_check_models(providers=["ollama"])

        assert "ollama" in status["healthy"]
        assert status["baseline_available"]

    @pytest.mark.asyncio
    async def test_health_check_ollama_unavailable(self):
        """Should report Ollama as unavailable when not running"""
        router = LLMRouter()

        with patch("urllib.request.urlopen", side_effect=Exception("Connection refused")):
            status = await router.health_check_models(providers=["ollama"])

        assert len(status["unavailable"]) > 0
        assert any("ollama" in item for item in status["unavailable"])

    @pytest.mark.asyncio
    async def test_health_check_baseline_missing(self):
        """Should recommend pulling baseline when missing"""
        router = LLMRouter()

        # Mock Ollama running but without baseline model
        mock_response = Mock()
        mock_response.read.return_value = b'{"models": [{"name": "llama2:7b"}]}'
        mock_response.__enter__ = Mock(return_value=mock_response)
        mock_response.__exit__ = Mock(return_value=False)

        with patch("urllib.request.urlopen", return_value=mock_response):
            status = await router.health_check_models(providers=["ollama"])

        assert not status["baseline_available"]
        assert any("pull" in rec.lower() for rec in status["recommendations"])


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
