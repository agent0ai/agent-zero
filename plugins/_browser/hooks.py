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
    if browser_runtime_config(normalized) != browser_runtime_config(current):
        close_all_runtimes_sync()
    return normalized



def install():
    return {'sandbox': True, 'installed_on_demand': True}


def disable():
    close_all_runtimes_sync()
    from plugins._browser.helpers.sandbox import worker
    worker.stop()


def uninstall():
    disable()
    from plugins._browser.helpers.sandbox import worker
    from helpers.sandbox import get_manager
    manager = get_manager()
    if (manager.config.instances_dir / worker.name / 'metadata.json').exists():
        manager.delete(worker.name)
