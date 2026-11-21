import os
import subprocess
import sys

import pytest

from plugins._time_travel.helpers import retention


def test_cleanup_skips_history_locked_by_another_process(tmp_path):
    shadow = tmp_path / "workspaces"
    entry = shadow / ("a" * 32)
    entry.mkdir(parents=True)
    (entry / "old-history").write_text("fixture")
    os.utime(entry, (0, 0))
    script = """
import sys
from pathlib import Path
from plugins._time_travel.helpers.locking import workspace_lock
with workspace_lock(Path(sys.argv[1])):
    print("locked", flush=True)
    sys.stdin.read(1)
"""
    process = subprocess.Popen(
        [sys.executable, "-c", script, str(entry)],
        stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True,
    )
    try:
        assert process.stdout.readline().strip() == "locked"
        stats = retention.sweep(shadow_root=str(shadow), live_ids=set(), state_dir=str(tmp_path))
        assert entry.exists()
        assert stats["orphans_removed"] == 0
    finally:
        process.communicate("x", timeout=5)
    assert process.returncode == 0
    stats = retention.sweep(shadow_root=str(shadow), live_ids=set(), state_dir=str(tmp_path))
    assert stats["orphans_removed"] == 1
    assert (shadow / ".locks" / f"{entry.name}.lock").exists()


def test_failed_owner_discovery_never_deletes_history(tmp_path, monkeypatch):
    entry = tmp_path / ("a" * 32)
    entry.mkdir()
    os.utime(entry, (0, 0))

    def unreadable():
        raise PermissionError("owner directory unreadable")

    monkeypatch.setattr(retention, "live_workspace_ids", unreadable)
    with pytest.raises(PermissionError):
        retention.sweep(shadow_root=str(tmp_path), state_dir=str(tmp_path))
    assert entry.exists()


def test_cleanup_skips_symlinks_and_does_not_count_failed_deletions(tmp_path, monkeypatch):
    shadow = tmp_path / "workspaces"
    shadow.mkdir()
    outside = tmp_path / "outside"
    outside.mkdir()
    (shadow / ("a" * 32)).symlink_to(outside, target_is_directory=True)
    entry = shadow / ("b" * 32)
    entry.mkdir()
    os.utime(entry, (0, 0))
    def denied(_path):
        raise PermissionError()

    monkeypatch.setattr(retention.shutil, "rmtree", denied)
    stats = retention.sweep(shadow_root=str(shadow), live_ids=set(), state_dir=str(tmp_path))
    assert stats["orphans_removed"] == 0
    assert outside.exists() and entry.exists()


def test_cleanup_does_not_follow_symlinked_repository(tmp_path):
    outside = tmp_path / "outside"
    outside.mkdir()
    lock = outside / "index.lock"
    lock.write_text("protected")
    os.utime(lock, (0, 0))
    shadow = tmp_path / "workspaces"
    entry = shadow / ("a" * 32)
    entry.mkdir(parents=True)
    (entry / "repo.git").symlink_to(outside, target_is_directory=True)
    stats = retention.sweep(shadow_root=str(shadow), live_ids={entry.name}, state_dir=str(tmp_path))
    assert stats["stale_locks_removed"] == 0
    assert lock.read_text() == "protected"
