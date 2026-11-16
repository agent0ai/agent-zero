import os
from pathlib import Path
import subprocess
import sys

import pytest


@pytest.mark.parametrize("requested,existing", [(None, False), ("/usr/local/bin/python", False), ("/usr/local/bin/python", True)])
def test_worker_python_selection_preserves_existing_environments(tmp_path, requested, existing):
    runtime = tmp_path / "runtime"
    commands = tmp_path / "commands"
    commands.mkdir()
    log = tmp_path / "commands.log"
    for name in ("python", "uv"):
        command = commands / name
        command.write_text('#!/bin/sh\nprintf "%s\\n" "$*" >> "$BOOTSTRAP_LOG"\n')
        command.chmod(0o755)
    if existing:
        (runtime / "bin").mkdir(parents=True)
        (runtime / "bin/python").symlink_to(sys.executable)
    source = Path(__file__).resolve().parents[1] / "plugins/_sandboxing/sandbox/python.sh"
    script = source.read_text().replace("/opt/runtime", str(runtime)).replace("/usr/local/share/fonts", str(tmp_path / "fonts"))
    env = {**os.environ, "PATH": f"{commands}:{os.environ['PATH']}", "BOOTSTRAP_LOG": str(log)}
    env.pop("WORKER_PYTHON", None)
    if requested:
        env["WORKER_PYTHON"] = requested
    subprocess.run(["sh", "-c", script], env=env, check=True)
    if existing:
        assert not log.exists()
        assert (runtime / "bin/python").resolve() == Path(sys.executable).resolve()
    else:
        assert log.read_text().splitlines() == [
            "-m pip install --no-cache-dir uv",
            f"venv --python {requested or '3.12'} {runtime}",
        ]
