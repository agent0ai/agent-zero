"""File Browser adapter for live, bounded CLI and Launcher workspaces."""
import asyncio
from contextlib import contextmanager
import hashlib
from pathlib import Path
import tempfile
import threading
import uuid

from helpers import files
from helpers.ws_manager import get_shared_ws_manager
from plugins._a0_connector.helpers import ws_runtime as runtime


INCOMING = {}
INCOMING_LOCK = threading.RLock()


def receive_upload(token, storage):
    from api.upload import save_upload_atomic
    with INCOMING_LOCK:
        transfer = INCOMING.get(token)
        if not transfer:
            raise ValueError("File transfer expired.")
        item, destination, limit = transfer
        current = Provider().connections().get(item["id"])
        if not current or not current["permissions"]["download"]:
            raise PermissionError("Host download access is no longer available.")
        metadata = save_upload_atomic(storage, str(destination), max_bytes=limit)
        return {"filenames": ["content"], "files": [{"filename": "content", **metadata}]}


class Provider:
    id = "host"
    title = "Connected host folder"
    plugin_name = "_a0_connector"
    fields = []

    def connections(self):
        result = {}
        for sid in runtime.remote_tool_sids_for_context(""):
            metadata = runtime.remote_file_metadata_for_sid(sid)
            if not metadata or not metadata["enabled"] or not metadata["root_path"]:
                continue
            gateway = runtime.launcher_gateway_metadata_for_sid(sid)
            label = "A0 Launcher" if gateway else "A0 CLI"
            root = metadata["root_path"]
            cid = hashlib.sha256((sid + "\0" + root).encode()).hexdigest()[:32]
            readable = metadata["file_browser"]
            writable = readable and metadata["write_enabled"]
            result[cid] = {"id": cid, "provider": self.id, "name": f"{label} — {root}",
                           "managed": True, "_sid": sid, "root_path": root,
                           "status": "" if readable else "Update and restart the Connector to browse this folder.",
                           "permissions": {"browse": readable, "download": readable,
                                           "upload": writable, "edit": writable,
                                           "rename": writable, "delete": writable}}
        return result

    @contextmanager
    def open(self, item, data_dir):
        yield HostFiles(item)


class HostFiles:
    def __init__(self, item):
        self.item = item

    def call(self, op, path, **kwargs):
        return asyncio.run(self.request(op, path, **kwargs))

    async def request(self, op, path, **kwargs):
        current = Provider().connections().get(self.item["id"])
        if not current:
            raise ValueError("Host folder disconnected or changed. Reopen it from Files settings.")
        permission = "download" if op == "read_http" else "browse" if op in ("list", "stat", "read") else "upload"
        if not current["permissions"][permission]:
            raise PermissionError(current["status"] or "Host file access is disabled.")
        op_id = uuid.uuid4().hex
        loop = asyncio.get_running_loop()
        future = loop.create_future()
        sid = current["_sid"]
        runtime.store_pending_file_op(op_id, sid=sid, future=future, loop=loop)
        try:
            await runtime.emit_connector_event(
                sid, "connector_file_op",
                {"op_id": op_id, "op": "files_" + op, "path": path or ".",
                 "root_path": current["root_path"], **kwargs},
                handler_id="plugins._a0_connector.helpers.file_browser",
                manager=get_shared_ws_manager(),
            )
            result = await asyncio.wait_for(future, max(30, 30 + kwargs.get("size", 0) / (1024 * 1024)))
            if not result.get("ok"):
                raise ValueError(result.get("error") or "Host file operation failed.")
            return result["result"]
        except asyncio.TimeoutError:
            raise ValueError("The connected host did not respond in time.") from None
        finally:
            runtime.clear_pending_file_op(op_id)

    def list(self, path):
        return self.call("list", path)["entries"]

    def stat(self, path):
        return self.call("stat", path)

    def read(self, path, limit):
        with tempfile.TemporaryDirectory(prefix="host-download-", dir=files.get_abs_path("tmp")) as directory:
            destination = Path(directory) / "content"
            token = uuid.uuid4().hex
            with INCOMING_LOCK:
                INCOMING[token] = (self.item, destination, limit)
            try:
                result = self.call("read_http", path, transfer_token=token, limit=limit, size=limit)
                content = destination.read_bytes()
                if hashlib.sha256(content).hexdigest() != result["revision"]:
                    raise ValueError("Host file changed during download.")
                return content, result["revision"]
            finally:
                with INCOMING_LOCK:
                    INCOMING.pop(token, None)

    def write(self, path, content, expected=None):
        with tempfile.TemporaryDirectory(prefix="host-upload-", dir=files.get_abs_path("tmp")) as directory:
            source = Path(directory) / "content"
            source.write_bytes(content)
            return self.call("write_http", path, source_path=str(source), size=len(content),
                             sha256=hashlib.sha256(content).hexdigest(), expected=expected)["revision"]

    def mkdir(self, path):
        self.call("mkdir", path)

    def rename(self, path, destination):
        self.call("rename", path, destination=destination)

    def remove(self, path, directory=False):
        self.call("remove", path)
