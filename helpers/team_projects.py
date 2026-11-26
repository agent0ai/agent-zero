"""Authorized, revision-checked access to native team project data."""

from collections import defaultdict
from contextlib import ExitStack, contextmanager
import ctypes
import errno
import hashlib
from io import BytesIO
import os
from pathlib import Path, PurePosixPath
import re
import shutil
import stat
from threading import RLock

from helpers import projects, team_access
from helpers.file_browser import FileBrowser
from helpers.file_transfers import copy_stream, stream_file_download, write_stream_atomic
from helpers.team_store import ADMIN_ACTOR_ID, get_store


EDITABLE_FIELDS = {"title": 200, "description": 20_000, "instructions": 80_000, "color": 9}
AREAS = {
    "workspace": (),
    "instructions": (projects.PROJECT_META_DIR, projects.PROJECT_INSTRUCTIONS_DIR),
    "knowledge": (projects.PROJECT_META_DIR, projects.PROJECT_KNOWLEDGE_DIR),
}
_locks = defaultdict(RLock)


class RevisionConflict(ValueError):
    pass


@contextmanager
def project_lock(name: str, scope: team_access.MemberScope | None):
    """Resolve the binding again while serializing managed changes to one project."""
    project_id = team_access.bound_project_id(name)
    if not project_id or (scope is not None and scope.project_ids.get(name) != project_id):
        raise PermissionError("Project access denied.")
    with _locks[project_id]:
        if team_access.bound_project_id(name) != project_id:
            raise PermissionError("Project access denied.")
        if scope is not None and scope.account_id != ADMIN_ACTOR_ID and get_store().memberships(scope.account_id).get(name) != project_id:
            raise PermissionError("Project access denied.")
        yield project_id


@contextmanager
def activity(action: str, actor_id: str, project_id: str, *, context_id: str | None = None):
    store = get_store()
    event_id = store.start_project_activity(action, actor_id, project_id, context_id=context_id)
    result = "failed"
    try:
        yield
        result = "ok"
    except RevisionConflict:
        result = "conflict"
        raise
    finally:
        store.finish_project_activity(event_id, result)


def header_revision(name: str) -> str:
    header = Path(projects.get_project_meta(name, projects.PROJECT_HEADER_FILE))
    return hashlib.sha256(header.read_bytes()).hexdigest()


def require_revision(expected: object, current: str | None):
    if expected != current:
        raise RevisionConflict("This version has changed. Reload the latest version before saving your changes.")


def load_member_settings(name: str) -> dict:
    data = projects.load_basic_project_data(name)
    return {"name": name, "revision": header_revision(name), "include_agents_md": data["include_agents_md"],
            **{field: data[field] for field in EDITABLE_FIELDS}}


def save_member_settings(name: str, data: dict) -> dict:
    require_revision(data.get("revision"), header_revision(name))
    extras = data.keys() - (EDITABLE_FIELDS.keys() | {"name", "revision", "include_agents_md"})
    if extras:
        raise ValueError("Only ordinary project settings can be edited here.")
    header = projects.load_basic_project_data(name)
    for field, limit in EDITABLE_FIELDS.items():
        if field not in data:
            continue
        value = data[field]
        if not isinstance(value, str) or len(value) > limit:
            raise ValueError(f"Invalid {field}.")
        if field == "color" and value and not re.fullmatch(r"#[0-9A-Fa-f]{6}([0-9A-Fa-f]{2})?", value):
            raise ValueError("Choose a hex project color.")
        header[field] = value
    if "include_agents_md" in data:
        if not isinstance(data["include_agents_md"], bool):
            raise ValueError("Include AGENTS.md must be true or false.")
        header["include_agents_md"] = data["include_agents_md"]
    projects.save_project_header(name, header, atomic=True)
    projects.reactivate_project_in_chats(name)
    return load_member_settings(name)


def file_parts(path: object, *, allow_root: bool = False) -> tuple[str, ...]:
    if allow_root and path == "":
        return ()
    if not isinstance(path, str) or len(path) > 2048:
        raise ValueError("Choose a project-relative path.")
    parts = tuple(path.split("/"))
    if any(not part or part.startswith(".") or "\\" in part or any(ord(ch) < 32 for ch in part) for part in parts):
        raise ValueError("Choose a visible project-relative path.")
    return parts


