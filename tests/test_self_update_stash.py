import importlib.util
import subprocess
from pathlib import Path


_MODULE_PATH = Path(__file__).parents[1] / "docker/run/fs/exe/self_update_manager.py"
_SPEC = importlib.util.spec_from_file_location("self_update_manager", _MODULE_PATH)
assert _SPEC and _SPEC.loader
_MODULE = importlib.util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(_MODULE)
get_top_stash_commit = _MODULE.get_top_stash_commit
get_top_stash_ref = _MODULE.get_top_stash_ref


def git(repo: Path, *args: str) -> str:
    return subprocess.check_output(["git", *args], cwd=repo, text=True).strip()


def test_new_stash_is_detected_when_stash_list_is_nonempty(tmp_path: Path) -> None:
    git(tmp_path, "init", "-q")
    git(tmp_path, "config", "user.email", "test@example.invalid")
    git(tmp_path, "config", "user.name", "Test")
    (tmp_path / "tracked.txt").write_text("base\n")
    git(tmp_path, "add", "tracked.txt")
    git(tmp_path, "commit", "-qm", "initial")

    (tmp_path / "tracked.txt").write_text("existing\n")
    git(tmp_path, "stash", "push", "-qm", "existing")
    previous_commit = get_top_stash_commit(tmp_path)

    (tmp_path / "tracked.txt").write_text("rollback\n")
    git(tmp_path, "stash", "push", "-qm", "rollback")

    assert get_top_stash_commit(tmp_path) != previous_commit
    assert get_top_stash_ref(tmp_path) == "stash@{0}"


def test_stash_ref_remains_usable_for_lifecycle_operations(tmp_path: Path) -> None:
    git(tmp_path, "init", "-q")
    git(tmp_path, "config", "user.email", "test@example.invalid")
    git(tmp_path, "config", "user.name", "Test")
    (tmp_path / "tracked.txt").write_text("base\n")
    git(tmp_path, "add", "tracked.txt")
    git(tmp_path, "commit", "-qm", "initial")

    (tmp_path / "tracked.txt").write_text("rollback\n")
    git(tmp_path, "stash", "push", "-qm", "rollback")
    ref = get_top_stash_ref(tmp_path)

    git(tmp_path, "stash", "apply", ref)
    assert (tmp_path / "tracked.txt").read_text() == "rollback\n"
    git(tmp_path, "reset", "--hard", "-q")
    git(tmp_path, "stash", "drop", ref)
