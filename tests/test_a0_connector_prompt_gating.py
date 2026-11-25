import sys
import time
import uuid
from pathlib import Path
from types import SimpleNamespace

import pytest
import yaml

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


def _restore_real_helpers_package() -> None:
    helpers_module = sys.modules.get("helpers")
    if (
        helpers_module is None
        or getattr(helpers_module, "__file__", "")
        or list(getattr(helpers_module, "__path__", []))
    ):
        return

    for name in list(sys.modules):
        if name == "helpers" or name.startswith("helpers."):
            del sys.modules[name]


_restore_real_helpers_package()

from plugins._a0_connector.helpers import ws_runtime


PROMPT_ROOT = PROJECT_ROOT / "plugins" / "_a0_connector" / "prompts"
SKILL_PATH = PROMPT_ROOT.parent / "skills" / "host-computer-use" / "SKILL.md"
COMPUTER_USE_ID = "plugin:_a0_connector:computer_use_remote"


class FakeContext:
    def __init__(self, context_id: str):
        self.id = context_id

    def get_data(self, key: str, recursive: bool = True):
        return None


def _context_id() -> str:
    return f"ctx-{uuid.uuid4()}"


def _sid() -> str:
    return f"sid-{uuid.uuid4()}"


def _parse_skill_frontmatter(path: Path) -> dict:
    text = path.read_text(encoding="utf-8")
    assert text.startswith("---")
    return yaml.safe_load(text.split("---", 2)[1]) or {}


@pytest.mark.asyncio
async def test_host_computer_use_requires_skill_load_live_host_and_tool_access(monkeypatch):
    from agent import Agent
    from helpers import responses_tools, skills, subagents, tool_policy
    from helpers.errors import RepairableException
    from helpers.tool_actions import BUNDLED_ACTIONS
    from plugins._a0_connector.helpers.host_computer_use import ComputerUseRemote
    from plugins._tool_access.extensions.python.tool_execute_before._10_enforce_tool_policy import EnforceToolPolicy
    from tools.skills_tool import SkillsTool
    from tools.unknown import Unknown

    def get_paths(_agent, *parts, **kwargs):
        if parts == ("skills",):
            return [str(PROMPT_ROOT.parent / "skills")]
        if parts == ("extensions/python", "_functions/agent/Agent/get_tool/end"):
            return [str(PROJECT_ROOT.joinpath(*parts))]
        return [str(PROMPT_ROOT.parent.joinpath(*parts))]

    monkeypatch.setattr(subagents, "get_paths", get_paths)
    monkeypatch.setattr(skills, "get_hidden_skills", lambda agent: [])
    monkeypatch.setattr(skills, "get_visibility_policy", lambda agent: {"mode": "inherit"})
    monkeypatch.setattr(responses_tools, "_mcp_tools", lambda agent: [])
    monkeypatch.setattr(responses_tools, "_vision_tool_prompt", lambda agent: "")
    policy = tool_policy.normalize_policy({"mode": "custom", "default": "block"})
    monkeypatch.setattr(tool_policy, "get_policy", lambda agent: policy)
    state = {}
    agent = object.__new__(Agent)
    agent.context = SimpleNamespace(id=_context_id(), get_data=state.get, set_data=state.__setitem__)
    agent.config = SimpleNamespace(profile="host-computer-use-test")
    agent.loop_data = SimpleNamespace(current_tool=None)
    agent.data = {}
    name = "computer_use_remote"
    capture = {"action": "capture"}

    def native():
        declarations, _ = responses_tools.build_responses_function_tools(agent)
        return next((tool for tool in declarations if tool["name"] == name), None)

    async def expect_denied(args):
        selected = agent.get_tool(name, None, args, "", agent.loop_data)
        assert isinstance(selected, Unknown)
        agent.loop_data.current_tool = selected
        with pytest.raises(RepairableException, match="is blocked"):
            await EnforceToolPolicy(agent).execute(tool_name=name, tool_args=args)

    catalog_item = next(item for item in tool_policy.get_tool_catalog(agent) if item["id"] == COMPUTER_USE_ID)
    assert catalog_item["actions"] == list(BUNDLED_ACTIONS[COMPUTER_USE_ID].actions)
    assert native() is None
    await expect_denied(capture)

    sid = _sid()
    ws_runtime.register_sid(sid)
    try:
        ws_runtime.store_sid_computer_use_metadata(sid, {"supported": True, "enabled": True, "status": "ready"})
        policy["allowed"] = [COMPUTER_USE_ID + ":capture", COMPUTER_USE_ID + ":type"]
        policy["blocked"] = [COMPUTER_USE_ID + ":type"]
        assert native() is None
        await expect_denied(capture)
        loader = SkillsTool(agent, "skills_tool", None, {}, "", agent.loop_data)
        assert '"tool_name": "computer_use_remote"' in loader._load("host-computer-use").message
        assert native()["parameters"]["properties"]["action"]["enum"] == ["capture"]
        tool = agent.get_tool(name, None, capture, "", agent.loop_data)
        assert isinstance(tool, ComputerUseRemote)
        agent.loop_data.current_tool = tool
        await EnforceToolPolicy(agent).execute(tool_name=name, tool_args=capture)
        await expect_denied({"action": "type"})
        policy["blocked"] = [COMPUTER_USE_ID]
        assert native() is None
        await expect_denied(capture)
        policy["blocked"] = []

        for metadata in (
            {"supported": True, "enabled": False, "status": "off"},
            {"supported": False, "enabled": True, "status": "ready"},
            {"supported": True, "enabled": True, "status": "rearm required"},
        ):
            ws_runtime.store_sid_computer_use_metadata(sid, metadata)
            assert native() is None
            await expect_denied(capture)
    finally:
        ws_runtime.unregister_sid(sid)
    assert native() is None
    await expect_denied(capture)


