import importlib.util
import sys
import time
import uuid
from pathlib import Path

import yaml

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


def _restore_real_helpers_package() -> None:
    helpers_module = sys.modules.get("helpers")
    if helpers_module is None or getattr(helpers_module, "__file__", ""):
        return

    for name in list(sys.modules):
        if name == "helpers" or name.startswith("helpers."):
            del sys.modules[name]


_restore_real_helpers_package()

from plugins._a0_connector.helpers import ws_runtime


PROMPT_ROOT = PROJECT_ROOT / "plugins" / "_a0_connector" / "prompts"
GATE_PATH = (
    PROJECT_ROOT
    / "plugins"
    / "_a0_connector"
    / "extensions"
    / "python"
    / "_functions"
    / "extensions"
    / "python"
    / "system_prompt"
    / "_11_tools_prompt"
    / "build_prompt"
    / "end"
    / "_70_include_remote_tool_stubs.py"
)


def _load_gate_class():
    spec = importlib.util.spec_from_file_location(
        "test_a0_connector_remote_tool_gate",
        GATE_PATH,
    )
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module.IncludeRemoteToolStubs


IncludeRemoteToolStubs = _load_gate_class()


class FakeContext:
    def __init__(self, context_id: str):
        self.id = context_id


class FakeAgent:
    def __init__(self, context_id: str):
        self.context = FakeContext(context_id)

    def read_prompt(self, file: str, **kwargs) -> str:
        text = (PROMPT_ROOT / file).read_text(encoding="utf-8")
        for key, value in kwargs.items():
            text = text.replace("{{" + key + "}}", str(value))
        return text


def _context_id() -> str:
    return f"ctx-{uuid.uuid4()}"


def _sid() -> str:
    return f"sid-{uuid.uuid4()}"


def _parse_skill_frontmatter(path: Path) -> dict:
    text = path.read_text(encoding="utf-8")
    assert text.startswith("---")
    return yaml.safe_load(text.split("---", 2)[1]) or {}


def _apply_gate(context_id: str) -> str:
    data = {"result": "## available tools\nbase_tool"}
    IncludeRemoteToolStubs(agent=FakeAgent(context_id)).execute(data=data)
    return data["result"]


def _subscribe(
    context_id: str,
    *,
    remote_files: dict | None = None,
    remote_exec: dict | None = None,
    computer_use: dict | None = None,
) -> str:
    sid = _sid()
    ws_runtime.register_sid(sid)
    ws_runtime.subscribe_sid_to_context(sid, context_id)
    if remote_files is not None:
        ws_runtime.store_sid_remote_file_metadata(sid, remote_files)
    if remote_exec is not None:
        ws_runtime.store_sid_remote_exec_metadata(sid, remote_exec)
    if computer_use is not None:
        ws_runtime.store_sid_computer_use_metadata(sid, computer_use)
    return sid


def test_legacy_dynamic_remote_tool_gate_is_noop():
    prompt = _apply_gate(_context_id())

    assert "text_editor_remote tool" not in prompt
    assert "code_execution_remote tool" not in prompt
    assert "computer_use_remote tool" not in prompt


def test_remote_file_and_exec_tools_are_standard_tool_prompts_independent_from_context():
    text_stub = (PROMPT_ROOT / "agent.system.tool.text_editor_remote.md").read_text(encoding="utf-8")
    exec_stub = (PROMPT_ROOT / "agent.system.tool.code_execution_remote.md").read_text(encoding="utf-8")

    assert '"tool_name": "text_editor_remote"' in text_stub
    assert '"tool_name": "code_execution_remote"' in exec_stub
    assert "Availability and permissions are checked when the tool runs" in text_stub
    assert "Availability and permissions are checked when the tool runs" in exec_stub


def test_beta_computer_use_remote_is_skill_only_not_standard_tool_prompt():
    skill = (
        PROJECT_ROOT
        / "plugins"
        / "_a0_connector"
        / "skills"
        / "host-computer-use"
        / "SKILL.md"
    )

    assert not (PROMPT_ROOT / "agent.system.tool.computer_use_remote.md").exists()
    assert '"tool_name": "computer_use_remote"' in skill.read_text(encoding="utf-8")


def test_old_connector_prompt_files_removed():
    assert not (PROMPT_ROOT / "agent.connector_tool.text_editor_remote.md").exists()
    assert not (PROMPT_ROOT / "agent.connector_tool.code_execution_remote.md").exists()
    assert not (PROMPT_ROOT / "agent.connector_tool.computer_use_remote.md").exists()


