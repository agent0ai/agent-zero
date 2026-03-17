from __future__ import annotations

from datetime import datetime, timezone
import json
import os
import time
from turtle import stamp
import urllib.request
import uuid
import zipfile
from pathlib import Path
from typing import Any

from helpers import files, print_style, plugins, git
from helpers import yaml as yaml_helper
from helpers.plugins import (
    META_FILE_NAME,
    PluginMetadata,
    get_plugins_list,
    after_plugin_change,
)
from werkzeug.datastructures import FileStorage
from werkzeug.utils import secure_filename


def _get_user_plugins_dir() -> str:
    """Return absolute path to usr/plugins/."""
    return files.get_abs_path(files.USER_DIR, files.PLUGINS_DIR)


def _get_plugin_name(meta: PluginMetadata) -> str:
    plugin_name = (meta.name or "").strip()
    if not plugin_name:
        raise ValueError(f"{META_FILE_NAME} is missing required field 'name'")
    return plugin_name


def validate_plugin_dir(path: str, plugin_name: str = "") -> PluginMetadata:
    """Check directory contains plugin.yaml and return parsed metadata.
    Raises ValueError if plugin.yaml is missing or invalid."""
    meta_path = os.path.join(path, META_FILE_NAME)
    if not os.path.isfile(meta_path):
        raise ValueError(f"No {META_FILE_NAME} found in {os.path.basename(path)}")
    with open(meta_path, "r", encoding="utf-8") as f:
        content = f.read()
    data = yaml_helper.loads(content)
    model = PluginMetadata.model_validate(data)
    if plugin_name and plugin_name != model.name:
        raise ValueError(
            f"Plugin name is incorrect: expected '{plugin_name}', got '{model.name}'. The author needs to correct this in the plugin.yaml file."
        )
    return model


def check_plugin_conflict(name: str) -> None:
    """Raise ValueError if a plugin with this name already exists in usr/plugins/."""
    dest = os.path.join(_get_user_plugins_dir(), name)
    if os.path.exists(dest):
        raise ValueError(f"Plugin '{name}' is already installed")


def _find_plugin_root(extracted_dir: str) -> str:
    """Walk extracted directory to find the parent of plugin.yaml.
    Returns absolute path to the plugin root directory."""
    for root, dirs, dir_files in os.walk(extracted_dir):
        if META_FILE_NAME in dir_files:
            return root
    raise ValueError(f"No {META_FILE_NAME} found in the uploaded archive")


def install_uploaded_zip(plugin_file: FileStorage) -> dict:
    """Persist an uploaded ZIP temporarily and install it."""
    original_filename = Path((plugin_file.filename or "").strip()).name
    if not original_filename:
        raise ValueError("No file selected")

    tmp_dir = Path(files.get_abs_path("tmp", "plugin_uploads"))
    tmp_dir.mkdir(parents=True, exist_ok=True)

    temp_name = secure_filename(original_filename) or "plugin.zip"
    if not temp_name.lower().endswith(".zip"):
        temp_name = f"{temp_name}.zip"

    unique = uuid.uuid4().hex[:8]
    stamp = time.strftime("%Y%m%d_%H%M%S")
    tmp_path = str(tmp_dir / f"plugin_{stamp}_{unique}_{temp_name}")
    plugin_file.save(tmp_path)

    return install_from_zip(tmp_path, original_filename=original_filename)


def install_from_zip(zip_path: str, original_filename: str | None = None) -> dict:
    """Extract ZIP, find plugin.yaml, move its parent to usr/plugins/.
    Returns dict with plugin name and metadata.
    Cleans up tmp files regardless of outcome."""
    temp_name = f"tmp_plugin_{time.strftime('%Y%m%d_%H%M%S')}_{uuid.uuid4().hex[:8]}"
    extract_dir = files.get_abs_path(files.TEMP_DIR, "plugin_installs", temp_name)
    extract_dir = files.create_dir_safe(extract_dir)
    dest = ""

    try:
        try:
            # Extract with path traversal protection
            with zipfile.ZipFile(zip_path, "r") as z:
                for member in z.namelist():
                    member_path = os.path.realpath(os.path.join(extract_dir, member))
                    if not (files.is_in_dir(member_path, extract_dir)):
                        raise ValueError(f"Unsafe path in archive: {member}")
                z.extractall(extract_dir)

            # Find plugin.yaml
            plugin_root = _find_plugin_root(extract_dir)
            meta = validate_plugin_dir(plugin_root)
            plugin_name = _get_plugin_name(meta)

            check_plugin_conflict(plugin_name)

            # Move to usr/plugins/
            dest = os.path.join(_get_user_plugins_dir(), plugin_name)
            files.create_dir(os.path.dirname(dest))
            files.move_dir(plugin_root, dest)
        except Exception as e:
            print_style.PrintStyle.error(f"Failed to validate plugin: {e}")
            files.delete_dir(extract_dir)
            raise

        # run installation hook
        try:
            run_install_hook(plugin_name)
        except Exception as e:
            print_style.PrintStyle.error(
                f"Failed to run installation hook for {plugin_name}: {e}"
            )
            files.delete_dir(dest)
            raise

        after_plugin_change([plugin_name])

        return {
            "success": True,
            "plugin_name": plugin_name,
            "title": meta.title or plugin_name,
            "path": files.deabsolute_path(dest),
        }
    finally:
        # Cleanup: extracted files and the archive
        try:
            files.delete_dir(extract_dir)
            files.delete_file(zip_path)
        except Exception as e:
            pass


