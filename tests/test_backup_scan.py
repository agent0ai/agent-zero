import asyncio
import datetime
import os
import threading
from pathlib import Path
from types import SimpleNamespace

import pytest
from pathspec import PathSpec

from helpers.backup import BackupService, Localization


@pytest.fixture
def scan_service(tmp_path, monkeypatch):
    root = tmp_path / "a0"
    for relative in (
        "root.txt",
        "cache/unrelated.txt",
        "usr/settings.json",
        "usr/.secret",
        "usr/workdir/project/code.py",
        "usr/workdir/project/data.txt",
        "usr/.hidden/explicit.txt",
        "usr/.time_travel/keep.txt",
        "usr/.time_travel/objects/history.txt",
        "usr/plugins/_orchestrator/config.json",
        "usr/plugins/_orchestrator/data/state.txt",
        "usr/literal[dir]/data.txt",
        "usr2/sibling.txt",
    ):
        path = root / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(relative, encoding="utf-8")
    outside = tmp_path / "outside"
    outside.mkdir()
    (outside / "other.txt").write_text("outside", encoding="utf-8")
    (root / "usr" / "linked-directory").symlink_to(outside, target_is_directory=True)
    (root / "usr" / "linked-file.txt").symlink_to(root / "usr" / "settings.json")
    (root / "usr" / "broken-link").symlink_to(outside / "missing")

    service = BackupService.__new__(BackupService)
    service.agent_zero_root = str(root)
    service.base_paths = {str(root): str(root)}
    monkeypatch.setattr(
        Localization, "get",
        lambda: SimpleNamespace(get_tzinfo=lambda: datetime.timezone.utc),
    )
    return service


def unpruned_matches(service, metadata, max_files):
    """Reference the original walk order and matching contract without pruning."""
    lines = service._patterns_to_string(
        metadata["include_patterns"], metadata["exclude_patterns"]
    ).splitlines()
    spec = PathSpec.from_lines("gitignore", lines)
    explicit = service._get_explicit_patterns(metadata["include_patterns"])
    matches = []
    for base in service.base_paths.values():
        for root, dirs, files in os.walk(base):
            if not metadata["include_hidden"]:
                dirs[:] = [
                    name for name in dirs
                    if not name.startswith(".")
                    or service._is_explicitly_included(os.path.join(root, name), explicit)
                ]
            for name in files:
                if max_files is not None and len(matches) >= max_files:
                    return matches
                path = os.path.join(root, name)
                if (not metadata["include_hidden"] and name.startswith(".")
                        and not service._is_explicitly_included(path, explicit)):
                    continue
                if spec.match_file(path.lstrip("/")):
                    try:
                        stat = os.stat(path)
                    except OSError:
                        continue
                    matches.append({
                        "path": path,
                        "real_path": path,
                        "size": stat.st_size,
                        "modified": datetime.datetime.fromtimestamp(
                            stat.st_mtime, tz=datetime.timezone.utc,
                        ).isoformat(),
                        "type": "file",
                    })
    return matches


