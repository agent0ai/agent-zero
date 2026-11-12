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


@pytest.mark.parametrize("package_index", [None, "mirror_Packages", "mirror_Packages.lz4"])
def test_initialize_updates_only_an_empty_package_cache(tmp_path, package_index):
    lists = tmp_path / "lists"
    lists.mkdir()
    (lists / "partial").mkdir()
    (lists / "lock").touch()
    if package_index:
        (lists / package_index).write_text("cached package index")
    calls = tmp_path / "apt-calls"
    function = _script_function("initialize_package_lists").replace(
        "/var/lib/apt/lists", str(lists)
    )

    _run_bash(f"""
        set -euo pipefail
        apt-get() {{ echo "$*" >> "{calls}"; }}
        {function}
        initialize_package_lists
        wait
    """)

    assert (calls.read_text() if calls.exists() else "") == (
        "" if package_index else "update\n"
    )
