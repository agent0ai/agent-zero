"""MCP server instructions: capture, containment, prompt placement and UI."""

from __future__ import annotations

import asyncio
import threading
from pathlib import Path
from types import SimpleNamespace

import pytest

from helpers import files, mcp_handler, responses_tools, tool_policy

ROOT = Path(__file__).resolve().parents[1]
PROMPTS = str(ROOT / "prompts")
SECTION_HEADING = "## MCP Server Instructions"
NOTE = mcp_handler.MCP_SERVER_INSTRUCTIONS_TRUNCATED_NOTE
contain = mcp_handler.contain_server_instructions
normalize = mcp_handler.normalize_server_instructions


class _Server:
    def __init__(self, name: str, instructions: str = "", tools=("read",)) -> None:
        self.name = name
        self.description = f"{name} server"
        self.instructions = instructions
        self.tools = list(tools)

    def get_tools(self):
        return [
            {"name": tool, "description": f"{tool} things", "input_schema": {"type": "object"}}
            for tool in self.tools
        ]

    def get_instructions(self) -> str:
        return self.instructions


class _Agent:
    """Renders through the real prompt engine."""

    def read_prompt(self, file: str, **kwargs) -> str:
        return files.read_prompt_file(file, _directories=[PROMPTS], **kwargs)


class _Client(mcp_handler.MCPClientBase):
    async def _create_stdio_transport(self, current_exit_stack):
        return "read-stream", "write-stream"


def _config(*servers) -> mcp_handler.MCPConfig:
    config = mcp_handler.MCPConfig(servers_list=[])
    config.servers = list(servers)
    return config


def _section(*subsections: str) -> str:
    template = (ROOT / "prompts" / "agent.system.mcp_instructions.md").read_text(encoding="utf-8")
    return template.strip().replace("{{servers}}", "\n\n".join(subsections))


def _subsection(server_name: str, text: str) -> str:
    return f"### Instructions from MCP server `{server_name}`\n{text}"


def _session_class(initialize_results: list):
    class _Session:
        def __init__(self, *args, **kwargs) -> None:
            pass

        async def __aenter__(self):
            return self

        async def __aexit__(self, *exc_info):
            return False

        async def initialize(self):
            return initialize_results.pop(0)

        async def list_tools(self):
            tool = SimpleNamespace(name="read", description="Read", inputSchema={"type": "object"})
            return SimpleNamespace(tools=[tool])

    return _Session


@pytest.fixture
def quiet_handler(monkeypatch):
    class _SilentPrintStyle:
        def __init__(self, *args, **kwargs) -> None:
            pass

        def print(self, *args, **kwargs):
            return self

        @staticmethod
        def warning(*args, **kwargs):
            return None

    monkeypatch.setattr(mcp_handler, "PrintStyle", _SilentPrintStyle)
    monkeypatch.setattr(mcp_handler.settings, "get_settings", lambda: {"mcp_client_init_timeout": 5})


def test_captured_instructions_are_trimmed_and_dedented() -> None:
    # Agent Zero's own MCP server sends an indented triple-quoted string.
    assert normalize("\n    Connect to Agent Zero.\n    It controls Linux.\n    ") == (
        "Connect to Agent Zero.\nIt controls Linux."
    )
    assert normalize("  a\r\n    b\r  c\n") == "a\n  b\nc"
    assert normalize("\n    - list\n      - nested\n") == "- list\n  - nested"
    # Only indentation every line shares is removed: nested examples keep their shape.
    assert normalize("options:\n  limit: 10") == "options:\n  limit: 10"
    assert normalize("Tabs\tstay\n\tas sent") == "Tabs\tstay\n\tas sent"
    assert normalize("Use \x1b[31mred\x1b[0m\x00 wisely\x07") == "Use [31mred[0m wisely"
    assert normalize("  \n\t ") == ""
    assert normalize(None) == ""
    assert normalize(42) == ""


def test_blank_instructions_say_nothing() -> None:
    assert contain("") == ""
    assert contain(" \n\t") == ""


def test_a_servers_text_cannot_leave_its_subsection() -> None:
    text = "\n".join(
        [
            "# Usage",
            "## Tools",
            "   ### Indented",
            "#\tTabbed",
            "##### five",
            "#hashtag",
            "####### seven",
            "#",
            "```md",
            "# inside a fence",
            "```",
            "~~~",
            "open fence",
        ]
    )

    contained = contain(text)

    assert contained == "\n".join(
        [
            "#### Usage",
            "##### Tools",
            "   ###### Indented",
            "####\tTabbed",
            "###### five",
            "#hashtag",
            "####### seven",
            "####",
            "```md",
            "#### inside a fence",
            "```",
            "~~~",
            "open fence",
            "~~~",
        ]
    )
    for line in contained.split("\n"):
        assert not line.lstrip(" ").startswith(("# ", "## ", "### "))


