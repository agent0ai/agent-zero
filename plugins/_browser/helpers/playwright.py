import json
import os
import re
import subprocess
import sys
from importlib import resources
from pathlib import Path

from helpers import files

FULL_CHROMIUM_PATTERNS = (
    "chromium-*/chrome-linux*/chrome",
    "chromium-*/chrome-win*/chrome.exe",
)
PLAYWRIGHT_CACHE_ENV = "A0_BROWSER_PLAYWRIGHT_CACHE_DIR"
PLAYWRIGHT_CACHE_DIR = ("tmp", "playwright")
RETIRED_PLAYWRIGHT_CACHE_DIRS = (
    ("usr", "plugins", "_browser", "playwright"),
    ("usr", "browser", "playwright"),
)


def _primary_cache_dir() -> Path:
    override = os.environ.get(PLAYWRIGHT_CACHE_ENV, "").strip()
    if override:
        return Path(override).expanduser()
    return Path(files.get_abs_path(*PLAYWRIGHT_CACHE_DIR))


def get_playwright_cache_dir() -> str:
    return str(_primary_cache_dir())


def get_playwright_cache_dirs() -> list[Path]:
    primary = _primary_cache_dir()
    candidates = [primary, *get_retired_playwright_cache_dirs()]
    seen: set[str] = set()
    unique: list[Path] = []
    for candidate in candidates:
        key = str(candidate)
        if key in seen:
            continue
        seen.add(key)
        unique.append(candidate)
    return unique


def get_retired_playwright_cache_dirs() -> list[Path]:
    return [Path(files.get_abs_path(*parts)) for parts in RETIRED_PLAYWRIGHT_CACHE_DIRS]


def configure_playwright_env() -> str:
    cache_dir = get_playwright_cache_dir()
    Path(cache_dir).mkdir(parents=True, exist_ok=True)
    os.environ["PLAYWRIGHT_BROWSERS_PATH"] = cache_dir
    return cache_dir


def find_playwright_binary(cache_dir: Path, revision: str = "") -> Path | None:
    prefix = f"chromium-{revision}" if revision.isdigit() else "chromium-*"
    binaries = [
        binary
        for pattern in FULL_CHROMIUM_PATTERNS
        for binary in cache_dir.glob(pattern.replace("chromium-*", prefix))
        if binary.exists()
    ]
    return max(binaries, key=_chromium_revision) if binaries else None


def _chromium_revision(binary: Path) -> int:
    match = re.search(r"chromium-(\d+)", binary.as_posix())
    return int(match.group(1)) if match else -1


def get_playwright_binary() -> Path | None:
    cache_dir = _primary_cache_dir()
    binary = find_playwright_binary(_primary_cache_dir())
    revision = get_playwright_chromium_revision()
    if revision and (not binary or _chromium_revision(binary) != int(revision)):
        return find_playwright_binary(cache_dir, revision=revision)
    return binary


def get_playwright_chromium_revision() -> str:
    try:
        manifest = resources.files("patchright").joinpath("driver/package/browsers.json")
        browsers = json.loads(manifest.read_text(encoding="utf-8"))["browsers"]
        revision = next(
            str(browser.get("revision", ""))
            for browser in browsers
            if browser.get("name") == "chromium"
        )
    except (ImportError, FileNotFoundError, KeyError, StopIteration, TypeError, ValueError):
        return ""
    return revision if revision.isdigit() else ""


def ensure_playwright_binary() -> Path:
    binary = get_playwright_binary()
    if binary:
        return binary

    cache_dir = configure_playwright_env()
    env = os.environ.copy()
    env["PLAYWRIGHT_BROWSERS_PATH"] = cache_dir
    subprocess.check_call(
        [sys.executable, "-m", "patchright", "install", "chromium", "--no-shell"],
        env=env,
    )

    binary = get_playwright_binary()
    if not binary:
        raise RuntimeError("Patchright Chromium binary not found after installation")
    return binary
