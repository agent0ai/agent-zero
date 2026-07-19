from __future__ import annotations

import stat
import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from extensions.python.startup_migration import _10_self_update_manager as migration


SAFE_SOURCE = """#!/usr/bin/env python3
from pathlib import Path


REPO_DIR = Path("/a0")


def should_include_usr_backup_entry(source_file, logger):
    logger.log("Skipping non-regular usr backup entry")
    return False


def clean_transient_desktop_agent_state(repo_dir, logger):
    return None


def refresh_codex_cli(logger):
    return None


def docker_run_ui():
    clean_transient_desktop_agent_state(REPO_DIR, logger)
    refresh_codex_cli(logger)
"""


def test_self_update_runtime_sync_replaces_stale_manager(tmp_path):
    source = tmp_path / "source_self_update_manager.py"
    target = tmp_path / "self_update_manager.py"
    stale = "# old updater without non-regular usr backup guards\n"
    source.write_text(SAFE_SOURCE, encoding="utf-8")
    target.write_text(stale, encoding="utf-8")
    target.chmod(0o600)

    result = migration.ensure_self_update_manager_runtime_current(
        target_path=target,
        source_path=source,
    )

    assert result["ok"] is True
    assert result["updated"] is True
    assert target.read_text(encoding="utf-8") == SAFE_SOURCE
    assert (target.stat().st_mode & 0o777) == 0o600
    backup = target.with_name(f"{target.name}{migration.BACKUP_SUFFIX}")
    assert backup.read_text(encoding="utf-8") == stale


def test_self_update_runtime_sync_accepts_repository_manager_source(tmp_path):
    source = PROJECT_ROOT / "docker" / "run" / "fs" / "exe" / "self_update_manager.py"
    target = tmp_path / "self_update_manager.py"
    stale = "# old updater without non-regular usr backup guards\n"
    target.write_text(stale, encoding="utf-8")

    result = migration.ensure_self_update_manager_runtime_current(
        target_path=target,
        source_path=source,
    )

    assert result["ok"] is True
    assert result["updated"] is True
    assert target.read_text(encoding="utf-8") == source.read_text(encoding="utf-8")


def test_self_update_runtime_sync_starts_codex_refresh(monkeypatch, tmp_path):
    calls = []
    manager_path = tmp_path / "self_update_manager.py"
    monkeypatch.setattr(
        migration.subprocess,
        "Popen",
        lambda *args, **kwargs: calls.append((args, kwargs)),
    )

    assert migration.start_codex_cli_refresh(manager_path) == ""
    assert calls[0][0][0] == [sys.executable, str(manager_path), "refresh-codex"]
    assert calls[0][1]["start_new_session"] is True


def test_self_update_runtime_sync_skips_current_manager(tmp_path):
    source = tmp_path / "source_self_update_manager.py"
    target = tmp_path / "self_update_manager.py"
    source.write_text(SAFE_SOURCE, encoding="utf-8")
    target.write_text(SAFE_SOURCE, encoding="utf-8")

    result = migration.ensure_self_update_manager_runtime_current(
        target_path=target,
        source_path=source,
    )

    assert result == {"ok": True, "updated": False, "reason": "already-current"}
    backup = target.with_name(f"{target.name}{migration.BACKUP_SUFFIX}")
    assert not backup.exists()


def test_self_update_runtime_sync_refuses_source_without_required_markers(tmp_path):
    source = tmp_path / "source_self_update_manager.py"
    target = tmp_path / "self_update_manager.py"
    stale = "# old updater without non-regular usr backup guards\n"
    source.write_text("def create_usr_backup():\n    pass\n", encoding="utf-8")
    target.write_text(stale, encoding="utf-8")

    result = migration.ensure_self_update_manager_runtime_current(
        target_path=target,
        source_path=source,
    )

    assert result["ok"] is False
    assert result["updated"] is False
    assert "missing required safety markers" in result["warning"]
    assert target.read_text(encoding="utf-8") == stale
    backup = target.with_name(f"{target.name}{migration.BACKUP_SUFFIX}")
    assert not backup.exists()


def test_self_update_runtime_sync_missing_target_is_quiet(tmp_path):
    source = tmp_path / "source_self_update_manager.py"
    target = tmp_path / "missing_self_update_manager.py"
    source.write_text(SAFE_SOURCE, encoding="utf-8")

    result = migration.ensure_self_update_manager_runtime_current(
        target_path=target,
        source_path=source,
    )

    assert result["ok"] is True
    assert result["updated"] is False
    assert "not found" in result["reason"]


def test_self_update_runtime_sync_skips_non_regular_target(tmp_path):
    source = tmp_path / "source_self_update_manager.py"
    target = tmp_path / "self_update_manager.py"
    link_target = tmp_path / "linked_self_update_manager.py"
    source.write_text(SAFE_SOURCE, encoding="utf-8")
    link_target.write_text("# linked updater\n", encoding="utf-8")
    target.symlink_to(link_target)

    result = migration.ensure_self_update_manager_runtime_current(
        target_path=target,
        source_path=source,
    )

    assert result["ok"] is True
    assert result["updated"] is False
    assert "not a regular file" in result["reason"]
    assert stat.S_ISLNK(target.lstat().st_mode)
    assert link_target.read_text(encoding="utf-8") == "# linked updater\n"
