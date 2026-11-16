from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / "docker" / "base"
RUN = ROOT / "docker" / "run"


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def test_base_image_uses_builtin_utf8_locale() -> None:
    dockerfile = _read(BASE / "Dockerfile")

    assert "ENV LANG=C.UTF-8" in dockerfile
    assert "ENV LC_ALL=C.UTF-8" in dockerfile
    assert "en_US.UTF-8" not in dockerfile
    assert "install -y locales" not in dockerfile
    assert "/etc/locale.gen" not in dockerfile


def test_every_build_time_apt_layer_removes_its_own_lists() -> None:
    apt_layers = (
        BASE / "Dockerfile",
        BASE / "fs/ins/install_base_packages.sh",
        RUN / "fs/ins/install_additional.sh",
    )

    for path in apt_layers:
        contents = _read(path)
        assert "/var/lib/apt/lists/*" in contents, path


def test_base_image_keeps_runtime_libraries_without_build_or_unused_cli_tools() -> None:
    install_script = _read(BASE / "fs" / "ins" / "install_base_packages.sh")

    for package in ("build-essential", "cmake", "wget", "unzip"):
        assert package not in install_script
    for package in ("libstdc++6", "libatomic1", "7zip"):
        assert package in install_script
    assert "libasound2" not in _read(BASE / "fs/ins/install_base_packages.sh")
    assert "libsndfile1" not in _read(RUN / "fs/ins/install_additional.sh")
