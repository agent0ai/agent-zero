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
import subprocess
import sys

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


def prepare_workspace(path: Path, seed: Path | None = None, *, gid: int | None = None, mode=0o770) -> bool:
    """Publish once, with creation credentials local to a child process."""
    try:
        os.close(open_directory(path))
        return False
    except FileNotFoundError:
        pass
    script = Path(__file__).with_name('binding_directory.py')
    command = [sys.executable, '-I', str(script), str(path), oct(mode)]
    if seed is not None:
        command.append(str(seed))
    result = subprocess.run(command, group=gid, umask=0, capture_output=True, text=True)
    if result.returncode not in (0, errno.EEXIST):
        raise OSError(f'Cannot create sandbox directory {path}: {result.stderr.strip()}')
    os.close(open_directory(path))
    return result.returncode == 0


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
                    os.mkdir(part, mode=0o755, dir_fd=fd)
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


def _mode_allows(fd, uid, bits):
    info = os.fstat(fd)
    if info.st_uid == uid:
        return (info.st_mode >> 6) & bits == bits
    if _has_acl(f'/proc/self/fd/{fd}'):
        return False
    shift = 3 if info.st_gid == uid else 0
    return (info.st_mode >> shift) & bits == bits


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
    principal = f'user:{uid}:'
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


def traverse(path: Path, uid: int, *, root: Path) -> None:
    for parent in (*reversed(path.parents), path):
        if parent != root and root not in parent.parents:
            continue
        fd = _open(parent)
        try:
            if not _mode_allows(fd, uid, 1):
                _acl(fd, uid, '--x', augment=True)
        finally:
            os.close(fd)


def _visit_tree(root_fd, path, apply, *, children_first=False):
    def visit(fd, logical):
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


def _legacy_grants(fd, users, group):
    """Only convert ACLs whose group mode already equals the old guests' effective access."""
    lines = subprocess.check_output(
        ['getfacl', '-cnEp', f'/proc/self/fd/{fd}'], pass_fds=(fd,), text=True,
    ).splitlines()
    access = dict(line.rsplit(':', 1) for line in lines if line and not line.startswith('default:'))
    mask = access.get('mask:')
    named = {who for who in access if not who.endswith(':')}
    if not mask or named.isdisjoint(users) or named - users - {group}:
        return False
    effective = set(mask) - {'-'}
    if any(not effective.issubset(access[who]) for who in named):
        return False

    defaults = {line.removeprefix('default:') for line in lines if line.startswith('default:')}
    if not defaults:
        return True
    # The old manager seeded defaults from the directory mode after granting guest access.
    stock = {'user::rwx', 'group::rwx', 'mask::rwx', f"other::{access['other:']}"}
    stock.update(f'{who}:rwx' for who in named)
    return access['user:'] == 'rwx' and defaults == stock


def migrate_shared_group(path: Path, gid: int, registry: Path, *, recursive=False) -> None:
    """Convert traversal on the common parent or read/write access in the built-in exchange."""
    fd = open_directory(path)
    try:
        root = f'/proc/self/fd/{fd}'
        if not _has_acl(root):
            return
        with (registry / str(gid)).open('rb') as lease:
            fcntl.flock(lease, fcntl.LOCK_EX)
            users = {f'user:{p.name}' for p in registry.iterdir() if p.name.isdecimal()}
            group = f'group:{gid}'
            required = 0o070 if recursive else 0o010
            info = os.fstat(fd)
            if info.st_gid and f'user:{info.st_gid}' not in users:
                return
            if info.st_mode & 0o070 != required or not _legacy_grants(fd, users, group):
                return

            def convert(child, _path, info):
                target = f'/proc/self/fd/{child}'
                if info.st_gid not in (0, gid) and f'user:{info.st_gid}' not in users:
                    return
                if not info.st_mode & 0o070:
                    return
                if stat.S_ISREG(info.st_mode) and (info.st_nlink > 1 or info.st_mode & 0o6000
                                                   or 'security.capability' in os.listxattr(target)):
                    return
                if child != fd and (not _has_acl(target) or not _legacy_grants(child, users, group)):
                    return
                os.chown(target, -1, gid)
                if _has_acl(target, 'default'):
                    os.removexattr(target, 'system.posix_acl_default')
                # Linux keeps the ACL mask as the group mode when removing the access ACL.
                os.removexattr(target, 'system.posix_acl_access')

            if recursive:
                _visit_tree(fd, path, convert, children_first=True)
            else:
                convert(fd, path, info)
    finally:
        os.close(fd)


def grant_worker_input(path: Path, uid: int, *, root: Path) -> None:
    """Private worker requests are replaced by the manager while the guest runs."""
    traverse(path.parent, uid, root=root)

    def apply(fd, logical, info):
        is_dir = stat.S_ISDIR(info.st_mode)
        execute = is_dir or bool(info.st_mode & 0o111)
        bits = 4 | int(execute)
        if _mode_allows(fd, uid, bits):
            return
        permissions = 'r-x' if execute else 'r--'
        _acl(fd, uid, permissions)
        if is_dir:
            _acl(fd, uid, 'r-x', default=True)

    fd = _open(path)
    try:
        _visit_tree(fd, path, apply)
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
