"""Exercise the real slash-command parser with isolated runtime services."""

import importlib.util
import sys
from pathlib import Path
from types import ModuleType, SimpleNamespace
from unittest.mock import Mock

import pytest


@pytest.fixture
def commands(monkeypatch):
    # Loading the complete module keeps parsing/dispatch/matching real without
    # importing the agent/model runtimes or touching persisted user state.
    modules = {}
    for name in (
        "helpers",
        "helpers.message_queue",
        "helpers.projects",
        "helpers.persist_chat",
        "helpers.state_monitor_integration",
        "helpers.subagents",
        "initialize",
        "plugins",
        "plugins._model_config",
        "plugins._model_config.helpers",
        "plugins._model_config.helpers.model_config",
    ):
        module = ModuleType(name)
        modules[name] = module
        monkeypatch.setitem(sys.modules, name, module)
        parent, _, child = name.rpartition(".")
        if parent:
            setattr(modules[parent], child, module)
    modules["helpers.persist_chat"].save_tmp_chat = Mock()
    modules["helpers.state_monitor_integration"].mark_dirty_for_context = Mock()
    projects = modules["helpers.projects"]
    projects.get_active_projects_list = Mock(return_value=[])
    projects.activate_project = Mock()
    projects.deactivate_project = Mock()
    config = modules["plugins._model_config.helpers.model_config"]
    config.is_chat_override_allowed = Mock(return_value=True)
    config.get_presets = Mock(return_value=[])
    config.get_effective_preset_name = Mock(return_value="Default")
    modules["helpers.subagents"].get_all_agents_list = Mock(return_value=[])
    modules["initialize"].initialize_agent = Mock()
    path = Path(__file__).resolve().parents[1] / "helpers/integration_commands.py"
    spec = importlib.util.spec_from_file_location("_integration_names_test", path)
    module = importlib.util.module_from_spec(spec)
    monkeypatch.setitem(sys.modules, spec.name, module)
    spec.loader.exec_module(module)
    return module


@pytest.fixture
def context():
    data = {"project": "old", "chat_model_override": {"preset_name": "Old"}}
    return SimpleNamespace(
        id="chat",
        agent0=SimpleNamespace(config=SimpleNamespace(profile="old")),
        get_data=data.get,
        set_data=data.__setitem__,
        is_running=lambda: False,
    )


@pytest.mark.parametrize(
    "name", ["研究", "研究2", "模型 Pro_2", "Café", "Δοκιμή", "123"]
)
def test_project_command_selects_unicode_title(commands, context, name):
    commands.projects.get_active_projects_list.return_value = [
        {"name": "selected", "title": name},
        {"name": "other", "title": "其他"},
    ]
    result = commands.try_handle_command(
        context, f'/project@OurBot "{name}"', integration="telegram"
    )
    assert result == f"Switched project to {name}."
    commands.projects.activate_project.assert_called_once_with("chat", "selected")
    commands.projects.deactivate_project.assert_not_called()


@pytest.mark.parametrize("command", ["model", "config", "preset"])
def test_model_command_selects_distinct_chinese_name(commands, context, command):
    commands.model_config.get_presets.return_value = [
        {"name": "研究"},
        {"name": "写作"},
    ]
    result = commands.try_handle_command(context, f"/{command} 写作")
    assert result == "Switched model preset to 写作."
    assert context.get_data("chat_model_override") == {"preset_name": "写作"}
    commands.save_tmp_chat.assert_called_once_with(context)


@pytest.mark.parametrize("name", ["未知", "!!!", "__--"])
@pytest.mark.parametrize("command", ["project", "model", "agent"])
def test_unmatched_name_does_not_clear_or_select(commands, context, command, name):
    commands.projects.get_active_projects_list.return_value = [
        {"name": "only", "title": "研究"}
    ]
    commands.model_config.get_presets.return_value = [{"name": "研究"}]
    sys.modules["helpers.subagents"].get_all_agents_list.return_value = [
        {"key": "only", "label": "研究"}
    ]
    result = commands.try_handle_command(context, f"/{command} {name}")
    assert "was not found" in result
    commands.projects.activate_project.assert_not_called()
    commands.projects.deactivate_project.assert_not_called()
    commands.save_tmp_chat.assert_not_called()
    sys.modules["initialize"].initialize_agent.assert_not_called()
    assert context.get_data("chat_model_override") == {"preset_name": "Old"}


@pytest.mark.parametrize("query", ["my MODEL-2", "my_model_2", "  My   Model 2  "])
def test_ascii_name_normalization_is_preserved(commands, context, query):
    commands.model_config.get_presets.return_value = [{"name": "My Model 2"}]
    assert (
        commands.try_handle_command(context, f"/model {query}")
        == "Switched model preset to My Model 2."
    )


@pytest.mark.parametrize(
    "names,query", [(["研究一", "研究二"], "研究"), (["a-b", "a_b"], "a b")]
)
def test_ambiguous_names_do_not_change_selection(commands, context, names, query):
    commands.model_config.get_presets.return_value = [{"name": name} for name in names]
    assert "ambiguous" in commands.try_handle_command(context, f"/model {query}")
    commands.save_tmp_chat.assert_not_called()
    assert context.get_data("chat_model_override") == {"preset_name": "Old"}


@pytest.mark.parametrize(
    "command,value",
    [("project", value) for value in ("DEFAULT", "NONE", "CLEAR", "OFF", '""')]
    + [("model", value) for value in ("NONE", "CLEAR", "OFF", "INHERIT", '""')],
)
def test_explicit_clear_commands_remain_supported(commands, context, command, value):
    result = commands.try_handle_command(context, f"/{command} {value}")
    if command == "project":
        assert result == "Cleared the active project."
        commands.projects.deactivate_project.assert_called_once_with("chat")
    else:
        assert result == "Switched back to the scoped model preset: Default."
        assert context.get_data("chat_model_override") is None


@pytest.mark.parametrize(
    "names,query",
    [
        (["研究2", "写作2"], "写作2"),
        (["模型 Pro_2", "其他 Pro_2"], "模型 Pro_2"),
        (["Caf", "Café"], "Café"),
    ],
)
def test_unicode_letters_disambiguate_mixed_names(commands, context, names, query):
    commands.model_config.get_presets.return_value = [{"name": name} for name in names]
    assert (
        commands.try_handle_command(context, f"/model {query}")
        == f"Switched model preset to {query}."
    )
    assert context.get_data("chat_model_override") == {"preset_name": query}


def test_agent_command_selects_chinese_label(commands, context):
    sys.modules["helpers.subagents"].get_all_agents_list.return_value = [
        {"key": "research", "label": "研究"},
        {"key": "writing", "label": "写作"},
    ]
    initialize = sys.modules["initialize"].initialize_agent
    assert (
        commands.try_handle_command(context, "/agent 写作") == "Switched agent to 写作."
    )
    initialize.assert_called_once_with(override_settings={"agent_profile": "writing"})
    assert context.agent0.config is initialize.return_value


def test_empty_normalized_names_never_match_each_other(commands):
    assert commands._match_named_item([{"name": "!!!"}], "???", keys=("name",)) == (
        None,
        [],
    )
