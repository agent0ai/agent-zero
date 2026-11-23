"""Regression tests for code execution shell environment isolation.

The WebUI process runs inside the framework virtual environment
(``/opt/venv-a0``). Its ``VIRTUAL_ENV`` and ``PATH`` values leak into the
shells the code execution tool spawns, because ``/root/.bashrc`` only
*prepends* the agent runtime ``/opt/venv/bin`` and never removes
``/opt/venv-a0/bin``. Any binary that is not shadowed in ``/opt/venv/bin``
then resolves from the framework venv, so an agent ``pip install`` mutates
the framework runtime and the damage only surfaces at the next WebUI
restart.

``sanitize_execution_env`` must remove the framework venv from the spawned
shell environment, while leaving the agent runtime in place.
"""

import os

from plugins._code_execution.helpers import shell_local


FRAMEWORK_BIN = "/opt/venv-a0/bin"
AGENT_BIN = "/opt/venv/bin"


def test_sanitize_removes_framework_bin_from_path():
    env = shell_local.sanitize_execution_env({
        "PATH": f"{AGENT_BIN}:{FRAMEWORK_BIN}:/usr/local/bin:/usr/bin:/bin",
        "VIRTUAL_ENV": "/opt/venv-a0",
    })

    entries = env["PATH"].split(os.pathsep)
    assert FRAMEWORK_BIN not in entries
    assert entries == [AGENT_BIN, "/usr/local/bin", "/usr/bin", "/bin"]


def test_sanitize_removes_framework_virtualenv_vars():
    env = shell_local.sanitize_execution_env({
        "VIRTUAL_ENV": "/opt/venv-a0",
        "VIRTUAL_ENV_PROMPT": "(venv-a0)",
        "PATH": "/usr/bin:/bin",
    })

    assert "VIRTUAL_ENV" not in env
    assert "VIRTUAL_ENV_PROMPT" not in env


def test_sanitize_keeps_agent_virtualenv():
    env = shell_local.sanitize_execution_env({
        "VIRTUAL_ENV": "/opt/venv",
        "PATH": f"{AGENT_BIN}:/usr/bin:/bin",
    })

    assert env["VIRTUAL_ENV"] == "/opt/venv"
    assert env["PATH"].split(os.pathsep)[0] == AGENT_BIN


def test_sanitize_preserves_unrelated_paths():
    env = shell_local.sanitize_execution_env({
        "PATH": "/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin",
    })

    assert env["PATH"] == "/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin"


def test_sanitize_does_not_mutate_input():
    src = {
        "PATH": f"{AGENT_BIN}:{FRAMEWORK_BIN}:/usr/bin",
        "VIRTUAL_ENV": "/opt/venv-a0",
    }
    shell_local.sanitize_execution_env(src)

    assert src["PATH"] == f"{AGENT_BIN}:{FRAMEWORK_BIN}:/usr/bin"
    assert src["VIRTUAL_ENV"] == "/opt/venv-a0"


def test_sanitize_handles_trailing_slash_and_prefix_lookalikes():
    env = shell_local.sanitize_execution_env({
        "PATH": "/opt/venv-a0/:/opt/venv-a0-projects/bin:/opt/venv-a0x/bin:/usr/bin",
    })

    entries = env["PATH"].split(os.pathsep)
    assert "/opt/venv-a0/" not in entries
    assert "/opt/venv-a0" not in entries
    # A path that merely starts with the framework root string but is a
    # different directory must stay.
    assert "/opt/venv-a0-projects/bin" in entries
    assert "/opt/venv-a0x/bin" in entries


def test_sanitize_tolerates_missing_path():
    env = shell_local.sanitize_execution_env({"VIRTUAL_ENV": "/opt/venv-a0"})

    assert "PATH" not in env
    assert "VIRTUAL_ENV" not in env


def test_sanitize_composes_with_pager_helper():
    base = {
        "PATH": f"{AGENT_BIN}:{FRAMEWORK_BIN}:/usr/bin",
        "VIRTUAL_ENV": "/opt/venv-a0",
        "PAGER": "less",
    }
    env = shell_local.sanitize_execution_env(shell_local.disable_pagers_in_env(base))

    assert env["PAGER"] == "cat"
    assert env["GIT_PAGER"] == "cat"
    assert FRAMEWORK_BIN not in env["PATH"].split(os.pathsep)
    assert "VIRTUAL_ENV" not in env


def test_sanitize_strips_framework_bin_reaching_agent_shell(monkeypatch):
    """End-to-end: an agent shell started with sanitized env must not resolve
    framework-only binaries such as ``python3.12`` / ``pip3.12`` that live in
    ``/opt/venv-a0/bin`` and are not shadowed in ``/opt/venv/bin``."""

    if not os.path.isdir("/opt/venv-a0/bin"):
        # Developer machine without the container layout: still assert the
        # sanitizer behaves as a pure function.
        env = shell_local.sanitize_execution_env({
            "PATH": f"{FRAMEWORK_BIN}:/usr/bin:/bin",
            "VIRTUAL_ENV": "/opt/venv-a0",
        })
        assert FRAMEWORK_BIN not in env["PATH"].split(os.pathsep)
        return

    source_env = shell_local.sanitize_execution_env({
        "PATH": f"{AGENT_BIN}:{FRAMEWORK_BIN}:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin",
        "VIRTUAL_ENV": "/opt/venv-a0",
        "HOME": os.environ.get("HOME", "/root"),
    })

    import subprocess

    proc = subprocess.run(
        ["/bin/bash", "--noprofile", "--norc", "-c", "command -v python3.12 || true; command -v pip3.12 || true"],
        env={**os.environ, **source_env},
        capture_output=True,
        text=True,
        timeout=15,
    )

    assert FRAMEWORK_BIN not in proc.stdout, proc.stdout


def test_is_framework_venv_path_matches_root_and_children():
    assert shell_local._is_framework_venv_path("/opt/venv-a0")
    assert shell_local._is_framework_venv_path("/opt/venv-a0/")
    assert shell_local._is_framework_venv_path("/opt/venv-a0/bin")
    assert shell_local._is_framework_venv_path("/opt/venv-a0/lib/python3.12/site-packages")

    assert not shell_local._is_framework_venv_path("/opt/venv")
    assert not shell_local._is_framework_venv_path("/opt/venv/bin")
    assert not shell_local._is_framework_venv_path("/opt/venv-a0-projects/bin")
    assert not shell_local._is_framework_venv_path("/opt/venv-a0x/bin")
    assert not shell_local._is_framework_venv_path("/usr/bin")
