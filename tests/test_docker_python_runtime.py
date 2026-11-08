import runpy
import sys
from pathlib import Path
from types import SimpleNamespace


PROJECT_ROOT = Path(__file__).resolve().parents[1]
REQUIREMENTS = PROJECT_ROOT / "requirements.txt"
BASE_DOCKERFILE = PROJECT_ROOT / "docker" / "base" / "Dockerfile"
INSTALL_PYTHON = (
    PROJECT_ROOT / "docker" / "base" / "fs" / "ins" / "install_python.sh"
)
INSTALL_PACKAGES3 = (
    PROJECT_ROOT / "docker" / "base" / "fs" / "ins" / "install_base_packages3.sh"
)
SETUP_VENV = PROJECT_ROOT / "docker" / "run" / "fs" / "ins" / "setup_venv.sh"
SUPERVISOR_CONFIG = (
    PROJECT_ROOT
    / "docker"
    / "run"
    / "fs"
    / "etc"
    / "supervisor"
    / "conf.d"
    / "supervisord.conf"
)
TRIGGER_SELF_UPDATE = (
    PROJECT_ROOT / "docker" / "run" / "fs" / "exe" / "trigger_self_update.sh"
)


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="ignore")


def test_base_image_uses_official_python_trixie_image() -> None:
    dockerfile = _read(BASE_DOCKERFILE)

    assert dockerfile.count("FROM ") == 3
    assert "FROM debian:trixie-slim AS gvisor-package" in dockerfile
    assert "FROM python:3.12-slim-trixie AS runtime" in dockerfile
    assert "ENV UV_SYSTEM_PYTHON=1" in dockerfile
    assert "PIP_ROOT_USER_ACTION=ignore" in dockerfile
    assert "kalilinux" not in dockerfile.lower()


def test_node_and_bundled_npm_come_from_official_node_stage() -> None:
    dockerfile = _read(BASE_DOCKERFILE)
    install_script = _read(INSTALL_PACKAGES3)

    assert "FROM node:22-trixie-slim AS node-runtime" in dockerfile
    assert "COPY --from=node-runtime /usr/local/bin/node" in dockerfile
    assert "COPY --from=node-runtime /usr/local/lib/node_modules" in dockerfile
    assert "node --version" in install_script
    assert "npm --version" in install_script
    assert "apt-get install" not in install_script
    assert "nodejs npm" not in install_script


def test_docker_installs_into_global_python_without_virtualenv() -> None:
    install_script = _read(INSTALL_PYTHON)
    assert not SETUP_VENV.exists()
    assert "python -m pip install" in install_script
    assert "python3-venv" not in install_script
    assert " -m venv " not in install_script
    assert "bin/activate" not in install_script


def test_torch_pruning_targets_only_development_artifacts() -> None:
    install_script = _read(INSTALL_PYTHON)

    assert "rm -rf" in install_script
    assert "/site-packages/torch/test" in install_script
    assert "/site-packages/torch/include" in install_script
    assert "/site-packages/torch/bin" in install_script


def test_python_service_entrypoints_use_the_global_runtime() -> None:
    supervisor = _read(SUPERVISOR_CONFIG)
    trigger = _read(TRIGGER_SELF_UPDATE)

    assert (
        "command=/usr/local/bin/python /exe/supervisor_event_listener.py"
        in supervisor
    )
    assert 'exec depfix run "$SCRIPT_DIR/self_update_manager.py"' in trigger


def test_requirements_bootstrap_is_independent_of_working_directory(
    monkeypatch, tmp_path: Path
) -> None:
    captured: list[Path] = []
    monkeypatch.setitem(
        sys.modules,
        "depfix",
        SimpleNamespace(default_requirements=lambda path: captured.append(Path(path))),
    )
    monkeypatch.chdir(tmp_path)

    runpy.run_path(str(PROJECT_ROOT / "requirements.py"))

    assert captured == [PROJECT_ROOT / "requirements.txt"]


def test_tracked_outer_docker_setup_has_no_virtualenv_or_legacy_python_runtime() -> None:
    paths = [
        PROJECT_ROOT / "DockerfileLocal",
        *(
            path
            for path in (PROJECT_ROOT / "docker").rglob("*")
            if path.is_file()
        ),
    ]
    combined = "\n".join(_read(path) for path in paths)

    for forbidden in (
        "/opt/venv",
        "/opt/venv-a0",
        "/opt/pyenv",
        "python3.13",
        "setup_venv.sh",
        "bin/activate",
        "kalilinux/kali-rolling",
    ):
        assert forbidden not in combined


def test_runtime_dependencies_and_playwright_use_depfix_store() -> None:
    install_python = _read(INSTALL_PYTHON)
    requirements = _read(REQUIREMENTS)
    install_a0 = _read(PROJECT_ROOT / "docker" / "run" / "fs" / "ins" / "install_A0.sh")
    install_a02 = _read(PROJECT_ROOT / "docker" / "run" / "fs" / "ins" / "install_A02.sh")
    install_playwright = _read(
        PROJECT_ROOT / "docker" / "run" / "fs" / "ins" / "install_playwright.sh"
    )

    assert "depfix" in install_python
    assert "depfix" in requirements
    assert "depfix pip install -r /git/agent-zero/requirements.txt" in install_a0
    assert "uv pip install" not in install_a0
    assert "uv pip install" not in install_playwright
    assert "depfix run -m patchright install chromium --no-shell" in install_playwright
    assert 'bash /ins/install_A0.sh "$@"' in install_a02
    assert 'bash /ins/install_playwright.sh "$@"' in install_a02
    assert "depfix run /git/agent-zero/preload.py --dockerized=true" in install_a02
    assert "pip cache purge" not in install_a02
    assert "uv cache" not in install_a02


def test_runtime_python_launchers_enable_depfix_store_fallback() -> None:
    run_a0 = _read(PROJECT_ROOT / "docker" / "run" / "fs" / "exe" / "run_A0.sh")
    run_tunnel = _read(
        PROJECT_ROOT / "docker" / "run" / "fs" / "exe" / "run_tunnel_api.sh"
    )
    trigger_update = _read(TRIGGER_SELF_UPDATE)

    assert "exec depfix run /exe/self_update_manager.py docker-run-ui" in run_a0
    assert "exec depfix run /a0/run_tunnel.py" in run_tunnel
    assert 'exec depfix run "$SCRIPT_DIR/self_update_manager.py"' in trigger_update


def test_runsc_process_sidecars_are_shipped():
    dockerfile = _read(BASE_DOCKERFILE)
    for sidecar in ("gvisor_sentry", "gvisor-sentry-prewarmer", "gvisor-proc-umounter", "runsc-fd-parking"):
        assert f"/usr/bin/gvisor-bin/{sidecar} /usr/bin/gvisor-bin/{sidecar}" in dockerfile


def test_cpu_bootstrap_matches_application_dependency_bounds():
    script = _read(INSTALL_PYTHON)
    assert "'numpy<2'" in script
    assert "'filelock>=3.20.3,<4'" in script
    assert "--index-url https://download.pytorch.org/whl/cpu" in script
