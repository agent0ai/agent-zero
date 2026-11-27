from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DOCKERFILE = (ROOT / "Dockerfile").read_text()


def test_image_uses_builtin_utf8_locale() -> None:
    assert "LANG=C.UTF-8 LC_ALL=C.UTF-8" in DOCKERFILE
    assert "en_US.UTF-8" not in DOCKERFILE
    assert "install -y locales" not in DOCKERFILE
    assert "/etc/locale.gen" not in DOCKERFILE


def test_every_build_time_apt_layer_removes_its_own_lists() -> None:
    sandbox_recipe = (ROOT / "docker/sandbox/install.sh").read_text()
    transactions = [run for run in DOCKERFILE.split("\nRUN ") if "apt-get update" in run]
    assert transactions
    for contents in [*transactions, sandbox_recipe]:
        assert "/var/lib/apt/lists/*" in contents


def test_runtime_keeps_shared_libraries_without_build_tools_or_systemd() -> None:
    runtime = DOCKERFILE.rsplit("\nFROM ", 1)[1]
    assert "systemd-standalone-sysusers" in runtime
    for package in ("supervisor", "systemd", "build-essential", "cmake", "wget", "unzip", "libasound2", "libsndfile1"):
        assert package not in runtime.split()
    for package in ("libstdc++6", "libatomic1", "libtalloc2", "libseccomp2"):
        assert package in runtime.split()
