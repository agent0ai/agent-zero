"""
Tests for baseline model auto-pull functionality
"""

import os
from unittest.mock import Mock, patch

import pytest

from python.helpers.llm_router import ensure_baseline_model


class TestBaselineAutoPull:
    """Test baseline model auto-pull"""

    @pytest.mark.asyncio
    async def test_baseline_already_available(self):
        """Should return True immediately if baseline already available"""
        with patch("python.helpers.llm_router.get_router") as mock_get_router:
            mock_router = Mock()
            mock_baseline = Mock()
            mock_baseline.is_available = True
            mock_baseline.display_name = "Qwen 2.5 Coder 3B"
            mock_router.get_baseline_model.return_value = mock_baseline
            mock_get_router.return_value = mock_router

            result = await ensure_baseline_model()

            assert result is True

    @pytest.mark.asyncio
    async def test_auto_pull_disabled(self):
        """Should return False when auto-pull disabled"""
        with patch.dict(os.environ, {"BASELINE_AUTO_PULL": "false"}):
            with patch("python.helpers.llm_router.get_router") as mock_get_router:
                mock_router = Mock()
                mock_router.get_baseline_model.return_value = None
                mock_get_router.return_value = mock_router

                result = await ensure_baseline_model()

                assert result is False

    @pytest.mark.asyncio
    async def test_auto_pull_success(self):
        """Should pull baseline model when missing and auto-pull enabled"""
        with patch.dict(os.environ, {"BASELINE_AUTO_PULL": "true"}):
            with patch("python.helpers.llm_router.get_router") as mock_get_router:
                with patch("subprocess.run") as mock_run:
                    # Setup mocks
                    mock_router = Mock()
                    mock_router.get_baseline_model.return_value = None

                    # Mock discover_models as async function
                    async def mock_discover(force=False):
                        return []

                    mock_router.discover_models = mock_discover
                    mock_get_router.return_value = mock_router

                    # Mock successful subprocess
                    mock_result = Mock()
                    mock_result.returncode = 0
                    mock_run.return_value = mock_result

                    result = await ensure_baseline_model()

                    assert result is True
                    mock_run.assert_called_once()
                    # Verify safe command (no shell injection)
                    call_args = mock_run.call_args
                    assert call_args[0][0][0] == "docker"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
