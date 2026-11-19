"""Locks shared by history operations and retention, outside removable repositories."""

from pathlib import Path

from filelock import FileLock


def workspace_lock(shadow_path: Path) -> FileLock:
    lock_dir = shadow_path.parent / ".locks"
    lock_dir.mkdir(parents=True, exist_ok=True)
    return FileLock(str(lock_dir / f"{shadow_path.name}.lock"), timeout=20, is_singleton=True)