def install_from_git(url: str, token: str | None = None, plugin_name: str = "") -> dict:
    """Clone git repo into usr/plugins/, validate plugin.yaml.
    Returns dict with plugin name and metadata."""
    from helpers.git import clone_repo

    temp_name = f"tmp_plugin_{time.strftime('%Y%m%d_%H%M%S')}_{uuid.uuid4().hex[:8]}"
    git_dir = files.get_abs_path(files.TEMP_DIR, "plugins_installer", temp_name)

    try:
        files.create_dir_safe(git_dir)
        clone_repo(url, git_dir, token=token or None)
        meta = validate_plugin_dir(git_dir, plugin_name=plugin_name)
        plugin_name = _get_plugin_name(meta)
        check_plugin_conflict(plugin_name)
        final_dir = os.path.join(_get_user_plugins_dir(), plugin_name)
        files.move_dir(git_dir, final_dir)
    except Exception as e:
        # No plugin.yaml — remove cloned repo
        print_style.PrintStyle.error(f"Failed to validate plugin: {e}")
        files.delete_dir(git_dir)
        raise

    # run installation hook
    try:
        run_install_hook(plugin_name)
    except Exception as e:
        print_style.PrintStyle.error(
            f"Failed to run installation hook for {plugin_name}: {e}"
        )
        files.delete_dir(final_dir)
        raise

    after_plugin_change([plugin_name])

    return {
        "success": True,
        "plugin_name": plugin_name,
        "title": meta.title or plugin_name,
        "path": files.deabsolute_path(final_dir),
    }


def update_from_git(plugin_name: str) -> dict:
    plugin_name = (plugin_name or "").strip()
    if not plugin_name:
        raise ValueError("Missing plugin_name")

    plugin_dir = plugins.find_plugin_dir(plugin_name)
    if not plugin_dir:
        raise ValueError("Plugin not found")

    custom_plugins_dir = files.get_abs_path(files.USER_DIR, files.PLUGINS_DIR)
    if not files.is_in_dir(plugin_dir, custom_plugins_dir):
        raise ValueError("Only custom plugins can be updated")

    try:
        repo = git.update_repo(plugin_dir)
        meta = plugins.get_plugin_meta(plugin_name)
    except Exception as e:
        print_style.PrintStyle.error(f"Failed to update plugin: {e}")
        raise

    try:
        run_install_hook(plugin_name)
    except Exception as e:
        print_style.PrintStyle.error(
            f"Failed to run installation hook for {plugin_name}: {e}"
        )
        raise

    after_plugin_change([plugin_name])
    head = repo.head.commit

    return {
        "ok": True,
        "success": True,
        "plugin_name": plugin_name,
        "title": meta.title if meta else plugin_name,
        "path": files.deabsolute_path(plugin_dir),
        "current_commit": head.hexsha,
        "current_commit_timestamp": datetime.fromtimestamp(head.committed_date, timezone.utc).strftime("%Y-%m-%d %H:%M:%S"),
        "version": getattr(meta, "version", "") or "",
        "branch": repo.active_branch.name if not repo.head.is_detached else "",
        "remote_url": git.strip_auth_from_url(repo.remotes.origin.url) if repo.remotes else "",
        "directory_name": Path(plugin_dir).name,
    }


def run_install_hook(plugin_name: str):
    return plugins.call_plugin_hook(plugin_name, "install")


def get_plugin_hub_index() -> dict[str, Any]:
    """Return the plugin index plus installed Plugin Hub keys."""
    index_data = fetch_plugin_index()
    if not isinstance(index_data, dict):
        raise ValueError("Plugin index response was not a JSON object")

    plugins = index_data.get("plugins")
    if not isinstance(plugins, dict):
        raise ValueError("Plugin index payload is missing a valid 'plugins' map")

    installed_dirs = set(get_plugins_list())
    installed_keys: list[str] = []
    for key, plugin_data in plugins.items():
        if not isinstance(plugin_data, dict):
            continue
        if key in installed_dirs:
            installed_keys.append(key)

    return {"index": index_data, "installed_plugins": installed_keys}


def fetch_plugin_index() -> dict:
    """Download the plugin index from GitHub releases."""
    index_url = "https://github.com/agent0ai/a0-plugins/releases/download/generated-index/index.json"
    req = urllib.request.Request(index_url, headers={"User-Agent": "AgentZero"})
    with urllib.request.urlopen(req, timeout=30) as resp:
        data = json.loads(resp.read().decode())
    return data
