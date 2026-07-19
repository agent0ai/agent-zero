import re
import resource
import subprocess
from pathlib import Path

import pytest


REPO_ROOT = Path(__file__).resolve().parents[1]
INITIALIZE_SCRIPT = REPO_ROOT / "docker" / "run" / "fs" / "exe" / "initialize.sh"


def _raise_limit_function() -> str:
    text = INITIALIZE_SCRIPT.read_text(encoding="utf-8")
    match = re.search(r"^raise_open_file_limit\(\) \{\n.*?^\}\n", text, re.M | re.S)
    assert match, "initialize.sh must define raise_open_file_limit"
    return match.group(0)


def _run_bash(script: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["bash", "-c", script],
        check=True,
        text=True,
        capture_output=True,
    )


def test_initialize_raises_soft_open_file_limit_to_requested_target():
    function = _raise_limit_function()

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

    function = _raise_limit_function()

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
