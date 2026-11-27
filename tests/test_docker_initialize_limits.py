import resource
import subprocess
import time
from pathlib import Path

import pytest


REPO_ROOT = Path(__file__).resolve().parents[1]
RUNTIME = REPO_ROOT / "docker/run/fs"
ENTRYPOINT = RUNTIME / "exe/tuxee-entrypoint.sh"
INIT_SCRIPT = (RUNTIME / "opt/agent-zero/init/agent-zero.sh").read_text()
OPEN_FILE_SETUP = INIT_SCRIPT[INIT_SCRIPT.index("requested="):INIT_SCRIPT.index("\n\ncp -r")]
APT_SETUP = INIT_SCRIPT[INIT_SCRIPT.index("marker="):INIT_SCRIPT.index("\n\n# Give each attempt")]


def _run_bash(script: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["bash", "-c", script],
        check=True,
        text=True,
        capture_output=True,
        timeout=10,
    )


def test_initialize_raises_soft_open_file_limit_to_requested_target():
    _run_bash(
        f"""
        set -euo pipefail
        ulimit -S -n 1024
        A0_NOFILE_LIMIT=4096
        {OPEN_FILE_SETUP}
        test "$(ulimit -S -n)" = "4096"
        """
    )


def test_initialize_caps_open_file_limit_at_hard_limit():
    _soft, hard = resource.getrlimit(resource.RLIMIT_NOFILE)
    if hard != resource.RLIM_INFINITY and hard < 2048:
        pytest.skip("host hard open-file limit is too low for this regression test")

    _run_bash(
        f"""
        set -euo pipefail
        ulimit -S -n 1024
        ulimit -H -n 2048
        A0_NOFILE_LIMIT=65535
        {OPEN_FILE_SETUP}
        test "$(ulimit -S -n)" = "2048"
        """
    )


def test_initialize_refreshes_package_indexes_silently_once_per_container(tmp_path):
    marker = tmp_path / "started"
    calls = tmp_path / "calls"
    setup = APT_SETUP.replace(
        "/var/lib/apt/a0-initial-update-started", str(marker)
    )
    result = _run_bash(f'''
        set -euo pipefail
        apt-get() {{ echo "$*" >> "{calls}"; echo noisy; echo noisy >&2; return 1; }}
        {setup}
        wait
        {setup}
        wait
    ''')
    assert marker.exists()
    assert calls.read_text() == "update\n"
    assert result.stdout == result.stderr == ""


def test_initialize_does_not_wait_for_package_update(tmp_path):
    marker = tmp_path / "started"
    setup = APT_SETUP.replace(
        "/var/lib/apt/a0-initial-update-started", str(marker)
    )
    result = _run_bash(f'''
        set -euo pipefail
        mkfifo "{tmp_path / 'gate'}"
        apt-get() {{ read -r _ < "{tmp_path / 'gate'}"; }}
        {setup}
        pid=$!
        kill -0 "$pid"
        echo continued
        kill "$pid"
        wait "$pid" || true
    ''')
    assert result.stdout.strip() == "continued"


def test_initialize_explains_hidden_application_before_mutating_data(tmp_path):
    script = ENTRYPOINT.read_text().replace("/a0/run_ui.py", str(tmp_path / "run_ui.py"))
    result = subprocess.run(["bash", "-c", script],
                            text=True, capture_output=True)
    assert result.returncode == 1
    assert "./agent-zero/usr:/a0/usr" in result.stderr
    assert "Mount persistent data at /a0/usr" in result.stderr


def test_application_presence_check_accepts_populated_development_mount(tmp_path):
    (tmp_path / "run_ui.py").touch()
    script = ENTRYPOINT.read_text().split("password_file=", 1)[0]
    script = script.replace("/a0/run_ui.py", str(tmp_path / "run_ui.py"))
    result = _run_bash(script + "\necho accepted")
    assert "accepted" in result.stdout


def test_agent_zero_relaunches_after_exit_zero_and_stops_the_active_attempt(tmp_path):
    first = tmp_path / "first"
    started = tmp_path / "started"
    stopped = tmp_path / "stopped"
    loop = INIT_SCRIPT[INIT_SCRIPT.index("set -m"):]
    loop = loop.replace("/exe/run_A0.sh", "run_a0")
    script = f"""
    set -eu
    run_a0() {{
        if [[ ! -e "{first}" ]]; then
            touch "{first}"
            return
        fi
        trap 'touch "{stopped}"; exit 0' TERM
        touch "{started}"
        sleep 30
    }}
    {loop}
    """
    process = subprocess.Popen(["bash", "-c", script], stderr=subprocess.PIPE, text=True)
    try:
        deadline = time.monotonic() + 5
        while not started.exists():
            assert process.poll() is None and time.monotonic() < deadline
            time.sleep(0.02)
        process.terminate()
        _, stderr = process.communicate(timeout=5)
        assert process.returncode == 0 and stopped.exists()
        assert stderr.count("Agent Zero exited (status 0)") == 1
    finally:
        if process.poll() is None:
            process.kill()
            process.wait()
