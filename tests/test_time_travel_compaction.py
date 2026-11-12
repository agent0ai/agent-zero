import datetime
import os
import subprocess
import time

import pytest

from plugins._time_travel.helpers import compaction, retention, time_travel as tt
from plugins._time_travel.helpers.locking import workspace_lock


@pytest.fixture
def history(tmp_path, monkeypatch):
    monkeypatch.setattr(tt, "plugin_config", lambda: {})
    work = tmp_path / "work"
    work.mkdir()
    shadow = tmp_path / "workspaces" / ("a" * 32)
    service = tt.TimeTravelService(tt.WorkspaceInfo(
        id=shadow.name, display_path="/a0/usr/workdir", real_path=work,
        shadow_path=shadow, repo_git_path=shadow / "repo.git",
    ))
    return work, service


def capture(work, service, count=8, *, start=None):
    start = time.time() - count * 60 if start is None else start
    commits = []
    for index in range(count):
        (work / "file.txt").write_text(f"version {index}\n")
        stamp = datetime.datetime.fromtimestamp(start + index * 60, datetime.timezone.utc).isoformat()
        commits.append(service.snapshot(metadata={"timestamp": stamp, "version": index}).hash)
    return commits


def compact(service, *, count=3, days=0):
    with workspace_lock(service.workspace.shadow_path):
        return compaction.compact_repository(
            service.workspace.repo_git_path, max_snapshots=count, max_age_days=days, now=time.time(),
        )


def refs(service):
    return service._git("for-each-ref", "--format=%(refname) %(objectname)").stdout


def test_compaction_retains_recent_deltas_and_reclaims_expired_blobs(history):
    work, service = history
    (work / "expired.bin").write_bytes(os.urandom(1024 * 1024))
    old = service.snapshot().hash
    blob = service._git("rev-parse", f"{old}:expired.bin").stdout.strip()
    (work / "expired.bin").unlink()
    capture(work, service)
    tree = service._commit_tree(service.current_hash())
    result = compact(service)
    assert result["repositories_compacted"] == 1
    assert result["gc_runs"] == 1
    assert result["bytes_reclaimed"] > 0
    assert service._commit_tree(service.current_hash()) == tree
    assert (work / "file.txt").read_text() == "version 7\n"
    assert service._git("cat-file", "-e", blob, check=False).returncode != 0
    page = service.history_list()
    assert len(page["commits"]) == 4
    assert [c["metadata"].get("version") for c in page["commits"][:3]] == [7, 6, 5]
    baseline = page["commits"][-1]
    assert baseline["metadata"]["retention_checkpoint"]
    with pytest.raises(tt.TimeTravelConflictError, match="checkpoint"):
        service.revert(commit_hash=baseline["hash"])
    with pytest.raises(tt.TimeTravelConflictError, match="checkpoint"):
        service.preview(operation="revert", commit_hash=baseline["hash"])
    assert compact(service)["gc_runs"] == 0
    oldest = page["commits"][-2]["hash"]
    service.travel(commit_hash=oldest)
    service.revert(commit_hash=oldest)
    assert (work / "file.txt").read_text() == "version 4\n"


def test_compaction_preserves_recent_alternate_timeline(history):
    work, service = history
    commits = capture(work, service, 5)
    preserved_tree = service._commit_tree(commits[-1])
    service.travel(commit_hash=commits[-2])
    (work / "branch.txt").write_text("alternate\n")
    service.snapshot()
    current_tree = service._commit_tree(service.current_hash())
    compact(service, count=2)
    assert service._commit_tree(service.current_hash()) == current_tree
    preserved = service._git("for-each-ref", "--format=%(objectname)", tt.PRESERVED_REF_PREFIX).stdout.splitlines()
    assert len(preserved) == 1
    assert service._commit_tree(preserved[0]) == preserved_tree
    assert len(service._rev_list_all()) == 3


