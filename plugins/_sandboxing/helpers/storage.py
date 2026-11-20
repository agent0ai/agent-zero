"""Immutable image data with private directory entries and copy-on-write files."""
from __future__ import annotations

import collections
import fcntl
import os
from pathlib import Path
import pwd
import stat
import shutil
import tempfile

from helpers.sandbox_types import SandboxError
from plugins._sandboxing.helpers.process import real_uid


def walk(root: Path):
    yield root
    for directory, dirs, files in os.walk(root, followlinks=False):
        for name in dirs + files:
            yield Path(directory) / name


def lease_uid(registry: Path, owner: Path) -> int:
    """Persistent leases are never recycled: stopped guests also own private files."""
    if os.geteuid() != 0:
        raise PermissionError('PRoot sandbox management needs root to assign separate Linux users; run A0 in Docker')
    registry.mkdir(mode=0o700, parents=True, exist_ok=True)
    with (registry / '.lock').open('a') as lock:
        fcntl.flock(lock, fcntl.LOCK_EX)
        occupied = {entry.pw_uid for entry in pwd.getpwall()}
        for process in Path('/proc').iterdir():
            if process.name.isdigit():
                occupied.add(real_uid(process))
        for uid in range(20000, 60000):
            record = registry / str(uid)
            if record.exists():
                if record.read_text() == str(owner):
                    return uid
                continue
            # An unrelated live process must never become part of an A0 UID group.
            if uid in occupied:
                continue
            with record.open('x') as handle:
                handle.write(str(owner))
            record.chmod(0o600)
            return uid
    raise RuntimeError('No sandbox UIDs available')


def prepare(base: Path, root: Path, control: Path, uid: int) -> None:
    """A private directory/symlink tree; regular files initially share base inodes."""
    if base.stat().st_dev != root.parent.stat().st_dev:
        raise RuntimeError('Sandbox images and instances must be on the same filesystem for copy-on-write')
    counts = collections.Counter()
    root.mkdir(mode=0o700)
    os.chown(root, uid, uid)
    pending = [(str(base), str(root))]
    while pending:
        directory, target = pending.pop()
        with os.scandir(directory) as entries:
            for entry in entries:
                destination = os.path.join(target, entry.name)
                info = entry.stat(follow_symlinks=False)
                if stat.S_ISREG(info.st_mode):
                    if info.st_uid != 0 or info.st_mode & 0o022 or not info.st_mode & 0o004:
                        raise RuntimeError(f'Image is not prepared for immutable sharing: {entry.path}')
                    os.link(entry.path, destination)
                    counts[(info.st_dev, info.st_ino)] += 1
                elif stat.S_ISDIR(info.st_mode):
                    os.mkdir(destination)
                    os.chown(destination, uid, uid)
                    os.chmod(destination, stat.S_IMODE(info.st_mode) | 0o700)
                    pending.append((entry.path, destination))
                elif stat.S_ISLNK(info.st_mode):
                    os.symlink(os.readlink(entry.path), destination)
                    os.lchown(destination, uid, uid)
                elif stat.S_ISFIFO(info.st_mode):
                    os.mkfifo(destination, stat.S_IMODE(info.st_mode))
                    os.chown(destination, uid, uid)
                # Device nodes are supplied by the explicit /dev binding, never copied.
    control.mkdir(mode=0o700, exist_ok=True)
    (control / 'aliases').mkdir(exist_ok=True)
    (control / 'lock').touch()
    for (dev, ino), count in counts.items():
        if count > 1:
            (control / 'aliases' / f'{dev}-{ino}').touch()
    for path in walk(control):
        os.chown(path, uid, uid, follow_symlinks=False)


def freeze(root: Path) -> None:
    """Only image-import/build code calls this, before publishing the immutable base."""
    for path in walk(root):
        info = path.lstat()
        os.chown(path, 0, 0, follow_symlinks=False)
        if stat.S_ISREG(info.st_mode):
            path.chmod((stat.S_IMODE(info.st_mode) & 0o755) | 0o444 | ((info.st_mode & 0o100) >> 6))
        elif stat.S_ISDIR(info.st_mode):
            path.chmod(stat.S_IMODE(info.st_mode) | 0o755)


