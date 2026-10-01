"""Retire the former community ACP plugin after Core ships its replacement."""
from __future__ import annotations

import shutil
from pathlib import Path
from typing import Any

from helpers import cache, files
from helpers.extension import Extension
from helpers.print_style import PrintStyle


LEGACY_PLUGIN_NAME = "a0_acp"


class LegacyAcpMigration(Extension):
    def execute(self, **kwargs: Any) -> None:
        result = migrate_legacy_acp()
        if result["removed_roots"]:
            PrintStyle.info("Removed retired ACP plugin files:", result["removed_roots"])


def migrate_legacy_acp(base_dir: str | Path | None = None) -> dict[str, list[str]]:
    root = Path(base_dir or files.get_abs_path("")).resolve()
    removed_roots: list[str] = []
    errors: list[str] = []

    for plugin_root in _legacy_plugin_roots(root):
        try:
            if plugin_root.is_dir() and not plugin_root.is_symlink():
                shutil.rmtree(plugin_root)
            else:
                plugin_root.unlink()
            removed_roots.append(str(plugin_root))
        except OSError as exc:
            errors.append(f"Could not remove retired ACP plugin at {plugin_root}: {exc}")

    if removed_roots:
        cache.clear("*(plugins)*")
        cache.clear("*(extensions)*")
        cache.clear("*(api)*")

    return {"removed_roots": removed_roots, "errors": errors}


def _legacy_plugin_roots(root: Path) -> list[Path]:
    candidates = [
        root / "usr" / "plugins" / LEGACY_PLUGIN_NAME,
        *root.glob(f"usr/projects/*/.a0proj/plugins/{LEGACY_PLUGIN_NAME}"),
        *root.glob(f"usr/projects/*/.a0proj/agents/*/plugins/{LEGACY_PLUGIN_NAME}"),
        *root.glob(f"usr/agents/*/plugins/{LEGACY_PLUGIN_NAME}"),
    ]
    return [candidate for candidate in candidates if candidate.exists() or candidate.is_symlink()]
