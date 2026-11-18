"""Local JSON requests dispatched to socket/ handlers in the running framework."""

from abc import ABC, abstractmethod
import asyncio
from contextlib import asynccontextmanager, suppress
import errno
import json
import logging
import math
import os
from pathlib import Path
import re
import socket
import stat
import threading


# JSON is buffered; bulk file transfers continue to use the streaming HTTP API.
MAX_MESSAGE_BYTES = int(os.environ.get("A0_SOCKET_MAX_MESSAGE_BYTES", 64 * 1024 * 1024))
IO_TIMEOUT = float(os.environ.get("A0_SOCKET_IO_TIMEOUT", 60))
REQUEST_TIMEOUT = float(os.environ.get("A0_SOCKET_REQUEST_TIMEOUT", 0)) or None
if (MAX_MESSAGE_BYTES < 1024 or not math.isfinite(IO_TIMEOUT) or IO_TIMEOUT <= 0
        or (REQUEST_TIMEOUT is not None and (not math.isfinite(REQUEST_TIMEOUT) or REQUEST_TIMEOUT < 0))):
    raise ValueError("Invalid A0 socket limits")
COMMAND_PATTERN = re.compile(r"[A-Za-z0-9_-]+(?:/[A-Za-z0-9_-]+)*\Z")
logger = logging.getLogger(__name__)


def get_socket_path() -> Path:
    return Path(os.environ.get("A0_SOCKET_PATH") or (
        Path(__file__).resolve().parents[1] / "tmp/socket/a0.sock"
    )).absolute()


class SocketError(Exception):
    """An expected failure whose code and message are safe to return to the caller."""

    def __init__(self, code: str, message: str, *, details: dict | None = None):
        if not isinstance(code, str) or not isinstance(message, str):
            raise TypeError("Socket error code and message must be strings")
        super().__init__(message)
        self.code = code
        self.details = details


def error_response(code: str, message: str, details: dict | None = None) -> dict:
    error = {"code": code, "message": message}
    if details is not None:
        error["details"] = details
    return {"ok": False, "error": error}


def encode_message(value: dict) -> bytes:
    return (json.dumps(value, ensure_ascii=False, allow_nan=False, separators=(",", ":")) + "\n").encode("utf-8")


def _reject_constant(value: str):
    raise ValueError(f"Invalid JSON constant: {value}")


def decode_message(value: bytes | str):
    if isinstance(value, bytes):
        value = value.decode("utf-8")
    return json.loads(value, parse_constant=_reject_constant)


class SocketHandler(ABC):
    def __init__(self, app, thread_lock):
        self.app = app
        self.thread_lock = thread_lock

    @abstractmethod
    async def process(self, input: dict) -> dict:
        """Validate operation arguments and return a JSON-serializable dictionary."""
        raise NotImplementedError


def _handler_class(command: str) -> type[SocketHandler]:
    from helpers import files, plugins
    from helpers.modules import load_classes_from_file

    candidates = [(Path(files.get_abs_path("socket")), command)]
    if command.startswith("plugins/"):
        parts = command.split("/", 2)
        if len(parts) == 3:
            plugin_dir = plugins.find_plugin_dir(parts[1])
            if plugin_dir:
                candidates.append((Path(plugin_dir) / "socket", parts[2]))
    candidates.append((Path(files.get_abs_path(files.USER_DIR, "socket")), command))

    for root, name in candidates:
        path = (root / f"{name}.py").resolve()
        if not path.is_relative_to(root.resolve()):
            raise SocketError("INVALID_COMMAND", "Handler path escapes its socket directory.")
        if path.is_file():
            classes = load_classes_from_file(str(path), SocketHandler)
            if classes:
                return classes[0]
    raise SocketError("NOT_FOUND", "Socket handler not found.")


