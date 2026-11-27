"""Stop the old engine before checkout; retain desired-running flags for restoration."""
import os
from pathlib import Path
import subprocess
import sys

repo = Path(os.environ['A0_UPDATE_REPO_DIR'])
source = repo / 'plugins/_sandboxing/helpers/manager.py'
if source.is_file() and 'def _runsc_command(' in source.read_text():
    subprocess.run([sys.executable, '-c', '''
from helpers import dotenv
dotenv.load_dotenv()
from helpers.sandbox import get_manager
manager = get_manager()
for info in manager.list():
    if info.status == 'running':
        wanted = info.desired_running
        manager.stop(info.name)
        path = manager.config.instances_dir / info.name / 'metadata.json'
        value = manager._read_metadata(info.name)
        value['desired_running'] = wanted
        manager._atomic_write_json(path, value)
'''], cwd=repo, check=True, timeout=300)