def test_age_expiry_protects_current_state_even_when_old(history):
    work, service = history
    old = capture(work, service, 3, start=time.time() - 60 * 86400)
    recent = capture(work, service, 2)
    recent_tree = service._commit_tree(recent[-1])
    service.travel(commit_hash=old[0])
    old_tree = service._commit_tree(old[0])
    compact(service, count=0, days=1)
    assert service._commit_tree(service.current_hash()) == old_tree
    preserved = service._git("for-each-ref", "--format=%(objectname)", tt.PRESERVED_REF_PREFIX).stdout.splitlines()
    assert len(preserved) == 1
    assert service._commit_tree(preserved[0]) == recent_tree


@pytest.mark.parametrize("failure", ["update-ref", "gc"])
def test_compaction_recovers_from_ref_transaction_or_gc_failure(history, monkeypatch, failure):
    work, service = history
    capture(work, service)
    before_refs = refs(service)
    tree = service._commit_tree(service.current_hash())
    original = compaction._git

    def fail(repo, *args, **kwargs):
        if failure in args:
            raise RuntimeError("injected interruption")
        return original(repo, *args, **kwargs)

    monkeypatch.setattr(compaction, "_git", fail)
    with pytest.raises(RuntimeError, match="interruption"):
        compact(service)
    assert service._commit_tree(service.current_hash()) == tree
    if failure == "update-ref":
        assert refs(service) == before_refs
    assert (service.workspace.shadow_path / "compaction.pending").exists()
    monkeypatch.setattr(compaction, "_git", original)
    compact(service)
    assert not (service.workspace.shadow_path / "compaction.pending").exists()
    assert len(service._rev_list_all()) == 4
    assert (work / "file.txt").read_text() == "version 7\n"
    assert service._git("fsck", "--no-reflogs", check=False).returncode == 0


def test_retention_requires_opt_in_and_expires_old_preserved_refs(history, tmp_path):
    work, service = history
    old = capture(work, service, 5, start=time.time() - 60 * 86400)
    service.travel(commit_hash=old[0])
    capture(work, service)
    before = refs(service)
    args = dict(shadow_root=str(service.workspace.shadow_path.parent), live_ids={service.workspace.id}, state_dir=str(tmp_path))
    retention.sweep(cfg={}, **args)
    assert refs(service) == before
    stats = retention.sweep(cfg={"history_retention_enabled": True, "history_max_snapshots": 3, "history_max_age_days": 1}, **args)
    assert stats["repositories_compacted"] == 1
    assert not service._git("for-each-ref", "--format=%(refname)", tt.PRESERVED_REF_PREFIX).stdout.strip()
    assert len(service._rev_list_all()) == 4


def test_unmanaged_refs_prevent_destructive_cleanup(history):
    work, service = history
    commits = capture(work, service)
    service._git("update-ref", "refs/tags/user-kept", commits[0])
    before = refs(service)
    with pytest.raises(RuntimeError, match="unmanaged"):
        compact(service)
    assert refs(service) == before


def test_compaction_does_not_refresh_workspace_inactivity(history, tmp_path):
    work, service = history
    capture(work, service)
    marker = service.workspace.shadow_path / "last_activity"
    old = time.time() - 2 * 86400
    os.utime(marker, (old, old))
    retention.sweep(
        cfg={"history_retention_enabled": True, "history_max_snapshots": 3},
        shadow_root=str(service.workspace.shadow_path.parent), live_ids={service.workspace.id},
        state_dir=str(tmp_path),
    )
    assert retention._last_activity(str(service.workspace.shadow_path)) == old


def test_snapshot_expiry_requires_a_boolean_opt_in():
    assert not retention.effective_config({"history_retention_enabled": "false"})["history_retention_enabled"]


def test_maintenance_timeout_stops_git_children(tmp_path, monkeypatch):
    executable = tmp_path / "git"
    executable.write_text('#!/bin/sh\n(sleep 0.5; printf orphan > "$TT_CHILD_MARKER") &\nwait\n')
    executable.chmod(0o755)
    marker = tmp_path / "child-completed"
    monkeypatch.setenv("PATH", f"{tmp_path}:{os.environ['PATH']}")
    monkeypatch.setenv("TT_CHILD_MARKER", str(marker))
    with pytest.raises(subprocess.TimeoutExpired):
        compaction._git(tmp_path, "gc", timeout=0.1)
    time.sleep(0.6)
    assert not marker.exists(), "Timed-out GC must not leave children writing after the lock is released"
