import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from helpers import responses_tools


class FakeAgent:
    def __init__(self, prompt_root: Path):
        self.prompt_root = prompt_root

    def read_prompt(self, file: str, **kwargs) -> str:
        return (self.prompt_root / file).read_text(encoding="utf-8")


def _write_prompt(prompt_root: Path, basename: str, content: str) -> None:
    (prompt_root / basename).write_text(content.strip() + "\n", encoding="utf-8")


def test_responses_function_tools_use_prompt_declared_names(monkeypatch, tmp_path):
    prompt_root = tmp_path / "prompts"
    prompt_root.mkdir()
    _write_prompt(
        prompt_root,
        "agent.system.tool.code_exe.md",
        """
        ### code_execution_tool
        run terminal commands
        ```json
        {"tool_name": "code_execution_tool", "tool_args": {"runtime": "terminal"}}
        ```
        """,
    )
    _write_prompt(
        prompt_root,
        "agent.system.tool.memory.md",
        """
        ## memory tools
        durable memory operations
        ```json
        {"tool_name": "memory_load", "tool_args": {"query": "responses naming"}}
        ```
        """,
    )
    _write_prompt(
        prompt_root,
        "agent.system.tool.call_sub.md",
        """
        ### call_subordinate
        delegate a subtask
        ```json
        {"tool_name": "call_subordinate", "tool_args": {"message": "inspect"}}
        ```
        """,
    )
    _write_prompt(
        prompt_root,
        "agent.system.tool.behaviour.md",
        """
        ### behaviour_adjustment
        update persistent behavioral rules
        """,
    )
    _write_prompt(
        prompt_root,
        "agent.system.tool.filename_only.md",
        "plain prompt with no declared callable name",
    )

    monkeypatch.setattr(
        responses_tools.subagents,
        "get_paths",
        lambda *args, **kwargs: [str(prompt_root)],
    )
    monkeypatch.setattr(
        responses_tools,
        "_include_local_tool_prompt",
        lambda agent, tool_name: True,
    )
    monkeypatch.setattr(responses_tools, "_mcp_tools", lambda agent: [])

    tools, name_map = responses_tools.build_responses_function_tools(
        FakeAgent(prompt_root)
    )

    names = {tool["name"] for tool in tools}
    assert {
        "code_execution_tool",
        "memory_load",
        "call_subordinate",
        "behaviour_adjustment",
        "filename_only",
    } <= names
    assert not {"code_exe", "memory", "call_sub", "behaviour"} & names
    assert name_map["code_execution_tool"] == "code_execution_tool"
    assert name_map["memory_load"] == "memory_load"
    assert name_map["call_subordinate"] == "call_subordinate"
    assert name_map["behaviour_adjustment"] == "behaviour_adjustment"
    assert name_map["filename_only"] == "filename_only"
    assert all(isinstance(tool["parameters"].get("properties"), dict) for tool in tools)


def test_responses_function_tools_add_empty_properties_to_mcp_schemas(
    monkeypatch,
    tmp_path,
):
    prompt_root = tmp_path / "prompts"
    prompt_root.mkdir()

    monkeypatch.setattr(
        responses_tools.subagents,
        "get_paths",
        lambda *args, **kwargs: [str(prompt_root)],
    )
    monkeypatch.setattr(
        responses_tools,
        "_mcp_tools",
        lambda agent: [
            (
                "remote_noop",
                {
                    "description": "Remote noop",
                    "input_schema": {"type": "object"},
                },
            )
        ],
    )

    tools, _name_map = responses_tools.build_responses_function_tools(
        FakeAgent(prompt_root)
    )

    assert tools == [
        {
            "type": "function",
            "name": "remote_noop",
            "description": "Remote noop",
            "parameters": {
                "type": "object",
                "properties": {},
                "additionalProperties": True,
            },
        }
    ]