def test_legacy_remote_tool_prompts_and_entrypoints_are_removed():
    for name in ("text_editor_remote", "code_execution_remote", "input_remote", "computer_use_remote"):
        assert not (PROMPT_ROOT / f"agent.system.tool.{name}.md").exists()
        assert not (PROMPT_ROOT.parent / "tools" / f"{name}.py").exists()
    assert _parse_skill_frontmatter(SKILL_PATH)["metadata"]["tool"]["name"] == "computer_use_remote"


def test_host_computer_use_keeps_permission_and_visual_verification_guidance():
    skill = SKILL_PATH.read_text()
    linux_skill = (SKILL_PATH.parent.parent / "host-computer-use-linux" / "SKILL.md").read_text()
    assert "The host grant belongs to the CLI session or Launcher Host access lease." in skill
    assert "Each chat starts and reuses its own desktop session." in skill
    assert "COMPUTER_USE_REARM_REQUIRED" in skill
    assert "/computer-use on" in skill
    assert "A0 Launcher chat" in skill
    assert "cannot actually see the image" in skill
    assert "A `type` tool result confirms the destination only when" in skill
    assert "visibly confirms" in skill
    assert "focus_verified=true" in skill
    assert "Pass the same verified active `window_id` to `type`" in linux_skill
    assert "never use it on an application/frame/window" in linux_skill


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
    assert "text_editor" in text_editor_skill["description"]
    assert "not Docker/server files" in text_editor_skill["description"]
    assert code_execution_skill["name"] == "host-code-execution"
    assert "code_execution_tool" in code_execution_skill["description"]
    assert "not Docker" in code_execution_skill["description"]
    assert computer_skill["name"] == "host-computer-use"
    assert "connected host desktop" in computer_skill["description"]
    assert "host computer" in computer_skill["triggers"]
    assert "Ubuntu Wayland desktop" in computer_skill["triggers"]
    assert macos_computer_skill["name"] == "host-computer-use-macos"
    assert "macOS guidance" in macos_computer_skill["description"]
    assert windows_computer_skill["name"] == "host-computer-use-windows"
    assert "Windows guidance" in windows_computer_skill["description"]


def test_host_computer_use_keeps_backend_actions_in_their_skills():
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

    assert "With `app-scoped-semantic-targeting`" in macos_computer_skill
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
    assert "a0-cli-remote-workflows" not in computer_skill


