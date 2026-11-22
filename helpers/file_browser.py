import os
import tempfile
from pathlib import Path
import shutil
import base64
import io
import stat
from helpers.file_transfers import write_stream_atomic, FileLimitExceeded, rename_no_replace
from typing import Dict, List, Tuple
from helpers.security import safe_filename
from datetime import datetime

from helpers import files
from helpers.localization import Localization
from helpers.print_style import PrintStyle


def copy_regular(source, destination):
    flags = os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0) | getattr(os, "O_NONBLOCK", 0)
    descriptor = os.open(source, flags)
    with os.fdopen(descriptor, "rb") as stream:
        if not stat.S_ISREG(os.fstat(stream.fileno()).st_mode):
            raise ValueError("Only regular files, directories and symbolic links can be copied.")
        with open(destination, "xb") as output:
            shutil.copyfileobj(stream, output)
    shutil.copystat(source, destination, follow_symlinks=False)


class FileBrowser:
    ALLOWED_EXTENSIONS = {
        'image': {'jpg', 'jpeg', 'png', 'bmp'},
        'code': {'py', 'js', 'sh', 'html', 'css'},
        'document': {'md', 'pdf', 'txt', 'csv', 'json'}
    }

    @classmethod
    def max_file_bytes(cls):
        from helpers.settings import get_settings
        return get_settings()["file_browser_max_transfer_size_mb"] * 1024 * 1024

    @classmethod
    def max_text_bytes(cls):
        from helpers.settings import get_settings
        return get_settings()["file_browser_max_text_size_mb"] * 1024 * 1024

    @classmethod
    def max_extract_bytes(cls):
        from helpers.settings import get_settings
        return get_settings()["file_browser_max_extract_size_mb"] * 1024 * 1024

    @classmethod
    def max_archive_entries(cls):
        from helpers.settings import get_settings
        return get_settings()["file_browser_max_archive_entries"]

    @classmethod
    def limits(cls):
        return {"max_file_bytes": cls.max_file_bytes(), "max_text_bytes": cls.max_text_bytes(),
                "max_extract_bytes": cls.max_extract_bytes(), "max_archive_entries": cls.max_archive_entries()}

    @classmethod
    def decode_text(cls, data: bytes) -> str:
        limit = cls.max_text_bytes()
        if len(data) > limit:
            raise ValueError(f"Text files are limited to {limit / (1024 * 1024):g} MiB.")
        if files.is_probably_binary_bytes(data):
            raise ValueError("Binary file detected; editing is not supported")
        try:
            return data.decode("utf-8")
        except UnicodeDecodeError as error:
            raise ValueError("Unable to decode file as UTF-8; editing is not supported") from error

    @classmethod
    def text_bytes(cls, content: str) -> bytes:
        data = content.encode("utf-8")
        cls.decode_text(data)
        return data

    @classmethod
    def read_text(cls, path):
        descriptor = os.open(path, os.O_RDONLY | getattr(os, "O_NONBLOCK", 0))
        with os.fdopen(descriptor, "rb") as stream:
            if not stat.S_ISREG(os.fstat(stream.fileno()).st_mode):
                raise ValueError("Choose a regular text file.")
            return cls.decode_text(stream.read(cls.max_text_bytes() + 1))

    @classmethod
    def encode_upload(cls, storage):
        from helpers.file_transfers import copy_stream
        output = io.BytesIO()
        copy_stream(storage.stream, output, cls.max_file_bytes())
        return base64.b64encode(output.getvalue()).decode("ascii")

    def __init__(self):
        self.base_dir = Path("/")

    def save_file_b64(self, current_path: str, filename: str, base64_content: str):
        try:
            filename = safe_filename(filename)
            if not filename:
                raise ValueError("Invalid filename")
            limit = self.max_file_bytes()
            if len(base64_content) > ((limit + 2) // 3) * 4:
                raise FileLimitExceeded(limit)
            # Resolve the target directory path
            target_file = (self.base_dir / current_path / filename).resolve()
            if not str(target_file).startswith(str(self.base_dir)):
                raise ValueError("Invalid target directory")

            os.makedirs(target_file.parent, exist_ok=True)
            content = base64.b64decode(base64_content, validate=True)
            write_stream_atomic(io.BytesIO(content), target_file, max_bytes=limit)
            return True
        except FileLimitExceeded:
            raise
        except Exception as e:
            PrintStyle.error(f"Error saving file {filename}: {e}")
            return False

    def save_files(self, files: List, current_path: str = "") -> Tuple[List[str], List[str]]:
        """Save uploaded files and return successful and failed filenames"""
        successful = []
        failed = []
        from helpers import file_connections
        if file_connections.is_remote(current_path):
            import posixpath
            for file in files:
                filename = safe_filename(file.filename)
                if not filename:
                    raise ValueError("Invalid filename")
                file_connections.write_from(posixpath.join(current_path, filename), file.stream)
                successful.append(filename)
            return successful, failed

        try:
            # Resolve the target directory path
            target_dir = (self.base_dir / current_path).resolve()
            if not str(target_dir).startswith(str(self.base_dir)):
                raise ValueError("Invalid target directory")

            os.makedirs(target_dir, exist_ok=True)

            for file in files:
                try:
                    if file:
                        filename = safe_filename(file.filename)
                        if not filename:
                            raise ValueError("Invalid filename")
                        file_path = target_dir / filename

                        write_stream_atomic(file.stream, file_path, max_bytes=self.max_file_bytes())
                        successful.append(filename)
                    else:
                        failed.append(file.filename)
                except FileLimitExceeded:
                    raise
                except Exception as e:
                    PrintStyle.error(f"Error saving file {file.filename}: {e}")
                    failed.append(file.filename)

            return successful, failed

        except FileLimitExceeded:
            raise
        except Exception as e:
            PrintStyle.error(f"Error in save_files: {e}")
            return successful, failed

    def upload_tree(self, uploads, directory, names, folders):
        """Stage a device drop privately, then publish complete top-level items."""
        from helpers.file_transfers import copy_stream
        from helpers import file_connections

        if file_connections.is_remote(directory):
            raise ValueError("This connection supports individual file uploads.")
        if not isinstance(names, list) or not isinstance(folders, list) or len(names) != len(uploads):
            raise ValueError("Invalid upload manifest")
        if not names and not folders:
            raise ValueError("No items to upload")
        target = (self.base_dir / directory).resolve()
        if not target.is_dir() or not target.is_relative_to(self.base_dir.resolve()):
            raise ValueError("Choose a valid destination directory")

        original_prefixes = {}

        def validate(relative):
            if not isinstance(relative, str):
                raise ValueError("Invalid upload path")
            parts = relative.split("/")
            if any(not part or part in (".", "..") or "\\" in part or "\x00" in part for part in parts):
                raise ValueError("Invalid upload path")
            clean = [safe_filename(part) for part in parts]
            if any(not part for part in clean):
                raise ValueError("Invalid upload name")
            for depth in range(1, len(parts) + 1):
                prefix = tuple(clean[:depth])
                original = tuple(parts[:depth])
                if original_prefixes.setdefault(prefix, original) != original:
                    raise ValueError("Duplicate upload name after cleaning")
            return Path(*clean)

        file_paths = [validate(name) for name in names]
        folder_paths = [validate(name) for name in folders]
        if len(set(file_paths + folder_paths)) != len(file_paths) + len(folder_paths):
            raise ValueError("Duplicate upload name")
        published, failed = [], []
        with tempfile.TemporaryDirectory(prefix=".a0-upload-", dir=target) as tmp:
            stage = Path(tmp)
            for path in folder_paths:
                (stage / path).mkdir(parents=True, exist_ok=True)
            for upload, path in zip(uploads, file_paths):
                destination = stage / path
                destination.parent.mkdir(parents=True, exist_ok=True)
                with destination.open("xb") as output:
                    copy_stream(upload.stream, output, self.max_file_bytes())
            for item in sorted(stage.iterdir()):
                suffix = "" if item.is_dir() else item.suffix
                stem = item.name.removesuffix(suffix)
                name = item.name
                counter = 1
                while True:
                    try:
                        rename_no_replace(item, target / name)
                        published.append(name)
                        break
                    except FileExistsError:
                        name = f"{stem} ({counter}){suffix}"
                        counter += 1
                    except OSError as error:
                        failed.append({"name": item.name, "error": str(error)})
                        break
        return published, failed

    def _entry_path(self, file_path: str) -> Path:
        if not file_path or not str(file_path).strip():
            raise ValueError("File path is required")
        requested = self.base_dir / file_path
        if requested.name in ("", ".", ".."):
            raise ValueError("Choose a file or folder, not the filesystem root")
        entry = requested.parent.resolve() / requested.name
        base = self.base_dir.resolve()
        if entry == base or not entry.is_relative_to(base):
            raise ValueError("Invalid file path")
        return entry

    def delete_file(self, file_path: str) -> bool:
        """Delete a file or empty directory"""
        try:
            full_path = self._entry_path(file_path)
            if full_path.exists() or full_path.is_symlink():
                if full_path.is_symlink() or full_path.is_file():
                    os.remove(full_path)
                elif os.path.isdir(full_path):
                    shutil.rmtree(full_path)
                return True

            return False

        except Exception as e:
            PrintStyle.error(f"Error deleting {file_path}: {e}")
            return False

    def rename_item(self, file_path: str, new_name: str) -> bool:
        try:
            if not new_name or new_name in {".", ".."}:
                raise ValueError("Invalid new name")
            if "/" in new_name or "\\" in new_name:
                raise ValueError("New name cannot include path separators")

            full_path = self._entry_path(file_path)
            if not full_path.exists() and not full_path.is_symlink():
                raise FileNotFoundError("File or folder not found")

            new_path = full_path.with_name(new_name)
            if not str(new_path).startswith(str(self.base_dir)):
                raise ValueError("Invalid target path")
            if full_path == new_path:
                return True
            if new_path.exists() or new_path.is_symlink():
                raise FileExistsError("Target already exists")

            rename_no_replace(full_path, new_path)
            return True
        except Exception as e:
            PrintStyle.error(f"Error renaming {file_path}: {e}")
            raise

    def move_items(self, file_paths: List[str], destination_path: str) -> List[str]:
        return self.transfer_items(file_paths, destination_path, copy=False)

    def transfer_items(self, file_paths: List[str], destination_path: str, *, copy: bool) -> List[str]:
        if not file_paths:
            raise ValueError("No items selected")

        base_dir = self.base_dir.resolve()
        destination = (self.base_dir / destination_path).resolve()
        if not destination.is_relative_to(base_dir):
            raise ValueError("Invalid destination path")
        if not destination.is_dir():
            raise NotADirectoryError("Destination folder not found")

        moves: List[Tuple[Path, Path]] = []
        targets: set[Path] = set()
        for file_path in dict.fromkeys(file_paths):
            source = self._entry_path(file_path)
            if not source.exists() and not source.is_symlink():
                raise FileNotFoundError(f"Item not found: {source.name}")
            if source == destination:
                raise ValueError("A folder cannot be moved into itself")
            if (
                source.is_dir()
                and not source.is_symlink()
                and destination.is_relative_to(source)
            ):
                raise ValueError("A folder cannot be moved into itself")

            target = destination / source.name
            if copy and target == source:
                suffix = "" if source.is_dir() and not source.is_symlink() else source.suffix
                stem = source.name.removesuffix(suffix)
                number = 1
                while target in targets or os.path.lexists(target):
                    label = "copy" if number == 1 else f"copy {number}"
                    target = destination / f"{stem} ({label}){suffix}"
                    number += 1
            if target == source:
                raise ValueError(f"{source.name} is already in this folder")
            if target.exists() or target.is_symlink():
                raise FileExistsError(
                    f'An item named "{source.name}" already exists'
                )
            if target in targets:
                raise FileExistsError(f'Multiple items are named "{source.name}"')
            targets.add(target)
            moves.append((source, target))

        if copy:
            # Stage the whole selection before publishing any item. Symlinks stay links.
            with tempfile.TemporaryDirectory(prefix=".a0-copy-", dir=destination) as tmp:
                staged = Path(tmp)
                for index, (source, _) in enumerate(moves):
                    path = staged / str(index)
                    if source.is_symlink():
                        path.symlink_to(os.readlink(source))
                    elif source.is_dir():
                        shutil.copytree(source, path, symlinks=True, copy_function=copy_regular)
                    else:
                        copy_regular(source, path)
                moves = [(staged / str(index), target) for index, (_, target) in enumerate(moves)]
                return self._publish_transfers(moves)
        return self._publish_transfers(moves)

    @staticmethod
    def _publish_transfers(moves: List[Tuple[Path, Path]]) -> List[str]:
        moved: List[Tuple[Path, Path]] = []
        try:
            for source, target in moves:
                rename_no_replace(source, target)
                moved.append((source, target))
        except Exception:
            for source, target in reversed(moved):
                try:
                    rename_no_replace(target, source)
                except Exception as rollback_error:
                    PrintStyle.error(f"Error restoring {source}: {rollback_error}")
            raise

        return [str(target) for _, target in moved]

    def create_folder(self, parent_path: str, folder_name: str) -> bool:
        try:
            if not folder_name or folder_name in {".", ".."}:
                raise ValueError("Invalid folder name")
            if "/" in folder_name or "\\" in folder_name:
                raise ValueError("Folder name cannot include path separators")

            parent_full = (self.base_dir / parent_path).resolve()
            if not str(parent_full).startswith(str(self.base_dir)):
                raise ValueError("Invalid parent path")

            target_dir = (parent_full / folder_name).resolve()
            if not str(target_dir).startswith(str(self.base_dir)):
                raise ValueError("Invalid target path")
            if target_dir.exists():
                raise FileExistsError("Folder already exists")

            os.makedirs(target_dir, exist_ok=False)
            return True
        except Exception as e:
            PrintStyle.error(f"Error creating folder {folder_name}: {e}")
            raise

    def save_text_file(self, file_path: str, content: str) -> bool:
        try:
            if not isinstance(content, str):
                raise ValueError("Content must be a string")
            data = self.text_bytes(content)

            full_path = (self.base_dir / file_path).resolve()
            if not str(full_path).startswith(str(self.base_dir)):
                raise ValueError("Invalid path")
            if full_path.exists() and full_path.is_dir():
                raise ValueError("Target is a directory")

            os.makedirs(full_path.parent, exist_ok=True)
            write_stream_atomic(io.BytesIO(data), full_path)
            return True
        except Exception as e:
            PrintStyle.error(f"Error saving file {file_path}: {e}")
            raise

    def _get_file_extension(self, filename: str) -> str:
        return filename.rsplit('.', 1)[1].lower() if '.' in filename else ''

    def get_files(self, current_path: str = "") -> Dict:
        try:
            directory = (self.base_dir / current_path).resolve()
            if not directory.is_relative_to(self.base_dir.resolve()):
                raise ValueError("Invalid path")
            entries = []
            timezone = Localization.get().get_tzinfo()
            with os.scandir(directory) as listing:
                for item in listing:
                    link = item.is_symlink()
                    try:
                        info = item.stat()
                    except OSError:
                        if not link:
                            continue
                        try:
                            info = item.stat(follow_symlinks=False)
                        except FileNotFoundError:
                            continue
                    is_dir = stat.S_ISDIR(info.st_mode)
                    if not (is_dir or link or stat.S_ISREG(info.st_mode)):
                        continue
                    entry = {
                        "name": item.name,
                        "mode": stat.filemode(info.st_mode),
                        "path": str(Path(item.path).relative_to(self.base_dir)),
                        "type": "folder" if is_dir else self._get_file_type(item.name),
                        "size": 0 if is_dir else info.st_size,
                        "is_dir": is_dir,
                        "modified": datetime.fromtimestamp(info.st_mtime, tz=timezone).isoformat(),
                    }
                    if link:
                        try:
                            entry.update(is_symlink=True, symlink_target=os.readlink(item.path))
                        except FileNotFoundError:
                            continue
                    entries.append(entry)
                    if len(entries) >= 10000:
                        break
            entries.sort(key=lambda item: (not item["is_dir"], item["name"]))
            parent = str(Path(current_path).parent) if directory != self.base_dir else ""
            return {"entries": entries, "current_path": current_path, "parent_path": parent}
        except (OSError, ValueError) as error:
            message = "Directory not found" if isinstance(error, FileNotFoundError) else str(error)
            return {"entries": [], "current_path": current_path, "parent_path": "", "error": message}

    def get_full_path(self, file_path: str, allow_dir: bool = False) -> str:
        """Get full file path if it exists and is within base_dir"""
        full_path = files.get_abs_path(self.base_dir, file_path)
        if not files.exists(full_path):
            raise ValueError(f"File {file_path} not found")
        return full_path

    def _get_file_type(self, filename: str) -> str:
        ext = self._get_file_extension(filename)
        for file_type, extensions in self.ALLOWED_EXTENSIONS.items():
            if ext in extensions:
                return file_type
        return 'unknown'


def prepare_files_download(paths, current_path=""):
    """Resolve the Files operation's policy before any transport adapter runs."""
    import posixpath
    import tempfile
    from helpers import file_connections
    from helpers.file_archives import normalize_paths, create_selected_zip, selected_archive_name
    from helpers.file_transfers import copy_stream
    paths = normalize_paths(paths)
    if not paths:
        raise ValueError("No files selected.")
    limit = FileBrowser.max_file_bytes()
    remote = [file_connections.is_remote(path) for path in paths]
    if any(remote) and not all(remote):
        raise ValueError("Select files from the same filesystem.")
    temporary = False
    if all(remote):
        single = False
        if len(paths) == 1:
            pid, cid, relative = file_connections.split(paths[0])
            provider, item = file_connections.get_connection(pid, cid)
            file_connections.require(item, "download")
            with file_connections.filesystem(provider, item) as fs:
                single = not fs.stat(relative)["is_dir"]
        handle = tempfile.NamedTemporaryFile(prefix="files-download-", delete=False)
        path = handle.name
        try:
            with handle:
                if single:
                    file_connections.read_into(paths[0], handle, limit=limit)
                else:
                    with file_connections.archive(paths) as archive:
                        copy_stream(archive, handle, limit)
        except BaseException:
            Path(path).unlink(missing_ok=True)
            raise
        name = posixpath.basename(paths[0]) if single else (
            f"{posixpath.basename(paths[0])}.zip" if len(paths) == 1 else selected_archive_name(len(paths))
        )
        temporary = True
    elif len(paths) == 1 and Path(paths[0]).is_file():
        import stat
        source_path = Path(paths[0]).resolve()
        name = source_path.name
        handle = tempfile.NamedTemporaryFile(prefix="files-download-", delete=False)
        path = handle.name
        try:
            with handle:
                descriptor = os.open(source_path, os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0) | getattr(os, "O_NONBLOCK", 0))
                with os.fdopen(descriptor, "rb") as source:
                    before = os.fstat(source.fileno())
                    if not stat.S_ISREG(before.st_mode):
                        raise ValueError("Choose a regular file.")
                    copy_stream(source, handle, limit)
                    after = os.fstat(source.fileno())
                    if (before.st_size, before.st_mtime_ns) != (after.st_size, after.st_mtime_ns):
                        raise ValueError("The file changed during download preparation. Try again.")
        except BaseException:
            Path(path).unlink(missing_ok=True)
            raise
        temporary = True
    else:
        path = create_selected_zip(paths, current_path, limit, FileBrowser.max_archive_entries())
        name = (
            f"{Path(paths[0]).name}.zip" if len(paths) == 1
            else selected_archive_name(len(paths))
        )
        temporary = True
    return {"file_source": path, "download_name": name, "max_bytes": limit, "delete_after": temporary}


