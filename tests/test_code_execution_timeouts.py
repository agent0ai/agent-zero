"""Regression tests for the code execution timeout families.

The automatic re-poll loop in ``_execute`` must use the ``code_exec`` timeout
family and one cumulative deadline shared across re-polls; ``runtime:output``
keeps the ``output`` family. Exhausting the deadline without output returns an
explicit failure prompt instead of a "might still be running" marker.
"""

import asyncio
import inspect
import time

from plugins._code_execution.tools.code_execution_tool import (
    CodeExecution,
    _parse_timeouts,
    _TIMEOUT_KEYS,
)

PROMPTS_DIR = "/a0/plugins/_code_execution/prompts"


# ---------------------------------------------------------------------
# Fakes
# ---------------------------------------------------------------------


def _render_prompt(name: str, **kwargs) -> str:
    """Render a real prompt file so template variables are exercised."""
    with open(f"{PROMPTS_DIR}/{name}", encoding="utf-8") as fh:
        text = fh.read()
    for key, value in kwargs.items():
        text = text.replace("{{" + key + "}}", str(value))
    return text


class _FakeAgent:
    agent_name = "test-agent"

    def read_prompt(self, name: str, **kwargs) -> str:
        return _render_prompt(name, **kwargs)

    async def handle_intervention(self):
        return None


class _FakeLog:
    def update(self, **kwargs):
        return None


class _IdleShell:
    """Never produces output and never terminates."""

    def __init__(self):
        self.reads = 0

    def is_terminated(self) -> bool:
        return False

    def get_exit_code(self):
        return None

    async def read_output(self, timeout=0, reset_full_output=False):
        self.reads += 1
        return ("", "")


class _Wrap:
    def __init__(self):
        self.id = 0
        self.session = _IdleShell()
        self.running = True


class _State:
    def __init__(self):
        self.ssh_enabled = False
        self.shells = {0: _Wrap()}


def _cfg() -> dict:
    return {
        "prompt_patterns": [],
        "dialog_patterns": [],
        "code_exec_timeouts": _parse_timeouts({}, "code_exec", (30, 15, 240, 5)),
        "output_timeouts": _parse_timeouts({}, "output", (120, 60, 600, 5)),
    }


def _make_tool(cfg: dict) -> CodeExecution:
    tool = CodeExecution(
        agent=_FakeAgent(),
        name="code_execution_tool",
        method=None,
        args={"runtime": "terminal", "code": "true", "session": 0},
        message="",
        loop_data=None,
    )
    tool.log = _FakeLog()
    tool.state = _State()
    tool.execution_failed = False

    async def _prepare_state(*args, **kwargs):
        return tool.state

    async def _set_progress(content=None):
        return None

    tool.prepare_state = _prepare_state
    tool.set_progress = _set_progress
    return tool


# ---------------------------------------------------------------------
# (a) timeout family parsing
# ---------------------------------------------------------------------


def test_parse_timeouts_maps_both_prefixes():
    cfg = {
        "code_exec_first_output_timeout": 15,
        "code_exec_between_output_timeout": 20,
        "code_exec_max_exec_timeout": 120,
        "code_exec_dialog_timeout": 30,
        "output_first_output_timeout": 60,
        "output_between_output_timeout": 300,
        "output_max_exec_timeout": 1800,
        "output_dialog_timeout": 60,
    }

    code_exec = _parse_timeouts(cfg, "code_exec", (30, 15, 240, 5))
    output = _parse_timeouts(cfg, "output", (120, 60, 600, 5))

    assert code_exec == dict(zip(_TIMEOUT_KEYS, (15, 20, 120, 30)))
    assert output == dict(zip(_TIMEOUT_KEYS, (60, 300, 1800, 60)))
    # the families must not bleed into each other
    assert code_exec["first_output_timeout"] != output["first_output_timeout"]


def test_parse_timeouts_falls_back_to_defaults():
    assert _parse_timeouts({}, "code_exec", (30, 15, 240, 5)) == dict(
        zip(_TIMEOUT_KEYS, (30, 15, 240, 5))
    )
    assert _parse_timeouts({}, "output", (120, 60, 600, 5)) == dict(
        zip(_TIMEOUT_KEYS, (120, 60, 600, 5))
    )


# ---------------------------------------------------------------------
# (b) the re-poll loop uses the code_exec family and one deadline
# ---------------------------------------------------------------------


def test_repoll_loop_uses_code_exec_timeouts_and_deadline():
    src = inspect.getsource(CodeExecution._execute)

    repoll = src.split("if job and runtime_arg in", 1)[1]
    assert 'timeouts=cfg["code_exec_timeouts"]' in repoll
    assert "deadline=deadline" in repoll
    assert "attempts=attempts" in repoll
    assert 'timeouts=cfg["output_timeouts"]' not in repoll

    output_branch = src.split('elif runtime_arg == "output"', 1)[1].split(
        "elif runtime_arg", 1
    )[0]
    assert 'timeouts=cfg["output_timeouts"]' in output_branch


def test_deadline_exits_the_poll_loop_instead_of_repeating_markers():
    cfg = _cfg()
    tool = _make_tool(cfg)

    started = time.time()
    response = asyncio.run(
        tool.get_terminal_output(
            cfg,
            session=0,
            timeouts=cfg["code_exec_timeouts"],
            deadline=time.time() - 1,  # already exhausted
            attempts=2,
        )
    )
    elapsed = time.time() - started

    assert elapsed < 5, f"deadline path must return promptly, took {elapsed:.1f}s"
    assert tool.execution_failed is True
    assert response


def test_deadline_expiry_does_not_idle_the_session():
    """The shell may still be running; handle_running_session guidance must survive."""
    cfg = _cfg()
    tool = _make_tool(cfg)

    asyncio.run(
        tool.get_terminal_output(
            cfg,
            session=0,
            timeouts=cfg["code_exec_timeouts"],
            deadline=time.time() - 1,
            attempts=1,
        )
    )

    assert tool.state.shells[0].running is True


# ---------------------------------------------------------------------
# (c) the failure path returns the failure prompt, filled in
# ---------------------------------------------------------------------


def test_deadline_exhaustion_returns_failure_prompt():
    cfg = _cfg()
    tool = _make_tool(cfg)

    response = asyncio.run(
        tool.get_terminal_output(
            cfg,
            session=0,
            timeouts=cfg["code_exec_timeouts"],
            deadline=time.time() - 1,
            attempts=2,
        )
    )

    assert "Code execution FAILED" in response
    assert "2 polling attempts" in response
    assert "session 0" in response
    # failed call, not a completed run
    assert "do not treat it as finished" in response
    assert "runtime=output" in response
    assert "reset=true" in response


def test_without_deadline_markers_still_report_enforced_timeout():
    """Existing markers keep reporting the value actually enforced."""
    cfg = _cfg()
    cfg["code_exec_timeouts"]["first_output_timeout"] = 0
    tool = _make_tool(cfg)

    response = asyncio.run(
        tool.get_terminal_output(
            cfg, session=0, timeouts=cfg["code_exec_timeouts"]
        )
    )

    assert tool.execution_failed is False
    assert "0 seconds with no output" in response
