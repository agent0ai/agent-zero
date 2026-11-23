import os
import platform
import select
import subprocess
import time
import sys
from typing import Optional, Tuple
from helpers import runtime
from plugins._code_execution.helpers import tty_session
from plugins._code_execution.helpers.shell_ssh import clean_string


FRAMEWORK_VENV_ROOT = "/opt/venv-a0"


def _is_framework_venv_path(path_entry: str, root: str = FRAMEWORK_VENV_ROOT) -> bool:
    normalized = path_entry.rstrip("/\\")
    normalized_root = root.rstrip("/\\")
    return normalized == normalized_root or normalized.startswith(normalized_root + "/") or normalized.startswith(normalized_root + "\\")


def disable_pagers_in_env(env: dict | None = None) -> dict:
    """Return a copy of ``env`` with terminal pagers disabled.

    Commands such as ``git diff``/``git log`` detect a TTY and pipe their output
    through a pager (``more``/``less``). The non-interactive shells created by
    the code execution tool never receive any user input, so the pager blocks
    forever and spins at 100% CPU per process. Pointing the pager variables at
    ``cat`` lets the output stream through instead. See issue #1697.
    """
    env = dict(env if env is not None else os.environ)
    env["PAGER"] = "cat"
    env["GIT_PAGER"] = "cat"
    return env


def sanitize_execution_env(env: dict | None = None) -> dict:
    """Return a copy of ``env`` safe for an agent code execution shell.

    The WebUI process runs inside the framework virtual environment
    (``/opt/venv-a0``) and therefore advertises ``VIRTUAL_ENV=/opt/venv-a0``
    plus ``/opt/venv-a0/bin`` early in ``PATH``. Those values leak into every
    shell the code execution tool spawns. Because the local interactive shell
    starts with ``/bin/bash`` and ``/root/.bashrc`` only *prepends* the agent
    runtime ``/opt/venv/bin``, the framework runtime stays reachable. Any
    command that is not shadowed in ``/opt/venv/bin`` (``python3.12``,
    ``pip3.12``, ``fastmcp``, ``jsondiff``, ...) then resolves out of the
    framework runtime, so a plain ``pip install`` from a normal agent task
    mutates the framework venv, and a task dependency can silently upgrade
    or downgrade packages Agent Zero itself pins. The damage is invisible
    until the next WebUI restart, when the new versions are imported and the
    process enters a crash loop.

    Removing ``VIRTUAL_ENV`` pointing at the framework root and dropping any
    ``PATH`` entry that lies inside ``/opt/venv-a0`` prevents that class of
    failure. The shell still activates ``/opt/venv`` via ``/root/.bashrc``,
    giving callers the documented agent execution runtime.
    """
    env = dict(env if env is not None else os.environ)

    path = env.get("PATH")
    if path:
        kept = []
        for entry in path.split(os.pathsep):
            if not entry:
                continue
            if _is_framework_venv_path(entry):
                continue
            kept.append(entry)
        env["PATH"] = os.pathsep.join(kept)

    current_venv = env.get("VIRTUAL_ENV")
    if current_venv and _is_framework_venv_path(str(current_venv)):
        env.pop("VIRTUAL_ENV", None)
        env.pop("VIRTUAL_ENV_PROMPT", None)

    return env


class LocalInteractiveSession:
    def __init__(self, cwd: str|None = None):
        self.session: tty_session.TTYSession|None = None
        self.full_output = ''
        self.cwd = cwd

    def __del__(self):
        try:
            if self.session:
                self.session.kill()
        except Exception:
            pass

    async def connect(self):
        self.session = tty_session.TTYSession(
            runtime.get_terminal_executable(),
            cwd=self.cwd,
            env=sanitize_execution_env(disable_pagers_in_env()),
        )
        await self.session.start()
        await self.session.read_full_until_idle(idle_timeout=1, total_timeout=1)

    async def close(self):
        if self.session:
            session = self.session
            self.session = None
            try:
                await session.close()
            except Exception:
                try:
                    session.kill()
                except Exception:
                    pass

    async def send_command(self, command: str):
        if not self.session:
            raise Exception("Shell not connected")
        self.full_output = ""
        await self.session.sendline(command)

    def is_terminated(self) -> bool:
        return self.session is None or self.session.is_terminated()

    def get_exit_code(self) -> int | None:
        if not self.session:
            return None
        return self.session.get_exit_code()
 
    async def read_output(self, timeout: float = 0, reset_full_output: bool = False) -> Tuple[str, Optional[str]]:
        if not self.session:
            raise Exception("Shell not connected")

        if reset_full_output:
            self.full_output = ""

        # get output from terminal
        partial_output = await self.session.read_full_until_idle(idle_timeout=0.01, total_timeout=timeout)
        self.full_output += partial_output

        # clean output
        partial_output = clean_string(partial_output)
        clean_full_output = clean_string(self.full_output)

        if not partial_output:
            return clean_full_output, None
        return clean_full_output, partial_output
