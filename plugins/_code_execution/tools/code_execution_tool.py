import asyncio
import errno
from dataclasses import dataclass
import re
import shlex
import sys
import time
from typing import Any

from helpers.tool import Tool, Response, coerce_bool
from helpers.errors import RepairableException
from helpers.tool_policy import ensure_retired_host_tool_allowed
from helpers import files, projects, runtime, secrets, settings
from helpers.print_style import PrintStyle
from helpers.strings import truncate_text as truncate_text_string
from helpers.messages import truncate_text as truncate_text_agent
from helpers import plugins

from plugins._code_execution.helpers.shell_local import LocalInteractiveSession
from plugins._code_execution.helpers.destinations import (
    ExecutionDestination,
    resolve_code_execution_destination,
)


def _is_closed_pty_error(exc: BaseException) -> bool:
    if isinstance(exc, RuntimeError):
        message = str(exc)
        if "TTYSpawn PTY is closed" in message or "TTYSpawn process has exited" in message:
            return True
    if isinstance(exc, OSError) and exc.errno in (errno.EBADF, errno.EIO, errno.EINVAL):
        return True
    cause = getattr(exc, "__cause__", None)
    if cause and cause is not exc:
        return _is_closed_pty_error(cause)
    return False


def _group_multiline_command(command: str, powershell: bool = False) -> str:
    body = command.rstrip("\n")
    if "\n" not in body:
        return body
    opener = ". {" if powershell else "{"
    return f"{opener}\n{body}\n}}"


@dataclass
class ShellWrap:
    id: int
    session: Any
    running: bool


@dataclass
class State:
    shells: dict[int | str, ShellWrap]


