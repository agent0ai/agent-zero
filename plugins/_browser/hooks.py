from __future__ import annotations

import importlib
import importlib.metadata
import importlib.util
import shutil
import subprocess
import sys
import threading
from pathlib import Path

from helpers import files, plugins, yaml as yaml_helper
from plugins._browser.helpers.config import (
    PLUGIN_NAME,
    browser_runtime_config,
    normalize_browser_config,
    validate_extension_browser_selection_change,
)
from plugins._browser.helpers.playwright import (
    ensure_playwright_binary,
    find_playwright_binary,
    get_playwright_cache_dir,
    get_retired_playwright_cache_dirs,
)
from plugins._browser.helpers.runtime import close_all_runtimes_sync


_SETUP_LOCK = threading.Lock()
_PLUGIN_DIR = Path(__file__).resolve().parent
_ROOT_REQUIREMENTS_FILE = _PLUGIN_DIR.parents[1] / "requirements.txt"


def _load_saved_browser_config(project_name: str = "", agent_profile: str = "") -> dict:
    entries = plugins.find_plugin_assets(
        plugins.CONFIG_FILE_NAME,
        plugin_name=PLUGIN_NAME,
        project_name=project_name,
        agent_profile=agent_profile,
        only_first=True,
    )
    path = entries[0].get("path", "") if entries else ""
    if path and files.exists(path):
        return files.read_file_json(path) or {}

    plugin_dir = plugins.find_plugin_dir(PLUGIN_NAME)
    default_path = (
        files.get_abs_path(plugin_dir, plugins.CONFIG_DEFAULT_FILE_NAME)
        if plugin_dir
        else ""
    )
    if default_path and files.exists(default_path):
        return yaml_helper.loads(files.read_file(default_path)) or {}

    return {}


def get_plugin_config(default=None, **kwargs):
    return normalize_browser_config(default)


def save_plugin_config(settings=None, project_name="", agent_profile="", **kwargs):
    normalized = normalize_browser_config(settings)
    current = normalize_browser_config(
        _load_saved_browser_config(project_name=project_name, agent_profile=agent_profile)
    )
    validate_extension_browser_selection_change(
        proposed_value=normalized.get("host_browser_selection"),
        current_value=current.get("host_browser_selection"),
        proposed_runtime_backend=normalized.get("runtime_backend"),
        current_runtime_backend=current.get("runtime_backend"),
    )
    from plugins._browser.helpers.config import parse_extension_browser_selection

    try:
        previous_extension = parse_extension_browser_selection(current.get("host_browser_selection"))
    except ValueError:
        previous_extension = None
    if previous_extension is not None and (
        normalized.get("host_browser_selection") != previous_extension.value
        or normalized.get("runtime_backend") != "host_required"
    ):
        from plugins._a0_connector.helpers.browser_bridge_bootstrap import get_browser_bridge_application

        application = get_browser_bridge_application()
        if application is not None:
            application.registry.retire_bridge(previous_extension.bridge_id)
    if browser_runtime_config(normalized) != browser_runtime_config(current):
        close_all_runtimes_sync()
    return normalized


def cleanup_playwright_cache() -> dict:
    primary = Path(get_playwright_cache_dir())
    retired_dirs = [
        path for path in get_retired_playwright_cache_dirs() if path.resolve() != primary.resolve()
    ]
    result = {"primary": str(primary), "migrated": "", "removed": [], "errors": []}

    if find_playwright_binary(primary):
        _remove_cache_dirs(retired_dirs, result)
        return result

    source = _best_playwright_cache(retired_dirs)
    if not source:
        return result

    backup = _next_backup_path(primary) if primary.exists() else None
    try:
        if backup:
            primary.rename(backup)
        primary.parent.mkdir(parents=True, exist_ok=True)
        shutil.move(str(source), str(primary))
        result["migrated"] = str(source)
    except Exception as exc:
        if backup and backup.exists() and not primary.exists():
            backup.rename(primary)
        result["errors"].append(f"Failed to migrate {source} to {primary}: {exc}")
        return result

    if not find_playwright_binary(primary):
        result["errors"].append(f"Migrated Playwright cache is not valid: {primary}")
        if backup:
            result["errors"].append(f"Previous primary Playwright cache retained at {backup}")
        return result

    if backup:
        _remove_cache_dirs([backup], result)
    _remove_cache_dirs(retired_dirs, result)
    return result


def prepare_playwright_cache() -> dict:
    with _SETUP_LOCK:
        _ensure_patchright_dependency()
        result = cleanup_playwright_cache()
        if result["errors"]:
            return result
        result["binary"] = str(ensure_playwright_binary())
        return result


def install() -> dict:
    return prepare_playwright_cache()


def _ensure_patchright_dependency() -> None:
    requirement = _patchright_requirement()
    if _patchright_is_current(requirement):
        return

    uv = shutil.which("uv")
    if not uv:
        raise RuntimeError("Browser plugin requires 'uv' to install Patchright automatically")

    subprocess.check_call(
        [uv, "pip", "install", "--python", sys.executable, requirement],
        cwd=str(_PLUGIN_DIR),
    )
    importlib.invalidate_caches()
    if not _patchright_is_current(requirement):
        raise RuntimeError(
            f"Browser dependency {requirement!r} is unavailable after installation"
        )


def _patchright_requirement() -> str:
    if _ROOT_REQUIREMENTS_FILE.is_file():
        for line in _ROOT_REQUIREMENTS_FILE.read_text(encoding="utf-8").splitlines():
            requirement = line.strip()
            if requirement.startswith("patchright=="):
                return requirement
    raise RuntimeError(f"Browser Patchright requirement not found in {_ROOT_REQUIREMENTS_FILE}")


def _patchright_is_current(requirement: str) -> bool:
    expected_version = requirement.partition("==")[2]
    if not expected_version or importlib.util.find_spec("patchright") is None:
        return False
    try:
        return importlib.metadata.version("patchright") == expected_version
    except importlib.metadata.PackageNotFoundError:
        return False


def _best_playwright_cache(candidates: list[Path]) -> Path | None:
    valid = [path for path in candidates if path.is_dir() and find_playwright_binary(path)]
    if not valid:
        return None

    def modified_at(path: Path) -> float:
        binary = find_playwright_binary(path)
        try:
            return binary.stat().st_mtime if binary else path.stat().st_mtime
        except OSError:
            return 0

    return max(valid, key=modified_at)


def _next_backup_path(path: Path) -> Path:
    backup = path.with_name(f"{path.name}.migration-backup")
    counter = 2
    while backup.exists():
        backup = path.with_name(f"{path.name}.migration-backup-{counter}")
        counter += 1
    return backup


def _remove_cache_dirs(paths: list[Path], result: dict) -> None:
    for path in paths:
        if not path.exists():
            continue
        try:
            shutil.rmtree(path)
            result["removed"].append(str(path))
        except Exception as exc:
            result["errors"].append(f"Failed to remove Playwright cache {path}: {exc}")