def adopt(root: Path, control: Path, uid: int) -> None:
    """Existing disk roots are already private: retain every file and ownership access."""
    for path in walk(root):
        os.chown(path, uid, uid, follow_symlinks=False)
    root.chmod(0o700)
    control.mkdir(mode=0o700, exist_ok=True)
    (control / 'aliases').mkdir(exist_ok=True)
    (control / 'lock').touch()
    for path in walk(control):
        os.chown(path, uid, uid, follow_symlinks=False)


def prepare_workspace(path: Path, seed: Path | None = None) -> None:
    """Publish a new workspace once. A restored or previously used workspace wins."""
    parent = _open(path.parent, create_dirs=True)
    try:
        try:
            fd = os.open(path.name, os.O_DIRECTORY | os.O_NOFOLLOW, dir_fd=parent)
        except FileNotFoundError:
            if seed is None or not any(seed.iterdir()):
                os.mkdir(path.name, mode=0o700, dir_fd=parent)
            else:
                # Stage beside the destination so a failed copy cannot become user data.
                with tempfile.TemporaryDirectory(dir=f'/proc/self/fd/{parent}') as stage:
                    tree = Path(stage) / 'workspace'
                    shutil.copytree(seed, tree, symlinks=True)
                    os.rename(tree, path.name, dst_dir_fd=parent)
        else:
            os.close(fd)
    finally:
        os.close(parent)


def link_sandbox_data(link: Path, data: Path) -> None:
    target = Path(os.path.relpath(data, link.parent))
    try:
        link.symlink_to(target, target_is_directory=True)
    except FileExistsError:
        if not link.is_symlink() or link.readlink() != target:
            raise SandboxError(f"Sandbox data shortcut already exists with different contents: {link}") from None


def _open(path: Path, *, create_dirs: bool = False) -> int:
    fd = os.open('/', os.O_PATH | os.O_DIRECTORY)
    try:
        for part in path.parts[1:]:
            flags = os.O_PATH | os.O_NOFOLLOW
            try:
                next_fd = os.open(part, flags, dir_fd=fd)
            except FileNotFoundError:
                if not create_dirs:
                    raise
                try:
                    os.mkdir(part, mode=0o700, dir_fd=fd)
                except FileExistsError:
                    pass
                next_fd = os.open(part, flags | os.O_DIRECTORY, dir_fd=fd)
            os.close(fd); fd = next_fd
            if stat.S_ISLNK(os.fstat(fd).st_mode):
                raise PermissionError('Refusing a symlink in a binding source')
        return fd
    except BaseException:
        os.close(fd)
        raise


def open_directory(path: Path) -> int:
    fd = _open(path)
    if not stat.S_ISDIR(os.fstat(fd).st_mode):
        os.close(fd)
        raise NotADirectoryError(str(path))
    return fd