def test_host_browser_requests_route_to_browser_tool_not_desktop_or_shell_fallbacks():
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

    browser_skill = (
        PROJECT_ROOT / "plugins" / "_browser" / "skills" / "browser-automation" / "SKILL.md"
    ).read_text(encoding="utf-8")
    assert 'When the user asks for "my browser"' in browser_skill
    assert "references/browser-controls.md" in browser_skill
    controls = (PROJECT_ROOT / "plugins/_browser/skills/browser-automation/references/browser-controls.md").read_text()
    assert "Do not substitute `computer_use_remote`" in controls
    assert "code_execution_tool" in controls
    assert "Python `webbrowser.open`" in controls
    assert "chrome://inspect/#remote-debugging" in controls
    assert "opera://inspect/#remote-debugging" in controls
    assert "Do not start `computer_use_remote` for web-page navigation" in computer_skill
    assert (
        "Do not fall back to `code_execution_tool` with `destination: host`, `xdg-open`, `sensible-browser`, "
        "or Python `webbrowser.open`"
    ) in computer_skill
    assert "do not use shell launchers" in exec_skill
    assert "Use a shell launcher only when the user explicitly wants" not in exec_skill


def test_host_computer_use_does_not_fall_back_to_linux_desktop_skill():
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

    assert "Never switch to `linux-desktop`" in host_skill
    assert "Those paths only see the internal Agent Zero runtime" in host_skill
    assert "Docker/Tuxee" in linux_frontmatter["description"]
    assert "not the user's host computer" in linux_frontmatter["description"]
    assert "host-computer-use" in linux_skill
    assert "computer_use_remote" in linux_skill
    assert "Tuxee only controls the internal Agent Zero container" in linux_skill
    assert "use the OS" not in linux_frontmatter["triggers"]
    assert "terminal app" not in linux_frontmatter["triggers"]
    assert any("Tuxee" in trigger for trigger in linux_frontmatter["triggers"])


def test_connector_skill_root_follows_connection_without_mutating_cached_paths(monkeypatch):
    from agent import Agent
    from helpers import skills, subagents

    agent = object.__new__(Agent)
    agent.context = FakeContext(_context_id())
    agent.config = SimpleNamespace(profile="default")
    connector = PROJECT_ROOT / "plugins" / "_a0_connector"
    roots = [str(connector / "skills"), str(PROJECT_ROOT / "skills")]

    def get_paths(_agent, *parts, **kwargs):
        if parts == ("skills",):
            return roots
        return [str(connector.joinpath(*parts))]

    monkeypatch.setattr(subagents, "get_paths", get_paths)
    monkeypatch.setattr(skills, "get_hidden_skills", lambda agent: [])
    monkeypatch.setattr(skills, "get_visibility_policy", lambda agent: {"mode": "inherit"})
    remote_names = {path.parent.name for path in (connector / "skills").glob("*/SKILL.md")}
    sid = _sid()
    try:
        for state in ("offline", "webui_only", "cli_disabled", "cli_enabled", "disconnected"):
            if state == "webui_only":
                ws_runtime.register_sid(sid)
            elif state.startswith("cli_"):
                ws_runtime.store_sid_remote_file_metadata(sid, {"enabled": state == "cli_enabled"})
            elif state == "disconnected":
                ws_runtime.unregister_sid(sid)

            connected = state.startswith("cli_")
            names = {skill.name for skill in skills.list_skills(agent)}
            assert "a0-development" in names
            assert "setup-a0-cli" not in names
            setup_matches = skills.search_skills("A0 CLI setup", limit=1, agent=agent)
            assert [skill.name for skill in setup_matches] == ["a0-development"]
            assert (remote_names <= names) if connected else names.isdisjoint(remote_names)
            assert bool(skills.find_skill("host-file-editing", agent)) == connected
            matches = {skill.name for skill in skills.search_skills("host", agent=agent)}
            assert ("host-file-editing" in matches) == connected
            assert len(roots) == 2
        assert str(connector / "skills") in skills.get_skill_roots()
    finally:
        ws_runtime.unregister_sid(sid)
