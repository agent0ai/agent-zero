import re
import resource
import subprocess
from pathlib import Path

import pytest


REPO_ROOT = Path(__file__).resolve().parents[1]
INITIALIZE_SCRIPT = REPO_ROOT / "docker" / "run" / "fs" / "exe" / "initialize.sh"


def _script_function(name: str) -> str:
    text = INITIALIZE_SCRIPT.read_text(encoding="utf-8")
    match = re.search(rf"^{name}\(\) \{{\n.*?^\}}\n", text, re.M | re.S)
    assert match, f"initialize.sh must define {name}"
    return match.group(0)


def _run_bash(script: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["bash", "-c", script],
        check=True,
        text=True,
        capture_output=True,
        timeout=10,
    )


def test_initialize_raises_soft_open_file_limit_to_requested_target():
    function = _script_function("raise_open_file_limit")

    result = _run_bash(
        f"""
        set -euo pipefail
        {function}
        ulimit -S -n 1024
        A0_NOFILE_LIMIT=4096
        raise_open_file_limit
        test "$(ulimit -S -n)" = "4096"
        """
    )

    assert "Raised open file soft limit from 1024 to 4096" in result.stdout


def test_initialize_caps_open_file_limit_at_hard_limit():
    _soft, hard = resource.getrlimit(resource.RLIMIT_NOFILE)
    if hard != resource.RLIM_INFINITY and hard < 2048:
        pytest.skip("host hard open-file limit is too low for this regression test")

    function = _script_function("raise_open_file_limit")

    result = _run_bash(
        f"""
        set -euo pipefail
        {function}
        ulimit -S -n 1024
        ulimit -H -n 2048
        A0_NOFILE_LIMIT=65535
        raise_open_file_limit
        test "$(ulimit -S -n)" = "2048"
        """
    )

    assert "Raised open file soft limit from 1024 to 2048" in result.stdout


def test_initialize_refreshes_package_indexes_silently_once_per_container(tmp_path):
    marker = tmp_path / "started"
    calls = tmp_path / "calls"
    function = _script_function("initialize_package_lists").replace(
        "/var/lib/apt/a0-initial-update-started", str(marker)
    )
    result = _run_bash(f'''
        set -euo pipefail
        apt-get() {{ echo "$*" >> "{calls}"; echo noisy; echo noisy >&2; return 1; }}
        {function}
        initialize_package_lists
        wait
        initialize_package_lists
        wait
    ''')
    assert marker.exists()
    assert calls.read_text() == "update\n"
    assert result.stdout == result.stderr == ""


def test_initialize_does_not_wait_for_package_update(tmp_path):
    marker = tmp_path / "started"
    function = _script_function("initialize_package_lists").replace(
        "/var/lib/apt/a0-initial-update-started", str(marker)
    )
    result = _run_bash(f'''
        set -euo pipefail
        mkfifo "{tmp_path / 'gate'}"
        apt-get() {{ read -r _ < "{tmp_path / 'gate'}"; }}
        {function}
        initialize_package_lists
        pid=$!
        kill -0 "$pid"
        echo continued
        kill "$pid"
        wait "$pid" || true
    ''')
    assert result.stdout.strip() == "continued"


def test_initialize_explains_hidden_application_before_mutating_data(tmp_path):
    script = INITIALIZE_SCRIPT.read_text().replace("/a0/run_ui.py", str(tmp_path / "run_ui.py"))
    result = subprocess.run(["bash", "-c", script, "initialize.sh", "local"],
                            text=True, capture_output=True)
    assert result.returncode == 1
    assert "./agent-zero/usr:/a0/usr" in result.stderr
    assert "Mount persistent data at /a0/usr" in result.stderr


def test_application_presence_check_accepts_populated_development_mount(tmp_path):
    (tmp_path / "run_ui.py").touch()
    script = INITIALIZE_SCRIPT.read_text().split("raise_open_file_limit()", 1)[0]
    script = script.replace("/a0/run_ui.py", str(tmp_path / "run_ui.py"))
    result = _run_bash('set -- local\n' + script + "\necho accepted")
    assert "accepted" in result.stdout