def test_remote_tool_selection_prefers_context_cli_then_global_cli():
    context_id = _context_id()
    sid_context = _sid()
    sid_global = _sid()
    for sid in (sid_context, sid_global):
        ws_runtime.register_sid(sid)
        ws_runtime.store_sid_remote_exec_metadata(sid, {"enabled": True})
        ws_runtime.store_sid_remote_file_metadata(
            sid,
            {"enabled": True, "write_enabled": True, "mode": "read_write"},
        )
    ws_runtime.subscribe_sid_to_context(sid_context, context_id)
    try:
        assert ws_runtime.remote_tool_sids_for_context(context_id) == [
            sid_context,
            sid_global,
        ]
        assert ws_runtime.select_remote_exec_target_sid(context_id) == sid_context
        assert (
            ws_runtime.select_remote_exec_target_sid(context_id, require_writes=True)
            == sid_context
        )
        assert ws_runtime.select_remote_file_target_sid(context_id) == sid_context
    finally:
        ws_runtime.unregister_sid(sid_context)
        ws_runtime.unregister_sid(sid_global)


def test_remote_tool_selection_falls_back_to_global_cli():
    context_id = _context_id()
    sid = _sid()
    ws_runtime.register_sid(sid)
    ws_runtime.store_sid_remote_exec_metadata(sid, {"enabled": True})
    ws_runtime.store_sid_remote_file_metadata(
        sid,
        {"enabled": True, "write_enabled": True, "mode": "read_write"},
    )
    try:
        assert ws_runtime.select_remote_exec_target_sid(context_id) == sid
        assert (
            ws_runtime.select_remote_exec_target_sid(context_id, require_writes=True)
            == sid
        )
        assert ws_runtime.select_remote_file_target_sid(context_id) == sid
    finally:
        ws_runtime.unregister_sid(sid)


def test_latest_remote_tree_falls_back_to_global_cli_snapshot():
    context_id = _context_id()
    sid = _sid()
    ws_runtime.register_sid(sid)
    ws_runtime.store_remote_tree_snapshot(
        sid,
        {
            "root_path": "/home/example",
            "tree": "README.md",
            "generated_at": "2026-05-09T12:00:00Z",
        },
    )
    try:
        snapshot = ws_runtime.latest_remote_tree_for_context(
            context_id,
            max_age_seconds=90,
        )
    finally:
        ws_runtime.unregister_sid(sid)

    assert snapshot is not None
    assert snapshot["sid"] == sid
    assert snapshot["tree"] == "README.md"


def test_latest_remote_tree_prefers_context_cli_snapshot():
    context_id = _context_id()
    sid_context = _sid()
    sid_global = _sid()
    now = time.time()
    for sid in (sid_context, sid_global):
        ws_runtime.register_sid(sid)
    ws_runtime.subscribe_sid_to_context(sid_context, context_id)
    ws_runtime.store_remote_tree_snapshot(
        sid_context,
        {
            "root_path": "/context",
            "tree": "context.txt",
            "generated_at": "2026-05-09T12:00:00Z",
        },
    )
    ws_runtime.store_remote_tree_snapshot(
        sid_global,
        {
            "root_path": "/global",
            "tree": "global.txt",
            "generated_at": "2026-05-09T12:00:01Z",
        },
    )
    try:
        # Make the global snapshot newer; context affinity should still win.
        ws_runtime._remote_tree_snapshots[sid_global] = ws_runtime.RemoteTreeSnapshot(
            sid=sid_global,
            payload=ws_runtime._remote_tree_snapshots[sid_global].payload,
            updated_at=now + 5,
        )
        snapshot = ws_runtime.latest_remote_tree_for_context(
            context_id,
            max_age_seconds=90,
        )
    finally:
        ws_runtime.unregister_sid(sid_context)
        ws_runtime.unregister_sid(sid_global)

    assert snapshot is not None
    assert snapshot["sid"] == sid_context
    assert snapshot["tree"] == "context.txt"


def test_remote_exec_mutating_runtime_requires_explicit_write_access():
    context_id = _context_id()
    sid = _sid()
    ws_runtime.register_sid(sid)
    ws_runtime.store_sid_remote_exec_metadata(sid, {"enabled": True})
    try:
        assert ws_runtime.select_remote_exec_target_sid(context_id) == sid
        assert ws_runtime.select_remote_exec_target_sid(context_id, require_writes=True) is None
    finally:
        ws_runtime.unregister_sid(sid)


