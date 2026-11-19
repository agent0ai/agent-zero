"""Regression tests for code execution shell lifecycle behavior.

Pagers (more/less) must be disabled in the non-interactive shells created by the
code execution tool: without user input they block forever and spin at 100% CPU.
"""

import asyncio
from types import SimpleNamespace

from helpers.strings import clean_string
from plugins._code_execution.helpers import shell_local
from plugins._code_execution.helpers.tty_session import TTYSession
from plugins._code_execution.tools.code_execution_tool import (
    CodeExecution,
    ShellWrap,
    State,
    _group_multiline_command,
    _is_closed_pty_error,
)


def test_local_env_disables_pagers_and_preserves_existing():
    env = shell_local.disable_pagers_in_env({"PATH": "/usr/bin", "PAGER": "less"})
    assert env["PAGER"] == "cat"
    assert env["GIT_PAGER"] == "cat"
    # pre-existing keys are preserved
    assert env["PATH"] == "/usr/bin"


def test_local_env_defaults_to_environ():
    env = shell_local.disable_pagers_in_env()
    assert env["PAGER"] == "cat"
    assert env["GIT_PAGER"] == "cat"


def test_local_env_does_not_mutate_input():
    src = {"PATH": "/usr/bin"}
    shell_local.disable_pagers_in_env(src)
    assert src == {"PATH": "/usr/bin"}


def test_shell_output_preserves_unicode_and_last_progress_update():
    raw = "\r\r\n> > \x1b[32mfirst\x1b[0m\x00\r\n10%\r100% ✓\r\n"
    assert clean_string(raw) == "first\n100% ✓\n"


def test_multiline_terminal_commands_are_one_current_shell_compound():
    assert _group_multiline_command("pwd") == "pwd"
    assert _group_multiline_command("cd /tmp\npwd") == "{\ncd /tmp\npwd\n}"
    assert _group_multiline_command("$env:FOO='bar'\n$env:FOO", powershell=True) == (
        ". {\n$env:FOO='bar'\n$env:FOO\n}"
    )


def test_exited_tty_process_is_a_recoverable_closed_session():
    assert _is_closed_pty_error(RuntimeError("TTYSpawn process has exited"))


def test_tty_close_kills_term_resistant_process():
    async def run():
        session = TTYSession("bash -lc 'trap \"\" TERM; sleep 30'")
        await session.start()
        await asyncio.wait_for(session.close(), timeout=6)
        assert session._proc is None

    asyncio.run(run())


def test_tty_reports_strict_mode_shell_exit():
    async def run():
        session = TTYSession("/bin/bash --noprofile --norc -i")
        await session.start()
        await session.read_full_until_idle(idle_timeout=0.05, total_timeout=1)
        await session.sendline("{\nset -euo pipefail\nfalse\nprintf 'unreachable\\n'\n}")

        exit_code = await asyncio.wait_for(session.wait(), timeout=5)

        assert exit_code != 0
        assert session.is_terminated()
        assert session.get_exit_code() == exit_code
        await session.close()

    asyncio.run(run())


def test_code_execution_returns_immediately_when_shell_exits():
    class FinishedSession:
        async def read_output(self, timeout=0, reset_full_output=False):
            return "nothing to commit, working tree clean\n", "nothing to commit, working tree clean\n"

        @staticmethod
        def is_terminated():
            return True

        @staticmethod
        def get_exit_code():
            return 1

    class FakeAgent:
        agent_name = "test"

        async def handle_intervention(self):
            return None

        @staticmethod
        def read_prompt(name, **kwargs):
            if name == "fw.code.shell_exit.md":
                return f"Terminal shell exited{kwargs['status']}. The command has finished."
            if name == "fw.code.info.md":
                return f"[SYSTEM: {kwargs['info']}]"
            raise AssertionError(f"Unexpected prompt: {name}")

    async def run():
        session = FinishedSession()
        state = State(
            shells={0: ShellWrap(id=0, session=session, running=True)},
        )
        tool = CodeExecution(
            FakeAgent(),
            "code_execution_tool",
            "",
            {"runtime": "terminal", "session": 0},
            "",
            None,
        )
        updates = []
        tool.log = SimpleNamespace(update=lambda **kwargs: updates.append(kwargs))

        async def prepare_state(*args, **kwargs):
            return state

        async def set_progress(content):
            return None

        tool.prepare_state = prepare_state
        tool.set_progress = set_progress
        tool.fix_full_output = lambda output: output

        response = await tool.get_terminal_output(
            {"prompt_patterns": [], "dialog_patterns": []},
            session=0,
            sleep_time=0,
        )

        assert "nothing to commit" in response
        assert "exit code 1" in response
        assert "command has finished" in response
        assert not state.shells[0].running
        assert updates[-1]["heading"].endswith(" icon://done_all")

    asyncio.run(run())
