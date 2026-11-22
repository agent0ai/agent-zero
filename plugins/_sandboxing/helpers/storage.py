"""Immutable image preparation, sparse guest storage, UID leases and binding ACLs."""
from __future__ import annotations

import collections
import errno
import fcntl
import grp
import os
from pathlib import Path
import pwd
import stat
import shutil
import tempfile

from helpers.sandbox_types import SandboxError


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
        occupied = set()
        for record in registry.iterdir():
            if record.name.isdigit() and 20000 <= int(record.name) < 60000:
                identity = int(record.name)
                if record.read_text() == str(owner):
                    return identity
                occupied.add(identity)
        occupied.update(entry.pw_uid for entry in pwd.getpwall())
        occupied.update(entry.gr_gid for entry in grp.getgrall())
        occupied.update(entry.pw_gid for entry in pwd.getpwall())
        for process in Path('/proc').iterdir():
            if process.name.isdigit():
                try:
                    for line in (process / 'status').read_text().splitlines():
                        if line.startswith(('Uid:', 'Gid:', 'Groups:')):
                            occupied.update(map(int, line.split()[1:]))
                except (FileNotFoundError, ProcessLookupError):
                    pass
        for uid in range(20000, 60000):
            record = registry / str(uid)
            # An unrelated live process must never become part of an A0 UID group.
            if uid in occupied:
                continue
            with record.open('x') as handle:
                handle.write(str(owner))
            record.chmod(0o600)
            return uid
    raise RuntimeError('No sandbox UIDs available')


def prepare(root: Path, control: Path, uid: int) -> None:
    """Only allocate the upper directory and its controls for a new guest."""
    for path in (root, control, control / 'whiteouts'):
        path.mkdir(mode=0o700)
        os.chown(path, uid, uid)
    lock = control / 'lock'
    lock.touch(mode=0o600)
    os.chown(lock, uid, uid)


def freeze(root: Path) -> None:
    """Only image-import/build code calls this, before publishing the immutable base."""
    aliases = collections.defaultdict(list)
    for path in walk(root):
        info = path.lstat()
        os.chown(path, 0, 0, follow_symlinks=False)
        if stat.S_ISREG(info.st_mode):
            if info.st_nlink > 1:
                aliases[info.st_ino].append(os.fsencode('/' + str(path.relative_to(root))))
            path.chmod((stat.S_IMODE(info.st_mode) & 0o755) | 0o444 | ((info.st_mode & 0o100) >> 6))
        elif stat.S_ISDIR(info.st_mode):
            path.chmod((stat.S_IMODE(info.st_mode) | 0o755) & ~0o022)
        elif not stat.S_ISLNK(info.st_mode):
            path.chmod(stat.S_IMODE(info.st_mode) & ~0o022)
    index = root.parent / 'overlay-links'
    index.mkdir(exist_ok=True)
    index.chmod(0o755)
    for inode, paths in aliases.items():
        if len(paths) > 1:
            entry = index / str(inode)
            entry.write_bytes(b'\0'.join(paths) + b'\0')
            entry.chmod(0o444)


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


def _has_acl(path, name='access'):
    try:
        os.getxattr(path, 'system.posix_acl_' + name)
        return True
    except OSError as exc:
        if exc.errno in (errno.ENODATA, errno.ENOTSUP):
            return False
        raise


def _mode_allows(fd, uid, bits, shared_gid=None):
    info = os.fstat(fd)
    if info.st_uid == uid:
        return (info.st_mode >> 6) & bits == bits
    if _has_acl(f'/proc/self/fd/{fd}'):
        return False
    shift = 3 if info.st_gid in (uid, shared_gid) else 0
    return (info.st_mode >> shift) & bits == bits


def _acl(fd: int, uid: int | None, permissions: str, *, default=False, augment=False) -> None:
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
    if not original and ctypes.get_errno() not in (errno.ENODATA, errno.ENOTSUP):
        raise OSError(ctypes.get_errno(), 'Cannot read sandbox binding ACL', os.fsdecode(os.readlink(path)))
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
    principal = 'group::' if uid is None else f'user:{uid}:'
    if augment:
        previous = next((line.split(':')[2] for line in entries if line.startswith(f'user:{uid}:')), '')
        permissions = ''.join(c if c in permissions or c in previous and c in old_mask else '-' for c in 'rwx')
    updated = []
    for line in entries:
        if line.startswith(('mask:', principal)):
            continue
        label, identifier, perms = line.split(':')
        if label == 'group' or label == 'user' and identifier:
            perms = ''.join(c if c in old_mask else '-' for c in perms)
        updated.append(f'{label}:{identifier}:{perms}')
    updated.append(principal + permissions)
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
            raise OSError(ctypes.get_errno(), 'Cannot grant sandbox binding access via ACL', os.fsdecode(os.readlink(path)))
    finally:
        library.acl_free(acl)


