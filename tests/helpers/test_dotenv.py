"""Tests for python/helpers/dotenv.py — load_dotenv, get_dotenv_value, save_dotenv_value, get_dotenv_file_path."""

import sys
from pathlib import Path
from unittest.mock import patch, mock_open

import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from python.helpers import dotenv


class TestGetDotenvFilePath:
    def test_returns_usr_env_path(self):
        with patch("python.helpers.dotenv.get_abs_path") as m:
            m.return_value = "/a0/usr/.env"
            path = dotenv.get_dotenv_file_path()
        m.assert_called_once_with("usr/.env")
        assert path == "/a0/usr/.env"


class TestGetDotenvValue:
    def test_returns_env_value(self):
        with patch.dict("os.environ", {"TEST_KEY_DOTENV": "test_value"}, clear=False):
            assert dotenv.get_dotenv_value("TEST_KEY_DOTENV") == "test_value"

    def test_returns_default_when_missing(self):
        assert dotenv.get_dotenv_value("MISSING_KEY_XYZ_12345", "my_default") == "my_default"


class TestLoadDotenv:
    def test_calls_load_dotenv_with_path(self):
        with patch("python.helpers.dotenv._load_dotenv") as m:
            with patch("python.helpers.dotenv.get_dotenv_file_path", return_value="/usr/.env"):
                dotenv.load_dotenv()
        m.assert_called_once_with("/usr/.env", override=True)


class TestSaveDotenvValue:
    def test_creates_file_if_not_exists(self, tmp_path):
        env_path = tmp_path / ".env"
        with patch("python.helpers.dotenv.get_dotenv_file_path", return_value=str(env_path)):
            with patch("python.helpers.dotenv.load_dotenv"):
                dotenv.save_dotenv_value("NEW_KEY", "new_value")
        content = env_path.read_text()
        assert "NEW_KEY=new_value" in content

    def test_updates_existing_key(self, tmp_path):
        env_path = tmp_path / ".env"
        env_path.write_text("OLD_KEY=old\n")
        with patch("python.helpers.dotenv.get_dotenv_file_path", return_value=str(env_path)):
            with patch("python.helpers.dotenv.load_dotenv"):
                dotenv.save_dotenv_value("OLD_KEY", "updated")
        content = env_path.read_text()
        assert "OLD_KEY=updated" in content

    def test_appends_new_key_if_not_found(self, tmp_path):
        env_path = tmp_path / ".env"
        env_path.write_text("A=1\n")
        with patch("python.helpers.dotenv.get_dotenv_file_path", return_value=str(env_path)):
            with patch("python.helpers.dotenv.load_dotenv"):
                dotenv.save_dotenv_value("B", "2")
        content = env_path.read_text()
        assert "B=2" in content

    def test_converts_none_to_empty_string(self, tmp_path):
        env_path = tmp_path / ".env"
        env_path.write_text("")
        with patch("python.helpers.dotenv.get_dotenv_file_path", return_value=str(env_path)):
            with patch("python.helpers.dotenv.load_dotenv"):
                dotenv.save_dotenv_value("K", None)  # type: ignore
        content = env_path.read_text()
        assert "K=" in content