def test_remote_affordance_skills_parse():
    legacy_connector_skill = (
        PROJECT_ROOT
        / "plugins"
        / "_a0_connector"
        / "skills"
        / "a0-cli-remote-workflows"
        / "SKILL.md"
    )
    text_editor_skill = _parse_skill_frontmatter(
        PROJECT_ROOT
        / "plugins"
        / "_a0_connector"
        / "skills"
        / "host-file-editing"
        / "SKILL.md"
    )
    code_execution_skill = _parse_skill_frontmatter(
        PROJECT_ROOT
        / "plugins"
        / "_a0_connector"
        / "skills"
        / "host-code-execution"
        / "SKILL.md"
    )
    computer_skill = _parse_skill_frontmatter(
        PROJECT_ROOT
        / "plugins"
        / "_a0_connector"
        / "skills"
        / "host-computer-use"
        / "SKILL.md"
    )

    assert not legacy_connector_skill.exists()
    assert text_editor_skill["name"] == "host-file-editing"
    assert "text_editor_remote" in text_editor_skill["description"]
    assert "not Docker/server files" in text_editor_skill["description"]
    assert code_execution_skill["name"] == "host-code-execution"
    assert "code_execution_remote" in code_execution_skill["description"]
    assert "not Docker" in code_execution_skill["description"]
    assert computer_skill["name"] == "host-computer-use"
    assert "computer_use_remote" in computer_skill["description"]


def test_remote_tool_stubs_are_self_contained_and_reference_per_tool_skills():
    text_stub = (PROMPT_ROOT / "agent.system.tool.text_editor_remote.md").read_text(encoding="utf-8")
    exec_stub = (PROMPT_ROOT / "agent.system.tool.code_execution_remote.md").read_text(encoding="utf-8")
    computer_skill = (
        PROJECT_ROOT
        / "plugins"
        / "_a0_connector"
        / "skills"
        / "host-computer-use"
        / "SKILL.md"
    ).read_text(encoding="utf-8")

    assert "optionally load skill `host-file-editing`" in text_stub
    assert "optionally load skill `host-code-execution`" in exec_stub
    assert '"tool_name": "text_editor_remote"' in text_stub
    assert '"tool_name": "code_execution_remote"' in exec_stub
    assert '"tool_name": "computer_use_remote"' in computer_skill
    assert "Availability, backend support, and trust mode are checked when the tool runs" in computer_skill
    assert "not `code_execution_tool`" in exec_stub
    assert "not to" in exec_stub
    assert "Docker/server/container execution" in exec_stub
    assert "a0-cli-remote-workflows" not in text_stub
    assert "a0-cli-remote-workflows" not in exec_stub
    assert "a0-cli-remote-workflows" not in computer_skill


def test_host_browser_requests_route_to_browser_tool_not_desktop_or_shell_fallbacks():
    browser_prompt = (
        PROJECT_ROOT / "plugins" / "_browser" / "prompts" / "agent.system.tool.browser.md"
    ).read_text(encoding="utf-8")
    exec_stub = (PROMPT_ROOT / "agent.system.tool.code_execution_remote.md").read_text(encoding="utf-8")
    exec_skill = (
        PROJECT_ROOT
        / "plugins"
        / "_a0_connector"
        / "skills"
        / "host-code-execution"
        / "SKILL.md"
    ).read_text(encoding="utf-8")
    computer_skill = (
        PROJECT_ROOT
        / "plugins"
        / "_a0_connector"
        / "skills"
        / "host-computer-use"
        / "SKILL.md"
    ).read_text(encoding="utf-8")

    assert 'When the user asks for "my browser"' in browser_prompt
    assert "Do not substitute `computer_use_remote`" in browser_prompt
    assert "code_execution_remote" in browser_prompt
    assert "Python `webbrowser.open`" in browser_prompt
    assert "chrome://inspect/#remote-debugging" in browser_prompt
    assert "Do not start `computer_use_remote` for web-page navigation" in computer_skill
    assert (
        "Do not fall back to `code_execution_remote`, `xdg-open`, `sensible-browser`, "
        "or Python `webbrowser.open`"
    ) in computer_skill
    assert "do not use shell launchers" in exec_skill
    assert "Use a shell launcher only when the user explicitly wants" not in exec_skill
    assert "Do not use this tool as a fallback for host-browser navigation/control" in exec_stub