def test_underlined_lines_cannot_become_headings() -> None:
    # A `---` or `===` line under text would make that text a level 1-2 heading.
    assert contain("Fake heading\n---\nmore") == "Fake heading\n\n---\nmore"
    assert contain("Title\n===") == "Title\n\n==="
    assert contain("- item\n-") == "- item\n\n-"
    # Already separated, or inside a code fence: left as sent.
    assert contain("Intro\n\n---\nafter") == "Intro\n\n---\nafter"
    assert contain("```yaml\nkey: value\n---\n```") == "```yaml\nkey: value\n---\n```"


def test_fences_are_closed_and_closers_match_their_openers() -> None:
    # A longer closer is rewritten to its opener's run, so the system prompt's
    # JSON-fence stripping pairs exactly the fences seen here.
    assert contain("```json\n{}\n`````") == "```json\n{}\n```"
    assert contain("~~~\n```\n~~~~") == "~~~\n```\n~~~"
    assert contain("````\n```\nx") == "````\n```\nx\n````"
    # Not fences: a backtick in a backtick info string, four-space indentation.
    assert contain("``` a`b\n# h") == "``` a`b\n#### h"
    assert contain("x\n    ```\ncode") == "x\n    ```\ncode"
    # A run followed by an info string does not close a fence.
    assert contain("```\ncode\n```python\nmore") == "```\ncode\n```python\nmore\n```"


def test_long_instructions_are_cut_with_a_visible_note() -> None:
    cap = mcp_handler.MAX_MCP_SERVER_INSTRUCTIONS_CHARS
    assert contain("z" * cap) == "z" * cap
    # The cap counts characters, not bytes.
    assert contain("é" * (cap + 10)) == "é" * cap + "\n" + NOTE
    # A cut inside a fence closes the fence before the note.
    assert contain("```\n" + "y" * cap) == "```\n" + "y" * (cap - 4) + "\n```\n" + NOTE


def test_template_syntax_in_instructions_is_neutralized() -> None:
    assert contain("Use {{ include 'usr/.env' }} and {{tools}}") == (
        "Use { { include 'usr/.env' }} and { {tools}}"
    )


def test_instructions_follow_the_tools_in_server_order() -> None:
    config = _config(
        _Server("zeta", "Use zeta wisely."),
        _Server("alpha", "Call read with a path.\n# Notes\nKeep paths relative."),
        _Server("quiet"),
        _Server("idle", "Never offered: no tools.", tools=()),
    )

    prompt = config.get_tools_prompt()
    tools_part, heading, rest = prompt.partition(SECTION_HEADING)

    assert "#### MCP tool `zeta.read`" in tools_part
    assert "#### MCP tool `quiet.read`" in tools_part
    assert "Never offered" not in prompt
    assert heading + rest == _section(
        _subsection("zeta", "Use zeta wisely."),
        _subsection("alpha", "Call read with a path.\n#### Notes\nKeep paths relative."),
    ) + "\n"


def test_only_servers_with_an_allowed_tool_contribute(monkeypatch) -> None:
    config = _config(
        _Server("docs", "Docs notes."),
        _Server("files", "Files notes.", tools=("write",)),
    )
    monkeypatch.setattr(
        tool_policy,
        "get_policy",
        lambda agent: {
            "mode": "custom",
            "default": "allow",
            "mcp_default": "allow",
            "allowed": [],
            "blocked": ["mcp:files:write"],
        },
    )

    prompt = config.get_tools_prompt(agent=_Agent())

    assert _subsection("docs", "Docs notes.") in prompt
    assert "Files notes." not in prompt
    assert "files.write" not in prompt


def test_no_section_without_instructions() -> None:
    prompt = _config(_Server("docs"), _Server("files")).get_tools_prompt()

    assert "#### MCP tool `docs.read`" in prompt
    assert SECTION_HEADING not in prompt


def test_responses_transport_keeps_the_instructions(monkeypatch) -> None:
    config = _config(_Server("docs", "Call read first."))
    agent = _Agent()
    monkeypatch.setattr(tool_policy, "get_policy", lambda agent: {"mode": "inherit"})
    monkeypatch.setattr(mcp_handler.MCPConfig, "get_for_agent", lambda agent: config)

    prompt = config.get_tools_prompt(agent=agent)
    loop_data = SimpleNamespace(params_temporary={})
    responses_tools.register_prompt(agent, loop_data, "mcp", prompt)
    native = loop_data.params_temporary["responses_prompt_replacements"][prompt]

    subsection = _subsection("docs", "Call read first.")
    assert prompt.count(subsection) == 1
    assert "tool_args" not in native
    assert native.count(SECTION_HEADING) == 1
    assert native.index("## MCP server context") < native.index(subsection)


