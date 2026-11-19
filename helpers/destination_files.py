"""Bounded file access in the filesystem selected by an agent tool."""

import asyncio
import hashlib
import io
import ntpath
import posixpath
from pathlib import Path
import os
import select
import subprocess
import tempfile
import time

from helpers import files
from plugins._code_execution.helpers.destinations import ExecutionDestination, resolve_code_execution_destination

# Resolve and open inside PRoot, including paths backed by guest mounts.
_GUEST_FILE = """
import hashlib, os, stat, sys, tempfile
from pathlib import Path

operation, name, limit, expected = sys.argv[1:]
path = Path(name).expanduser().resolve()
limit = int(limit)

def read():
    if not stat.S_ISREG(path.stat().st_mode):
        raise ValueError('Expected a regular file')
    with os.fdopen(os.open(path, os.O_RDONLY | os.O_NONBLOCK), 'rb') as stream:
        if not stat.S_ISREG(os.fstat(stream.fileno()).st_mode):
            raise ValueError('Expected a regular file')
        data = stream.read(limit + 1)
        if len(data) > limit:
            raise ValueError(f'File exceeds {limit} bytes')
        return data

if operation == 'read':
    sys.stdout.buffer.write(read())
else:
    data = sys.stdin.buffer.read(limit + 1)
    if len(data) > limit:
        raise ValueError(f'File exceeds {limit} bytes')
    path.parent.mkdir(parents=True, exist_ok=True)
    try:
        info = path.stat()
        if not stat.S_ISREG(info.st_mode):
            raise ValueError('Expected a regular file')
    except FileNotFoundError:
        info = None
    with tempfile.NamedTemporaryFile(dir=path.parent, delete=False) as stream:
        staged = Path(stream.name)
        try:
            stream.write(data)
            stream.flush()
            os.fsync(stream.fileno())
            stream.close()
            if info:
                staged.chmod(stat.S_IMODE(info.st_mode) & 0o777)
            if expected and hashlib.sha256(read()).hexdigest() != expected:
                raise ValueError('File changed since it was read')
            if info is None:
                os.link(staged, path)
            else:
                current = path.stat()
                if (current.st_dev, current.st_ino, current.st_mtime_ns, current.st_size) != (
                    info.st_dev, info.st_ino, info.st_mtime_ns, info.st_size
                ):
                    raise ValueError('File changed during write')
                os.replace(staged, path)
        finally:
            staged.unlink(missing_ok=True)
"""


async def resolve(agent, destination: str = "local") -> ExecutionDestination:
    # File permission and execution permission are announced independently.
    destination = str(destination or "local").strip() or "local"
    if destination == "host":
        return ExecutionDestination("host", "host", "Connected host", "Connected host files")
    return await resolve_code_execution_destination(agent, destination)


def _sandbox_command(agent, sandbox, operation, path, limit, expected, payload):
    from plugins._sandboxing.helpers.runtime import defaults, get_manager

    manager = get_manager(agent=agent)
    if (manager.config.instances_dir / sandbox / "metadata.json").exists():
        if manager.inspect(sandbox).service:
            raise PermissionError("Plugin service sandboxes are not agent file destinations")
    _, sandbox_type, network = defaults(agent=agent)
    manager.ensure_running(sandbox, sandbox_type=sandbox_type, network=network)
    argv = manager.process_command(
        sandbox, ["python3", "-I", "-c", _GUEST_FILE, operation, path, str(limit), expected or ""],
        agent_only=True,
    )
    deadline = time.monotonic() + 30
    # A staged stdin lets us drain bounded output without a second pipe writer.
    with tempfile.TemporaryFile() as source:
        source.write(payload)
        source.seek(0)
        with subprocess.Popen(argv, stdin=source, stdout=subprocess.PIPE, stderr=subprocess.STDOUT) as process:
            output = bytearray()
            ceiling = max(limit, 4096) if operation == "read" else 4096
            try:
                while True:
                    remaining = deadline - time.monotonic()
                    if remaining <= 0 or not select.select([process.stdout], [], [], remaining)[0]:
                        raise TimeoutError("Sandbox file operation timed out")
                    chunk = os.read(process.stdout.fileno(), min(65536, ceiling + 1 - len(output)))
                    if not chunk:
                        break
                    output.extend(chunk)
                    if len(output) > ceiling:
                        raise ValueError("Sandbox file operation exceeded its output limit")
                status = process.wait(timeout=max(0, deadline - time.monotonic()))
            except BaseException:
                process.terminate()
                try:
                    process.wait(timeout=8)
                except subprocess.TimeoutExpired:
                    process.kill()
                raise
    if status:
        detail = output.decode("utf-8", "replace").strip()
        raise OSError(detail[-2048:] if detail else "Sandbox file operation failed")
    if operation == "read" and len(output) > limit:
        raise ValueError(f"File exceeds {limit} bytes")
    return bytes(output)


