from __future__ import annotations

import shutil
from pathlib import Path
from typing import Any

from helpers import cache, files, plugins
from helpers.extension import Extension
from helpers.print_style import PrintStyle


LEGACY_PLUGIN_NAME = "commands"
PLUGIN_NAME = "_commands"
COMMANDS_DIR = "commands"
SKILLS_DIR = "skills"


class LegacyCommandsMigration(Extension):
    def execute(self, **kwargs):
        result = migrate_legacy_commands()
        if result["copied_commands"] or result["copied_skills"] or result["disabled_roots"]:
            PrintStyle.info("Migrated legacy commands plugin data:", result)


def migrate_legacy_commands(base_dir: str | Path | None = None) -> dict[str, Any]:
    root = Path(base_dir or files.get_abs_path("")).resolve()
    result: dict[str, Any] = {
        "copied_commands": 0,
        "copied_skills": 0,
        "disabled_roots": 0,
    }

    legacy_plugin_dir = root / "usr" / "plugins" / LEGACY_PLUGIN_NAME
    if not legacy_plugin_dir.exists() and not _legacy_scoped_plugin_dirs(root):
        return result

    for legacy_commands_dir in _legacy_command_dirs(root):
        target = _replace_plugin_segment(legacy_commands_dir, PLUGIN_NAME)
        result["copied_commands"] += _copy_tree_files(legacy_commands_dir, target)

    result["copied_skills"] += _copy_tree_files(
        legacy_plugin_dir / SKILLS_DIR,
        root / "usr" / "plugins" / PLUGIN_NAME / SKILLS_DIR,
    )

    for legacy_plugin_root in _legacy_plugin_roots(root):
        if _disable_legacy_plugin_root(legacy_plugin_root):
            result["disabled_roots"] += 1

    if result["disabled_roots"]:
        _clear_runtime_caches()

    return result


def _legacy_command_dirs(root: Path) -> list[Path]:
    return [
        plugin_root / COMMANDS_DIR
        for plugin_root in _legacy_plugin_roots(root)
        if (plugin_root / COMMANDS_DIR).is_dir()
    ]


def _legacy_plugin_roots(root: Path) -> list[Path]:
    roots = []
    for candidate in [
        root / "usr" / "plugins" / LEGACY_PLUGIN_NAME,
        *root.glob(f"usr/projects/*/.a0proj/plugins/{LEGACY_PLUGIN_NAME}"),
        *root.glob(f"usr/projects/*/.a0proj/agents/*/plugins/{LEGACY_PLUGIN_NAME}"),
        *root.glob(f"usr/agents/*/plugins/{LEGACY_PLUGIN_NAME}"),
    ]:
        if candidate.exists() and candidate not in roots:
            roots.append(candidate)
    return roots


def _legacy_scoped_plugin_dirs(root: Path) -> list[Path]:
    return [
        *root.glob(f"usr/projects/*/.a0proj/plugins/{LEGACY_PLUGIN_NAME}"),
        *root.glob(f"usr/projects/*/.a0proj/agents/*/plugins/{LEGACY_PLUGIN_NAME}"),
        *root.glob(f"usr/agents/*/plugins/{LEGACY_PLUGIN_NAME}"),
    ]


def _replace_plugin_segment(path: Path, plugin_name: str) -> Path:
    parts = list(path.parts)
    for index in range(len(parts) - 1):
        if parts[index] == "plugins" and parts[index + 1] == LEGACY_PLUGIN_NAME:
            parts[index + 1] = plugin_name
            return Path(*parts)
    return path


def _copy_tree_files(source: Path, target: Path) -> int:
    if not source.is_dir():
        return 0

    copied = 0
    for source_file in source.rglob("*"):
        if not source_file.is_file():
            continue
        relative_path = source_file.relative_to(source)
        target_file = target / relative_path
        if target_file.exists():
            continue
        target_file.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source_file, target_file)
        copied += 1
    return copied


def _disable_legacy_plugin_root(plugin_root: Path) -> bool:
    plugin_root.mkdir(parents=True, exist_ok=True)
    enabled_file = plugin_root / plugins.ENABLED_FILE_NAME
    disabled_file = plugin_root / plugins.DISABLED_FILE_NAME
    changed = enabled_file.exists() or not disabled_file.exists()
    enabled_file.unlink(missing_ok=True)
    disabled_file.write_text("", encoding="utf-8")
    return changed


def _clear_runtime_caches() -> None:
    cache.clear("*(plugins)*")
    cache.clear("*(extensions)*")
