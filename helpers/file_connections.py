"""Files provider interface: saved connections, permissions and remote Editor sessions."""
from __future__ import annotations

import io
from contextlib import contextmanager
import json
import os
import posixpath
import re
import threading
import tempfile
import uuid
import zipfile
from pathlib import Path

from helpers import extension, files
from helpers.file_browser import FileBrowser
from helpers.file_transfers import copy_stream, TransferWriter

API_VERSION = 1
PREFIX = "/@connections/"
PERMISSIONS = ("browse", "download", "upload", "edit", "rename", "delete")
LOCK = threading.RLock()
SESSIONS = {}


def providers():
    result = {}
    extension.call_extensions_sync("file_browser_providers", providers=result)
    return result


def provider(name):
    value = providers().get(name)
    if value is None:
        raise ValueError("This connection plugin is not installed or enabled.")
    return value


@contextmanager
def filesystem(value, item):
    try:
        with value.open(item, data_dir(value)) as fs:
            yield fs
    except (ValueError, PermissionError, FileNotFoundError):
        raise
    except Exception:
        raise ValueError("Remote file operation failed. Check connection access and server availability.") from None


def data_dir(value):
    path = Path(files.get_abs_path("usr", "plugins", value.plugin_name, "data"))
    path.mkdir(mode=0o700, parents=True, exist_ok=True)
    return path


def _load(value):
    if hasattr(value, "connections"):
        return value.connections()
    path = data_dir(value) / "connections.json"
    if path.exists():
        return files.read_file_json(str(path))
    return {}


def _store(value, data):
    path = data_dir(value) / "connections.json"
    temporary = path.with_suffix("." + uuid.uuid4().hex + ".tmp")
    try:
        with os.fdopen(os.open(temporary, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600), "w") as stream:
            json.dump(data, stream)
        os.replace(temporary, path)
    finally:
        temporary.unlink(missing_ok=True)


def public_connection(value, item):
    secrets = {field["name"] for field in value.fields if field.get("secret")}
    return {key: val for key, val in item.items() if key not in secrets and key != "auth" and not key.startswith("_")} | {
        "savedSecrets": {key: bool(item.get(key)) for key in secrets},
        "provider": value.id,
    }


def listing_config():
    result, metadata = [], []
    with LOCK:
        for value in providers().values():
            metadata.append({"id": value.id, "title": value.title, "plugin": value.plugin_name,
                             "managed": hasattr(value, "connections"),
                             "fields": value.fields, "permissions": getattr(value, "permissions", PERMISSIONS)})
            result.extend(public_connection(value, item) for item in _load(value).values())
    return {"interface_version": API_VERSION, "providers": metadata, "connections": result}


def get_connection(provider_id, cid):
    value = provider(provider_id)
    with LOCK:
        item = _load(value).get(cid)
    if not item:
        raise ValueError("Connection no longer exists.")
    return value, item


def save_connection(item):
    value = provider(item.get("provider"))
    if hasattr(value, "connections"):
        raise ValueError("This connection is managed by its host application.")
    cid = str(item.get("id") or uuid.uuid4().hex)
    if not re.fullmatch(r"[a-f0-9]{32}", cid):
        raise ValueError("Invalid connection ID.")
    with LOCK:
        data = _load(value)
        old = data.get(cid, {})
        allowed = {field["name"] for field in value.fields}
        config = {key: item[key] for key in allowed if key in item}
        for field in value.fields:
            if field.get("secret") and field["name"] not in config:
                config[field["name"]] = old.get(field["name"], "")
        config = value.validate(config)
        config.update(id=cid, provider=value.id, name=str(item.get("name", "")).strip()[:100] or value.title,
                      permissions={p: item.get("permissions", {}).get(p) is True and p in getattr(value, "permissions", PERMISSIONS) for p in PERMISSIONS})
        data[cid] = config
        _store(value, data)
        _expire(value.id, cid)
        return public_connection(value, config)


def remove_connection(provider_id, cid):
    value = provider(provider_id)
    if hasattr(value, "connections"):
        raise ValueError("Disconnect this folder from its host application.")
    with LOCK:
        data = _load(value)
        data.pop(cid, None)
        _store(value, data)
        _expire(provider_id, cid)


