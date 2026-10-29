import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from helpers import files, runtime
from plugins._time_travel.helpers import time_travel

NESTED_BASE = "/a0/usr/projects/nested"


def test_fix_dev_path_keeps_paths_inside_a_nested_checkout(monkeypatch):
    monkeypatch.setattr(files, "_base_dir", NESTED_BASE)
    monkeypatch.setattr(runtime, "is_development", lambda: True)

    inside = f"{NESTED_BASE}/usr/workdir"
    assert files.fix_dev_path(inside) == inside
    assert files.fix_dev_path("/a0/usr/workdir") == inside


def test_fix_dev_path_leaves_paths_alone_outside_development(monkeypatch):
    monkeypatch.setattr(files, "_base_dir", NESTED_BASE)
    monkeypatch.setattr(runtime, "is_development", lambda: False)

    assert files.fix_dev_path("/a0/usr/workdir") == "/a0/usr/workdir"


def test_canonical_workspace_display_path_normalizes_root():
    assert time_travel.canonical_workspace_display_path("/a0") == "/a0"
    assert (
        time_travel.canonical_workspace_display_path("/a0/usr/workdir")
        == "/a0/usr/workdir"
    )


def test_canonical_workspace_display_path_uses_logical_paths_in_nested_checkout(monkeypatch):
    monkeypatch.setattr(files, "_base_dir", NESTED_BASE)

    assert time_travel.canonical_workspace_display_path("/a0") == "/a0"
    assert (
        time_travel.canonical_workspace_display_path(f"{NESTED_BASE}/usr/workdir")
        == "/a0/usr/workdir"
    )
    assert time_travel.workspace_id_for(f"{NESTED_BASE}/usr/workdir") == time_travel.workspace_id_for(
        "/a0/usr/workdir"
    )


def test_canonical_workspace_display_path_uses_posix_separators(monkeypatch):
    # Windows relpath yields backslash components, so normalize_a0_path can return /a0/usr\workdir
    monkeypatch.setattr(files, "normalize_a0_path", lambda path: "/a0/usr\\workdir")

    assert time_travel.canonical_workspace_display_path("/a0") == "/a0/usr/workdir"


def test_real_path_for_display_keeps_paths_inside_a_nested_checkout(monkeypatch):
    monkeypatch.setattr(files, "_base_dir", NESTED_BASE)

    assert time_travel.real_path_for_display(f"{NESTED_BASE}/usr/workdir") == Path(
        NESTED_BASE, "usr/workdir"
    )
    assert time_travel.real_path_for_display("/a0/usr/workdir") == Path(
        NESTED_BASE, "usr/workdir"
    )
