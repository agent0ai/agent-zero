import ast
from pathlib import Path

import pytest


PROJECT_ROOT = Path(__file__).resolve().parents[1]
REQUIREMENTS = PROJECT_ROOT / "requirements.txt"
DOCKERFILE = PROJECT_ROOT / "Dockerfile"
RUNTIME = PROJECT_ROOT / "docker/run/fs"


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="ignore")


def test_outer_image_uses_tuxee_and_official_trixie_runtimes() -> None:
    dockerfile = _read(DOCKERFILE)

    assert "FROM agent0ai/tuxee@sha256:" in dockerfile
    assert "FROM python:3.12-slim-trixie AS python-runtime" in dockerfile
    assert "from=python-runtime,source=/usr/local" in dockerfile
    assert "FROM node:22-trixie-slim AS node-runtime" in dockerfile
    assert "strip --strip-unneeded -o /usr/local/bin/node /node" in dockerfile
    assert "cp -a /node/lib/node_modules/npm /usr/local/lib/node_modules/" in dockerfile
    assert "UV_SYSTEM_PYTHON=1" in dockerfile
    assert "PIP_ROOT_USER_ACTION=ignore" in dockerfile
    assert "PYTHONDONTWRITEBYTECODE=1" in dockerfile
    assert "nodejs npm" not in dockerfile
    assert "kalilinux" not in dockerfile.lower()


def test_outer_runtime_uses_onnx_without_training_dependencies() -> None:
    requirements = _read(REQUIREMENTS)
    dockerfile = _read(DOCKERFILE)
    for package in ("sentence-transformers", "torch", "torchvision", "scipy", "scikit-learn", "transformers"):
        assert not any(line.startswith(package + "=") for line in requirements.splitlines())
    assert "onnxruntime==1.25.1" in requirements
    assert dockerfile.index("-m helpers.local_embeddings") < dockerfile.index("preload.py")


@pytest.mark.parametrize("entrypoint", ["prepare.py", "preload.py", "run_ui.py", "run_tunnel.py"])
def test_entrypoints_use_installed_dependencies_without_bootstrap(entrypoint: str) -> None:
    tree = ast.parse(_read(PROJECT_ROOT / entrypoint))
    imports = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imports.update(alias.name.split(".")[0] for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            imports.add(node.module.split(".")[0])
    assert imports.isdisjoint({"requirements", "depfix"})
    assert not (PROJECT_ROOT / "requirements.py").exists()


def test_tracked_outer_docker_setup_has_no_virtualenv_or_legacy_python_runtime() -> None:
    combined = "\n".join(_read(path) for path in [DOCKERFILE, *RUNTIME.rglob("*.sh")])

    for forbidden in (
        "/opt/venv",
        "/opt/venv-a0",
        "/opt/pyenv",
        "setup_venv.sh",
        "bin/activate",
        "kalilinux/kali-rolling",
    ):
        assert forbidden not in combined


def test_runtime_dependencies_install_once_into_global_python() -> None:
    dockerfile = _read(DOCKERFILE)
    assert dockerfile.count("uv pip install --no-cache --python /usr/local/bin/python -r /requirements.txt") == 1
    assert "/usr/local/bin/python -m pip install --no-cache-dir --no-compile" in dockerfile
    assert "pipx==1.16.7" in dockerfile
    assert "/usr/local/bin/python preload.py --dockerized=true" in dockerfile


def test_tuxee_starts_agent_zero_through_the_global_python_bootstrap() -> None:
    assert "/exe/run_A0.sh" in _read(RUNTIME / "opt/agent-zero/init/agent-zero.sh")
    assert "exec /usr/local/bin/python /exe/self_update_manager.py docker-run-ui" in _read(RUNTIME / "exe/run_A0.sh")
    assert 'exec /usr/local/bin/python "$SCRIPT_DIR/self_update_manager.py"' in _read(RUNTIME / "exe/trigger_self_update.sh")
    assert not (RUNTIME / "etc/supervisor").exists()


def test_proot_replaces_large_engine_sidecars():
    dockerfile = _read(DOCKERFILE)
    assert '/tools/usr/local/bin/a0-proot /usr/local/bin/' in dockerfile
    assert 'runsc' not in dockerfile and 'gvisor' not in dockerfile


def test_shared_numpy_and_filelock_bounds_remain_declared():
    requirements = _read(REQUIREMENTS)
    assert "numpy>=1.26.4,<2" in requirements
    assert "filelock>=4.2.1" in requirements


def test_build_precompiles_with_source_validated_hashes():
    dockerfile = _read(DOCKERFILE)
    assert "python -X no_debug_ranges -m compileall -q -f --invalidation-mode checked-hash" in dockerfile
    assert r"-x '(^|/)(tests?/|test_[^/]*\.py$|[^/]*_test\.py$)' /usr/local/lib/python3.12/site-packages /a0" in dockerfile
