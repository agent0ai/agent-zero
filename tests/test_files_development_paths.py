from pathlib import Path

import pytest

from helpers import files, images, runtime, strings


@pytest.mark.parametrize("dockerized", [False, True])
@pytest.mark.parametrize(
    ("path", "relative"),
    [
        ("/a0/usr/workdir/report.txt", "usr/workdir/report.txt"),
        ("/a0/usr/workdir/a0/report.txt", "usr/workdir/a0/report.txt"),
        ("/a0/usr/a0/project/a0/report.txt", "usr/a0/project/a0/report.txt"),
        ("/a0/a0/report.txt", "a0/report.txt"),
        ("/a0/a0/", "a0/"),
        ("/a0/", ""),
    ],
)
def test_fix_dev_path_replaces_only_the_root_prefix(
    tmp_path, monkeypatch, dockerized, path, relative
):
    monkeypatch.setattr(files, "_base_dir", str(tmp_path))
    monkeypatch.setattr(runtime, "args", {"dockerized": dockerized})

    expected = path if dockerized else files.get_abs_path(relative)

    assert files.fix_dev_path(path) == expected
    assert files.get_abs_path_development(path) == expected


@pytest.mark.parametrize("dockerized", [False, True])
@pytest.mark.parametrize(
    "path",
    [
        "/a0",
        "/a0-other/usr/a0/report.txt",
        "/tmp/a0/report.txt",
        "usr/workdir/a0/report.txt",
        "a0/report.txt",
    ],
)
def test_fix_dev_path_preserves_paths_without_the_root_prefix(
    tmp_path, monkeypatch, dockerized, path
):
    monkeypatch.setattr(files, "_base_dir", str(tmp_path))
    monkeypatch.setattr(runtime, "args", {"dockerized": dockerized})

    assert files.fix_dev_path(path) == files.get_abs_path(path)


@pytest.mark.parametrize(
    "relative", ["usr/workdir/a0/report.txt", "usr/a0/资料/a0/my file.txt"]
)
def test_dockerized_path_round_trip_preserves_nested_a0(
    tmp_path, monkeypatch, relative
):
    monkeypatch.setattr(files, "_base_dir", str(tmp_path))
    monkeypatch.setattr(runtime, "args", {"dockerized": False})
    local_path = str(tmp_path / relative)

    assert files.fix_dev_path(files.normalize_a0_path(local_path)) == local_path


def test_file_include_reads_the_nested_directory_not_the_colliding_path(
    tmp_path, monkeypatch
):
    monkeypatch.setattr(files, "_base_dir", str(tmp_path))
    monkeypatch.setattr(runtime, "args", {"dockerized": False})
    correct_path = tmp_path / "usr/workdir/a0/report.txt"
    correct_path.parent.mkdir(parents=True)
    correct_path.write_text("correct report", encoding="utf-8")
    (tmp_path / "usr/workdirreport.txt").write_text("wrong report", encoding="utf-8")

    assert (
        strings.replace_file_includes(
            "Before §§include(/a0/usr/workdir/a0/report.txt) after"
        )
        == "Before correct report after"
    )


def test_image_reference_resolves_the_nested_directory(tmp_path, monkeypatch):
    monkeypatch.setattr(files, "_base_dir", str(tmp_path))
    monkeypatch.setattr(runtime, "args", {"dockerized": False})
    relative = f"usr/workdir/a0/{tmp_path.name}.png"
    image_path = tmp_path / relative
    image_path.parent.mkdir(parents=True)
    image_path.write_bytes(b"image reference fixture")

    assert images.resolve_ref(f"/a0/{relative}") == Path(image_path)
