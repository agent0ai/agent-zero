from __future__ import annotations

import os
import shutil
import stat
import subprocess
import sys
from pathlib import Path
from typing import Any

from helpers.extension import Extension
from helpers.print_style import PrintStyle


SELF_UPDATE_MANAGER_PATH = Path(
    os.environ.get("A0_SELF_UPDATE_MANAGER_PATH", "/exe/self_update_manager.py")
)
SELF_UPDATE_MANAGER_SOURCE_PATH = Path(
    os.environ.get(
        "A0_SELF_UPDATE_MANAGER_SOURCE_PATH",
        "/a0/docker/run/fs/exe/self_update_manager.py",
    )
)
BACKUP_SUFFIX = ".startup-migration-backup"
REQUIRED_RUNTIME_MARKERS = (
    "def should_include_usr_backup_entry(",
    "Skipping non-regular usr backup entry",
    "def clean_transient_desktop_agent_state(",
    "clean_transient_desktop_agent_state(REPO_DIR, logger)",
    "def refresh_codex_cli(",
    "refresh_codex_cli(logger)",
)


class SelfUpdateManagerRuntimeSync(Extension):
    def execute(self, **kwargs):
        result = ensure_self_update_manager_runtime_current()
        if result.get("updated"):
            PrintStyle.info("Self-update manager runtime synchronized:", result["target"])
            warning = start_codex_cli_refresh(result["target"])
            if warning:
                PrintStyle.warning("Codex CLI refresh could not be started:", warning)
        elif result.get("warning"):
            PrintStyle.warning("Self-update manager runtime sync skipped:", result["warning"])


def ensure_self_update_manager_runtime_current(
    *,
    target_path: Path | str | None = None,
    source_path: Path | str | None = None,
) -> dict[str, Any]:
    target = Path(target_path) if target_path is not None else SELF_UPDATE_MANAGER_PATH
    source = Path(source_path) if source_path is not None else SELF_UPDATE_MANAGER_SOURCE_PATH

    target_text, target_warning = _read_regular_text(target, role="runtime self-update manager")
    if target_text is None:
        return {"ok": True, "updated": False, "reason": target_warning}

    source_text, source_warning = _read_regular_text(source, role="source self-update manager")
    if source_text is None:
        return {"ok": False, "updated": False, "warning": source_warning}

    missing_source_markers = _missing_required_markers(source_text)
    if missing_source_markers:
        return {
            "ok": False,
            "updated": False,
            "warning": (
                "source self-update manager is missing required safety markers: "
                + ", ".join(missing_source_markers)
            ),
        }

    if not _missing_required_markers(target_text):
        return {"ok": True, "updated": False, "reason": "already-current"}

    try:
        backup = _replace_runtime_manager(target, source_text)
    except OSError as exc:
        return {
            "ok": False,
            "updated": False,
            "warning": f"could not update {target}: {exc}",
        }

    return {
        "ok": True,
        "updated": True,
        "target": str(target),
        "backup": str(backup),
    }


def start_codex_cli_refresh(manager_path: Path | str) -> str:
    try:
        subprocess.Popen(
            [sys.executable, str(manager_path), "refresh-codex"],
            stdin=subprocess.DEVNULL,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            start_new_session=True,
        )
    except OSError as exc:
        return str(exc)
    return ""


def _missing_required_markers(text: str) -> list[str]:
    return [marker for marker in REQUIRED_RUNTIME_MARKERS if marker not in text]


def _read_regular_text(path: Path, *, role: str) -> tuple[str | None, str]:
    try:
        path_stat = path.lstat()
    except FileNotFoundError:
        return None, f"{role} not found: {path}"
    except OSError as exc:
        return None, f"{role} could not be inspected: {path}: {exc}"

    if not stat.S_ISREG(path_stat.st_mode):
        return None, f"{role} is not a regular file: {path}"

    try:
        return path.read_text(encoding="utf-8"), ""
    except OSError as exc:
        return None, f"{role} could not be read: {path}: {exc}"


def _replace_runtime_manager(target: Path, source_text: str) -> Path:
    target_stat = target.stat()
    backup = _ensure_backup(target)
    temp_path = target.with_name(f".{target.name}.{os.getpid()}.tmp")
    try:
        temp_path.write_text(source_text, encoding="utf-8")
        os.chmod(temp_path, stat.S_IMODE(target_stat.st_mode))
        os.replace(temp_path, target)
    finally:
        temp_path.unlink(missing_ok=True)
    return backup


def _ensure_backup(target: Path) -> Path:
    backup = target.with_name(f"{target.name}{BACKUP_SUFFIX}")
    if not backup.exists():
        shutil.copy2(target, backup)
    return backup
