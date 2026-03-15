"""Tests for python/helpers/browser.py.

Note: The browser module is currently fully commented out. These tests verify
module structure and prepare for when the implementation is restored.
"""

import sys
from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


class TestBrowserModule:
    """Tests for the browser module (currently commented out)."""

    def test_browser_module_imports(self):
        """Module can be imported without error."""
        import python.helpers.browser as browser_module

        assert browser_module is not None

    def test_browser_module_has_no_exports_when_commented(self):
        """When implementation is commented out, module has no public exports."""
        import python.helpers.browser as browser_module

        # Filter out dunder and private names
        public = [
            name
            for name in dir(browser_module)
            if not name.startswith("_") and name.isupper() or name[0].isupper()
        ]
        # With all code commented, we expect no Browser class or similar
        assert "Browser" not in dir(browser_module)
        assert "NoPageError" not in dir(browser_module)

    def test_browser_file_exists(self):
        """Source file exists at expected path."""
        browser_path = PROJECT_ROOT / "python" / "helpers" / "browser.py"
        assert browser_path.exists()
        assert browser_path.is_file()

    def test_browser_file_contains_browser_reference(self):
        """Source file contains expected class/exception names (in comments)."""
        browser_path = PROJECT_ROOT / "python" / "helpers" / "browser.py"
        content = browser_path.read_text()
        assert "Browser" in content
        assert "NoPageError" in content
        assert "async_playwright" in content