def remove_download_temporary(path):
    Path(path).unlink(missing_ok=True)


def register_files_download(response, paths):
    from helpers.file_archives import normalize_paths
    paths = normalize_paths(paths)
    from helpers.file_transfers import prepare_download_response
    from helpers import file_connections
    def authorize():
        try:
            for path in paths:
                if file_connections.is_remote(path):
                    pid, cid, _ = file_connections.split(path)
                    file_connections.require(file_connections.get_connection(pid, cid)[1], "download")
        except (ValueError, PermissionError):
            raise PermissionError("The file connection is no longer available for download.") from None
    return prepare_download_response(response, authorize)


async def prepare_files_response(paths, current_path=""):
    import asyncio
    import threading
    from helpers.file_transfers import stream_file_download
    state = {"cancelled": False, "response": None}
    lock = threading.Lock()
    def prepare():
        download = prepare_files_download(paths, current_path)
        response = stream_file_download(**download)
        with lock:
            state["response"] = response
            if state["cancelled"]:
                response.close()
        return response, download["download_name"]
    task = asyncio.create_task(asyncio.to_thread(prepare))
    try:
        return await asyncio.shield(task)
    except asyncio.CancelledError:
        with lock:
            state["cancelled"] = True
            if state["response"] is not None:
                state["response"].close()
        task.add_done_callback(lambda done: None if done.cancelled() else done.exception())
        raise
