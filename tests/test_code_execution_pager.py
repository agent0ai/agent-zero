"""Regression tests for code execution shell lifecycle behavior.

Pagers (more/less) must be disabled in the non-interactive shells created by the
code execution tool: without user input they block forever and spin at 100% CPU.
"""

import asyncio

from plugins._code_execution.helpers import shell_local, shell_ssh
from plugins._code_execution.helpers.tty_session import TTYSession
from plugins._code_execution.tools.code_execution_tool import _group_multiline_command


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


def test_ssh_command_disables_pagers():
    assert "GIT_PAGER=cat" in shell_ssh.PAGER_DISABLE_COMMAND
    assert "PAGER=cat" in shell_ssh.PAGER_DISABLE_COMMAND


def test_multiline_terminal_commands_are_one_current_shell_compound():
    assert _group_multiline_command("pwd") == "pwd"
    assert _group_multiline_command("cd /tmp\npwd") == "{\ncd /tmp\npwd\n}"
    assert _group_multiline_command("$env:FOO='bar'\n$env:FOO", powershell=True) == (
        ". {\n$env:FOO='bar'\n$env:FOO\n}"
    )


def test_tty_close_kills_term_resistant_process():
    async def run():
        session = TTYSession("bash -lc 'trap \"\" TERM; sleep 30'")
        await session.start()
        await asyncio.wait_for(session.close(), timeout=6)
        assert session._proc is None

    asyncio.run(run())