def traverse(path: Path, uid: int, shared_gid=None) -> None:
    for parent in (*reversed(path.parents), path):
        fd = _open(parent)
        try:
            if not _mode_allows(fd, uid, 1, shared_gid):
                _acl(fd, uid, '--x', augment=True)
        finally:
            os.close(fd)


def _visit_tree(root_fd, path, apply, exclude=(), *, children_first=False):
    excluded = set(exclude)
    def visit(fd, logical):
        if logical in excluded:
            return
        info = os.fstat(fd)
        if not (stat.S_ISDIR(info.st_mode) or stat.S_ISREG(info.st_mode)):
            return
        if not children_first:
            apply(fd, logical, info)
        if stat.S_ISDIR(info.st_mode):
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
        if children_first:
            apply(fd, logical, info)
    visit(root_fd, path)


def prepare_managed(path, identity, registry, *, shared=False):
    """Update the root last so an interrupted migration can be retried."""
    def update(child, logical, info):
        target = f'/proc/self/fd/{child}'
        is_dir = stat.S_ISDIR(info.st_mode)
        if not is_dir and info.st_nlink > 1:
            raise SandboxError(f'Cannot change ownership of a multiply linked managed file: {logical}')
        access = 7 if is_dir or info.st_mode & 0o111 else 6
        if shared:
            os.chown(target, -1, identity)
            mode = (info.st_mode & 0o1707) | (access << 3)
            if is_dir:
                mode |= stat.S_ISGID
            for kind in (('access', 'default') if is_dir else ('access',)):
                if _has_acl(target, kind):
                    _acl(child, None, 'rwx' if access == 7 else 'rw-', default=kind == 'default')
        else:
            os.chown(target, identity, identity)
            mode = 0o700 if logical == path else (info.st_mode & 0o077) | (access << 6)
        os.chmod(target, mode)
        current = os.fstat(child)
        if (current.st_gid != identity or stat.S_IMODE(current.st_mode) != mode
                or not shared and current.st_uid != identity):
            raise SandboxError(f'Filesystem did not retain sandbox permissions: {logical}')

    fd = open_directory(path)
    try:
        with (registry / str(identity)).open('rb') as lease:
            fcntl.flock(lease, fcntl.LOCK_EX)
            root = os.fstat(fd)
            if shared and root.st_gid == identity and root.st_mode & 0o2070 == 0o2070:
                return
            if not shared and root.st_uid == identity and root.st_mode & 0o777 == 0o700:
                return
            _visit_tree(fd, path, update, children_first=True)
    finally:
        os.close(fd)


def workspace_access(path, uid, registry):
    for parent in (path.parent.parent, path.parent):
        fd = open_directory(parent)
        try:
            if os.fstat(fd).st_uid != 0:
                raise SandboxError(f'Expected a manager-owned workspace parent: {parent}')
            target = f'/proc/self/fd/{fd}'
            if parent == path.parent:
                os.chown(target, -1, uid)
                os.chmod(target, 0o710)
            else:
                os.chmod(target, 0o711)
        finally:
            os.close(fd)
    prepare_managed(path, uid, registry)
    traverse(path, uid)


def grant(path: Path, uid: int, *, writable: bool, exclude=(), shared_gid=None) -> None:
    """Use existing permissions where possible, preserving other users' ownership."""
    traverse(path.parent, uid, shared_gid)

    def apply(fd, logical, info):
        is_dir = stat.S_ISDIR(info.st_mode)
        execute = is_dir or bool(info.st_mode & 0o111)
        bits = 4 | (2 if writable else 0) | int(execute)
        if _mode_allows(fd, uid, bits, shared_gid):
            return
        permissions = 'r' + ('w' if writable else '-') + ('x' if execute else '-')
        _acl(fd, uid, permissions)
        if is_dir:
            _acl(fd, uid, 'rwx' if writable else 'r-x', default=True)

    fd = _open(path)
    try:
        _visit_tree(fd, path, apply, exclude)
    finally:
        os.close(fd)


def ensure_base(root: Path) -> None:
    with (root.parent / '.cow.lock').open('a') as lock:
        fcntl.flock(lock, fcntl.LOCK_EX)
        marker = root.parent / '.overlay-ready'
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
