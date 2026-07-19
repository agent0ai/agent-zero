from __future__ import annotations

import os
import shutil
import subprocess
import sys
import threading
import uuid
from pathlib import Path
from types import ModuleType, SimpleNamespace

import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from plugins._time_travel.helpers import time_travel as tt
from plugins._time_travel.helpers.time_travel import (
    TimeTravelConflictError,
    TimeTravelError,
    TimeTravelService,
    WorkspaceRejectedError,
    _workspace_from_display,
    resolve_workspace,
)


def run_git(repo_dir: Path, *args: str, check: bool = True) -> str:
    completed = subprocess.run(
        ["git", "-C", str(repo_dir), *args],
        check=check,
        text=True,
        capture_output=True,
    )
    return completed.stdout.strip()


@pytest.fixture
def workspace():
    name = f"tt-{uuid.uuid4().hex}"
    root = PROJECT_ROOT / "usr" / "time-travel-tests" / name
    root.mkdir(parents=True)
    service = TimeTravelService(_workspace_from_display(f"/a0/usr/time-travel-tests/{name}"))
    try:
        yield root, service
    finally:
        shutil.rmtree(root, ignore_errors=True)
        shutil.rmtree(service.workspace.shadow_path, ignore_errors=True)


def tracked_paths(service: TimeTravelService, commit_hash: str = "HEAD") -> set[str]:
    output = service._git("ls-tree", "-r", "--name-only", commit_hash).stdout
    return {line.strip() for line in output.splitlines() if line.strip()}


def test_shadow_history_snapshot_diff_travel_preserve_refs_and_root_revert(workspace):
    root, service = workspace
    (root / "a.txt").write_text("one\n", encoding="utf-8")

    initial = service.snapshot(trigger="manual", metadata={"context_id": "ctx"})
    duplicate = service.snapshot(trigger="manual")

    assert initial.created is True
    assert duplicate.created is False
    assert duplicate.hash == initial.hash
    assert (service.workspace.repo_git_path / "objects").is_dir()

    (root / "a.txt").write_text("one\ntwo\n", encoding="utf-8")
    present = service.present_summary()
    assert present["dirty"] is True
    assert present["files"][0]["path"] == "a.txt"
    assert "+two" in service.history_diff(commit_hash=initial.hash, path="a.txt", mode="present")["patch"]

    second = service.snapshot(trigger="tool", metadata={"tool_name": "code_execution_tool"})
    history = service.history_list(limit=10)
    assert [commit["hash"] for commit in history["commits"][:2]] == [second.hash, initial.hash]
    assert history["commits"][0]["metadata"]["tool_name"] == "code_execution_tool"
    assert "+two" in service.history_diff(commit_hash=second.hash, path="a.txt", mode="commit")["patch"]

    service.travel(commit_hash=initial.hash)
    assert (root / "a.txt").read_text(encoding="utf-8") == "one\n"
    preserved = service._git(
        "for-each-ref",
        "--format=%(objectname)",
        "refs/a0-time-travel/preserved",
    ).stdout
    assert second.hash in preserved
    assert second.hash in [commit["hash"] for commit in service.history_list(limit=10)["commits"]]

    reverted = service.revert(commit_hash=initial.hash)
    assert reverted["ok"] is True
    assert not (root / "a.txt").exists()
    assert reverted["snapshot"]["created"] is True


def test_revert_conflict_auto_snapshots_present_without_losing_changes(workspace):
    root, service = workspace
    (root / "a.txt").write_text("one\n", encoding="utf-8")
    first = service.snapshot(trigger="manual")
    (root / "a.txt").write_text("one\ntwo\n", encoding="utf-8")
    second = service.snapshot(trigger="manual")
    (root / "a.txt").write_text("custom\n", encoding="utf-8")

    with pytest.raises(TimeTravelConflictError):
        service.revert(commit_hash=second.hash)

    assert (root / "a.txt").read_text(encoding="utf-8") == "custom\n"
    assert service.current_hash() not in {first.hash, second.hash}
    assert "custom" in service.history_diff(commit_hash=service.current_hash(), path="a.txt", mode="commit")["patch"]


