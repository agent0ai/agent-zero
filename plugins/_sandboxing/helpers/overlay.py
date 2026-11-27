"""Pinned host-side view of the same upper, immutable base and whiteouts as PRoot."""
from contextlib import ExitStack, contextmanager
from dataclasses import dataclass
import os
import stat

from plugins._sandboxing.helpers.storage import open_directory


@dataclass(frozen=True)
class Entry:
    upper: int | None
    lower: int | None = None
    markers: int | None = None

    @property
    def fd(self):
        return self.upper if self.upper is not None else self.lower

    @contextmanager
    def child(self, name):
        if not name or '/' in name or name in {'.', '..'}:
            raise ValueError("Invalid sandbox file path.")
        if not stat.S_ISDIR(os.fstat(self.fd).st_mode):
            raise NotADirectoryError(name)
        with ExitStack() as stack:
            def pin(parent):
                if parent is None:
                    return None
                try:
                    fd = os.open(name, os.O_PATH | os.O_NOFOLLOW, dir_fd=parent)
                except FileNotFoundError:
                    return None
                stack.callback(os.close, fd)
                return fd

            upper = pin(self.upper)
            marker = pin(self.markers)
            masked = marker is not None and os.fstat(marker).st_mode & stat.S_ISVTX
            lower = None if masked else pin(self.lower)
            if upper is None and lower is None:
                raise FileNotFoundError(name)
            if upper is not None and lower is not None:
                if not all(stat.S_ISDIR(os.fstat(fd).st_mode) for fd in (upper, lower)):
                    lower = None
            yield Entry(upper, lower, marker)

    @contextmanager
    def at(self, parts):
        with ExitStack() as stack:
            node = self
            for part in parts:
                node = stack.enter_context(node.child(part))
            yield node

    def names(self):
        names = set()
        for fd in (self.upper, self.lower):
            if fd is not None:
                directory = os.open('.', os.O_RDONLY | os.O_DIRECTORY, dir_fd=fd)
                try:
                    names.update(os.listdir(directory))
                finally:
                    os.close(directory)
        return names


@contextmanager
def open_root(upper, lower=None, markers=None):
    with ExitStack() as stack:
        def pin(path):
            if path is None:
                return None
            fd = open_directory(path)
            stack.callback(os.close, fd)
            return fd
        yield Entry(pin(upper), pin(lower), pin(markers))
