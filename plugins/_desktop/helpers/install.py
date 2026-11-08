"""Existing source installations use the image's pinned build recipe in a child sandbox."""
import base64
import io
import os
from pathlib import Path
import shutil
import tarfile
import tempfile
from helpers.sandbox_worker import SandboxWorker
from helpers import system_packages
from plugins._desktop.helpers.runtime import BUILD, BINARY


def install():
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
        # Publish the server last; a failed build never replaces the working binary.
        for path in staged.rglob('*'):
            relative = path.relative_to(staged)
            target = Path('/usr/local') / relative
            if path.is_dir() or path.is_symlink() or target in {BINARY, BINARY.parent / 'a0-build-id'}:
                continue
            target.parent.mkdir(parents=True, exist_ok=True)
            temporary = target.with_name(target.name + '.a0-new')
            shutil.copy2(path, temporary)
            os.replace(temporary, target)
        BINARY.parent.mkdir(parents=True, exist_ok=True)
        temporary = BINARY.with_name('tuxee.a0-new')
        shutil.copy2(staged / 'lib/tuxee/tuxee', temporary)
        os.replace(temporary, BINARY)
        link = Path('/usr/local/bin/tuxee')
        if not link.exists():
            link.symlink_to('../lib/tuxee/tuxee')
        marker = BINARY.parent / 'a0-build-id'
        temporary = marker.with_name('a0-build-id.a0-new')
        shutil.copy2(staged / 'lib/tuxee/a0-build-id', temporary)
        os.replace(temporary, marker)