def _acl(fd: int, uid: int, permissions: str, *, default=False, augment=False) -> None:
    # Descriptor paths pin the inode: a concurrent guest rename cannot redirect ACL changes.
    import ctypes
    library = ctypes.CDLL('libacl.so.1', use_errno=True)
    library.acl_get_file.argtypes = [ctypes.c_char_p, ctypes.c_int]
    library.acl_get_file.restype = ctypes.c_void_p
    library.acl_to_text.argtypes = [ctypes.c_void_p, ctypes.c_void_p]
    library.acl_to_text.restype = ctypes.c_void_p
    library.acl_from_text.argtypes = [ctypes.c_char_p]
    library.acl_from_text.restype = ctypes.c_void_p
    library.acl_set_file.argtypes = [ctypes.c_char_p, ctypes.c_int, ctypes.c_void_p]
    library.acl_free.argtypes = [ctypes.c_void_p]
    path = f'/proc/self/fd/{fd}'.encode()
    kind = 0x4000 if default else 0x8000
    original = library.acl_get_file(path, kind)
    text = ''
    if original:
        buffer = library.acl_to_text(original, None)
        if buffer:
            text = ctypes.string_at(buffer).decode(); library.acl_free(buffer)
        library.acl_free(original)
    entries = [line.split()[0] for line in text.splitlines() if line and not line.startswith('#')]
    if not entries:
        mode = os.fstat(fd).st_mode
        entries = [f'{label}::' + ''.join(c if mode & (bit << shift) else '-' for c,bit in [('r',4),('w',2),('x',1)])
                   for label,shift in [('user',6),('group',3),('other',0)]]
    old_mask = next((line.split(':')[2] for line in entries if line.startswith('mask:')), 'rwx')
    if augment:
        previous = next((line.split(':')[2] for line in entries if line.startswith(f'user:{uid}:')), '')
        permissions = ''.join(c if c in permissions or c in previous and c in old_mask else '-' for c in 'rwx')
    updated = []
    for line in entries:
        if line.startswith(('mask:', f'user:{uid}:')):
            continue
        label, identifier, perms = line.split(':')
        if label == 'group' or label == 'user' and identifier:
            perms = ''.join(c if c in old_mask else '-' for c in perms)
        updated.append(f'{label}:{identifier}:{perms}')
    updated.append(f'user:{uid}:{permissions}')
    mask = set(permissions)
    for line in updated:
        label, identifier, perms = line.split(':')
        if label == 'group' or label == 'user' and identifier:
            mask.update(perms)
    updated.append('mask::' + ''.join(c if c in mask else '-' for c in 'rwx'))
    acl = library.acl_from_text(('\n'.join(updated) + '\n').encode())
    if not acl:
        raise OSError(ctypes.get_errno(), 'Invalid sandbox access ACL')
    try:
        if library.acl_set_file(path, kind, acl):
            raise OSError(ctypes.get_errno(), 'Cannot grant sandbox binding access')
    finally:
        library.acl_free(acl)


def traverse(path: Path, uid: int) -> None:
    for parent in reversed(path.parents):
        fd = _open(parent)
        try:
            _acl(fd, uid, '--x', augment=True)
        finally:
            os.close(fd)
    fd = _open(path)
    try:
        if os.fstat(fd).st_uid != uid:
            _acl(fd, uid, '--x', augment=True)
    finally:
        os.close(fd)


def grant(path: Path, uid: int, *, writable: bool, exclude=()) -> None:
    """Grant explicit bindings, without following guest symlinks or changing masked state."""
    excluded = set(exclude)
    traverse(path, uid)
    def visit(fd, logical):
        if logical in excluded:
            return
        info = os.fstat(fd)
        if not (stat.S_ISDIR(info.st_mode) or stat.S_ISREG(info.st_mode)):
            return
        permissions = 'r' + ('w' if writable else '-') + ('x' if info.st_mode & 0o111 or stat.S_ISDIR(info.st_mode) else '-')
        _acl(fd, uid, permissions)
        if stat.S_ISDIR(info.st_mode):
            _acl(fd, uid, 'rwx' if writable else 'r-x', default=True)
            directory = os.open('.', os.O_RDONLY | os.O_DIRECTORY, dir_fd=fd)
            try:
                for name in os.listdir(directory):
                    try:
                        child = os.open(name, os.O_PATH | os.O_NOFOLLOW, dir_fd=directory)
                    except FileNotFoundError:
                        continue
                    try:
                        visit(child, logical / name)
                    finally:
                        os.close(child)
            finally:
                os.close(directory)
    fd = _open(path)
    try:
        visit(fd, path)
    finally:
        os.close(fd)


def ensure_base(root: Path) -> None:
    with (root.parent / '.cow.lock').open('a') as lock:
        fcntl.flock(lock, fcntl.LOCK_EX)
        marker = root.parent / '.cow-ready'
        if not marker.exists():
            freeze(root)
            marker.touch(mode=0o600)


def private_bytes(root: Path, uid: int | None) -> int:
    seen = set()
    total = 0
    for path in walk(root):
        try:
            info = path.lstat()
        except FileNotFoundError:
            continue
        key = (info.st_dev, info.st_ino)
        if key in seen:
            continue
        seen.add(key)
        if uid and stat.S_ISREG(info.st_mode) and info.st_uid == 0 and info.st_nlink > 1:
            continue
        total += info.st_blocks * 512
    return total
