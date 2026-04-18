import subprocess
import sys
from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from helpers import git as git_helpers
from plugins._plugin_installer.helpers import install


def run_git(repo: Path, *args: str) -> str:
    return subprocess.run(
        ["git", "-C", str(repo), *args],
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()


def git_status(repo: Path) -> str:
    return subprocess.run(
        ["git", "-C", str(repo), "status", "--porcelain"],
        check=True,
        capture_output=True,
        text=True,
    ).stdout.rstrip()


def make_plugin_repos(tmp_path: Path) -> tuple[Path, Path, Path]:
    remote = tmp_path / "remote.git"
    source = tmp_path / "source"
    installed = tmp_path / "installed"
    subprocess.run(["git", "init", "--bare", str(remote)], check=True, capture_output=True)
    subprocess.run(["git", "init", str(source)], check=True, capture_output=True)
    run_git(source, "config", "user.email", "tests@example.com")
    run_git(source, "config", "user.name", "Tests")
    (source / "plugin.py").write_text("value = 'old'\n", encoding="utf-8")
    (source / "README.md").write_text("old\n", encoding="utf-8")
    run_git(source, "add", ".")
    run_git(source, "commit", "-m", "initial")
    run_git(source, "branch", "-M", "main")
    run_git(source, "remote", "add", "origin", str(remote))
    run_git(source, "push", "-u", "origin", "main")
    subprocess.run(
        ["git", "-C", str(remote), "symbolic-ref", "HEAD", "refs/heads/main"],
        check=True,
        capture_output=True,
    )
    subprocess.run(["git", "clone", str(remote), str(installed)], check=True, capture_output=True)
    run_git(installed, "config", "user.email", "tests@example.com")
    run_git(installed, "config", "user.name", "Tests")
    return remote, source, installed


def push_source_change(source: Path, path: str, content: str) -> None:
    (source / path).write_text(content, encoding="utf-8")
    run_git(source, "add", path)
    run_git(source, "commit", "-m", f"update {path}")
    run_git(source, "push")


def test_update_repo_preserves_non_conflicting_tracked_and_untracked_files(tmp_path: Path):
    _, source, installed = make_plugin_repos(tmp_path)
    original_head = run_git(installed, "rev-parse", "HEAD")
    (installed / "README.md").write_text("local edit\n", encoding="utf-8")
    (installed / ".toggle-1").write_text("enabled\n", encoding="utf-8")
    push_source_change(source, "plugin.py", "value = 'upstream'\n")

    git_helpers.update_repo(str(installed))

    assert run_git(installed, "rev-parse", "HEAD") != original_head
    assert (installed / "plugin.py").read_text(encoding="utf-8") == "value = 'upstream'\n"
    assert (installed / "README.md").read_text(encoding="utf-8") == "local edit\n"
    assert (installed / ".toggle-1").read_text(encoding="utf-8") == "enabled\n"
    assert run_git(installed, "stash", "list") == ""


def test_update_repo_drops_local_edit_that_matches_the_new_upstream_version(tmp_path: Path):
    _, source, installed = make_plugin_repos(tmp_path)
    (installed / "plugin.py").write_text("value = 'upstream'\n", encoding="utf-8")
    push_source_change(source, "plugin.py", "value = 'upstream'\n")

    git_helpers.update_repo(str(installed))

    assert (installed / "plugin.py").read_text(encoding="utf-8") == "value = 'upstream'\n"
    assert git_status(installed) == ""
    assert run_git(installed, "stash", "list") == ""


def test_update_repo_restores_original_plugin_and_local_edit_after_conflict(tmp_path: Path):
    _, source, installed = make_plugin_repos(tmp_path)
    original_head = run_git(installed, "rev-parse", "HEAD")
    (installed / "plugin.py").write_text("value = 'local'\n", encoding="utf-8")
    push_source_change(source, "plugin.py", "value = 'upstream'\n")

    with pytest.raises(git_helpers.DirtyTreeConflictError) as exc_info:
        git_helpers.update_repo(str(installed))

    assert exc_info.value.conflicting_files == ["plugin.py"]
    assert run_git(installed, "rev-parse", "HEAD") == original_head
    assert (installed / "plugin.py").read_text(encoding="utf-8") == "value = 'local'\n"
    assert git_status(installed) == " M plugin.py"
    assert run_git(installed, "stash", "list") == ""


def test_plugin_hub_renders_dirty_update_errors_inline():
    store = (PROJECT_ROOT / "plugins/_plugin_installer/webui/pluginInstallStore.js").read_text(encoding="utf-8")
    detail = (PROJECT_ROOT / "plugins/_plugin_installer/webui/install-detail.html").read_text(encoding="utf-8")

    assert "detailError" in store
    assert "error_kind" in store
    assert "pi-detail-error" in detail
    assert "conflicting_files" in detail


def test_plugin_update_returns_structured_dirty_tree_error(monkeypatch, tmp_path: Path):
    plugin_dir = tmp_path / "plugin"
    plugin_dir.mkdir()
    monkeypatch.setattr(install.plugins, "find_plugin_dir", lambda _name: str(plugin_dir))
    monkeypatch.setattr(install.files, "get_abs_path", lambda *_parts: str(tmp_path))
    monkeypatch.setattr(install.files, "is_in_dir", lambda *_paths: True)
    monkeypatch.setattr(install, "run_pre_update_hook", lambda _name: None)

    def raise_conflict(_path: str):
        raise git_helpers.DirtyTreeConflictError(["plugin.py"])

    monkeypatch.setattr(install.git, "update_repo", raise_conflict)

    assert install.update_from_git("demo") == {
        "ok": False,
        "success": False,
        "error": "Local changes conflict with the update. Your plugin was restored without applying the update.",
        "error_kind": "dirty_tree_conflict",
        "plugin_name": "demo",
        "conflicting_files": ["plugin.py"],
    }