def test_kernel_boundary_real_git_repo_and_git_dir_exclusion(workspace):
    root, service = workspace
    with pytest.raises(WorkspaceRejectedError):
        _workspace_from_display("/tmp/outside")

    run_git(root, "init")
    run_git(root, "config", "user.name", "Test User")
    run_git(root, "config", "user.email", "test@example.com")
    (root / "tracked.txt").write_text("tracked\n", encoding="utf-8")
    run_git(root, "add", "tracked.txt")
    run_git(root, "commit", "-m", "real initial")
    real_head = run_git(root, "rev-parse", "HEAD")
    (root / "untracked.txt").write_text("shadow only\n", encoding="utf-8")
    real_status_before = run_git(root, "status", "--short")

    snapshot = service.snapshot(trigger="manual")

    assert snapshot.created is True
    assert run_git(root, "rev-parse", "HEAD") == real_head
    assert run_git(root, "status", "--short") == real_status_before
    assert all(not path.startswith(".git/") and path != ".git" for path in tracked_paths(service))
    assert "tracked.txt" in tracked_paths(service, snapshot.hash)
    assert "untracked.txt" in tracked_paths(service, snapshot.hash)


def test_snapshot_force_adds_curated_paths_ignored_by_workspace_gitignore(workspace):
    root, service = workspace
    (root / ".gitignore").write_text("ignored.txt\nignored-dir/\n.env\n", encoding="utf-8")
    (root / "ignored.txt").write_text("still important\n", encoding="utf-8")
    (root / "ignored-dir").mkdir()
    (root / "ignored-dir" / "note.txt").write_text("nested\n", encoding="utf-8")
    (root / ".env").write_text("SECRET=still excluded\n", encoding="utf-8")

    snapshot = service.snapshot(trigger="manual")
    paths = tracked_paths(service, snapshot.hash)

    assert ".gitignore" in paths
    assert "ignored.txt" in paths
    assert "ignored-dir/note.txt" in paths
    assert ".env" not in paths


def test_shadow_repo_empty_head_is_repaired_without_losing_history(workspace):
    root, service = workspace
    (root / "a.txt").write_text("one\n", encoding="utf-8")
    first = service.snapshot(trigger="manual")
    (service.workspace.repo_git_path / "HEAD").write_text("", encoding="utf-8")

    (root / "a.txt").write_text("one\ntwo\n", encoding="utf-8")
    second = service.snapshot(trigger="manual")

    assert second.created is True
    assert service.current_hash() == second.hash
    assert [commit["hash"] for commit in service.history_list(limit=10)["commits"][:2]] == [
        second.hash,
        first.hash,
    ]


def test_workspace_identity_canonicalizes_symlink_aliases():
    name = f"tt-{uuid.uuid4().hex}"
    root = PROJECT_ROOT / "usr" / "time-travel-tests" / name
    target = root / "target"
    alias = root / "alias"
    target.mkdir(parents=True)
    os.symlink(target, alias)

    target_workspace = _workspace_from_display(f"/a0/usr/time-travel-tests/{name}/target")
    alias_workspace = _workspace_from_display(f"/a0/usr/time-travel-tests/{name}/alias")
    try:
        assert alias_workspace.id == target_workspace.id
        assert alias_workspace.display_path == target_workspace.display_path
    finally:
        shutil.rmtree(root, ignore_errors=True)
        shutil.rmtree(target_workspace.shadow_path, ignore_errors=True)


def test_usr_root_snapshot_skips_plugins_and_nested_git_projects(tmp_path: Path):
    root = tmp_path / "usr"
    root.mkdir()
    (root / "workdir").mkdir()
    (root / "workdir" / "note.txt").write_text("note\n", encoding="utf-8")
    (root / "plugins" / "demo").mkdir(parents=True)
    (root / "plugins" / "demo" / "plugin.yaml").write_text("name: demo\n", encoding="utf-8")
    (root / "projects" / "git-project").mkdir(parents=True)
    (root / "projects" / "git-project" / ".git").mkdir()
    (root / "projects" / "git-project" / "app.py").write_text("print('tracked elsewhere')\n", encoding="utf-8")
    (root / "projects" / "plain-project").mkdir(parents=True)
    (root / "projects" / "plain-project" / "app.py").write_text("print('plain')\n", encoding="utf-8")

    paths = set(tt.iter_snapshot_paths(root, display_path="/a0/usr"))

    assert "workdir/note.txt" in paths
    assert "projects/plain-project/app.py" in paths
    assert "plugins/demo/plugin.yaml" not in paths
    assert "projects/git-project/app.py" not in paths