class CodeExecution(Tool):

    allow_running = False

    async def execute(self, **kwargs) -> Response:
        from helpers.parallel_tools import get_parallel_worker_job

        job = get_parallel_worker_job(self.agent)
        try:
            return await self._execute(job)
        finally:
            state = getattr(self, "state", None)
            if job and state:
                for shell in state.shells.values():
                    await shell.session.close()

    async def _execute(self, job) -> Response:
        await self.agent.handle_intervention()  # wait for intervention and handle it, if paused

        runtime_arg = str(self.args.get("runtime", "")).lower().strip()
        if runtime_arg in {"terminal", "python", "nodejs"} and not isinstance(self.args.get("code"), str):
            received = type(self.args["code"]).__name__ if "code" in self.args else "missing"
            raise RepairableException(
                f"code_execution_tool requires code to be a string for runtime {runtime_arg}; received {received}"
            )
        session = int(self.args.get("session", 0))
        reset = coerce_bool(self.args.get("reset", False), False) or runtime_arg == "reset"

        requested_destination = str(self.args.get("destination", "default") or "default")
        try:
            self.destination = await resolve_code_execution_destination(
                self.agent, requested_destination
            )
        except ValueError as exc:
            return Response(message=str(exc), break_loop=False)

        if self.destination.kind == "host":
            from plugins._a0_connector.helpers.host_execution import HostExecution

            ensure_retired_host_tool_allowed(self.agent, "code_execution_remote", tool_args=self.args)
            return await HostExecution(self.agent, self.args, allow_running=self.allow_running).execute()

        config = plugins.get_plugin_config("_code_execution", agent=self.agent) or {}
        if self.destination.kind == "local":
            # Older configurations could route "local" to a different machine.
            legacy_mode = config.get("ssh_enabled")
            if legacy_mode is None:
                legacy_mode = settings.get_default_value("_code_execution__ssh_enabled", "")
            if coerce_bool(legacy_mode, False) or (
                str(legacy_mode).strip().lower() == "auto" and runtime.is_development()
            ):
                return Response(
                    message="This configuration used SSH for local execution. Use a sandbox or the "
                    "connected host. To run on the Agent Zero machine, remove the old SSH setting "
                    "from the Code Execution configuration or environment.",
                    break_loop=False,
                )

        cfg = _parse_config(config)

        if runtime_arg == "python":
            response = await self.execute_python_code(
                cfg, code=self.args["code"], session=session, reset=reset
            )
        elif runtime_arg == "nodejs":
            response = await self.execute_nodejs_code(
                cfg, code=self.args["code"], session=session, reset=reset
            )
        elif runtime_arg == "terminal":
            response = await self.execute_terminal_command(
                cfg, command=self.args["code"], session=session, reset=reset
            )
        elif runtime_arg == "output":
            response = await self.get_terminal_output(
                cfg, session=session, timeouts=cfg["output_timeouts"]
            )
        elif runtime_arg == "reset":
            response = await self.reset_terminal(session=session)
        else:
            response = self.agent.read_prompt(
                "fw.code.runtime_wrong.md", runtime=runtime_arg
            )

        if job and runtime_arg in {"terminal", "python", "nodejs"}:
            while self._shell_wrap(session).running:
                job.result = response
                response = await self.get_terminal_output(
                    cfg, session=session, reset_full_output=False,
                    timeouts=cfg["output_timeouts"],
                )

        if not response:
            response = self.agent.read_prompt(
                "fw.code.info.md", info=self.agent.read_prompt("fw.code.no_output.md")
            )
        return Response(message=response, break_loop=False)

    def get_log_object(self):
        import uuid
        return self.agent.context.log.log(
            type="code_exe",
            heading=self.get_heading(),
            content="",
            kvps=self.args,
            id=str(uuid.uuid4()),
        )

    def get_heading(self, text: str = ""):
        if not text:
            text = f"{self.name} - {self.args['runtime'] if 'runtime' in self.args else 'unknown'}"
        session = self.args.get("session", None)
        destination = str(self.args.get("destination", "default") or "default")
        session_text = f"[{destination}/{session}] " if session or session == 0 else ""
        return f"icon://terminal {session_text}{truncate_text_string(text, 200)}"

    async def after_execution(self, response, **kwargs):
        self.agent.hist_add_tool_result(self.name, response.message, id=self.log.id if self.log else "", **(response.additional or {}))

    async def prepare_state(self, *, reset=False, session: int | None = None):
        self.state: State | None = self.agent.get_data("_cet_state")
        destination = self._destination()
        shells = self.state.shells.copy() if self.state else {}

        key = self._session_key(session) if session is not None else None

        # Only reset the specified session if provided
        if reset and key is not None and key in shells:
            await shells[key].session.close()
            del shells[key]
        elif reset and session is None:
            # Close all sessions if full reset requested
            for s in list(shells.keys()):
                await shells[s].session.close()
            shells = {}

        if session is not None and key not in shells:
            if destination.kind == "sandbox":
                from plugins._sandboxing.helpers.shell import SandboxInteractiveSession

                shell = SandboxInteractiveSession(
                    destination.target,
                    agent=self.agent,
                )
            else:
                cwd = await self.ensure_cwd()
                shell = LocalInteractiveSession(cwd=cwd)

            shells[key] = ShellWrap(id=session, session=shell, running=False)
            try:
                await shell.connect()
            except BaseException:
                await shell.close()
                raise

        self.state = State(shells=shells)
        self.agent.set_data("_cet_state", self.state)
        return self.state

    async def execute_python_code(self, cfg: dict, session: int, code: str, reset: bool = False):
        escaped_code = shlex.quote(code)
        runner = (
            f"{shlex.quote(sys.executable)} -m IPython"
            if self._destination().kind == "local" and not runtime.is_windows()
            else "ipython"
        )
        command = f"{runner} -c {escaped_code}"
        prefix = "python> " + self.format_command_for_output(code) + "\n\n"
        return await self.terminal_session(cfg, session, command, reset, prefix)

    async def execute_nodejs_code(self, cfg: dict, session: int, code: str, reset: bool = False):
        escaped_code = shlex.quote(code)
        command = (
            f"node -e {escaped_code}"
            if self._destination().kind == "sandbox"
            else f"node /exe/node_eval.js {escaped_code}"
        )
        prefix = "node> " + self.format_command_for_output(code) + "\n\n"
        return await self.terminal_session(cfg, session, command, reset, prefix)

    async def execute_terminal_command(
        self, cfg: dict, session: int, command: str, reset: bool = False
    ):
        powershell = self._destination().kind == "local" and runtime.is_windows()
        prefix = ("PS>" if powershell else "bash>") + self.format_command_for_output(command) + "\n\n"
        command = _group_multiline_command(command, powershell=powershell)
        return await self.terminal_session(cfg, session, command, reset, prefix)

    async def terminal_session(
        self, cfg: dict, session: int, command: str, reset: bool = False, prefix: str = "", timeouts: dict | None = None
    ):
        self.state = await self.prepare_state(reset=reset, session=session)

        await self.agent.handle_intervention()  # wait for intervention and handle it, if paused

        # Check if session is running and handle it
        if not self.allow_running:
            if response := await self.handle_running_session(cfg, session):
                return response

        # A strict-mode command can terminate the persistent shell itself.
        # Recreate such a session lazily before accepting the next command.
        if self._shell_wrap(session).session.is_terminated():
            await self.prepare_state(reset=True, session=session)

        # try again on lost connection
        for i in range(2):
            try:
                wrapper = self._shell_wrap(session)
                wrapper.running = True
                await wrapper.session.send_command(command)

                locl = f" ({self._destination().id})"

                PrintStyle(
                    background_color="white", font_color="#1B4F72", bold=True
                ).print(f"{self.agent.agent_name} code execution output{locl}")
                return await self.get_terminal_output(
                    cfg,
                    session=session,
                    prefix=prefix,
                    timeouts=(timeouts or cfg["code_exec_timeouts"]),
                )

            except Exception as e:
                if _is_closed_pty_error(e) and i == 0:
                    PrintStyle.warning(f"Terminal session {session} was closed; resetting and retrying once.")
                    await self.prepare_state(reset=True, session=session)
                    continue
                PrintStyle.error(str(e))
                raise

    def format_command_for_output(self, command: str):
        short_cmd = command[:250]
        short_cmd = " ".join(short_cmd.split())
        short_cmd = secrets.get_secrets_manager(self.agent.context).mask_values(short_cmd)
        short_cmd = truncate_text_string(short_cmd, 100)
        return f"{short_cmd}"

    async def get_terminal_output(
        self,
        cfg: dict,
        session=0,
        reset_full_output=True,
        first_output_timeout=30,
        between_output_timeout=15,
        dialog_timeout=5,
        max_exec_timeout=240,
        sleep_time=0.5,
        prefix="",
        timeouts: dict | None = None,
    ):
        self.state = await self.prepare_state(session=session)

        # Override timeouts if a dict is provided
        if timeouts:
            first_output_timeout = timeouts.get("first_output_timeout", first_output_timeout)
            between_output_timeout = timeouts.get("between_output_timeout", between_output_timeout)
            dialog_timeout = timeouts.get("dialog_timeout", dialog_timeout)
            max_exec_timeout = timeouts.get("max_exec_timeout", max_exec_timeout)

        prompt_patterns = cfg["prompt_patterns"]
        dialog_patterns = cfg["dialog_patterns"]

        start_time = time.time()
        last_output_time = start_time
        full_output = ""
        truncated_output = ""
        got_output = False

        # if prefix, log right away
        if prefix:
            self.log.update(content=prefix)

        while True:
            await asyncio.sleep(sleep_time)
            try:
                full_output, partial_output = await self._shell_wrap(session).session.read_output(
                    timeout=1, reset_full_output=reset_full_output
                )
            except Exception as e:
                if _is_closed_pty_error(e):
                    await self.prepare_state(reset=True, session=session)
                    self.mark_session_idle(session)
                    sysinfo = "Terminal session was closed and has been reset. Please run the command again."
                    response = self.agent.read_prompt("fw.code.info.md", info=sysinfo)
                    self.log.update(content=prefix + response)
                    return response
                raise
            reset_full_output = False  # only reset once

            await self.agent.handle_intervention()

            now = time.time()
            if partial_output:
                PrintStyle(font_color="#85C1E9").stream(partial_output)
                truncated_output = self.fix_full_output(full_output)
                await self.set_progress(truncated_output)
                heading = self.get_heading_from_output(truncated_output, 0)
                self.log.update(content=prefix + truncated_output, heading=heading)
                last_output_time = now
                got_output = True

            # A shell can exit without emitting a final prompt.
            shell = self._shell_wrap(session).session
            if shell.is_terminated():
                exit_code = shell.get_exit_code()
                status = f" with exit code {exit_code}" if exit_code is not None else ""
                sysinfo = self.agent.read_prompt(
                    "fw.code.shell_exit.md", status=status
                )
                response = self.agent.read_prompt("fw.code.info.md", info=sysinfo)
                if truncated_output:
                    response = truncated_output + "\n\n" + response
                PrintStyle.warning(sysinfo)
                heading = self.get_heading_from_output(truncated_output, 0, True)
                self.log.update(content=prefix + response, heading=heading)
                self.mark_session_idle(session)
                return response

            if partial_output:
                # Check for shell prompt at the end of output
                last_lines = (
                    truncated_output.splitlines()[-3:] if truncated_output else []
                )
                last_lines.reverse()
                for idx, line in enumerate(last_lines):
                    line = line.strip()
                    line = line if len(line) <= 500 else line[:250] + line[-250:] # only check start and end on long lines
                    for pat in prompt_patterns:
                        if pat.search(line):
                            PrintStyle.info(
                                "Detected shell prompt, returning output early."
                            )
                            last_lines.reverse()
                            heading = self.get_heading_from_output(
                                "\n".join(last_lines), idx + 1, True
                            )
                            self.log.update(heading=heading)
                            self.mark_session_idle(session)
                            return truncated_output

            # Check for max execution time
            if now - start_time > max_exec_timeout:
                sysinfo = self.agent.read_prompt(
                    "fw.code.max_time.md", timeout=max_exec_timeout
                )
                response = self.agent.read_prompt("fw.code.info.md", info=sysinfo)
                if truncated_output:
                    response = truncated_output + "\n\n" + response
                PrintStyle.warning(sysinfo)
                heading = self.get_heading_from_output(truncated_output, 0)
                self.log.update(content=prefix + response, heading=heading)
                return response

            # Waiting for first output
            if not got_output:
                if now - start_time > first_output_timeout:
                    sysinfo = self.agent.read_prompt(
                        "fw.code.no_out_time.md", timeout=first_output_timeout
                    )
                    response = self.agent.read_prompt("fw.code.info.md", info=sysinfo)
                    PrintStyle.warning(sysinfo)
                    self.log.update(content=prefix + response)
                    return response
            else:
                # Waiting for more output after first output
                if now - last_output_time > between_output_timeout:
                    sysinfo = self.agent.read_prompt(
                        "fw.code.pause_time.md", timeout=between_output_timeout
                    )
                    response = self.agent.read_prompt("fw.code.info.md", info=sysinfo)
                    if truncated_output:
                        response = truncated_output + "\n\n" + response
                    PrintStyle.warning(sysinfo)
                    heading = self.get_heading_from_output(truncated_output, 0)
                    self.log.update(content=prefix + response, heading=heading)
                    return response

                # potential dialog detection
                if now - last_output_time > dialog_timeout:
                    last_lines = (
                        truncated_output.splitlines()[-2:] if truncated_output else []
                    )
                    for line in last_lines:
                        for pat in dialog_patterns:
                            if pat.search(line.strip()):
                                PrintStyle.info(
                                    "Detected dialog prompt, returning output early."
                                )

                                sysinfo = self.agent.read_prompt(
                                    "fw.code.pause_dialog.md", timeout=dialog_timeout
                                )
                                response = self.agent.read_prompt(
                                    "fw.code.info.md", info=sysinfo
                                )
                                if truncated_output:
                                    response = truncated_output + "\n\n" + response
                                PrintStyle.warning(sysinfo)
                                heading = self.get_heading_from_output(
                                    truncated_output, 0
                                )
                                self.log.update(
                                    content=prefix + response, heading=heading
                                )
                                return response

    async def handle_running_session(
        self,
        cfg: dict,
        session=0,
        reset_full_output=True,
        prefix=""
    ):
        key = self._session_key(session)
        if not self.state or key not in self.state.shells:
            return None
        if not self.state.shells[key].running:
            return None

        prompt_patterns = cfg["prompt_patterns"]
        dialog_patterns = cfg["dialog_patterns"]

        try:
            full_output, _ = await self.state.shells[key].session.read_output(
                timeout=1, reset_full_output=reset_full_output
            )
        except Exception as e:
            if _is_closed_pty_error(e):
                await self.prepare_state(reset=True, session=session)
                self.mark_session_idle(session)
                return None
            raise
        truncated_output = self.fix_full_output(full_output)
        await self.set_progress(truncated_output)
        heading = self.get_heading_from_output(truncated_output, 0)

        if self.state.shells[key].session.is_terminated():
            self.mark_session_idle(session)
            return None

        last_lines = (
            truncated_output.splitlines()[-3:] if truncated_output else []
        )
        last_lines.reverse()
        for line in last_lines:
            for pat in prompt_patterns:
                if pat.search(line.strip()):
                    PrintStyle.info(
                        "Detected shell prompt, returning output early."
                    )
                    self.mark_session_idle(session)
                    return None

        has_dialog = False
        for line in last_lines:
            for pat in dialog_patterns:
                if pat.search(line.strip()):
                    has_dialog = True
                    break
            if has_dialog:
                break

        if has_dialog:
            sys_info = self.agent.read_prompt("fw.code.pause_dialog.md", timeout=1)
        else:
            sys_info = self.agent.read_prompt("fw.code.running.md", session=session)

        response = self.agent.read_prompt("fw.code.info.md", info=sys_info)
        if truncated_output:
            response = truncated_output + "\n\n" + response
        PrintStyle(font_color="#FFA500", bold=True).print(response)
        self.log.update(content=prefix + response, heading=heading)
        return response

    def mark_session_idle(self, session: int = 0):
        key = self._session_key(session)
        if self.state and key in self.state.shells:
            self.state.shells[key].running = False

    async def reset_terminal(self, session=0, reason: str | None = None):
        if reason:
            PrintStyle(font_color="#FFA500", bold=True).print(
                f"Resetting terminal session {session}... Reason: {reason}"
            )
        else:
            PrintStyle(font_color="#FFA500", bold=True).print(
                f"Resetting terminal session {session}..."
            )

        await self.prepare_state(reset=True, session=session)
        response = self.agent.read_prompt(
            "fw.code.info.md", info=self.agent.read_prompt("fw.code.reset.md")
        )
        self.log.update(content=response)
        return response

    def get_heading_from_output(self, output: str, skip_lines=0, done=False):
        done_icon = " icon://done_all" if done else ""

        if not output:
            return self.get_heading() + done_icon

        lines = output.splitlines()
        for i in range(len(lines) - skip_lines - 1, -1, -1):
            line = lines[i].strip()
            if not line:
                continue
            return self.get_heading(line) + done_icon

        return self.get_heading() + done_icon

    def fix_full_output(self, output: str):
        output = re.sub(r"(?<!\\)\\x[0-9A-Fa-f]{2}", "", output)
        output = truncate_text_agent(agent=self.agent, output=output, threshold=1000000)
        return output

    def _destination(self) -> ExecutionDestination:
        destination = getattr(self, "destination", None)
        if isinstance(destination, ExecutionDestination):
            return destination
        return ExecutionDestination(
            id="local",
            kind="local",
            label="Agent Zero system",
            description="Local compatibility destination.",
        )

    def _session_key(self, session: int | None) -> int | str:
        if session is None:
            raise ValueError("session is required")
        destination = self._destination()
        return session if destination.id == "local" else f"{destination.id}:{session}"

    def _shell_wrap(self, session: int) -> ShellWrap:
        if not self.state:
            raise RuntimeError("Code execution state is not prepared")
        return self.state.shells[self._session_key(session)]

    async def ensure_cwd(self) -> str | None:
        project_name = projects.get_context_project_name(self.agent.context)
        if project_name:
            path = projects.get_project_folder(project_name)
        else:
            path = settings.get_settings().get("workdir_path")
        if not path:
            return None

        normalized = files.fix_dev_path(path)
        make_dir(normalized)
        return normalized