@contextmanager
def open_directory(name: str, area: str, parts: tuple[str, ...]):
    if not isinstance(area, str) or area not in AREAS:
        raise ValueError("Unknown project file area.")
    root = Path(projects.get_projects_parent_folder()).resolve()
    flags = os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW
    with ExitStack() as stack:
        directory = os.open(root, flags)
        stack.callback(os.close, directory)
        for part in (name, *AREAS[area], *parts):
            directory = os.open(part, flags, dir_fd=directory)
            stack.callback(os.close, directory)
        yield directory


def open_file(directory: int, name: str):
    fd = os.open(name, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK, dir_fd=directory)
    metadata = os.fstat(fd)
    if not stat.S_ISREG(metadata.st_mode) or metadata.st_nlink != 1:
        os.close(fd)
        raise ValueError("Choose a regular project file.")
    return os.fdopen(fd, "rb")


def list_directory(directory: int, parts: tuple[str, ...]) -> list[dict]:
    entries = []
    for name in sorted(os.listdir(directory), key=str.casefold):
        try:
            file_parts(name)
            metadata = os.stat(name, dir_fd=directory, follow_symlinks=False)
        except (FileNotFoundError, ValueError):
            continue
        is_dir = stat.S_ISDIR(metadata.st_mode)
        if is_dir or (stat.S_ISREG(metadata.st_mode) and metadata.st_nlink == 1):
            entries.append({"name": name, "path": "/".join((*parts, name)), "directory": is_dir,
                            "size": None if is_dir else metadata.st_size})
    return entries


def prompt_variables(name: str) -> dict:
    header = projects.load_basic_project_data(name)
    chunks = [str(header["instructions"])[:80_000]]
    remaining = 24_000

    def append_instruction(directory, filename, label):
        nonlocal remaining
        if not remaining:
            return False
        try:
            with open_file(directory, filename) as stream:
                raw = stream.read(min(remaining, FileBrowser.max_text_bytes()))
            content = FileBrowser.decode_text(raw).strip()
        except (OSError, ValueError):
            return False
        remaining -= len(raw)
        if content:
            chunks.append(f"### {label}\n\n{content}")
        return True

    if header["include_agents_md"]:
        with open_directory(name, "workspace", ()) as root:
            for filename in projects.PROJECT_AGENTS_MD_FILES:
                if append_instruction(root, filename, filename):
                    break
    try:
        with open_directory(name, "instructions", ()) as root:
            for entry in list_directory(root, ()):
                filename = entry["name"]
                if not entry["directory"] and PurePosixPath(filename).suffix.lower() in {".md", ".txt", ".yaml", ".yml"}:
                    append_instruction(root, filename, f"instructions/{filename}")
    except (FileNotFoundError, NotADirectoryError):
        pass
    return {
        "project_name": header["title"], "project_description": header["description"],
        "project_instructions": "\n\n".join(part for part in chunks if part), "include_agents_md": header["include_agents_md"],
        "project_path": ".", "project_git_url": "",
    }


def _existing_revision(directory: int, name: str) -> str | None:
    try:
        stream = open_file(directory, name)
    except FileNotFoundError:
        return None
    with stream:
        return copy_stream(stream, None, FileBrowser.max_file_bytes())["sha256"]


def _entry_version(directory: int, name: str) -> tuple[str, bool]:
    entry_stat = os.stat(name, dir_fd=directory, follow_symlinks=False)
    if stat.S_ISDIR(entry_stat.st_mode):
        return f"directory:{entry_stat.st_ino}", True
    revision = _existing_revision(directory, name)
    if revision is None:
        raise FileNotFoundError(name)
    return revision, False


def _rename_entry(source_dir: int, source: str, target_dir: int, target: str) -> None:
    rename = ctypes.CDLL(None, use_errno=True).renameat2
    if rename(source_dir, os.fsencode(source), target_dir, os.fsencode(target), 1) != 0:
        code = ctypes.get_errno()
        if code == errno.EEXIST:
            raise RevisionConflict("A file or folder with this name already exists.")
        raise OSError(code, os.strerror(code))
    os.fsync(source_dir)
    os.fsync(target_dir)