def test_metadata_policy_tracks_safe_project_files_and_preserves_exclusions(workspace):
    root, service = workspace
    (root / "src").mkdir()
    (root / "src" / "app.py").write_text("print('one')\n", encoding="utf-8")
    (root / ".a0proj" / "instructions").mkdir(parents=True)
    (root / ".a0proj" / "knowledge").mkdir(parents=True)
    (root / ".a0proj" / "skills" / "demo").mkdir(parents=True)
    (root / ".a0proj" / "plugins" / "demo").mkdir(parents=True)
    (root / ".a0proj" / "memory").mkdir(parents=True)
    (root / "node_modules").mkdir()
    (root / "dist").mkdir()
    (root / "__pycache__").mkdir()
    (root / ".a0proj" / "project.json").write_text("{}", encoding="utf-8")
    (root / ".a0proj" / "agents.json").write_text("{}", encoding="utf-8")
    (root / ".a0proj" / "instructions" / "one.md").write_text("i\n", encoding="utf-8")
    (root / ".a0proj" / "knowledge" / "one.md").write_text("k\n", encoding="utf-8")
    (root / ".a0proj" / "skills" / "demo" / "SKILL.md").write_text("s\n", encoding="utf-8")
    (root / ".a0proj" / "plugins" / "demo" / "config.json").write_text("{}", encoding="utf-8")
    (root / ".a0proj" / "plugins" / "demo" / "presets.yaml").write_text("[]\n", encoding="utf-8")
    (root / ".a0proj" / "plugins" / "demo" / "state.json").write_text('{"state": true}\n', encoding="utf-8")
    (root / ".a0proj" / "secrets.env").write_text("SECRET=one\n", encoding="utf-8")
    (root / ".a0proj" / "variables.env").write_text("VAR=one\n", encoding="utf-8")
    (root / ".a0proj" / "memory" / "index.faiss").write_bytes(b"memory")
    (root / ".env").write_text("TOKEN=one\n", encoding="utf-8")
    (root / "node_modules" / "pkg.js").write_text("pkg\n", encoding="utf-8")
    (root / "dist" / "bundle.js").write_text("dist\n", encoding="utf-8")
    (root / "__pycache__" / "app.pyc").write_bytes(b"pyc")

    first = service.snapshot(trigger="manual")
    paths = tracked_paths(service, first.hash)

    assert "src/app.py" in paths
    assert ".a0proj/project.json" in paths
    assert ".a0proj/agents.json" in paths
    assert ".a0proj/instructions/one.md" in paths
    assert ".a0proj/knowledge/one.md" in paths
    assert ".a0proj/skills/demo/SKILL.md" in paths
    assert ".a0proj/plugins/demo/config.json" in paths
    assert ".a0proj/plugins/demo/presets.yaml" in paths
    assert ".a0proj/plugins/demo/state.json" not in paths
    assert ".a0proj/secrets.env" not in paths
    assert ".a0proj/variables.env" not in paths
    assert ".a0proj/memory/index.faiss" not in paths
    assert ".env" not in paths
    assert "node_modules/pkg.js" not in paths
    assert "dist/bundle.js" not in paths
    assert "__pycache__/app.pyc" not in paths

    (root / "src" / "app.py").write_text("print('two')\n", encoding="utf-8")
    (root / ".a0proj" / "secrets.env").write_text("SECRET=two\n", encoding="utf-8")
    service.snapshot(trigger="manual")
    service.travel(commit_hash=first.hash)

    assert (root / "src" / "app.py").read_text(encoding="utf-8") == "print('one')\n"
    assert (root / ".a0proj" / "secrets.env").read_text(encoding="utf-8") == "SECRET=two\n"


def test_symlink_entries_are_snapshotted_and_deleted_without_following_targets(workspace, tmp_path: Path):
    root, service = workspace
    outside = tmp_path / "outside.txt"
    outside.write_text("outside\n", encoding="utf-8")
    os.symlink(outside, root / "outside-link")

    first = service.snapshot(trigger="manual")
    assert "outside-link" in tracked_paths(service, first.hash)
    assert service._git("ls-tree", "HEAD", "outside-link").stdout.startswith("120000")

    (root / "outside-link").unlink()
    second = service.snapshot(trigger="manual")
    assert outside.exists()

    service.travel(commit_hash=first.hash)
    assert (root / "outside-link").is_symlink()
    assert outside.exists()

    service.travel(commit_hash=second.hash)
    assert not (root / "outside-link").exists()
    assert outside.exists()