def _host_file(agent, path, *, write=False):
    from plugins._a0_connector.helpers.file_browser import HostFiles, Provider
    from plugins._a0_connector.helpers.ws_runtime import remote_tool_sids_for_context

    connections = {item["_sid"]: item for item in Provider().connections().values()}
    action = "upload" if write else "download"
    for sid in remote_tool_sids_for_context(agent.context.id):
        item = connections.get(sid)
        if not item or not item["permissions"][action]:
            continue
        root = item["root_path"]
        platform = ntpath if ntpath.splitdrive(root)[0] else posixpath
        relative = platform.relpath(path, root) if platform.isabs(path) else platform.normpath(path)
        if platform.splitdrive(relative)[0] or relative == ".." or relative.startswith(".." + platform.sep):
            raise PermissionError("File is outside the connected host's exposed folder")
        return HostFiles(item), relative.replace(platform.sep, "/")
    raise PermissionError("The connected host has not enabled the required file transfer access")


async def read(agent, destination: str, path: str, *, limit: int) -> bytes:
    if limit < 0:
        raise ValueError("File limit must be nonnegative")
    selected = await resolve(agent, destination)
    if selected.kind == "sandbox":
        return await asyncio.to_thread(_sandbox_command, agent, selected.target, "read", path, limit, None, b"")
    if selected.kind == "host":
        backend, relative = _host_file(agent, path)
        buffer = io.BytesIO()
        await asyncio.to_thread(backend.read, relative, buffer, limit)
        return buffer.getvalue()

    def read_local():
        local = Path(files.fix_dev_path(path)).expanduser()
        if not local.is_file():
            raise FileNotFoundError(path)
        with local.open("rb") as stream:
            data = stream.read(limit + 1)
        if len(data) > limit:
            raise ValueError(f"File exceeds {limit} bytes")
        return data

    return await asyncio.to_thread(read_local)


async def write(
    agent, destination: str, path: str, content: bytes, *, limit: int, expected: str | None = None,
) -> str:
    if len(content) > limit:
        raise ValueError(f"File exceeds {limit} bytes")
    selected = await resolve(agent, destination)
    if selected.kind == "sandbox":
        await asyncio.to_thread(_sandbox_command, agent, selected.target, "write", path, limit, expected, content)
    elif selected.kind == "host":
        backend, relative = _host_file(agent, path, write=True)
        await asyncio.to_thread(backend.write, relative, io.BytesIO(content), expected)
    else:
        from helpers.file_transfers import write_stream_atomic

        def write_local():
            local = Path(files.fix_dev_path(path)).expanduser()
            if expected is not None:
                with local.open("rb") as stream:
                    if hashlib.sha256(stream.read(limit + 1)).hexdigest() != expected:
                        raise ValueError("File changed since it was read")
            write_stream_atomic(io.BytesIO(content), local, max_bytes=limit)

        await asyncio.to_thread(write_local)
    return hashlib.sha256(content).hexdigest()