def _expire(provider_id, cid):
    for sid, session in list(SESSIONS.items()):
        if split(session["path"])[:2] == (provider_id, cid):
            SESSIONS.pop(sid, None)


def is_remote(path):
    return isinstance(path, str) and (path == "/@connections" or path.startswith(PREFIX) or path == "/@ssh" or path.startswith("/@ssh/"))


def split(path):
    if not isinstance(path, str):
        raise ValueError("Invalid connection path.")
    if path.startswith("/@ssh/"):
        path = PREFIX + "ssh/" + path[len("/@ssh/"):]
    if not path.startswith(PREFIX):
        raise ValueError("Invalid connection path.")
    provider_id, cid, relative = (path[len(PREFIX):].split("/", 2) + ["", ""])[:3]
    if not re.fullmatch(r"[a-z0-9_]+", provider_id) or not re.fullmatch(r"[a-f0-9]{32}", cid):
        raise ValueError("Invalid connection path.")
    if "\x00" in relative or "\\" in relative or any(part in (".", "..") for part in relative.split("/")):
        raise ValueError("Invalid connection path.")
    return provider_id, cid, relative.strip("/")


def path_for(item, relative=""):
    return PREFIX + item["provider"] + "/" + item["id"] + ("/" + relative if relative else "")


def require(item, permission):
    if not item["permissions"].get(permission) or permission not in getattr(provider(item["provider"]), "permissions", PERMISSIONS):
        raise PermissionError(f"This connection does not allow {permission}.")


def valid_name(name):
    return isinstance(name, str) and name not in ("", ".", "..") and not any(c in name for c in ("/", "\\", "\x00"))


def listing(path):
    if path in ("/@connections", "/@ssh"):
        config = listing_config()
        return {"current_path": path, "parent_path": "/a0", "entries": [
            dict(name=item["name"], path=path_for(item), is_dir=True, size=0, modified=0,
                 type="unknown", permissions={p: False for p in PERMISSIONS})
            for item in config["connections"] if item["permissions"]["browse"] and (path != "/@ssh" or item["provider"] == "ssh")],
            "permissions": {p: False for p in PERMISSIONS}}
    pid, cid, relative = split(path)
    value, item = get_connection(pid, cid)
    require(item, "browse")
    with filesystem(value, item) as fs:
        entries = fs.list(relative)
    clean = []
    for entry in entries:
        if not valid_name(entry.get("name")) or entry.get("is_link"):
            continue
        clean.append(entry | {"path": path_for(item, posixpath.join(relative, entry["name"])),
                              "permissions": item["permissions"], "type": entry.get("type", "unknown")})
    current = path_for(item, relative)
    return {"entries": clean, "current_path": current,
            "parent_path": posixpath.dirname(current) if relative else "/@connections",
            "permissions": item["permissions"]}


def read_into(path, destination, permission="download", limit=None):
    if limit is None:
        limit = FileBrowser.max_file_bytes()
    pid, cid, relative = split(path)
    value, item = get_connection(pid, cid)
    require(item, permission)
    output = TransferWriter(destination, limit)
    with filesystem(value, item) as fs:
        revision = fs.read(relative, output, limit)
    require(get_connection(pid, cid)[1], permission)
    return revision


def read(path, permission="download", limit=None):
    output = io.BytesIO()
    revision = read_into(path, output, permission, limit)
    return output.getvalue(), revision


def write_from(path, source, *, expected=None, editing=False):
    pid, cid, relative = split(path)
    value, item = get_connection(pid, cid)
    permission = "edit" if expected is not None else "upload"
    require(item, permission)
    if not relative:
        raise ValueError("Choose a destination file.")
    limit = FileBrowser.max_text_bytes() if editing else FileBrowser.max_file_bytes()
    with tempfile.TemporaryFile() as staged:
        copy_stream(source, staged, limit)
        staged.seek(0)
        require(get_connection(pid, cid)[1], permission)
        with filesystem(value, item) as fs:
            return fs.write(relative, staged, expected=expected)


def write(path, content, *, expected=None, editing=False):
    return write_from(path, io.BytesIO(content), expected=expected, editing=editing)


