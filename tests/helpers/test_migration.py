"""Tests for python/helpers/migration.py — migrate_user_data, _move_dir, _move_file, _migrate_memory."""

import sys
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from python.helpers import migration


class TestMoveDir:
    def test_skips_when_src_not_exists(self):
        with patch("python.helpers.migration.files") as mf:
            mf.exists.side_effect = lambda p: False
            migration._move_dir("tmp/x", "usr/x")
        mf.move_dir.assert_not_called()

    def test_skips_when_dst_exists_and_no_overwrite(self):
        with patch("python.helpers.migration.files") as mf:
            mf.exists.side_effect = lambda p: True
            migration._move_dir("tmp/x", "usr/x", overwrite=False)
        mf.move_dir.assert_not_called()

    def test_moves_when_src_exists_and_dst_not(self):
        with patch("python.helpers.migration.files") as mf:
            mf.exists.side_effect = lambda p: p.startswith("tmp/")
            with patch("python.helpers.migration.PrintStyle"):
                migration._move_dir("tmp/chats", "usr/chats")
        mf.move_dir.assert_called_once_with("tmp/chats", "usr/chats")

    def test_overwrite_deletes_dst_first(self):
        with patch("python.helpers.migration.files") as mf:
            mf.exists.return_value = True
            with patch("python.helpers.migration.PrintStyle"):
                migration._move_dir("tmp/x", "usr/x", overwrite=True)
        mf.delete_dir.assert_called_with("usr/x")
        mf.move_dir.assert_called_once()


class TestMoveFile:
    def test_skips_when_src_not_exists(self):
        with patch("python.helpers.migration.files") as mf:
            mf.exists.side_effect = lambda p: False
            migration._move_file("tmp/x", "usr/x")
        mf.move_file.assert_not_called()

    def test_moves_when_src_exists(self):
        with patch("python.helpers.migration.files") as mf:
            mf.exists.side_effect = lambda p: p == "tmp/settings.json"
            with patch("python.helpers.migration.PrintStyle"):
                migration._move_file("tmp/settings.json", "usr/settings.json")
        mf.move_file.assert_called_once_with("tmp/settings.json", "usr/settings.json")


class TestMigrateMemory:
    def test_moves_embeddings_to_tmp(self):
        with patch("python.helpers.migration.files") as mf:
            mf.get_subdirectories.return_value = ["embeddings"]
            mf.exists.side_effect = lambda p: "memory/embeddings" in p or p == "memory"
            with patch("python.helpers.migration.PrintStyle"):
                migration._migrate_memory()
        mf.move_dir.assert_called()
        calls = [str(c) for c in mf.move_dir.call_args_list]
        assert any("embeddings" in c for c in calls)

    def test_moves_other_subdirs_to_usr_memory(self):
        with patch("python.helpers.migration.files") as mf:
            mf.get_subdirectories.return_value = ["cognee"]
            mf.exists.side_effect = lambda p: True
            with patch("python.helpers.migration.PrintStyle"):
                migration._migrate_memory()
        mf.move_dir.assert_called()
        assert any("usr/memory" in str(c) for c in mf.move_dir.call_args_list)


class TestMigrateUserData:
    def test_calls_move_operations(self):
        with patch("python.helpers.migration.files") as mf:
            mf.exists.return_value = False
            with patch("python.helpers.migration.PrintStyle"):
                with patch("python.helpers.migration._migrate_memory"):
                    with patch("python.helpers.migration._merge_dir_contents"):
                        with patch("python.helpers.migration._cleanup_obsolete"):
                            migration.migrate_user_data()
        assert mf.move_dir.called or mf.move_file.called
