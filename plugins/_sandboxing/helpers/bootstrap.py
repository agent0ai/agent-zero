"""Install the core runtime for source-updated instances; ready images do no work."""
from pathlib import Path
import fcntl
import os
import subprocess


def ready(executable: Path) -> bool:
    if not executable.is_file():
        return False
    result = subprocess.run([str(executable), '--version'], capture_output=True, timeout=5, text=True)
    return result.returncode == 0 and 'A0-COW-2' in result.stdout


def ensure(executable: Path) -> None:
    if ready(executable):
        return
    if executable != Path('/usr/local/bin/a0-proot') or os.geteuid() != 0:
        raise RuntimeError(f'Install the A0 PRoot CoW runtime at {executable}')
    fd = os.open('/var/lock/a0-proot-install.lock', os.O_CREAT | os.O_RDWR | os.O_NOFOLLOW, 0o600)
    with os.fdopen(fd, 'w') as lock:
        fcntl.flock(lock, fcntl.LOCK_EX)
        if ready(executable):
            return
        recipe = Path(__file__).resolve().parents[3] / 'docker/sandbox/proot/install.sh'
        subprocess.run(['sh', str(recipe)], check=True, timeout=600)
        if not ready(executable):
            raise RuntimeError('PRoot installation did not produce the required CoW runtime')
