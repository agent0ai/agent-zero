"""Tests for python/helpers/process.py."""

import sys
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


class TestProcessServer:
    """Tests for process server functions."""

    def test_set_server_stores_server(self):
        """set_server stores the server globally."""
        from python.helpers import process

        process._server = None
        mock_server = MagicMock()
        process.set_server(mock_server)
        assert process.get_server(None) == mock_server
        process._server = None  # reset

    def test_get_server_returns_stored_server(self):
        """get_server returns the stored server."""
        from python.helpers import process

        mock_server = MagicMock()
        process.set_server(mock_server)
        result = process.get_server(None)
        assert result == mock_server
        process._server = None

    def test_stop_server_shuts_down_and_clears(self):
        """stop_server shuts down server and clears reference."""
        from python.helpers import process

        mock_server = MagicMock()
        process.set_server(mock_server)
        process.stop_server()
        mock_server.shutdown.assert_called_once()
        assert process._server is None

    def test_stop_server_noop_when_none(self):
        """stop_server does nothing when server is None."""
        from python.helpers import process

        process._server = None
        process.stop_server()
        # No exception


class TestReload:
    """Tests for reload function."""

    def test_reload_calls_stop_server(self):
        """reload calls stop_server."""
        with patch("python.helpers.process.stop_server") as mock_stop:
            with patch("python.helpers.process.runtime") as mock_runtime:
                mock_runtime.is_dockerized.return_value = False
                with patch("python.helpers.process.restart_process") as mock_restart:
                    from python.helpers.process import reload

                    mock_restart.side_effect = SystemExit
                    with pytest.raises(SystemExit):
                        reload()
                    mock_stop.assert_called_once()

    def test_reload_exits_when_dockerized(self):
        """reload calls exit_process when dockerized."""
        with patch("python.helpers.process.stop_server"):
            with patch("python.helpers.process.runtime") as mock_runtime:
                mock_runtime.is_dockerized.return_value = True
                with patch("python.helpers.process.exit_process") as mock_exit:
                    from python.helpers.process import reload

                    mock_exit.side_effect = SystemExit
                    with pytest.raises(SystemExit):
                        reload()
                    mock_exit.assert_called_once()

    def test_reload_restarts_when_not_dockerized(self):
        """reload calls restart_process when not dockerized."""
        with patch("python.helpers.process.stop_server"):
            with patch("python.helpers.process.runtime") as mock_runtime:
                mock_runtime.is_dockerized.return_value = False
                with patch("python.helpers.process.restart_process") as mock_restart:
                    from python.helpers.process import reload

                    mock_restart.side_effect = SystemExit
                    with pytest.raises(SystemExit):
                        reload()
                    mock_restart.assert_called_once()


class TestRestartProcess:
    """Tests for restart_process."""

    def test_restart_process_calls_execv(self):
        """restart_process uses os.execv with python and argv."""
        with patch("python.helpers.process.os.execv") as mock_execv:
            with patch("python.helpers.process.sys") as mock_sys:
                mock_sys.executable = "/usr/bin/python3"
                mock_sys.argv = ["python", "-m", "app"]
                from python.helpers.process import restart_process

                mock_execv.side_effect = RuntimeError("execv called")
                with pytest.raises(RuntimeError):
                    restart_process()
                mock_execv.assert_called_once()
                args = mock_execv.call_args[0]
                assert args[0] == "/usr/bin/python3"
                assert args[1] == ["python", "-m", "app"]


class TestExitProcess:
    """Tests for exit_process."""

    def test_exit_process_calls_sys_exit(self):
        """exit_process calls sys.exit(0)."""
        with patch("python.helpers.process.sys.exit") as mock_exit:
            from python.helpers.process import exit_process

            mock_exit.side_effect = SystemExit(0)
            with pytest.raises(SystemExit):
                exit_process()
            mock_exit.assert_called_once_with(0)
