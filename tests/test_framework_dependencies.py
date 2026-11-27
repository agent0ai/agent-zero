import importlib.metadata
import subprocess
import sys

import pytest

from extensions.python.startup_migration import _05_framework_dependencies as migration


@pytest.fixture
def installed(monkeypatch):
    monkeypatch.setattr(sys, "platform", "linux")
    requirements = migration._requirements()
    versions = {req.name: next(spec.version for spec in req.specifier
                               if spec.operator in ("==", ">=")) for req in requirements}

    def version(name):
        if name not in versions:
            raise importlib.metadata.PackageNotFoundError(name)
        return versions[name]

    monkeypatch.setattr(migration.runtime, "is_dockerized", lambda: True)
    monkeypatch.setattr(migration.process, "restart_process", lambda: pytest.fail("Unexpected restart"))
    monkeypatch.setattr(migration.importlib.metadata, "version", version)
    monkeypatch.setattr(migration.shutil, "which", lambda _name: "/usr/bin/uv")
    return versions


@pytest.mark.parametrize("package,old_version", [
    ("litellm", "1.88.1"), ("openai", "2.41.1"),
    ("aiohttp", "3.14.0"), ("filelock", None), ("onnxruntime", "1.23.2"),
    ("faiss-cpu", "1.11.0"), ("numpy", "2.0.0"),
])
def test_self_update_installs_requirements_and_restarts_once(monkeypatch, installed, package, old_version):
    target = installed.copy()
    installed.pop(package)
    if old_version:
        installed[package] = old_version
    calls = []
    restarts = []

    def install(command, **kwargs):
        calls.append((command, kwargs))
        installed.update(target)

    monkeypatch.setattr(migration.subprocess, "check_call", install)
    monkeypatch.setattr(migration.process, "restart_process", lambda: restarts.append(True))
    extension = migration.FrameworkDependencies(None)
    extension.execute()
    extension.execute()
    assert restarts == [True]
    assert len(calls) == 1
    command, kwargs = calls[0]
    assert command[:6] == ["/usr/bin/uv", "pip", "install", "--no-cache", "--python", sys.executable]
    assert command[6:8] == ["-c", str(migration._REQUIREMENTS_FILE.parent / "docker/litellm-constraints.txt")]
    assert set(command[8:]) == {str(req) for req in migration._requirements()}
    assert kwargs == {"timeout": 600}


def test_current_image_skips_installer_and_restart(monkeypatch, installed):
    installed["filelock"] = "4.2.12"
    monkeypatch.setattr(migration.shutil, "which", lambda _name: pytest.fail("Installer lookup"))
    migration.FrameworkDependencies(None).execute()


@pytest.mark.parametrize("error", [
    subprocess.CalledProcessError(1, "uv"), subprocess.TimeoutExpired("uv", 60),
])
def test_failed_install_stops_startup_without_restart(monkeypatch, installed, error):
    installed.pop("litellm")

    def fail(*args, **kwargs):
        raise error

    monkeypatch.setattr(migration.subprocess, "check_call", fail)
    with pytest.raises(type(error)):
        migration.FrameworkDependencies(None).execute()


def test_install_must_satisfy_requirements_before_restart(monkeypatch, installed):
    installed["openai"] = "2.41.1"
    monkeypatch.setattr(migration.subprocess, "check_call", lambda *args, **kwargs: None)
    with pytest.raises(RuntimeError, match="still unavailable"):
        migration.FrameworkDependencies(None).execute()


def test_non_docker_environment_skips_dependency_migration(monkeypatch):
    monkeypatch.setattr(migration.runtime, "is_dockerized", lambda: False)
    monkeypatch.setattr(migration, "_requirements", lambda: pytest.fail("Requirements check"))
    migration.FrameworkDependencies(None).execute()
