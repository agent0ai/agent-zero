from __future__ import annotations

import threading
import uuid
from dataclasses import dataclass, field
from pathlib import Path
import sys
from types import SimpleNamespace

import pytest
from flask import Flask

PROJECT_ROOT = Path(__file__).resolve().parents[4]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from agent import AgentContext
from helpers import files, projects, skills as skills_helper
from initialize import initialize_agent
from plugins._commands.api.commands import Commands
from plugins._commands.commands import connector_commands
from plugins._commands.extensions.python._functions.agent.AgentContext._process_chain.start._10_resolve_slash_command import (
    ResolveSlashCommand,
)
from plugins._commands.helpers import commands as commands_helper


@dataclass
class ScopeFixture:
    prefix: str
    project_name: str
    created_paths: list[str] = field(default_factory=list)


def _track_paths(scope: ScopeFixture, command: dict) -> dict:
    for key in ("path", "config_path", "content_path"):
        command_path = files.fix_dev_path(command.get(key, ""))
        if command_path and command_path not in scope.created_paths:
            scope.created_paths.append(command_path)
    return command


def _save_command(
    scope: ScopeFixture,
    *,
    project_name: str = "",
    name: str,
    description: str,
    body: str = "",
    argument_hint: str = "",
    command_type: str = "text",
    include_history: bool = False,
    extra_frontmatter: dict | None = None,
) -> dict:
    command = commands_helper.save_command(
        project_name=project_name,
        name=name,
        description=description,
        body=body,
        argument_hint=argument_hint,
        command_type=command_type,
        include_history=include_history,
        extra_frontmatter=extra_frontmatter or {},
    )
    return _track_paths(scope, command)


@pytest.fixture
def scope_fixture() -> ScopeFixture:
    suffix = uuid.uuid4().hex[:8]
    scope = ScopeFixture(
        prefix=f"commands-test-{suffix}",
        project_name=f"commands_project_{suffix}",
    )

    yield scope

    for path in reversed(scope.created_paths):
        files.delete_file(path)

    files.delete_dir(files.get_abs_path("usr", "projects", scope.project_name))


def _new_handler() -> Commands:
    app = Flask("commands_plugin_tests")
    app.secret_key = "commands-plugin-tests"
    return Commands(app, threading.RLock())


def test_command_config_and_template_files_round_trip(
    scope_fixture: ScopeFixture,
) -> None:
    command = _save_command(
        scope_fixture,
        name=f"Explain {scope_fixture.prefix}",
        description="Explain a code sample clearly.",
        body="Explain the sample.\n\n{raw}",
        argument_hint="Paste code or describe the module.",
        command_type="text",
        extra_frontmatter={"category": "analysis", "audience": "team"},
    )

    config_path = Path(files.fix_dev_path(command["path"]))
    content_path = Path(files.fix_dev_path(command["content_path"]))
    assert config_path.name == f"explain-{scope_fixture.prefix}.command.yaml"
    assert content_path.name == f"explain-{scope_fixture.prefix}.txt"

    loaded = commands_helper.get_command(command["path"])
    assert loaded["frontmatter_extra"] == {
        "category": "analysis",
        "audience": "team",
    }

    config_yaml = files.read_file(str(config_path))
    assert "category: analysis" in config_yaml
    assert "audience: team" in config_yaml
    assert f"name: explain-{scope_fixture.prefix}" in config_yaml
    assert "type: text" in config_yaml

    template_text = files.read_file(str(content_path))
    assert "Explain the sample." in template_text


def test_parse_arguments_and_render_template_support_flags() -> None:
    parsed = commands_helper.parse_arguments(
        '--git-url=https://github.com/acme/repo "quoted phrase" -v 30%'
    )
    assert parsed["flags"]["git_url"] == "https://github.com/acme/repo"
    assert parsed["flags"]["v"] is True
    assert parsed["positional"] == ["quoted phrase", "30%"]

    invocation = commands_helper.parse_slash_invocation(
        '/optimize 30% --mode fast --git-url=https://github.com/acme/repo'
    )
    rendered = commands_helper.render_text_template(
        "Pct: {args.positional.0}\nMode: {args.flags.mode}\nURL: {args.flags.git_url}\nRaw: {raw}",
        invocation,
    )
    assert rendered == (
        "Pct: 30%\n"
        "Mode: fast\n"
        "URL: https://github.com/acme/repo\n"
        "Raw: 30% --mode fast --git-url=https://github.com/acme/repo"
    )

    appended = commands_helper.render_text_template(
        "Summarize this request.",
        commands_helper.parse_slash_invocation("/summarize alpha beta"),
    )
    assert appended == "Summarize this request.\n\nArguments:\nalpha beta"

    invalid_invocation = commands_helper.parse_slash_invocation("/?")
    assert invalid_invocation["command_name"] == ""

    postfix_invocation = commands_helper.parse_slash_invocation(
        "Make goal execution tenacious\n/goal"
    )
    assert postfix_invocation["command_name"] == "goal"
    assert postfix_invocation["raw_arguments"] == "Make goal execution tenacious"


