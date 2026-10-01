import subprocess
import sys
from io import BytesIO
from pathlib import Path
from unittest.mock import Mock

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


def test_update_repo_rebases_local_commits_on_the_configured_upstream(tmp_path: Path):
    _, source, installed = make_plugin_repos(tmp_path)
    run_git(installed, "branch", "-m", "local")
    run_git(installed, "config", "pull.ff", "only")
    run_git(installed, "config", "rebase.updateRefs", "true")
    (installed / "local.py").write_text("local change\n")
    run_git(installed, "add", "local.py")
    run_git(installed, "commit", "-m", "local commit")
    original_head = run_git(installed, "rev-parse", "HEAD")
    run_git(installed, "branch", "keep-local")
    (installed / "README.md").write_text("uncommitted edit\n")
    (installed / ".toggle-1").write_text("")
    push_source_change(source, "plugin.py", "value = 'upstream'\n")

    git_helpers.update_repo(str(installed))

    assert run_git(installed, "branch", "--show-current") == "local"
    assert run_git(installed, "rev-parse", "HEAD^") == run_git(source, "rev-parse", "HEAD")
    assert run_git(installed, "rev-parse", "HEAD") != original_head
    assert run_git(installed, "rev-parse", "keep-local") == original_head
    assert (installed / "local.py").read_text() == "local change\n"
    assert (installed / "plugin.py").read_text() == "value = 'upstream'\n"
    assert (installed / "README.md").read_text() == "uncommitted edit\n"
    assert (installed / ".toggle-1").exists()
    assert run_git(installed, "stash", "list") == ""


@pytest.mark.parametrize("dirty", [False, True])
def test_rebase_conflict_restores_commits_edits_and_existing_stashes(tmp_path: Path, dirty: bool):
    _, source, installed = make_plugin_repos(tmp_path)
    (installed / "README.md").write_text("previous stash\n")
    run_git(installed, "stash", "push", "-m", "user stash")
    previous_stash = run_git(installed, "rev-parse", "refs/stash")
    (installed / "plugin.py").write_text("value = 'local commit'\n")
    run_git(installed, "add", "plugin.py")
    run_git(installed, "commit", "-m", "local commit")
    original_head = run_git(installed, "rev-parse", "HEAD")
    if dirty:
        (installed / "README.md").write_text("staged edit\n")
        run_git(installed, "add", "README.md")
        (installed / "README.md").write_text("staged and unstaged edit\n")
    (installed / ".toggle-1").write_text("enabled\n")
    original_status = git_status(installed)
    original_index = run_git(installed, "diff", "--cached")
    original_edits = run_git(installed, "diff")
    push_source_change(source, "plugin.py", "value = 'upstream'\n")

    with pytest.raises(git_helpers.DirtyTreeConflictError) as error:
        git_helpers.update_repo(str(installed))

    assert error.value.conflicting_files == ["plugin.py"]
    assert run_git(installed, "branch", "--show-current") == "main"
    assert run_git(installed, "rev-parse", "HEAD") == original_head
    assert git_status(installed) == original_status
    assert run_git(installed, "diff", "--cached") == original_index
    assert run_git(installed, "diff") == original_edits
    assert run_git(installed, "rev-parse", "refs/stash") == previous_stash
    assert not (installed / ".git/rebase-merge").exists()
    assert not (installed / ".git/rebase-apply").exists()


def test_update_repo_leaves_an_existing_rebase_untouched(tmp_path: Path):
    _, source, installed = make_plugin_repos(tmp_path)
    (installed / "plugin.py").write_text("local\n")
    run_git(installed, "add", "plugin.py")
    run_git(installed, "commit", "-m", "local commit")
    push_source_change(source, "plugin.py", "upstream\n")
    run_git(installed, "fetch")
    result = subprocess.run(
        ["git", "-C", str(installed), "rebase", "origin/main"], capture_output=True,
    )
    assert result.returncode != 0
    before = git_status(installed)

    with pytest.raises(ValueError):
        git_helpers.update_repo(str(installed))

    assert git_status(installed) == before
    assert (installed / ".git/rebase-merge").is_dir()


@pytest.mark.parametrize("extension", ["png", "jpg"])
def test_thumbnail_download_preserves_repo_image_and_allows_upstream_updates(
    tmp_path: Path, monkeypatch, extension: str
):
    _, source, installed = make_plugin_repos(tmp_path)
    (source / "webui").mkdir()
    thumbnail_path = f"webui/thumbnail.{extension}"
    push_source_change(source, thumbnail_path, "\x00original thumbnail\n")
    git_helpers.update_repo(str(installed))
    download = Mock(return_value=BytesIO(b"downloaded thumbnail"))
    monkeypatch.setattr(install.urllib.request, "urlopen", download)

    install._download_thumbnail("https://example.com/thumbnail.png", str(installed))

    download.assert_not_called()
    assert (installed / thumbnail_path).read_bytes() == b"\x00original thumbnail\n"
    assert git_status(installed) == ""

    push_source_change(source, thumbnail_path, "\x00upstream thumbnail\n")
    git_helpers.update_repo(str(installed))

    assert (installed / thumbnail_path).read_bytes() == b"\x00upstream thumbnail\n"
    assert git_status(installed) == ""


def test_thumbnail_download_fills_missing_image(tmp_path: Path, monkeypatch):
    download = Mock(return_value=BytesIO(b"fallback thumbnail"))
    monkeypatch.setattr(install.urllib.request, "urlopen", download)

    install._download_thumbnail("https://example.com/thumbnail.png", str(tmp_path))

    download.assert_called_once()
    assert (tmp_path / "webui/thumbnail.png").read_bytes() == b"fallback thumbnail"


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