def _save_stream(directory: int, name: str, stream, revision: object, limit: int) -> dict:
    require_revision(revision, _existing_revision(directory, name))
    # The descriptor pins the parent and prevents swaps of symlinked directories.
    target = Path(f"/proc/self/fd/{directory}") / name
    try:
        receipt = write_stream_atomic(stream, target, max_bytes=limit)
    except FileExistsError as error:
        raise RevisionConflict("A file with this name already exists. Reload the folder.") from error
    return {"revision": receipt["sha256"], "size": receipt["size"]}


def save_chat_attachments(name: str, run_id: str, uploads: list) -> list[dict[str, str]]:
    result = []
    with open_directory(name, "workspace", ()) as root:
        try:
            os.mkdir("attachments", 0o755, dir_fd=root)
        except FileExistsError:
            pass
    with open_directory(name, "workspace", ("attachments",)) as attachments:
        os.mkdir(run_id, 0o755, dir_fd=attachments)
        try:
            for parts, storage in uploads:
                parent = ("attachments", run_id)
                for folder in parts[:-1]:
                    with open_directory(name, "workspace", parent) as directory:
                        try:
                            os.mkdir(folder, 0o755, dir_fd=directory)
                        except FileExistsError:
                            pass
                    parent = (*parent, folder)
                with open_directory(name, "workspace", parent) as directory:
                    _save_stream(directory, parts[-1], storage.stream, None, FileBrowser.max_file_bytes())
                result.append({"name": parts[-1], "project": name, "path": "/".join((*parent, parts[-1]))})
        except BaseException:
            shutil.rmtree(run_id, dir_fd=attachments)
            raise
    return result


def file_action(name: str, action: str, data: dict, *, upload=None):
    area = data.get("area", "workspace")
    if action == "limits":
        return {"limits": FileBrowser.limits()}
    paths = file_parts(data.get("path", ""), allow_root=action == "list")
    if action == "list":
        with open_directory(name, area, paths) as directory:
            return {"entries": list_directory(directory, paths), "limits": FileBrowser.limits()}

    filename = paths[-1]
    with open_directory(name, area, paths[:-1]) as directory:
        if action == "read":
            with open_file(directory, filename) as stream:
                raw = stream.read(FileBrowser.max_text_bytes() + 1)
            return {"content": FileBrowser.decode_text(raw), "revision": hashlib.sha256(raw).hexdigest()}
        if action == "info":
            revision, is_directory = _entry_version(directory, filename)
            return {"revision": revision, "directory": is_directory}
        if action == "download":
            response = stream_file_download(open_file(directory, filename), filename, max_bytes=FileBrowser.max_file_bytes())
            response.headers["Cache-Control"] = "private, no-store"
            response.headers["X-Content-Type-Options"] = "nosniff"
            return response
        if action == "mkdir":
            try:
                os.mkdir(filename, 0o755, dir_fd=directory)
            except FileExistsError as error:
                raise RevisionConflict("A file or folder with this name already exists.") from error
            os.fsync(directory)
            return {}
        if action == "delete":
            revision, is_directory = _entry_version(directory, filename)
            require_revision(data.get("revision"), revision)
            try:
                if is_directory:
                    os.rmdir(filename, dir_fd=directory)
                else:
                    os.unlink(filename, dir_fd=directory)
            except OSError as error:
                if error.errno == errno.ENOTEMPTY:
                    raise RevisionConflict("Empty the folder before deleting it.") from error
                raise
            os.fsync(directory)
            return {}
        if action == "rename":
            target = file_parts(data.get("destination"))
            revision, _ = _entry_version(directory, filename)
            require_revision(data.get("revision"), revision)
            if target != paths:
                with open_directory(name, area, target[:-1]) as destination:
                    _rename_entry(directory, filename, destination, target[-1])
            return {"revision": revision}
        if action == "upload":
            return _save_stream(directory, filename, upload.stream, None, FileBrowser.max_file_bytes())
        content = data.get("content")
        if not isinstance(content, str):
            raise ValueError("Enter text to save.")
        return _save_stream(directory, filename, BytesIO(FileBrowser.text_bytes(content)), data.get("revision"),
                            FileBrowser.max_text_bytes())


def safe_file_error(error: OSError) -> tuple[str, int]:
    if isinstance(error, FileNotFoundError):
        return "Project file or folder was not found.", 404
    if error.errno in {errno.ELOOP, errno.ENOTDIR, errno.EACCES, errno.EPERM}:
        return "Choose a regular project file or folder.", 403
    return "The project file operation could not be completed.", 500
