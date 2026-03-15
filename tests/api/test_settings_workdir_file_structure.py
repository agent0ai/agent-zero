"""Tests for python/api/settings_workdir_file_structure.py — SettingsWorkdirFileStructure API handler."""

import sys
import threading
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from python.api.settings_workdir_file_structure import SettingsWorkdirFileStructure


def _make_handler():
    return SettingsWorkdirFileStructure(app=MagicMock(), thread_lock=threading.Lock())


class TestSettingsWorkdirFileStructure:
    @pytest.mark.asyncio
    async def test_returns_tree_data(self):
        handler = _make_handler()
        abs_path = "/tmp/test"
        tree_str = "usr/\n  data.json\n  settings.json"

        with patch("python.api.settings_workdir_file_structure.files.get_abs_path_development", return_value=abs_path), \
             patch("python.api.settings_workdir_file_structure.file_tree.file_tree", return_value=tree_str):
            result = await handler.process({"workdir_path": "usr"}, MagicMock())

        assert result["data"] == tree_str

    @pytest.mark.asyncio
    async def test_raises_when_workdir_path_empty(self):
        handler = _make_handler()
        with patch("python.api.settings_workdir_file_structure.files.get_abs_path_development", return_value=""):
            with pytest.raises(Exception, match="workdir_path is required"):
                await handler.process({"workdir_path": ""}, MagicMock())

    @pytest.mark.asyncio
    async def test_raises_when_workdir_path_returns_none(self):
        handler = _make_handler()
        with patch("python.api.settings_workdir_file_structure.files.get_abs_path_development", return_value=None):
            with pytest.raises(Exception, match="workdir_path is required"):
                await handler.process({}, MagicMock())

    @pytest.mark.asyncio
    async def test_passes_max_depth_max_files_to_file_tree(self):
        handler = _make_handler()
        with patch("python.api.settings_workdir_file_structure.files.get_abs_path_development", return_value="/tmp"), \
             patch("python.api.settings_workdir_file_structure.file_tree.file_tree") as mock_tree:
            mock_tree.return_value = "tree"
            await handler.process({
                "workdir_path": "usr",
                "workdir_max_depth": 3,
                "workdir_max_files": 100,
                "workdir_max_folders": 50,
                "workdir_max_lines": 500,
                "workdir_gitignore": "*.pyc",
            }, MagicMock())

        mock_tree.assert_called_once()
        call_kwargs = mock_tree.call_args[1]
        assert call_kwargs["max_depth"] == 3
        assert call_kwargs["max_files"] == 100
        assert call_kwargs["max_folders"] == 50
        assert call_kwargs["max_lines"] == 500
        assert call_kwargs["ignore"] == "*.pyc"

    @pytest.mark.asyncio
    async def test_appends_empty_marker_when_no_newline_in_tree(self):
        handler = _make_handler()
        with patch("python.api.settings_workdir_file_structure.files.get_abs_path_development", return_value="/tmp"), \
             patch("python.api.settings_workdir_file_structure.file_tree.file_tree", return_value="single_line"):
            result = await handler.process({"workdir_path": "usr"}, MagicMock())

        assert result["data"] == "single_line\n # Empty"

    def test_get_methods_returns_post_only(self):
        assert SettingsWorkdirFileStructure.get_methods() == ["POST"]