@pytest.mark.asyncio
async def test_incoming_postfix_command_is_resolved_before_the_agent(
    scope_fixture: ScopeFixture,
) -> None:
    command = _save_command(
        scope_fixture,
        name=f"Resolve {scope_fixture.prefix}",
        description="Resolve a postfix command.",
        body="Resolved: {raw}",
    )
    message = SimpleNamespace(message=f"from an AI /{command['name']}")
    data = {
        "args": (
            SimpleNamespace(id=f"missing-{uuid.uuid4().hex}"),
            None,
            message,
        )
    }

    await ResolveSlashCommand(agent=None).execute(data=data)

    assert message.message == "Resolved: from an AI"


def test_list_effective_commands_project_overrides_global(
    scope_fixture: ScopeFixture,
) -> None:
    shared_name = f"{scope_fixture.prefix}-shared"

    _save_command(
        scope_fixture,
        name=shared_name,
        description="global description",
        body="global body",
        command_type="text",
    )
    _save_command(
        scope_fixture,
        project_name=scope_fixture.project_name,
        name=shared_name,
        description="project description",
        body="project body",
        command_type="text",
    )

    project_commands, _ = commands_helper.list_effective_commands(
        scope_fixture.project_name
    )
    global_commands, _ = commands_helper.list_effective_commands("")

    assert {command["name"]: command for command in project_commands}[shared_name][
        "description"
    ] == "project description"
    assert {command["name"]: command for command in global_commands}[shared_name][
        "description"
    ] == "global description"

    scoped_commands, _ = commands_helper.list_scope_commands(scope_fixture.project_name)
    scoped_command = next(
        command for command in scoped_commands if command["name"] == shared_name
    )
    assert scoped_command["override_count"] == 1
    assert scoped_command["override_scopes"] == ["Global"]


def test_duplicate_builtin_creates_same_name_project_override(
    scope_fixture: ScopeFixture,
) -> None:
    builtin = next(
        command
        for command in commands_helper.list_builtin_commands()
        if command["name"] == "new"
    )

    override = _track_paths(
        scope_fixture,
        commands_helper.duplicate_command(
            builtin["path"],
            project_name=scope_fixture.project_name,
        ),
    )

    assert override["name"] == builtin["name"]
    assert override["scope_label"] == "Project"
    assert override["body"] == builtin["body"]

    effective, _ = commands_helper.list_effective_commands(scope_fixture.project_name)
    resolved = next(command for command in effective if command["name"] == "new")
    assert resolved["path"] == override["path"]


def test_models_command_always_opens_modal():
    result = connector_commands.run(
        {
            "invocation": {
                "command_name": "models",
                "raw_arguments": "default",
            },
            "context": {"context_id": ""},
        }
    )

    assert result == {
        "text": "",
        "effects": [{"type": "open_plugin_config", "plugin": "_model_config"}],
    }


@pytest.mark.parametrize(("argument", "enabled"), [("on", True), ("off", False)])
def test_computer_use_command_guides_launcher_or_cli(
    argument: str,
    enabled: bool,
):
    result = connector_commands.run(
        {
            "invocation": {
                "command_name": "computer-use",
                "raw_arguments": argument,
            },
            "context": {"context_id": ""},
        }
    )

    assert result["text"] == ""
    assert result["effects"] == [
        {
            "type": "computer_use",
            "enabled": enabled,
            "fallback": (
                "Computer Use permissions are controlled on the connected host. "
                "Use Host access in A0 Launcher, or run "
                f"`/computer-use {argument}` in the A0 CLI terminal."
            ),
        }
    ]


