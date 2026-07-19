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
REMOTE_PROMPT_FILES = {
    "code_execution_remote": "agent.system.tool.code_execution_remote.md",
    "computer_use_remote": "agent.system.tool.computer_use_remote.md",
    "text_editor_remote": "agent.system.tool.text_editor_remote.md",
}
GATE_PATH = (
    PROJECT_ROOT
    / "plugins"
    / "_a0_connector"
    / "extensions"
    / "python"
    / "_functions"
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


def _remote_prompt_blob() -> str:
    return "\n\n".join(
        (PROMPT_ROOT / prompt_file).read_text(encoding="utf-8").strip()
        for prompt_file in REMOTE_PROMPT_FILES.values()
    )


def _apply_gate(context_id: str, *, include_standard_remote_prompts: bool = True) -> str:
    result = "## available tools\nbase_tool"
    if include_standard_remote_prompts:
        result = f"{result}\n\n{_remote_prompt_blob()}"
    data = {"result": result}
    IncludeRemoteToolStubs(agent=FakeAgent(context_id)).execute(data=data)
    return data["result"]


def _assert_remote_tool_absent(prompt: str, tool_name: str) -> None:
    assert f'"tool_name": "{tool_name}"' not in prompt


def test_remote_tool_gate_hides_remote_prompts_without_connected_cli():
    prompt = _apply_gate(_context_id())

    for tool_name in REMOTE_PROMPT_FILES:
        _assert_remote_tool_absent(prompt, tool_name)
    assert "base_tool" in prompt


def test_remote_tool_gate_includes_file_prompt_for_read_only_connected_cli():
    context_id = _context_id()
    sid = _sid()
    ws_runtime.register_sid(sid)
    ws_runtime.store_sid_remote_file_metadata(
        sid,
        {"enabled": True, "write_enabled": False, "mode": "read_only"},
    )
    try:
        prompt = _apply_gate(context_id)
    finally:
        ws_runtime.unregister_sid(sid)

    assert '"tool_name": "text_editor_remote"' in prompt
    _assert_remote_tool_absent(prompt, "code_execution_remote")
    _assert_remote_tool_absent(prompt, "computer_use_remote")


def test_remote_tool_gate_requires_f4_enabled_remote_exec_metadata():
    context_id = _context_id()
    sid = _sid()
    ws_runtime.register_sid(sid)
    ws_runtime.store_sid_remote_file_metadata(
        sid,
        {"enabled": True, "write_enabled": True, "mode": "read_write"},
    )
    ws_runtime.store_sid_remote_exec_metadata(sid, {"enabled": False})
    try:
        prompt = _apply_gate(context_id)
        _assert_remote_tool_absent(prompt, "code_execution_remote")

        ws_runtime.store_sid_remote_exec_metadata(sid, {"enabled": True})
        prompt = _apply_gate(context_id)
    finally:
        ws_runtime.unregister_sid(sid)

    assert '"tool_name": "code_execution_remote"' in prompt


def test_remote_tool_gate_requires_enabled_computer_use_metadata():
    context_id = _context_id()
    sid = _sid()
    ws_runtime.register_sid(sid)
    ws_runtime.store_sid_computer_use_metadata(
        sid,
        {"supported": True, "enabled": False, "status": "off"},
    )
    try:
        prompt = _apply_gate(context_id)
        _assert_remote_tool_absent(prompt, "computer_use_remote")

        ws_runtime.store_sid_computer_use_metadata(
            sid,
            {"supported": True, "enabled": True, "status": "ready"},
        )
        prompt = _apply_gate(context_id)
    finally:
        ws_runtime.unregister_sid(sid)

    assert '"tool_name": "computer_use_remote"' in prompt
    assert "### computer_use_remote" in prompt


def test_remote_tool_gate_hides_rearm_required_computer_use_prompt():
    context_id = _context_id()
    sid = _sid()
    ws_runtime.register_sid(sid)
    ws_runtime.store_sid_computer_use_metadata(
        sid,
        {
            "supported": True,
            "enabled": True,
            "status": "rearm required",
            "last_error": "permission expired",
        },
    )
    try:
        prompt = _apply_gate(context_id)
    finally:
        ws_runtime.unregister_sid(sid)

    _assert_remote_tool_absent(prompt, "computer_use_remote")


def test_remote_tool_gate_appends_available_prompt_when_standard_prompt_missing():
    context_id = _context_id()
    sid = _sid()
    ws_runtime.register_sid(sid)
    ws_runtime.store_sid_remote_file_metadata(sid, {"enabled": True})
    try:
        prompt = _apply_gate(context_id, include_standard_remote_prompts=False)
    finally:
        ws_runtime.unregister_sid(sid)

    assert '"tool_name": "text_editor_remote"' in prompt
    _assert_remote_tool_absent(prompt, "code_execution_remote")
    _assert_remote_tool_absent(prompt, "computer_use_remote")


def test_responses_function_tools_follow_remote_prompt_gate(monkeypatch):
    from helpers import responses_tools

    context_id = _context_id()
    agent = FakeAgent(context_id)
    monkeypatch.setattr(
        responses_tools.subagents,
        "get_paths",
        lambda *args, **kwargs: [str(PROMPT_ROOT)],
    )

    names = {name for name, _prompt in responses_tools._local_tool_prompts(agent)}
    assert names.isdisjoint(REMOTE_PROMPT_FILES)

    sid = _sid()
    ws_runtime.register_sid(sid)
    ws_runtime.store_sid_remote_file_metadata(sid, {"enabled": True})
    ws_runtime.store_sid_remote_exec_metadata(sid, {"enabled": True})
    ws_runtime.store_sid_computer_use_metadata(
        sid,
        {"supported": True, "enabled": True, "status": "ready"},
    )
    try:
        names = {name for name, _prompt in responses_tools._local_tool_prompts(agent)}
    finally:
        ws_runtime.unregister_sid(sid)

    assert REMOTE_PROMPT_FILES.keys() <= names


def test_computer_use_remote_prompt_is_cli_session_wide_not_context_scoped():
    prompt = (PROMPT_ROOT / "agent.system.tool.computer_use_remote.md").read_text(
        encoding="utf-8"
    )

    assert "### computer_use_remote" in prompt
    assert '"tool_name": "computer_use_remote"' in prompt
    assert "scoped to the current CLI session" in prompt
    assert "not scoped to a single chat context" in prompt


def test_computer_use_remote_prompt_keeps_runtime_failures_actionable():
    prompt = (PROMPT_ROOT / "agent.system.tool.computer_use_remote.md").read_text(
        encoding="utf-8"
    )

    assert "no CLI" in prompt
    assert "disabled computer use" in prompt
    assert "COMPUTER_USE_REARM_REQUIRED" in prompt
    assert "/computer-use on" in prompt
    assert "A0 Launcher chat" in prompt


def test_computer_use_remote_prompt_requires_visual_verification_after_actions():
    prompt = (PROMPT_ROOT / "agent.system.tool.computer_use_remote.md").read_text(
        encoding="utf-8"
    )
    skill = (
        PROJECT_ROOT
        / "plugins"
        / "_a0_connector"
        / "skills"
        / "host-computer-use"
        / "SKILL.md"
    ).read_text(encoding="utf-8")

    assert "Treat key presses, clicks, scrolling, and typing" in prompt
    assert "attempts, not success" in prompt
    assert "visual verification is unavailable" in prompt
    assert "do not continue by assuming the host state" in prompt
    assert "Super+H" not in prompt
    assert "Alt+F9" not in prompt
    assert "hide" not in prompt.lower()
    assert "minimize" not in prompt.lower()
    assert "window-manager" not in prompt
    assert "cannot actually see the image" in skill
    assert "A `type` tool result only confirms keystrokes were sent" in skill
    assert "visibly confirms" in skill
    assert "hide window" not in skill
    assert "minimize window" not in skill
    assert "hide/minimize" not in skill
    assert "window-manager" not in skill


def test_remote_file_and_exec_tool_prompt_files_remain_standard_tool_prompts():
    text_stub = (PROMPT_ROOT / "agent.system.tool.text_editor_remote.md").read_text(encoding="utf-8")
    exec_stub = (PROMPT_ROOT / "agent.system.tool.code_execution_remote.md").read_text(encoding="utf-8")

    assert '"tool_name": "text_editor_remote"' in text_stub
    assert '"tool_name": "code_execution_remote"' in exec_stub
    assert "Availability and permissions are checked when the tool runs" in text_stub
    assert "Availability and permissions are checked when the tool runs" in exec_stub


def test_computer_use_remote_is_standard_prompt_with_runtime_checks():
    skill = (
        PROJECT_ROOT
        / "plugins"
        / "_a0_connector"
        / "skills"
        / "host-computer-use"
        / "SKILL.md"
    )
    standard_prompt = PROMPT_ROOT / "agent.system.tool.computer_use_remote.md"

    assert not (PROMPT_ROOT / "agent.system.runtime_tool.computer_use_remote.md").exists()
    assert standard_prompt.exists()
    assert '"tool_name": "computer_use_remote"' in standard_prompt.read_text(encoding="utf-8")
    assert "checked when the tool runs" in standard_prompt.read_text(encoding="utf-8")
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
    macos_computer_skill = _parse_skill_frontmatter(
        PROJECT_ROOT
        / "plugins"
        / "_a0_connector"
        / "skills"
        / "host-computer-use-macos"
        / "SKILL.md"
    )
    windows_computer_skill = _parse_skill_frontmatter(
        PROJECT_ROOT
        / "plugins"
        / "_a0_connector"
        / "skills"
        / "host-computer-use-windows"
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
    assert "Use instead of linux-desktop" in computer_skill["description"]
    assert "host computer" in computer_skill["triggers"]
    assert "Ubuntu Wayland desktop" in computer_skill["triggers"]
    assert macos_computer_skill["name"] == "host-computer-use-macos"
    assert "macOS guidance" in macos_computer_skill["description"]
    assert windows_computer_skill["name"] == "host-computer-use-windows"
    assert "Windows guidance" in windows_computer_skill["description"]


def test_remote_tool_stubs_are_self_contained_and_reference_per_tool_skills():
    text_stub = (PROMPT_ROOT / "agent.system.tool.text_editor_remote.md").read_text(encoding="utf-8")
    exec_stub = (PROMPT_ROOT / "agent.system.tool.code_execution_remote.md").read_text(encoding="utf-8")
    computer_stub = (PROMPT_ROOT / "agent.system.tool.computer_use_remote.md").read_text(encoding="utf-8")
    computer_skill = (
        PROJECT_ROOT
        / "plugins"
        / "_a0_connector"
        / "skills"
        / "host-computer-use"
        / "SKILL.md"
    ).read_text(encoding="utf-8")
    macos_computer_skill = (
        PROJECT_ROOT
        / "plugins"
        / "_a0_connector"
        / "skills"
        / "host-computer-use-macos"
        / "SKILL.md"
    ).read_text(encoding="utf-8")
    windows_computer_skill = (
        PROJECT_ROOT
        / "plugins"
        / "_a0_connector"
        / "skills"
        / "host-computer-use-windows"
        / "SKILL.md"
    ).read_text(encoding="utf-8")

    assert "optionally load skill `host-file-editing`" in text_stub
    assert "optionally load skill `host-code-execution`" in exec_stub
    assert '"tool_name": "text_editor_remote"' in text_stub
    assert '"tool_name": "code_execution_remote"' in exec_stub
    assert '"tool_name": "computer_use_remote"' in computer_stub
    assert "load and follow skill `host-computer-use`" in computer_stub
    assert "host-computer-use-macos" in computer_stub
    assert "host-computer-use-windows" in computer_stub
    assert "ax_snapshot" not in computer_stub
    assert "ax_action" not in computer_stub
    assert "uia_snapshot" not in computer_stub
    assert "uia_action" not in computer_stub
    assert "Do not substitute the `linux-desktop` skill" in computer_stub
    assert '"tool_name": "computer_use_remote"' in computer_skill
    assert '"tool_name": "computer_use_remote"' in macos_computer_skill
    assert '"tool_name": "computer_use_remote"' in windows_computer_skill
    assert "ax_snapshot" in macos_computer_skill
    assert "ax_snapshot" not in computer_skill
    assert "ax_action" not in computer_skill
    assert "uia_snapshot" in windows_computer_skill
    assert "uia_action" in windows_computer_skill
    assert "focus_window" in windows_computer_skill
    assert "minimize" in windows_computer_skill
    assert "If a node offers `invoke`, use `invoke`, not `click`" in windows_computer_skill
    assert "uia_snapshot" not in computer_skill
    assert "uia_action" not in computer_skill
    assert "Availability, backend support, and trust mode are checked when the tool runs" in computer_stub
    assert "not `code_execution_tool`" in exec_stub
    assert "not to" in exec_stub
    assert "Docker/server/container execution" in exec_stub
    assert "a0-cli-remote-workflows" not in text_stub
    assert "a0-cli-remote-workflows" not in exec_stub
    assert "a0-cli-remote-workflows" not in computer_stub
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
    assert "opera://inspect/#remote-debugging" in browser_prompt
    assert "Do not start `computer_use_remote` for web-page navigation" in computer_skill
    assert (
        "Do not fall back to `code_execution_remote`, `xdg-open`, `sensible-browser`, "
        "or Python `webbrowser.open`"
    ) in computer_skill
    assert "do not use shell launchers" in exec_skill
    assert "Use a shell launcher only when the user explicitly wants" not in exec_skill
    assert "Do not use this tool as a fallback for host-browser navigation/control" in exec_stub


def test_host_computer_use_does_not_fall_back_to_linux_desktop_skill():
    computer_stub = (PROMPT_ROOT / "agent.system.tool.computer_use_remote.md").read_text(encoding="utf-8")
    host_skill_path = (
        PROJECT_ROOT
        / "plugins"
        / "_a0_connector"
        / "skills"
        / "host-computer-use"
        / "SKILL.md"
    )
    linux_skill_path = (
        PROJECT_ROOT
        / "plugins"
        / "_desktop"
        / "skills"
        / "linux-desktop"
        / "SKILL.md"
    )
    host_skill = host_skill_path.read_text(encoding="utf-8")
    linux_skill = linux_skill_path.read_text(encoding="utf-8")
    linux_frontmatter = _parse_skill_frontmatter(linux_skill_path)

    assert "only desktop-control path for the user's connected host/local computer" in computer_stub
    assert "Do not substitute the `linux-desktop` skill" in computer_stub
    assert "Never switch to `linux-desktop`" in host_skill
    assert "Those paths only see the internal Agent Zero runtime" in host_skill
    assert "built-in Docker/Xpra Linux Desktop" in linux_frontmatter["description"]
    assert "Not for A0 CLI /computer-use" in linux_frontmatter["description"]
    assert "A0 CLI /computer-use" in linux_frontmatter["description"]
    assert "host-computer-use" in linux_skill
    assert "computer_use_remote" in linux_skill
    assert "`desktopctl.sh` only targets the internal Agent Zero Xpra display" in linux_skill
    assert "use the OS" not in linux_frontmatter["triggers"]
    assert "terminal app" not in linux_frontmatter["triggers"]
    assert any("Xpra" in trigger for trigger in linux_frontmatter["triggers"])