# ------------------------------------------------------------------
# Internal
# ------------------------------------------------------------------

def _parse_patterns(raw, flags=0) -> list[re.Pattern]:
    lines = [str(p) for p in raw] if isinstance(raw, list) else str(raw).splitlines()
    return [re.compile(p.strip(), flags) for p in lines if p.strip()]


_TIMEOUT_KEYS = ("first_output_timeout", "between_output_timeout", "max_exec_timeout", "dialog_timeout")


def _parse_timeouts(cfg: dict, prefix: str, defaults: tuple[int, ...]) -> dict:
    return {
        key: int(cfg.get(f"{prefix}_{key}", default))
        for key, default in zip(_TIMEOUT_KEYS, defaults)
    }


def _parse_config(cfg: dict) -> dict:
    return {
        "code_exec_timeouts": _parse_timeouts(cfg, "code_exec", (30, 15, 240, 5)),
        "output_timeouts": _parse_timeouts(cfg, "output", (120, 60, 600, 5)),
        "prompt_patterns": _parse_patterns(cfg.get("prompt_patterns", "")),
        "dialog_patterns": _parse_patterns(cfg.get("dialog_patterns", ""), re.IGNORECASE),
    }


def make_dir(path: str):
    import os
    os.makedirs(path, exist_ok=True)
