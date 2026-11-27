"""Existing source installations use the image's pinned build recipe in a child sandbox."""
import base64
import fcntl
import io
import os
from pathlib import Path
import shutil
import re
import subprocess
import tarfile
import tempfile
from plugins._desktop.helpers.runtime import BUILD, BINARY

PREFIX = Path('/usr/local')


def binary_version(path):
    result = subprocess.check_output([str(path), 'version'], text=True, timeout=10).strip()
    if result == 'Tuxee 0.0.0-a0':
        return (0, 0, 0)
    match = re.fullmatch(r'Tuxee (0|[1-9]\d*)\.(0|[1-9]\d*)\.(0|[1-9]\d*)', result)
    if not match:
        raise RuntimeError(f'Unrecognized Tuxee version at {path}; installation unchanged')
    return tuple(map(int, match.groups()))


def publish(staged):
    """Serialize with Tuxee's own updater and preserve newer official binaries."""
    BINARY.parent.mkdir(parents=True, exist_ok=True)
    fd = os.open(BINARY.parent / '.tuxee-update.lock', os.O_CREAT | os.O_RDWR | os.O_NOFOLLOW, 0o600)
    with os.fdopen(fd, 'w') as lock:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        if BINARY.is_symlink():
            raise RuntimeError(f'Refusing to replace non-regular binary {BINARY}')
        candidate = staged / 'lib/tuxee/tuxee'
        version = binary_version(candidate)
        replace = not BINARY.exists() or binary_version(BINARY) < version
        link = PREFIX / 'bin/tuxee'
        if (link.exists() or link.is_symlink()) and not (link.is_symlink() and link.resolve() == BINARY):
            raise RuntimeError(f'Refusing to replace unrelated command {link}')
        # Publish support files first and replace inodes used by surviving processes.
        for path in staged.rglob('*'):
            relative = path.relative_to(staged)
            target = PREFIX / relative
            if path.is_dir() or target in {BINARY, link, BINARY.parent / 'a0-build-id'}:
                continue
            target.parent.mkdir(parents=True, exist_ok=True)
            temporary = target.with_name(target.name + '.a0-new')
            temporary.unlink(missing_ok=True)
            shutil.copy2(path, temporary, follow_symlinks=False)
            os.replace(temporary, target)
        link.parent.mkdir(parents=True, exist_ok=True)
        temporary = link.with_name('tuxee.a0-new')
        temporary.unlink(missing_ok=True)
        temporary.symlink_to(BINARY)
        os.replace(temporary, link)
        if replace:
            temporary = BINARY.with_name('tuxee.a0-new')
            temporary.unlink(missing_ok=True)
            shutil.copy2(candidate, temporary)
            os.replace(temporary, BINARY)
        marker = BINARY.parent / 'a0-build-id'
        temporary = marker.with_name('a0-build-id.a0-new')
        temporary.unlink(missing_ok=True)
        shutil.copy2(staged / 'lib/tuxee/a0-build-id', temporary)
        os.replace(temporary, marker)


def install():
    from helpers.sandbox_worker import SandboxWorker
    from helpers import system_packages
    if os.geteuid() != 0:
        raise RuntimeError('Tuxee installation requires a rebuilt Agent Zero image or administrator setup')
    packages = (BUILD / 'runtime-packages.txt').read_text().split()
    for command in (['apt-get', 'update'], ['apt-get', 'install', '-y', '--no-install-recommends', *packages]):
        result = system_packages.run_runtime_apt(command, timeout=900)
        if result.returncode:
            raise RuntimeError('Tuxee runtime package installation failed')
    builder = SandboxWorker('_desktop', idle_seconds=0)
    try:
        bundle = builder.call({'action': 'build'}, timeout=1800)
    finally:
        builder.stop()
        manager, _ = builder._paths()
        manager.delete(builder.name, missing_ok=True)
    with tempfile.TemporaryDirectory() as directory:
        with tarfile.open(fileobj=io.BytesIO(base64.b64decode(bundle, validate=True))) as archive:
            archive.extractall(directory, filter='data')
        staged = Path(directory) / 'usr/local'
        publish(staged)
