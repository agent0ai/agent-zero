"""Provision source-updated images before the WebUI health-check window starts."""
import os
from pathlib import Path
import subprocess
import sys

subprocess.run([sys.executable, '-c',
               'from pathlib import Path; from plugins._sandboxing.helpers.bootstrap import ensure; ensure(Path("/usr/local/bin/a0-proot"))'],
               cwd=Path(os.environ['A0_UPDATE_REPO_DIR']), check=True, timeout=650)
