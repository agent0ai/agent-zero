from __future__ import annotations

import asyncio
import contextlib
import errno
import os
import pty
import signal
import termios
from typing import Any

from plugins._code_execution.helpers.shell_ssh import clean_string
from plugins._sandboxing.helpers.runtime import defaults, get_manager


class SandboxInteractiveSession:
    """Persistent Bash session transported by a direct `runsc exec` PTY."""

    def __init__(self, name: str, *, agent: object | None = None) -> None:
        self.name = name
        self.agent = agent
        self.full_output = ""
        self._proc: asyncio.subprocess.Process | None = None
        self._queue: asyncio.Queue[str] | None = None
        self._pump_task: asyncio.Task[None] | None = None
        self._master_fd: int | None = None

    async def connect(self) -> None:
        manager = get_manager(agent=self.agent)
        _, sandbox_type, network = defaults(agent=self.agent)
        await asyncio.to_thread(
            manager.ensure_running,
            self.name,
            sandbox_type=sandbox_type,
            network=network,
        )
        argv = await asyncio.to_thread(manager.interactive_command, self.name)
        master, slave = pty.openpty()
        attrs = termios.tcgetattr(slave)
        attrs[3] &= ~termios.ECHO
        termios.tcsetattr(slave, termios.TCSANOW, attrs)
        try:
            self._proc = await asyncio.create_subprocess_exec(
                *argv,
                stdin=slave,
                stdout=slave,
                stderr=slave,
                close_fds=True,
                start_new_session=True,
            )
        except BaseException:
            os.close(master)
            os.close(slave)
            raise
        os.close(slave)
        self._master_fd = master
        self._queue = asyncio.Queue()
        self._pump_task = asyncio.create_task(self._pump())
        await self._read_until_idle(0.1, 1.0)

    async def close(self) -> None:
        process = self._proc
        self._proc = None
        if process is not None and process.returncode is None:
            try:
                os.killpg(process.pid, signal.SIGTERM)
            except (ProcessLookupError, PermissionError):
                process.terminate()
            try:
                await asyncio.wait_for(process.wait(), timeout=2)
            except asyncio.TimeoutError:
                try:
                    os.killpg(process.pid, signal.SIGKILL)
                except (ProcessLookupError, PermissionError):
                    process.kill()
                with contextlib.suppress(Exception):
                    await asyncio.wait_for(process.wait(), timeout=2)
        if self._pump_task is not None:
            self._pump_task.cancel()
            with contextlib.suppress(asyncio.CancelledError, Exception):
                await self._pump_task
            self._pump_task = None
        self._release_master()

    async def send_command(self, command: str) -> None:
        if self.is_terminated() or self._master_fd is None:
            raise RuntimeError("Sandbox shell is not connected")
        await asyncio.to_thread(get_manager(agent=self.agent).touch, self.name)
        self.full_output = ""
        try:
            os.write(self._master_fd, (command + "\n").encode("utf-8"))
        except OSError as exc:
            if exc.errno in {errno.EBADF, errno.EIO, errno.EINVAL}:
                self._release_master()
                raise RuntimeError("TTYSpawn PTY is closed") from exc
            raise

    async def read_output(
        self, timeout: float = 0, reset_full_output: bool = False
    ) -> tuple[str, str | None]:
        if self._queue is None:
            raise RuntimeError("Sandbox shell is not connected")
        if reset_full_output:
            self.full_output = ""
        partial = await self._read_until_idle(0.01, timeout)
        self.full_output += partial
        clean_partial = clean_string(partial)
        clean_full = clean_string(self.full_output)
        return clean_full, clean_partial or None

    def is_terminated(self) -> bool:
        return self._proc is None or self._proc.returncode is not None

    def get_exit_code(self) -> int | None:
        return None if self._proc is None else self._proc.returncode

    async def _pump(self) -> None:
        assert self._queue is not None
        while self._master_fd is not None:
            try:
                chunk = await asyncio.to_thread(os.read, self._master_fd, 65536)
            except OSError as exc:
                if exc.errno == errno.EIO:
                    break
                raise
            if not chunk:
                break
            self._queue.put_nowait(chunk.decode("utf-8", "replace"))

    async def _read_until_idle(self, idle_timeout: float, total_timeout: float) -> str:
        if self._queue is None or total_timeout <= 0:
            return ""
        loop = asyncio.get_running_loop()
        deadline = loop.time() + total_timeout
        chunks: list[str] = []
        while loop.time() < deadline:
            wait = min(idle_timeout, max(0.0, deadline - loop.time()))
            try:
                chunks.append(await asyncio.wait_for(self._queue.get(), timeout=wait))
            except asyncio.TimeoutError:
                break
        return "".join(chunks)

    def _release_master(self) -> None:
        descriptor = self._master_fd
        self._master_fd = None
        if descriptor is not None:
            with contextlib.suppress(OSError):
                os.close(descriptor)
