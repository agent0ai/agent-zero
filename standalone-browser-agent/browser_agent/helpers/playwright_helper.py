"""
Playwright helper functions for ensuring browser binaries are installed.
"""

import subprocess
import sys
from pathlib import Path


def ensure_playwright_installed():
    """Ensure playwright browsers are installed."""
    try:
        # Check if playwright is installed
        import playwright

        # Try to get the browser path
        result = subprocess.run(
            [sys.executable, "-m", "playwright", "install", "chromium"],
            capture_output=True,
            text=True
        )

        if result.returncode != 0:
            print(f"Warning: Failed to install playwright browsers: {result.stderr}")

    except ImportError:
        raise ImportError(
            "Playwright is not installed. Please run: pip install playwright"
        )


def get_playwright_binary():
    """Get path to playwright chromium binary."""
    try:
        result = subprocess.run(
            [sys.executable, "-m", "playwright", "install", "chromium", "--dry-run"],
            capture_output=True,
            text=True
        )

        # Parse output to find browser path
        # This is a fallback - browser-use usually handles this automatically
        return None

    except Exception as e:
        print(f"Could not determine playwright binary path: {e}")
        return None
