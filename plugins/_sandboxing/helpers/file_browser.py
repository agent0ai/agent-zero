"""Read-only Files connections for persistent sandbox filesystems."""
import hashlib
import os
import stat
from contextlib import contextmanager

from helpers.file_connections import PERMISSIONS, path_for
from helpers.file_transfers import copy_stream
from plugins._sandboxing.helpers.runtime import get_manager


class SandboxFilesProvider:
    id = "sandbox"
    title = "Sandbox files"
    plugin_name = "_sandboxing"
    fields = []
    permissions = ("browse", "download")

    def connection(self, manager, info):
        if info.service or not info.disk_backed or info.status == "creating":
            return None
        identity = "\0".join((manager.config.instance_id, info.name, info.created_at))
        return {
            "id": hashlib.sha256(identity.encode()).hexdigest()[:32],
            "provider": self.id,
            "name": f"Sandbox — {info.name}",
            "managed": True,
            "permissions": {permission: permission in self.permissions for permission in PERMISSIONS},
            "_name": info.name,
            "_created_at": info.created_at,
        }

    def browse_path(self, manager, info):
        item = self.connection(manager, info)
        return path_for(item) if item else ""

    def connections(self):
        manager = get_manager()
        return {
            item["id"]: item for info in manager.list()
            if (item := self.connection(manager, info)) is not None
        }

    @contextmanager
    def open(self, item, data_dir):
        with get_manager().open_browse_root(item["_name"], item["_created_at"]) as fd:
            yield SandboxFiles(fd)


class SandboxFiles:
    def __init__(self, root_fd):
        self.root_fd = root_fd

    @contextmanager
    def _entry(self, relative):
        parts = relative.split("/") if relative else []
        if any(part in {"", ".", ".."} for part in parts):
            raise ValueError("Invalid sandbox file path.")
        fd = os.dup(self.root_fd)
        try:
            for index, part in enumerate(parts):
                flags = os.O_PATH | os.O_NOFOLLOW
                if index < len(parts) - 1:
                    flags |= os.O_DIRECTORY
                next_fd = os.open(part, flags, dir_fd=fd)
                os.close(fd)
                fd = next_fd
            yield fd
        finally:
            os.close(fd)

    @staticmethod
    def _info(name, info):
        return {"name": name, "is_dir": stat.S_ISDIR(info.st_mode), "size": info.st_size,
                "modified": info.st_mtime}

    def list(self, relative):
        entries = []
        with self._entry(relative) as fd:
            directory = os.open(".", os.O_RDONLY | os.O_DIRECTORY, dir_fd=fd)
            try:
                with os.scandir(directory) as children:
                    for child in children:
                        try:
                            info = child.stat(follow_symlinks=False)
                        except FileNotFoundError:
                            continue
                        if stat.S_ISREG(info.st_mode) or stat.S_ISDIR(info.st_mode):
                            entries.append(self._info(child.name, info))
            finally:
                os.close(directory)
        return entries

    def stat(self, relative):
        with self._entry(relative) as fd:
            info = os.fstat(fd)
            if not (stat.S_ISREG(info.st_mode) or stat.S_ISDIR(info.st_mode)):
                raise ValueError("Choose a regular file or directory.")
            return self._info(relative.rsplit("/", 1)[-1], info)

    def read(self, relative, destination, limit):
        with self._entry(relative) as fd:
            if not stat.S_ISREG(os.fstat(fd).st_mode):
                raise ValueError("Choose a regular file.")
            # Reopen the verified inode so a concurrent rename cannot redirect the read.
            with open(f"/proc/self/fd/{fd}", "rb") as source:
                return copy_stream(source, destination, limit)["sha256"]