class SocketServer:
    def __init__(self, app=None, thread_lock=None, *, path: Path | None = None):
        self.app = app
        self.thread_lock = thread_lock if thread_lock is not None else threading.RLock()
        self.path = Path(path).absolute() if path is not None else get_socket_path()
        self._server = None
        self._lock_fd = None
        self._identity = None
        self._tasks = {}

    async def dispatch(self, request: object) -> dict:
        try:
            if not isinstance(request, dict) or set(request) - {"command", "args"}:
                raise SocketError("INVALID_REQUEST", "Expected an object with command and args.")
            command = request.get("command")
            if not isinstance(command, str) or not COMMAND_PATTERN.fullmatch(command):
                raise SocketError("INVALID_COMMAND", "Use a handler path without a .py suffix.")
            arguments = request.get("args", {})
            if not isinstance(arguments, dict):
                raise SocketError("INVALID_ARGUMENT", "args must be a JSON object.")
            handler_class = await asyncio.to_thread(_handler_class, command)
            handler = handler_class(self.app, self.thread_lock)
            result = await handler.process(arguments)
            if not isinstance(result, dict):
                raise TypeError("Socket handlers must return a dictionary")
            return {"ok": True, "result": result}
        except SocketError as exc:
            return error_response(exc.code, str(exc), exc.details)
        except Exception:
            logger.exception("Socket handler failed")
            return error_response("INTERNAL_ERROR", "Socket handler failed.")

    async def start(self):
        import fcntl

        if self._server is not None:
            raise RuntimeError("Socket server is already started")
        self.path.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
        parent = self.path.parent.lstat()
        if not stat.S_ISDIR(parent.st_mode) or parent.st_uid != os.geteuid() or parent.st_mode & 0o077:
            raise PermissionError("Socket directory must be owned by this user with mode 0700")

        sock = None
        try:
            self._lock_fd = os.open(str(self.path) + ".lock", os.O_CREAT | os.O_RDWR | os.O_NOFOLLOW, 0o600)
            if not stat.S_ISREG(os.fstat(self._lock_fd).st_mode):
                raise PermissionError("Socket lock must be a regular file")
            fcntl.flock(self._lock_fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
            await self._remove_stale_socket()
            sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
            sock.bind(str(self.path))
            info = self.path.lstat()
            self._identity = (info.st_dev, info.st_ino)
            self.path.chmod(0o600)
            self._server = await asyncio.start_unix_server(self._accept, sock=sock, limit=MAX_MESSAGE_BYTES)
        except BaseException:
            if sock is not None:
                sock.close()
            await self.close()
            raise

    async def _remove_stale_socket(self):
        try:
            info = self.path.lstat()
        except FileNotFoundError:
            return
        if not stat.S_ISSOCK(info.st_mode) or info.st_uid != os.geteuid():
            raise FileExistsError("Refusing to replace a non-socket or another user's socket")
        try:
            _, writer = await asyncio.wait_for(asyncio.open_unix_connection(str(self.path)), 1)
        except OSError as exc:
            if exc.errno != errno.ECONNREFUSED:
                raise
            current = self.path.lstat()
            if (current.st_dev, current.st_ino) != (info.st_dev, info.st_ino):
                raise FileExistsError("Socket changed during startup")
            self.path.unlink()
        else:
            writer.close()
            await writer.wait_closed()
            raise FileExistsError("Socket is already listening")

    def _accept(self, reader, writer):
        task = asyncio.create_task(self._handle_client(reader, writer))
        self._tasks[task] = writer

        def completed(task):
            self._tasks.pop(task, None)
            # Cancellation before the coroutine starts cannot run its finally block.
            if not writer.is_closing():
                writer.transport.abort()

        task.add_done_callback(completed)

    async def _handle_client(self, reader, writer):
        try:
            try:
                async with asyncio.timeout(IO_TIMEOUT):
                    try:
                        raw = await reader.readline()
                    except ValueError:
                        raise SocketError("REQUEST_TOO_LARGE", "Request exceeds the size limit.") from None
                    if len(raw) > MAX_MESSAGE_BYTES:
                        raise SocketError("REQUEST_TOO_LARGE", "Request exceeds the size limit.")
                    if not raw.endswith(b"\n"):
                        raise SocketError("INVALID_REQUEST", "Request must end with a newline.")
                    try:
                        request = decode_message(raw)
                    except (ValueError, UnicodeError, RecursionError):
                        raise SocketError("INVALID_REQUEST", "Request must contain valid JSON.") from None
                async with asyncio.timeout(REQUEST_TIMEOUT):
                    response = await self.dispatch(request)
            except TimeoutError:
                response = error_response("TIMEOUT", "Socket request timed out.")
            except SocketError as exc:
                response = error_response(exc.code, str(exc), exc.details)
            try:
                encoded = encode_message(response)
            except (TypeError, ValueError, RecursionError):
                logger.exception("Socket handler returned invalid JSON")
                encoded = encode_message(error_response("INTERNAL_ERROR", "Socket handler failed."))
            if len(encoded) > MAX_MESSAGE_BYTES:
                encoded = encode_message(error_response("RESPONSE_TOO_LARGE", "Response exceeds the size limit."))
            writer.write(encoded)
            await asyncio.wait_for(writer.drain(), IO_TIMEOUT)
        except (ConnectionError, TimeoutError):
            writer.transport.abort()
        finally:
            writer.close()
            try:
                await asyncio.wait_for(writer.wait_closed(), 5)
            except (ConnectionError, TimeoutError):
                writer.transport.abort()

    async def close(self):
        try:
            if self._server is not None:
                self._server.close()
            tasks = list(self._tasks)
            for task in tasks:
                writer = self._tasks[task]
                if not writer.is_closing():
                    writer.transport.abort()
                task.cancel()
            await asyncio.gather(*tasks, return_exceptions=True)
            if self._server is not None:
                await self._server.wait_closed()
                self._server = None
            if self._identity is not None:
                with suppress(FileNotFoundError):
                    info = self.path.lstat()
                    if (info.st_dev, info.st_ino) == self._identity:
                        self.path.unlink()
                self._identity = None
        finally:
            if self._lock_fd is not None:
                os.close(self._lock_fd)
                self._lock_fd = None


@asynccontextmanager
async def socket_lifespan(app, thread_lock):
    # This local Linux transport is optional on platforms without Unix sockets.
    if os.name != "posix":
        yield
        return
    server = SocketServer(app, thread_lock)
    try:
        await server.start()
        logger.info("Local socket listening at %s", server.path)
        yield
    finally:
        await server.close()
