from __future__ import annotations

import sys
import types
from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from extensions.python.tool_execute_before._10_unmask_secrets import UnmaskToolSecrets
from helpers import secrets as secrets_module


class _Context:
    def get_data(self, key: str):
        return None


class _FakeAgent:
    def __init__(self) -> None:
        self.context = _Context()


def _patch_secrets(monkeypatch, secrets_env: str = "SOME_SECRET_TOKEN=actual-token-value\n"):
    monkeypatch.setattr(secrets_module.SecretsManager, "_instances", {})
    monkeypatch.setattr(secrets_module.dotenv, "get_dotenv_file_path", lambda: "usr/.env")
    contents = {"usr/secrets.env": secrets_env, "usr/.env": ""}
    monkeypatch.setattr(secrets_module.files, "read_file", contents.__getitem__)

    # helpers.extension's @extensible decorator does `from agent import Agent`
    # on every call to check the call's agent argument. Stub the heavy `agent`
    # module (which pulls in litellm etc.) the same way tests/test_error_retry_plugin.py
    # does, since none of this test's calls are actually `agent.Agent` instances.
    agent_stub = types.ModuleType("agent")

    class _StubAgent:
        pass

    class _StubAgentContextType:
        BACKGROUND = "background"

    agent_stub.Agent = _StubAgent  # type: ignore[attr-defined]
    agent_stub.AgentConfig = _StubAgent  # type: ignore[attr-defined]
    agent_stub.AgentContext = _StubAgent  # type: ignore[attr-defined]
    agent_stub.AgentContextType = _StubAgentContextType  # type: ignore[attr-defined]
    agent_stub.LoopData = object  # type: ignore[attr-defined]
    monkeypatch.setitem(sys.modules, "agent", agent_stub)

    # helpers.extension's extension-point lookup pulls in helpers.subagents,
    # which in turn drags in helpers.plugins (git/giturlparse/etc.) purely to
    # discover extension folders. None of that affects the UnmaskToolSecrets
    # instance under test (constructed and called directly), so short-circuit
    # extension-point discovery to an empty list instead of pulling in the
    # whole plugin/subagent machinery.
    from helpers import extension as extension_module

    monkeypatch.setattr(extension_module, "_get_extension_classes", lambda *a, **k: [])

    # helpers.secrets.get_secrets_manager unconditionally imports helpers.projects
    # (even when there is no active project) purely to look up an optional
    # per-project secrets file. That module transitively pulls in chat
    # persistence, tokenizers (tiktoken) and LLM call plumbing that this test
    # has nothing to do with, so stub it down to the one function actually used.
    projects_stub = types.ModuleType("helpers.projects")
    projects_stub.get_context_project_name = lambda context: None  # type: ignore[attr-defined]
    monkeypatch.setitem(sys.modules, "helpers.projects", projects_stub)


@pytest.mark.asyncio
async def test_unmask_secrets_recurses_into_parallel_tool_calls(monkeypatch):
    _patch_secrets(monkeypatch)

    # shape of a `parallel` tool call: the placeholder lives inside a nested
    # tool_calls[].tool_args dict, not a top-level string
    tool_args = {
        "tool_calls": [
            {
                "tool_name": "code_execution_tool",
                "tool_args": {
                    "code": (
                        "curl -H 'Authorization: Bearer "
                        "§§secret(SOME_SECRET_TOKEN)' https://example.com/api"
                    ),
                },
            }
        ]
    }

    await UnmaskToolSecrets(agent=_FakeAgent()).execute(tool_args=tool_args)

    inner_code = tool_args["tool_calls"][0]["tool_args"]["code"]
    assert "actual-token-value" in inner_code
    assert "§§secret(SOME_SECRET_TOKEN)" not in inner_code


@pytest.mark.asyncio
async def test_unmask_secrets_still_substitutes_top_level_strings(monkeypatch):
    _patch_secrets(monkeypatch)

    tool_args = {"code": "token=§§secret(SOME_SECRET_TOKEN)"}
    await UnmaskToolSecrets(agent=_FakeAgent()).execute(tool_args=tool_args)

    assert tool_args["code"] == "token=actual-token-value"


@pytest.mark.asyncio
async def test_unmask_secrets_noop_without_agent():
    # no agent attached (e.g. extension instantiated without context): must
    # not raise, must leave args untouched
    tool_args = {"code": "§§secret(SOME_SECRET_TOKEN)"}
    await UnmaskToolSecrets(agent=None).execute(tool_args=tool_args)
    assert tool_args["code"] == "§§secret(SOME_SECRET_TOKEN)"