@pytest.mark.asyncio
async def test_commands_api_crud_and_resolve_text_and_script(
    scope_fixture: ScopeFixture,
) -> None:
    handler = _new_handler()
    command_name = f"{scope_fixture.prefix}-context"

    context = AgentContext(
        config=initialize_agent({}),
        set_current=True,
    )
    context.set_data(projects.CONTEXT_DATA_KEY_PROJECT, scope_fixture.project_name)

    try:
        saved = await handler.process(
            {
                "action": "save",
                "project_name": scope_fixture.project_name,
                "name": command_name,
                "description": "context override",
                "command_type": "text",
                "body": (
                    "Repo: {args.flags.git_url}\n"
                    "Mode: {args.flags.mode}\n"
                    "Raw: {raw}"
                ),
            },
            None,
        )
        assert isinstance(saved, dict)
        assert saved["ok"] is True
        saved_command = _track_paths(scope_fixture, saved["command"])

        loaded = await handler.process(
            {
                "action": "get",
                "project_name": scope_fixture.project_name,
                "path": saved_command["path"],
            },
            None,
        )
        assert isinstance(loaded, dict)
        assert loaded["command"]["description"] == "context override"

        resolved_text = await handler.process(
            {
                "action": "resolve",
                "project_name": scope_fixture.project_name,
                "path": saved_command["path"],
                "slash_text": f"/{command_name} --git-url=https://github.com/acme/repo --mode deep",
                "context_id": context.id,
            },
            None,
        )
        assert isinstance(resolved_text, dict)
        assert resolved_text["ok"] is True
        rendered_text = resolved_text["resolution"]["result"]["text"]
        assert "Repo: https://github.com/acme/repo" in rendered_text
        assert "Mode: deep" in rendered_text

        script_saved = await handler.process(
            {
                "action": "save",
                "project_name": scope_fixture.project_name,
                "name": f"{command_name}-script",
                "description": "script command",
                "command_type": "script",
                "include_history": True,
                "body": (
                    "def run(payload):\n"
                    "    flags = payload['arguments'].get('flags', {})\n"
                    "    return {\n"
                    "        'text': f\"Script mode: {flags.get('mode', 'none')}\",\n"
                    "        'effects': [\n"
                    "            {'type': 'toast', 'level': 'success', 'message': 'Script executed'}\n"
                    "        ],\n"
                    "    }\n"
                ),
            },
            None,
        )
        assert isinstance(script_saved, dict)
        assert script_saved["ok"] is True
        script_command = _track_paths(scope_fixture, script_saved["command"])

        resolved_script = await handler.process(
            {
                "action": "resolve",
                "project_name": scope_fixture.project_name,
                "path": script_command["path"],
                "slash_text": f"/{command_name}-script --mode turbo",
                "context_id": context.id,
            },
            None,
        )
        assert isinstance(resolved_script, dict)
        assert resolved_script["ok"] is True
        assert resolved_script["resolution"]["result"]["text"] == "Script mode: turbo"
        assert resolved_script["resolution"]["result"]["effects"] == [
            {
                "type": "toast",
                "level": "success",
                "message": "Script executed",
            }
        ]

        duplicated = await handler.process(
            {
                "action": "duplicate",
                "project_name": scope_fixture.project_name,
                "path": saved_command["path"],
            },
            None,
        )
        assert isinstance(duplicated, dict)
        assert duplicated["ok"] is True
        assert duplicated["command"]["name"].startswith(f"{command_name}-copy")
        duplicated_command = _track_paths(scope_fixture, duplicated["command"])

        effective_list = await handler.process(
            {"action": "list_effective", "context_id": context.id},
            None,
        )
        assert isinstance(effective_list, dict)
        effective_by_name = {
            command["name"]: command for command in effective_list["commands"]
        }
        assert effective_by_name[command_name]["description"] == "context override"
        assert effective_by_name[command_name]["source_scope_key"] == "project"

        scope_info = await handler.process(
            {"action": "scope_info", "context_id": context.id},
            None,
        )
        assert isinstance(scope_info, dict)
        assert scope_info["scope"]["project_name"] == scope_fixture.project_name

        deleted = await handler.process(
            {
                "action": "delete",
                "project_name": scope_fixture.project_name,
                "path": duplicated_command["path"],
            },
            None,
        )
        assert isinstance(deleted, dict)
        assert deleted["ok"] is True
    finally:
        AgentContext.remove(context.id)
        AgentContext.set_current("")


def test_plugin_scoped_skill_is_discoverable() -> None:
    skill = skills_helper.find_skill("commands-create-slash-command")
    assert skill is not None
    assert skill.skill_md_path.as_posix().endswith(
        "plugins/_commands/skills/commands-create-slash-command/SKILL.md"
    )
