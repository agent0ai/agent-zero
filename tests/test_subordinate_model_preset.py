"""Regression tests: subordinates honour explicit scoped model presets.

A new subordinate must inherit the parent chat model override only when its
own scope (profile or project) does not select an explicit ``model_preset``.
An explicit scoped preset always wins; the global preset never counts as an
explicit scoped selection.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

import pytest

from agent import Agent, AgentConfig
from helpers import files, plugins, projects


PROFILE_PRESET = "Qwen27b"
PROJECT_PRESET = "ProjectPreset"
PARENT_OVERRIDE = {"preset_name": "DeepSeek 4.1 Flash"}


class _FakeContext:
    def __init__(self, id: str = "ctx") -> None:
        self.id = id
        self.name = None
        self.data = {}
        self.output_data = {}
        self.created_at = datetime.now(timezone.utc)
        self.agent0 = None

    def get_data(self, key: str, recursive: bool = True):
        return self.data.get(key)

    def set_data(self, key: str, value, recursive: bool = True):
        self.data[key] = value

    def get_output_data(self, key: str, recursive: bool = True):
        return self.output_data.get(key)

    def set_output_data(self, key: str, value, recursive: bool = True):
        self.output_data[key] = value

    def is_running(self) -> bool:
        return False


class _FakeParentAgent:
    def __init__(self, project: str = "") -> None:
        self.number = 0
        self.agent_name = "A0"
        self.config = AgentConfig(mcp_servers="", profile="agent0")
        self.context = _FakeContext()
        if project:
            self.context.data[projects.CONTEXT_DATA_KEY_PROJECT] = project
        self.data = {}

    def get_data(self, key: str):
        return self.data.get(key)

    def set_data(self, key: str, value):
        self.data[key] = value


class _FakeSubAgent:
    DATA_NAME_SUPERIOR = "_superior"
    DATA_NAME_SUBORDINATE = "_subordinate"

    _counter = 0

    def __init__(self, number: int, config: AgentConfig, context=None) -> None:
        if context is None:
            self.__class__._counter += 1
            context = _FakeContext(f"child-{self.__class__._counter}")
        self.number = number
        self.agent_name = f"A{number}"
        self.config = config
        self.context = context
        self.context.agent0 = self
        self.data = {}

    def set_data(self, key: str, value):
        self.data[key] = value

    def get_data(self, key: str):
        return self.data.get(key)


def _write_config(root: Path, *parts: str, preset: str) -> None:
    path = root.joinpath(*parts)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps({"model_preset": preset}), encoding="utf-8")


def _prepare_tree(monkeypatch, tmp_path: Path) -> None:
    """Point the framework at an isolated tree with global presets."""
    monkeypatch.setattr(files, "_base_dir", str(tmp_path))
    monkeypatch.setattr(
        plugins,
        "call_plugin_hook",
        lambda *args, default=None, **kwargs: default,
    )
    presets_path = tmp_path / "usr" / "plugins" / "_model_config" / "presets.yaml"
    presets_path.parent.mkdir(parents=True, exist_ok=True)
    presets_path.write_text(
        "\n".join(
            [
                "- name: Default",
                "  chat:",
                "    provider: openrouter",
                "    name: default-chat",
                "- name: Qwen27b",
                "  chat:",
                "    provider: ollama",
                "    name: qwen-27b",
                "- name: ProjectPreset",
                "  chat:",
                "    provider: openrouter",
                "    name: project-chat",
                "- name: DeepSeek 4.1 Flash",
                "  chat:",
                "    provider: openrouter",
                "    name: deepseek-chat",
            ]
        ),
        encoding="utf-8",
    )


def _prepare_call_subordinate(monkeypatch) -> None:
    import tools.call_subordinate as call_subordinate

    monkeypatch.setattr(call_subordinate, "Agent", _FakeSubAgent)
    monkeypatch.setattr(
        call_subordinate,
        "_subordinate_profile_labels",
        lambda _agent: {"tiny-local": "Tiny Local"},
    )
    monkeypatch.setattr(
        call_subordinate,
        "initialize_agent",
        lambda override_settings=None: AgentConfig(
            mcp_servers="",
            profile=(override_settings or {}).get("agent_profile", "agent0"),
        ),
    )
    monkeypatch.setattr(
        call_subordinate.projects, "activate_project", lambda *_args, **_kwargs: None
    )


def _create_child(
    parent: _FakeParentAgent,
    *,
    profile: str = "tiny-local",
) -> Agent:
    import tools.call_subordinate as call_subordinate

    return call_subordinate.get_or_create_subordinate(
        parent,  # type: ignore[arg-type]
        profile=profile,
        reset=True,
        message="work",
    )


def test_explicit_scoped_preset_precedence(monkeypatch, tmp_path: Path) -> None:
    import tools.call_subordinate as call_subordinate

    _prepare_tree(monkeypatch, tmp_path)
    _write_config(
        tmp_path,
        "usr",
        "agents",
        "tiny-local",
        "plugins",
        "_model_config",
        "config.json",
        preset=PROFILE_PRESET,
    )
    _write_config(
        tmp_path,
        "usr",
        "projects",
        "demo",
        ".a0proj",
        "plugins",
        "_model_config",
        "config.json",
        preset=PROJECT_PRESET,
    )
    _write_config(
        tmp_path,
        "usr",
        "projects",
        "demo",
        ".a0proj",
        "agents",
        "tiny-local",
        "plugins",
        "_model_config",
        "config.json",
        preset="ProfileInProject",
    )

    assert (
        call_subordinate.explicit_scoped_preset(
            project="demo", profile="tiny-local"
        )
        == "ProfileInProject"
    )
    assert (
        call_subordinate.explicit_scoped_preset(project="demo", profile="") ==
        PROJECT_PRESET
    )
    assert (
        call_subordinate.explicit_scoped_preset(project="", profile="tiny-local")
        == PROFILE_PRESET
    )
    assert call_subordinate.explicit_scoped_preset(project="", profile="") == ""


def test_global_preset_is_not_an_explicit_scoped_preset(
    monkeypatch, tmp_path: Path
) -> None:
    import tools.call_subordinate as call_subordinate

    _prepare_tree(monkeypatch, tmp_path)
    _write_config(
        tmp_path,
        "usr",
        "plugins",
        "_model_config",
        "config.json",
        preset="GLM 5.3 Flash",
    )

    assert (
        call_subordinate.explicit_scoped_preset(project="", profile="tiny-local")
        == ""
    )


def test_subordinate_without_parent_override_uses_scoped_profile_preset(
    monkeypatch, tmp_path: Path
) -> None:
    from plugins._model_config.helpers import model_config

    _prepare_tree(monkeypatch, tmp_path)
    _prepare_call_subordinate(monkeypatch)
    _write_config(
        tmp_path,
        "usr",
        "agents",
        "tiny-local",
        "plugins",
        "_model_config",
        "config.json",
        preset=PROFILE_PRESET,
    )

    parent = _FakeParentAgent()
    child = _create_child(parent)

    assert child.context.get_data("chat_model_override") is None
    assert (
        model_config.get_configured_preset_name(
            project_name=None, agent_profile="tiny-local"
        )
        == PROFILE_PRESET
    )


def test_subordinate_inherits_override_without_explicit_scoped_preset(
    monkeypatch, tmp_path: Path
) -> None:
    _prepare_tree(monkeypatch, tmp_path)
    _prepare_call_subordinate(monkeypatch)

    parent = _FakeParentAgent()
    parent.context.set_data("chat_model_override", dict(PARENT_OVERRIDE))
    child = _create_child(parent)

    assert child.context.get_data("chat_model_override") == PARENT_OVERRIDE


def test_explicit_profile_preset_wins_over_parent_override(
    monkeypatch, tmp_path: Path
) -> None:
    _prepare_tree(monkeypatch, tmp_path)
    _prepare_call_subordinate(monkeypatch)
    _write_config(
        tmp_path,
        "usr",
        "agents",
        "tiny-local",
        "plugins",
        "_model_config",
        "config.json",
        preset=PROFILE_PRESET,
    )

    parent = _FakeParentAgent()
    parent.context.set_data("chat_model_override", dict(PARENT_OVERRIDE))
    child = _create_child(parent)

    assert child.context.get_data("chat_model_override") is None
    assert child.config.profile == "tiny-local"


def test_explicit_project_preset_wins_over_parent_override(
    monkeypatch, tmp_path: Path
) -> None:
    _prepare_tree(monkeypatch, tmp_path)
    _prepare_call_subordinate(monkeypatch)
    _write_config(
        tmp_path,
        "usr",
        "projects",
        "demo",
        ".a0proj",
        "plugins",
        "_model_config",
        "config.json",
        preset=PROJECT_PRESET,
    )

    parent = _FakeParentAgent(project="demo")
    parent.context.set_data("chat_model_override", dict(PARENT_OVERRIDE))
    child = _create_child(parent)

    assert child.context.get_data("chat_model_override") is None


def test_profile_preset_wins_over_project_preset(
    monkeypatch, tmp_path: Path
) -> None:
    import tools.call_subordinate as call_subordinate

    _prepare_tree(monkeypatch, tmp_path)
    _prepare_call_subordinate(monkeypatch)
    _write_config(
        tmp_path,
        "usr",
        "projects",
        "demo",
        ".a0proj",
        "plugins",
        "_model_config",
        "config.json",
        preset=PROJECT_PRESET,
    )
    _write_config(
        tmp_path,
        "usr",
        "projects",
        "demo",
        ".a0proj",
        "agents",
        "tiny-local",
        "plugins",
        "_model_config",
        "config.json",
        preset=PROFILE_PRESET,
    )

    parent = _FakeParentAgent(project="demo")
    parent.context.set_data("chat_model_override", dict(PARENT_OVERRIDE))
    child = _create_child(parent)

    assert child.context.get_data("chat_model_override") is None
    assert (
        call_subordinate.explicit_scoped_preset(
            project="demo", profile="tiny-local"
        )
        == PROFILE_PRESET
    )
    assert (
        call_subordinate.explicit_scoped_preset(project="demo", profile="") ==
        PROJECT_PRESET
    )
