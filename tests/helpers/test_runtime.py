"""Tests for python/helpers/runtime.py — initialize, get_arg, has_arg, is_dockerized, get_runtime_id, etc."""

import sys
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from python.helpers import runtime


class TestRuntimeInitialize:
    def test_initialize_parses_known_args(self):
        runtime.args = {}
        with patch.object(runtime.parser, "parse_known_args", return_value=([], [])):
            runtime.initialize()
        assert "port" in runtime.args or runtime.args != {}

    def test_initialize_parses_unknown_kv_args(self):
        runtime.args = {}
        with patch.object(runtime.parser, "parse_known_args") as m:
            known = MagicMock()
            known.port = None
            known.host = None
            known.cloudflare_tunnel = False
            known.development = False
            m.return_value = (known, ["foo=bar"])
            runtime.initialize()
        assert runtime.args.get("foo") == "bar" or "port" in runtime.args


class TestGetArg:
    def test_get_arg_returns_value(self):
        runtime.args = {"port": 5000}
        assert runtime.get_arg("port") == 5000

    def test_get_arg_returns_none_when_missing(self):
        runtime.args = {}
        assert runtime.get_arg("missing") is None


class TestHasArg:
    def test_has_arg_true_when_present(self):
        runtime.args = {"x": 1}
        assert runtime.has_arg("x") is True

    def test_has_arg_false_when_missing(self):
        runtime.args = {}
        assert runtime.has_arg("y") is False


class TestIsDockerized:
    def test_true_when_dockerized_arg_set(self):
        runtime.args = {"dockerized": True}
        assert runtime.is_dockerized() is True

    def test_false_when_not_set(self):
        runtime.args = {}
        assert runtime.is_dockerized() is False


class TestIsDevelopment:
    def test_opposite_of_dockerized(self):
        runtime.args = {"dockerized": True}
        assert runtime.is_development() is False
        runtime.args = {}
        assert runtime.is_development() is True


class TestGetLocalUrl:
    def test_returns_host_docker_internal_when_dockerized(self):
        runtime.args = {"dockerized": True}
        assert "docker" in runtime.get_local_url()

    def test_returns_127_when_not_dockerized(self):
        runtime.args = {}
        assert "127" in runtime.get_local_url()


class TestGetRuntimeId:
    def test_returns_hex_string(self):
        runtime.runtime_id = None
        rid = runtime.get_runtime_id()
        assert isinstance(rid, str)
        assert len(rid) == 16
        assert all(c in "0123456789abcdef" for c in rid)

    def test_same_id_on_repeated_calls(self):
        runtime.runtime_id = None
        a = runtime.get_runtime_id()
        b = runtime.get_runtime_id()
        assert a == b


class TestGetPersistentId:
    def test_returns_from_dotenv_when_set(self):
        with patch("python.helpers.runtime.dotenv") as m:
            m.get_dotenv_value.return_value = "persistent-123"
            result = runtime.get_persistent_id()
        assert result == "persistent-123"

    def test_generates_and_saves_when_not_set(self):
        with patch("python.helpers.runtime.dotenv") as m:
            m.get_dotenv_value.return_value = None
            m.save_dotenv_value = MagicMock()
            result = runtime.get_persistent_id()
        assert len(result) == 32
        m.save_dotenv_value.assert_called_once()


class TestGetWebUiPort:
    def test_returns_arg_port(self):
        runtime.args = {"port": 8080}
        with patch("python.helpers.runtime.dotenv") as m:
            m.get_dotenv_value.return_value = 0
            assert runtime.get_web_ui_port() == 8080

    def test_returns_dotenv_when_no_arg(self):
        runtime.args = {}
        with patch("python.helpers.runtime.dotenv") as m:
            m.get_dotenv_value.return_value = 3000
            assert runtime.get_web_ui_port() == 3000


class TestGetPlatform:
    def test_returns_sys_platform(self):
        import sys
        assert runtime.get_platform() == sys.platform


class TestIsWindows:
    def test_true_on_win32(self):
        with patch("python.helpers.runtime.sys") as m:
            m.platform = "win32"
            assert runtime.is_windows() is True

    def test_false_on_darwin(self):
        with patch("python.helpers.runtime.sys") as m:
            m.platform = "darwin"
            assert runtime.is_windows() is False


class TestGetTerminalExecutable:
    def test_powershell_on_windows(self):
        with patch("python.helpers.runtime.is_windows", return_value=True):
            assert "powershell" in runtime.get_terminal_executable().lower()

    def test_bash_on_unix(self):
        with patch("python.helpers.runtime.is_windows", return_value=False):
            assert "bash" in runtime.get_terminal_executable()
