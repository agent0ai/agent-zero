"""Create a new binding with its initial group. Never change an existing binding."""
import os
from pathlib import Path
import shutil
import stat
import sys
import errno
import tempfile


def copy_seed(source, target):
    target.mkdir(mode=0o770)
    for name in os.listdir(source):
        dest = target / name
        mode = os.stat(name, dir_fd=source, follow_symlinks=False).st_mode
        if stat.S_ISLNK(mode):
            dest.symlink_to(os.readlink(name, dir_fd=source))
        elif stat.S_ISDIR(mode):
            child = os.open(name, os.O_DIRECTORY | os.O_NOFOLLOW, dir_fd=source)
            try:
                copy_seed(child, dest)
            finally:
                os.close(child)
        elif stat.S_ISREG(mode):
            fd = os.open(name, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK, dir_fd=source)
            with os.fdopen(fd, 'rb') as src:
                mode = os.fstat(fd).st_mode
                if not stat.S_ISREG(mode):
                    raise OSError(f'Unsupported seed entry: {name}')
                permissions = 0o770 if mode & 0o111 else 0o660
                out = os.open(dest, os.O_CREAT | os.O_EXCL | os.O_WRONLY, permissions)
                with os.fdopen(out, 'wb') as stream:
                    shutil.copyfileobj(src, stream)
        else:
            raise OSError(f'Unsupported seed entry: {name}')


def create(path, seed):
    from helpers.file_transfers import rename_no_replace
    from plugins._sandboxing.helpers.storage import _open, open_directory

    parent = _open(path.parent, create_dirs=True)
    try:
        target = Path('/proc/self/fd') / str(parent) / path.name
        if seed is not None:
            fd = open_directory(seed)
            try:
                source = os.open('.', os.O_RDONLY | os.O_DIRECTORY, dir_fd=fd)
                try:
                    with os.scandir(source) as entries:
                        populated = next(entries, None) is not None
                    if populated:
                        with tempfile.TemporaryDirectory(dir=target.parent) as stage:
                            tree = Path(stage) / 'binding'
                            copy_seed(source, tree)
                            rename_no_replace(tree, target)
                        return
                finally:
                    os.close(source)
            finally:
                os.close(fd)
        target.mkdir(mode=0o770)
    finally:
        os.close(parent)


if __name__ == '__main__':
    sys.path.insert(0, str(Path(__file__).resolve().parents[3]))
    try:
        create(Path(sys.argv[1]), Path(sys.argv[2]) if len(sys.argv) > 2 else None)
    except FileExistsError:
        sys.exit(errno.EEXIST)
    except OSError as exc:
        sys.exit(str(exc))
