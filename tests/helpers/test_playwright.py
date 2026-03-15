"""Tests for python/helpers/playwright.py."""

import sys
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


class TestGetPlaywrightCacheDir:
    """Tests for get_playwright_cache_dir."""

    def test_returns_path_from_files_get_abs_path(self):
        """get_playwright_cache_dir delegates to files.get_abs_path."""
        with patch("python.helpers.playwright.files") as mock_files:
            mock_files.get_abs_path.return_value = "/abs/tmp/playwright"
            from python.helpers.playwright import get_playwright_cache_dir

            result = get_playwright_cache_dir()
            mock_files.get_abs_path.assert_called_once_with("tmp/playwright")
            assert result == "/abs/tmp/playwright"


class TestGetPlaywrightBinary:
    """Tests for get_playwright_binary."""

    def test_returns_binary_when_found(self, tmp_path):
        """Returns path when chromium headless shell binary exists."""
        # Create directory structure that matches glob pattern
        shell_dir = tmp_path / "chromium_headless_shell-1" / "chrome-2"
        shell_dir.mkdir(parents=True)
        binary_file = shell_dir / "headless_shell"
        binary_file.touch()

        with patch("python.helpers.playwright.get_playwright_cache_dir", return_value=str(tmp_path)):
            from python.helpers.playwright import get_playwright_binary

            result = get_playwright_binary()
            assert result is not None
            assert "headless_shell" in str(result)

    def test_returns_none_when_not_found(self, tmp_path):
        """Returns None when no binary matches."""
        # Empty dir - no chromium binary
        with patch("python.helpers.playwright.get_playwright_cache_dir", return_value=str(tmp_path)):
            from python.helpers.playwright import get_playwright_binary

            result = get_playwright_binary()
            assert result is None


class TestEnsurePlaywrightBinary:
    """Tests for ensure_playwright_binary."""

    def test_returns_existing_binary_without_install(self):
        """When binary exists, returns it without calling subprocess."""
        fake_bin = Path("/cache/chromium_headless_shell-1/chrome-1/headless_shell")
        with patch("python.helpers.playwright.get_playwright_binary", return_value=fake_bin):
            with patch("python.helpers.playwright.subprocess") as mock_sub:
                from python.helpers.playwright import ensure_playwright_binary

                result = ensure_playwright_binary()
                assert result == fake_bin
                mock_sub.check_call.assert_not_called()

    def test_installs_when_binary_missing_then_returns(self):
        """When binary missing, runs playwright install then returns binary."""
        fake_bin = Path("/cache/chromium_headless_shell-1/chrome-1/headless_shell")
        with patch("python.helpers.playwright.get_playwright_binary", side_effect=[None, fake_bin]):
            with patch("python.helpers.playwright.get_playwright_cache_dir", return_value="/cache"):
                with patch("python.helpers.playwright.subprocess") as mock_sub:
                    with patch.dict("os.environ", {"PLAYWRIGHT_BROWSERS_PATH": ""}, clear=False):
                        from python.helpers.playwright import ensure_playwright_binary

                        result = ensure_playwright_binary()
                        assert result == fake_bin
                        mock_sub.check_call.assert_called_once()
                        call_args = mock_sub.check_call.call_args[0][0]
                        assert call_args == ["playwright", "install", "chromium", "--only-shell"]

    def test_raises_when_install_fails_to_produce_binary(self):
        """Raises when binary still missing after install."""
        with patch("python.helpers.playwright.get_playwright_binary", return_value=None):
            with patch("python.helpers.playwright.get_playwright_cache_dir", return_value="/cache"):
                with patch("python.helpers.playwright.subprocess"):
                    from python.helpers.playwright import ensure_playwright_binary

                    with pytest.raises(Exception, match="Playwright binary not found"):
                        ensure_playwright_binary()