def test_pagination_large_diff_and_invalid_inputs(workspace, monkeypatch: pytest.MonkeyPatch):
    root, service = workspace
    (root / "file.txt").write_text("0\n", encoding="utf-8")
    hashes = [service.snapshot(trigger="manual").hash]
    for index in range(1, 4):
        (root / "file.txt").write_text(("x\n" * index), encoding="utf-8")
        hashes.append(service.snapshot(trigger="manual").hash)

    page = service.history_list(limit=2)
    assert len(page["commits"]) == 2
    assert page["has_more"] is True
    page2 = service.history_list(limit=2, offset=2)
    assert page2["commits"][0]["hash"] == hashes[1]

    monkeypatch.setattr(tt, "MAX_RENDERED_PATCH_BYTES", 30)
    diff = service.history_diff(commit_hash=hashes[-1], path="file.txt", mode="commit")
    assert diff["too_large"] is True
    assert len(diff["patch"].encode("utf-8")) <= 30

    with pytest.raises(TimeTravelError):
        service.history_diff(commit_hash="not-a-commit", path="file.txt", mode="commit")
    with pytest.raises(TimeTravelError):
        service.history_diff(commit_hash=hashes[-1], path="../file.txt", mode="commit")


def test_debounced_snapshots_coalesce_to_one_commit(workspace):
    root, service = workspace
    tt.clear_debounced_snapshots()
    try:
        (root / "file.txt").write_text("one\n", encoding="utf-8")
        tt.schedule_debounced_snapshot(
            service.workspace,
            trigger="watchdog",
            metadata={"source": "watchdog", "changed_path_hints": ["/a0/usr/file.txt"]},
            delay=60,
        )
        assert service.current_hash() == ""

        (root / "file.txt").write_text("two\n", encoding="utf-8")
        tt.schedule_debounced_snapshot(
            service.workspace,
            trigger="text_editor_write",
            metadata={"source": "text_editor", "changed_path_hints": ["/a0/usr/other.txt"]},
            delay=60,
        )
        tt.flush_debounced_snapshots()

        current = service.current_hash()
        assert current
        commits = service.history_list(limit=10)["commits"]
        assert len(commits) == 1
        assert commits[0]["hash"] == current
        assert commits[0]["metadata"]["trigger"] == "text_editor_write"
        assert commits[0]["metadata"]["source"] == "text_editor"
        assert commits[0]["metadata"]["changed_path_hints"] == [
            "/a0/usr/file.txt",
            "/a0/usr/other.txt",
        ]
        assert "two" in service.history_diff(commit_hash=current, path="file.txt", mode="commit")["patch"]
    finally:
        tt.clear_debounced_snapshots()


def test_workspace_resolution_prefers_project_and_rejects_external_paths(monkeypatch: pytest.MonkeyPatch, workspace):
    root, _service = workspace
    projects_mod = ModuleType("helpers.projects")
    projects_mod.get_context_project_name = lambda _context: "demo"
    projects_mod.get_project_folder = lambda _name: str(root)
    settings_mod = ModuleType("helpers.settings")
    settings_mod.get_settings = lambda: {"workdir_path": "/tmp/not-a0"}

    import helpers

    monkeypatch.setitem(sys.modules, "helpers.projects", projects_mod)
    monkeypatch.setitem(sys.modules, "helpers.settings", settings_mod)
    monkeypatch.setattr(helpers, "projects", projects_mod, raising=False)
    monkeypatch.setattr(helpers, "settings", settings_mod, raising=False)

    resolved = resolve_workspace("ctx", context_loader=lambda _ctxid: SimpleNamespace(id="ctx"))
    assert resolved.project_name == "demo"
    assert resolved.display_path.startswith("/a0/usr/time-travel-tests/")

    projects_mod.get_context_project_name = lambda _context: ""
    with pytest.raises(WorkspaceRejectedError):
        resolve_workspace("ctx", context_loader=lambda _ctxid: SimpleNamespace(id="ctx"))