@pytest.mark.parametrize("include,exclude", [
    (["{root}/usr/**"], ["{root}/usr/.time_travel/**"]),
    (["{relative_root}/usr/**"], ["{relative_root}/usr/.time_travel/**"]),
    (["{root}/usr/**", "{root}/usr/workdir/**", "{root}/usr2/**"], []),
    (["{root}/usr/.hidden/explicit.txt", "{root}/usr/.secret"], []),
    (["{root}/usr/"], []),
    (["{root}/usr/*/*.txt"], []),
    (["{root}/usr/workdir/projec[t]/data.txt"], []),
    (["{root}/usr/settings.?son"], []),
    (["**/*.txt"], ["{root}/usr/.time_travel/**"]),
    (["*.json"], []),
    (["usr/**"], []),
    (["{root}/usr/**", "!{root}/usr/.time_travel/**",
      "{root}/usr/.time_travel/keep.txt"], []),
    (["{root}/usr/**"], ["{root}/usr/.time_travel/objects/*.txt"]),
    (["{root}/usr/linked-directory/**"], []),
    (["{root}/usr/missing/**"], []),
    ([], ["{root}/usr/**"]),
    ([], []),
])
@pytest.mark.parametrize("include_hidden", [True, False])
@pytest.mark.parametrize("max_files", [None, 0, 1, 4, 1000])
@pytest.mark.asyncio
async def test_scan_preserves_matches_metadata_order_and_limits(
    scan_service, include, exclude, include_hidden, max_files,
):
    root = scan_service.agent_zero_root
    substitutions = {"root": root, "relative_root": root.lstrip("/")}
    metadata = {
        "include_patterns": [pattern.format(**substitutions) for pattern in include],
        "exclude_patterns": [pattern.format(**substitutions) for pattern in exclude],
        "include_hidden": include_hidden,
    }
    expected = unpruned_matches(scan_service, metadata, max_files)

    assert await scan_service.test_patterns(metadata, max_files=max_files) == expected


@pytest.mark.asyncio
async def test_default_scan_does_not_descend_into_unrelated_or_excluded_trees(
    scan_service, monkeypatch,
):
    root = Path(scan_service.agent_zero_root)
    include, exclude = scan_service._parse_patterns(scan_service._get_default_patterns())
    metadata = {
        "include_patterns": include, "exclude_patterns": exclude, "include_hidden": True,
    }
    expected = unpruned_matches(scan_service, metadata, None)
    visited = []
    real_walk = os.walk

    def observed_walk(*args, **kwargs):
        for directory, dirs, files in real_walk(*args, **kwargs):
            visited.append(Path(directory).relative_to(root).as_posix())
            yield directory, dirs, files

    monkeypatch.setattr(os, "walk", observed_walk)
    assert await scan_service.test_patterns(metadata, max_files=None) == expected
    assert "usr/workdir/project" in visited
    for skipped in ("cache", "usr2", "usr/.time_travel", "usr/plugins/_orchestrator/data"):
        assert not any(path == skipped or path.startswith(skipped + "/") for path in visited)


@pytest.mark.asyncio
async def test_scan_keeps_event_loop_responsive(scan_service, monkeypatch):
    loop = asyncio.get_running_loop()
    callback_ran = threading.Event()
    real_walk = os.walk

    def waiting_walk(*args, **kwargs):
        loop.call_soon_threadsafe(callback_ran.set)
        assert callback_ran.wait(timeout=5), "filesystem scan blocked the event loop"
        yield from real_walk(*args, **kwargs)

    monkeypatch.setattr(os, "walk", waiting_walk)
    result = await scan_service.test_patterns({
        "include_patterns": [f"{scan_service.agent_zero_root}/usr/**"],
    })
    assert result
    assert callback_ran.is_set()


@pytest.mark.asyncio
async def test_scan_preserves_multiple_base_path_order(scan_service):
    root = scan_service.agent_zero_root
    scan_service.base_paths[str(Path(root) / "usr")] = str(Path(root) / "usr")
    metadata = {
        "include_patterns": [f"{root}/usr/**"],
        "exclude_patterns": [],
        "include_hidden": True,
    }
    assert await scan_service.test_patterns(metadata, max_files=None) == unpruned_matches(
        scan_service, metadata, None,
    )


@pytest.mark.asyncio
async def test_scan_normalizes_relative_base_paths(scan_service, monkeypatch):
    monkeypatch.chdir(scan_service.agent_zero_root)
    scan_service.base_paths = {".": "."}
    metadata = {
        "include_patterns": ["usr/**"],
        "exclude_patterns": ["usr/.time_travel/**"],
        "include_hidden": True,
    }
    expected = unpruned_matches(scan_service, metadata, None)
    assert expected
    assert await scan_service.test_patterns(metadata, max_files=None) == expected
