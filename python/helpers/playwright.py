
from pathlib import Path
import subprocess
import sys
import platform
from python.helpers import files


# this helper ensures that playwright is installed in /lib/playwright
# should work for both docker and local installation

def get_playwright_binary():
    """Get the Playwright Chromium binary path.

    Looks for full Chromium browser first (supports both headless and visible mode),
    falls back to headless shell if full browser not found.

    Platform-aware: Only searches for binaries matching the current OS to prevent
    attempting to run wrong-platform binaries (e.g., macOS binary in Linux Docker).
    """
    pw_cache = Path(get_playwright_cache_dir())

    # Detect current platform
    system = platform.system()

    # Search for platform-specific full Chromium browser (supports visible mode)
    full_browser = None
    if system == "Darwin":  # macOS
        full_browser = next(pw_cache.glob("chromium-*/chrome-mac/Chromium.app/Contents/MacOS/Chromium"), None)
    elif system == "Linux":
        full_browser = next(pw_cache.glob("chromium-*/chrome-linux/chrome"), None)
    elif system == "Windows":
        full_browser = next(pw_cache.glob("chromium-*/chrome-win/chrome.exe"), None)

    if full_browser:
        return full_browser

    # Fallback to platform-specific headless shell (headless-only, can't show GUI)
    headless_shell = None
    if system == "Darwin":  # macOS
        headless_shell = next(pw_cache.glob("chromium_headless_shell-*/chrome-mac/headless_shell"), None)
    elif system == "Linux":
        headless_shell = next(pw_cache.glob("chromium_headless_shell-*/chrome-linux/headless_shell"), None)
    elif system == "Windows":
        headless_shell = next(pw_cache.glob("chromium_headless_shell-*/chrome-win/headless_shell.exe"), None)

    return headless_shell

def get_playwright_cache_dir():
    return files.get_abs_path("tmp/playwright")

def ensure_playwright_binary():
    """Ensure Playwright browser is installed.

    Installs full Chromium browser (supports both visible and headless modes).
    Falls back to headless shell only if full browser installation fails.

    Cleans up wrong-platform binaries if found (e.g., macOS binary in Linux Docker).
    """
    import os
    import shutil

    bin = get_playwright_binary()
    if not bin:
        cache = get_playwright_cache_dir()
        pw_cache = Path(cache)

        # Clean up wrong-platform binaries to avoid confusion and save space
        system = platform.system()
        wrong_platform_dirs = []

        if system != "Darwin":  # Not macOS - remove macOS binaries
            wrong_platform_dirs.extend(pw_cache.glob("chromium-*/chrome-mac"))
        if system != "Linux":  # Not Linux - remove Linux binaries
            wrong_platform_dirs.extend(pw_cache.glob("chromium-*/chrome-linux"))
        if system != "Windows":  # Not Windows - remove Windows binaries
            wrong_platform_dirs.extend(pw_cache.glob("chromium-*/chrome-win"))

        for wrong_dir in wrong_platform_dirs:
            print(f"Removing wrong-platform binary: {wrong_dir}")
            # Remove the entire chromium-* directory, not just the platform subdirectory
            chromium_dir = wrong_dir.parent
            if chromium_dir.exists():
                shutil.rmtree(chromium_dir)

        env = os.environ.copy()
        env["PLAYWRIGHT_BROWSERS_PATH"] = cache

        # Install full Chromium browser (supports both visible and headless modes)
        print(f"Installing Playwright Chromium browser for {system} (supports visible mode)...")
        try:
            subprocess.check_call(
                [sys.executable, "-m", "playwright", "install", "chromium"],
                env=env
            )
        except subprocess.CalledProcessError as e:
            print(f"Failed to install full Chromium: {e}")
            print("Falling back to headless shell (headless-only)...")
            # Fallback: install headless shell only
            subprocess.check_call(
                [sys.executable, "-m", "playwright", "install", "chromium", "--only-shell"],
                env=env
            )

    bin = get_playwright_binary()
    if not bin:
        raise Exception("Playwright binary not found after installation")
    return bin