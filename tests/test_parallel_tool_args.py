from __future__ import annotations

from types import SimpleNamespace

import pytest

from helpers import parallel_tools


class _Response:
    message = "done"


@pytest.mark.asyncio
async def test_parallel_execute_applies_hook_mutations_to_tool_args(
    monkeypatch,
) -> None:
    observed = {}

    class FakeTool:
        def __init__(self, args):
            self.args = args

        def get_log_object(self):
            return None

        async def before_execution(self, **kwargs):
            pass

        async def execute(self, **kwargs):
            observed["tool_args"] = self.args
            observed["kwargs"] = kwargs
            return _Response()

        async def after_execution(self, response):
            pass

    class FakeAgent:
        context = SimpleNamespace()
        loop_data = SimpleNamespace(current_tool=None)

        def get_tool(self, **kwargs):
            return FakeTool(kwargs["args"])

        async def handle_intervention(self):
            pass

    async def unmask_secret(*_args, **kwargs):
        if not _args or _args[0] != "tool_execute_before":
            return
        tool_args = kwargs["tool_args"]
        tool_args["code"] = tool_args["code"].replace(
            "§§secret(TOKEN)", "resolved-secret"
        )

    monkeypatch.setattr(parallel_tools, "call_extensions_async", unmask_secret)
    worker_args = {"code": "curl -H 'Authorization: Bearer §§secret(TOKEN)'"}

    result = await parallel_tools.execute_tool_call(
        FakeAgent(),  # type: ignore[arg-type]
        "code_execution_tool",
        worker_args,
    )

    assert result == "done"
    assert observed["tool_args"] is worker_args
    assert observed["tool_args"]["code"] == (
        "curl -H 'Authorization: Bearer resolved-secret'"
    )
    assert observed["kwargs"]["code"] == (
        "curl -H 'Authorization: Bearer resolved-secret'"
    )