def test_update_tools_captures_initialize_instructions(quiet_handler, monkeypatch) -> None:
    results: list = [
        SimpleNamespace(instructions="\n    Call read first.\n    "),
        {"instructions": "  From a dict-shaped result. "},
        SimpleNamespace(instructions=None),
        None,
    ]
    monkeypatch.setattr(mcp_handler, "ClientSession", _session_class(results))
    client = _Client(SimpleNamespace(name="docs", init_timeout=0))

    asyncio.run(client.update_tools())
    assert client.get_instructions() == "Call read first."
    assert [tool["name"] for tool in client.get_tools()] == ["read"]

    # Every reconnect replaces them, including with nothing.
    asyncio.run(client.update_tools())
    assert client.get_instructions() == "From a dict-shaped result."
    asyncio.run(client.update_tools())
    assert client.get_instructions() == ""
    asyncio.run(client.update_tools())
    assert client.get_instructions() == ""
    assert client.error == ""


def test_a_listing_that_finishes_after_the_timeout_publishes_nothing(
    quiet_handler, monkeypatch
) -> None:
    release = threading.Event()
    finished = threading.Event()

    class _SlowSession:
        def __init__(self, *args, **kwargs) -> None:
            pass

        async def __aenter__(self):
            return self

        async def __aexit__(self, *exc_info):
            finished.set()
            return False

        async def initialize(self):
            return SimpleNamespace(instructions="Late instructions.")

        async def list_tools(self):
            while not release.is_set():
                await asyncio.sleep(0.01)
            tool = SimpleNamespace(name="read", description="Read", inputSchema={})
            return SimpleNamespace(tools=[tool])

    monkeypatch.setattr(mcp_handler, "ClientSession", _SlowSession)
    client = _Client(SimpleNamespace(name="docs", init_timeout=0))
    client._operation_timeout_seconds = lambda seconds: 0.05

    asyncio.run(client.update_tools())  # times out while the listing is still running
    release.set()
    assert finished.wait(5)  # the abandoned worker has now completed its listing

    assert client.get_tools() == []
    assert client.get_instructions() == ""
    assert client.error.startswith("Failed to initialize.")


def test_failed_reconnect_clears_stale_instructions(quiet_handler) -> None:
    class _Broken(mcp_handler.MCPClientBase):
        async def _create_stdio_transport(self, current_exit_stack):
            raise ConnectionError("server is down")

    client = _Broken(SimpleNamespace(name="docs", init_timeout=0))
    client.tools = [{"name": "read"}]
    client.instructions = "Stale."

    asyncio.run(client.update_tools())

    assert client.get_instructions() == ""
    assert client.get_tools() == []
    assert client.error.startswith("Failed to initialize.")


@pytest.mark.parametrize(
    ("server_class", "config"),
    [
        (mcp_handler.MCPServerLocal, {"name": "Docs", "command": "npx"}),
        (mcp_handler.MCPServerRemote, {"name": "Docs", "url": "https://mcp.example.invalid/mcp"}),
    ],
)
def test_server_detail_shows_instructions(server_class, config) -> None:
    server = server_class(config)
    client = getattr(server, f"_{server_class.__name__}__client")
    client.tools = [{"name": "read", "description": "Read", "input_schema": {}}]
    client.instructions = "Call read first."

    assert server.get_instructions() == "Call read first."
    assert _config(server).get_server_detail("docs")["instructions"] == "Call read first."


def test_status_rows_flag_servers_with_instructions() -> None:
    with_text = mcp_handler.MCPServerLocal({"name": "docs", "command": "npx"})
    without_text = mcp_handler.MCPServerLocal({"name": "files", "command": "npx"})
    getattr(with_text, "_MCPServerLocal__client").instructions = "Call read first."
    config = _config(with_text, without_text)
    config.disconnected_servers = [{"name": "off", "error": "Disabled in config", "config": {}}]

    flags = {row["name"]: row["has_instructions"] for row in config.get_servers_status()}

    assert flags == {"docs": True, "files": False, "off": False}


def test_settings_ui_shows_server_instructions() -> None:
    client = ROOT / "webui/components/settings/mcp/client"
    servers = (client / "mcp-servers.html").read_text(encoding="utf-8")
    detail = (client / "mcp-server-tools.html").read_text(encoding="utf-8")

    assert 'x-show="server.has_instructions"' in servers
    # With every tool disabled the detail view stays reachable for the instructions.
    assert 'x-show="server.tool_count > 0 || server.has_instructions"' in servers
    # Server text is untrusted: plain text only.
    assert 'x-text="$store.mcpServersStore.serverDetail.instructions"' in detail
    assert "x-html" not in detail
