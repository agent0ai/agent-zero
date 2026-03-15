"""Tests for python/helpers/subagents.py."""

import json
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


# --- SubAgentListItem & SubAgent ---


class TestSubAgentModels:
    def test_sub_agent_list_item_default_title_from_name(self):
        from python.helpers.subagents import SubAgentListItem

        item = SubAgentListItem(name="test_agent", title="")
        assert item.title == "test_agent"

    def test_sub_agent_list_item_preserves_explicit_title(self):
        from python.helpers.subagents import SubAgentListItem

        item = SubAgentListItem(name="test", title="Custom Title")
        assert item.title == "Custom Title"

    def test_sub_agent_extends_list_item_with_prompts(self):
        from python.helpers.subagents import SubAgent

        agent = SubAgent(name="x", prompts={"system": "You are helpful"})
        assert agent.prompts == {"system": "You are helpful"}


# --- _merge_agent_list_items (via get_agents_dict) ---


class TestMergeAgentListItems:
    def test_merge_agent_list_items_override_takes_precedence(self):
        from python.helpers.subagents import SubAgentListItem, _merge_agent_list_items

        base = SubAgentListItem(name="a", title="Base", description="d1")
        override = SubAgentListItem(name="a", title="Override", description="d2")
        merged = _merge_agent_list_items(base, override)
        assert merged.title == "Override"
        assert merged.description == "d2"

    def test_merge_agent_list_items_falls_back_to_base(self):
        from python.helpers.subagents import SubAgentListItem, _merge_agent_list_items

        base = SubAgentListItem(name="a", title="Base", description="d1", path="/base")
        override = SubAgentListItem(name="a", title="", description="", path="")
        merged = _merge_agent_list_items(base, override)
        assert merged.title == "a"
        assert merged.path == "/base"


# --- _merge_origins ---


class TestMergeOrigins:
    def test_merge_origins_concatenates(self):
        from python.helpers.subagents import _merge_origins

        result = _merge_origins(["default"], ["user"])
        assert result == ["default", "user"]


# --- get_agents_dict, get_agents_list ---


class TestGetAgents:
    def test_get_agents_dict_returns_dict_from_dirs(self):
        from python.helpers.subagents import get_agents_dict

        with patch("python.helpers.subagents._get_agents_list_from_dir") as mock_load:
            mock_load.return_value = {}
            result = get_agents_dict()
            assert isinstance(result, dict)
            assert mock_load.call_count >= 2  # default + user

    def test_get_agents_list_returns_list(self):
        from python.helpers.subagents import get_agents_list

        with patch("python.helpers.subagents.get_agents_dict") as mock:
            mock.return_value = {"a": MagicMock(), "b": MagicMock()}
            result = get_agents_list()
            assert isinstance(result, list)
            assert len(result) == 2


# --- load_agent_data ---


class TestLoadAgentData:
    def test_load_agent_data_raises_when_not_found(self):
        from python.helpers.subagents import load_agent_data

        with patch("python.helpers.subagents._load_agent_data_from_dir", return_value=None):
            with pytest.raises(FileNotFoundError, match="not found"):
                load_agent_data("nonexistent_agent")

    def test_load_agent_data_returns_merged_agent(self):
        from python.helpers.subagents import SubAgent, load_agent_data

        default_agent = SubAgent(
            name="test",
            title="Default",
            context="ctx",
            origin=["default"],
            prompts={"sys": "default prompt"},
        )
        with patch("python.helpers.subagents._load_agent_data_from_dir") as mock:
            mock.side_effect = [default_agent, None, None]
            result = load_agent_data("test")
            assert result.name == "test"
            assert result.title == "Default"


# --- save_agent_data ---


class TestSaveAgentData:
    def test_save_agent_data_writes_agent_json(self, tmp_path):
        from python.helpers.subagents import SubAgent, save_agent_data

        agent = SubAgent(
            name="saved",
            title="Saved Agent",
            description="Desc",
            context="Context",
            enabled=True,
            prompts={"system.md": "content"},
        )
        with patch("python.helpers.subagents.files") as mock_files:
            mock_files.get_abs_path = lambda *p: str(tmp_path / "/".join(str(x) for x in p))
            mock_files.write_file = MagicMock()
            mock_files.delete_dir = MagicMock()
            mock_files.safe_file_name = lambda x: x if x.endswith(".md") else x + ".md"
            mock_files.read_text_files_in_dir = MagicMock(return_value={})
            save_agent_data("saved", agent)
            assert mock_files.write_file.called
            call_args = mock_files.write_file.call_args_list[0]
            written = json.loads(call_args[0][1])
            assert written["title"] == "Saved Agent"
            assert written["description"] == "Desc"


# --- delete_agent_data ---


class TestDeleteAgentData:
    def test_delete_agent_data_calls_files_delete_dir(self):
        from python.helpers.subagents import delete_agent_data

        with patch("python.helpers.subagents.files") as mock_files:
            delete_agent_data("agent_name")
            mock_files.delete_dir.assert_called_once()
            call_path = mock_files.delete_dir.call_args[0][0]
            assert "agent_name" in call_path


# --- get_agents_roots ---


class TestGetAgentsRoots:
    def test_get_agents_roots_returns_paths(self):
        from python.helpers.subagents import get_agents_roots

        with patch("python.helpers.subagents.files") as mock_files:
            mock_files.find_existing_paths_by_pattern = MagicMock(return_value=[])
            mock_files.get_abs_path = lambda *p: "/abs/" + "/".join(str(x) for x in p)
            mock_files.deabsolute_path = lambda p: p.replace("/abs/", "")
            with patch("os.path.exists", return_value=True):
                result = get_agents_roots()
                assert isinstance(result, list)


# --- get_default_promp_file_names ---


class TestGetDefaultPromptFileNames:
    def test_get_default_promp_file_names_calls_files_list(self):
        from python.helpers.subagents import get_default_promp_file_names

        with patch("python.helpers.subagents.files") as mock_files:
            mock_files.list_files = MagicMock(return_value=["a.md", "b.md"])
            result = get_default_promp_file_names()
            assert result == ["a.md", "b.md"]
            mock_files.list_files.assert_called_once_with("prompts", filter="*.md")


# --- get_paths ---


class TestGetPaths:
    def test_get_paths_returns_list(self):
        from python.helpers.subagents import get_paths

        with patch("python.helpers.subagents.files") as mock_files:
            mock_files.exists = MagicMock(return_value=True)
            mock_files.get_abs_path = lambda *p: "/" + "/".join(str(x) for x in p)
            result = get_paths(
                None,
                "prompts",
                include_project=False,
                include_user=True,
                include_default=True,
                default_root="/def",
            )
            assert isinstance(result, list)