def mutate(action, path, destination=""):
    pid, cid, relative = split(path)
    value, item = get_connection(pid, cid)
    require(item, {"delete": "delete", "rename": "rename", "mkdir": "upload"}[action])
    if not relative:
        raise ValueError("The connection root cannot be changed.")
    with filesystem(value, item) as fs:
        if action == "mkdir":
            fs.mkdir(relative)
        elif action == "rename":
            other_pid, other_cid, target = split(destination)
            if (other_pid, other_cid) != (pid, cid) or not target:
                raise ValueError("Move files within the same connection.")
            if target.startswith(relative.rstrip("/") + "/"):
                raise ValueError("A folder cannot be moved into itself.")
            fs.rename(relative, target)
        else:
            def remove(target, depth=0):
                if depth > 64:
                    raise ValueError("Directory nesting is too deep.")
                info = fs.stat(target)
                if info["is_dir"] and not info.get("is_link"):
                    for entry in fs.list(target):
                        if not valid_name(entry.get("name")):
                            raise ValueError("Server returned an invalid entry name.")
                        remove(posixpath.join(target, entry["name"]), depth + 1)
                fs.remove(target, directory=info["is_dir"] and not info.get("is_link"))
            remove(relative)


def archive(paths):
    limit = FileBrowser.max_file_bytes()
    output, total, count = tempfile.TemporaryFile(), 0, 0
    try:
        with zipfile.ZipFile(output, "w", zipfile.ZIP_DEFLATED) as zipped:
            def add(path, name, depth=0):
                nonlocal total, count
                count += 1
                if count > FileBrowser.max_archive_entries() or depth > 64:
                    raise ValueError("Archive exceeds the configured entry count or supported nesting depth.")
                pid, cid, relative = split(path)
                value, item = get_connection(pid, cid)
                require(item, "download")
                with filesystem(value, item) as fs:
                    info = fs.stat(relative)
                    if info.get("is_link"):
                        return
                    if info["is_dir"]:
                        children = fs.list(relative)
                        zipped.writestr(name + "/", b"")
                    else:
                        with zipped.open(name, "w", force_zip64=True) as member:
                            counter = TransferWriter(member, limit - total)
                            fs.read(relative, counter, limit - total)
                            total += counter.size
                        return
                for child in children:
                    if valid_name(child.get("name")) and not child.get("is_link"):
                        add(path_for(item, posixpath.join(relative, child["name"])), name + "/" + child["name"], depth + 1)
            for path in paths:
                add(path, posixpath.basename(path.rstrip("/")))
    except BaseException:
        output.close()
        raise
    output.seek(0)
    return output


def editor(action, payload):
    if action in ("create", "save_as"):
        path = payload.get("path", "")
        pid, cid, _ = split(path)
        require(get_connection(pid, cid)[1], "edit")
        content = FileBrowser.text_bytes(str(payload.get("text", "")))
        write(path, content, editing=True)
        return editor("open", {"path": path})
    if action == "open":
        path = payload["path"]
        content, revision = read(path, "edit", FileBrowser.max_text_bytes())
        text = FileBrowser.decode_text(content)
        sid = "remote:" + uuid.uuid4().hex
        if len(SESSIONS) >= 256:
            SESSIONS.pop(next(iter(SESSIONS)))
        SESSIONS[sid] = {"path": path, "revision": revision}
        doc = {"path": path, "file_id": sid, "basename": posixpath.basename(path),
               "extension": posixpath.splitext(path)[1].lstrip("."), "kind": "text"}
        return {"ok": True, "session_id": sid, "file_id": sid, "document": doc, "text": text}
    sid = payload.get("session_id") or payload.get("file_id", "")
    session = SESSIONS.get(sid)
    if not session:
        raise ValueError("Remote session expired. Reopen the file.")
    if action in ("save", "renamed"):
        content = FileBrowser.text_bytes(str(payload.get("text", "")))
        if action == "renamed":
            pid, cid, _ = split(session["path"])
            require(get_connection(pid, cid)[1], "rename")
        if action == "save" or "text" in payload:
            session["revision"] = write(session["path"], content, expected=session["revision"], editing=True)
        if action == "renamed":
            mutate("rename", session["path"], payload["path"])
            session["path"] = payload["path"]
        return {"ok": True, "document": {"path": session["path"], "file_id": sid, "basename": posixpath.basename(session["path"])}}
    if action == "close":
        SESSIONS.pop(sid, None)
    elif action not in ("activate", "input"):
        raise ValueError("This action is not supported for remote files.")
    return {"ok": True}
