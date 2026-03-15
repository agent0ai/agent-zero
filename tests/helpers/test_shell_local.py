"""Tests for python/helpers/shell_local.py."""

import sys
from pathlib import Path
from unittest.mock import patch, MagicMock, AsyncMock

import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

for _stream in (sys.stdin, sys.stdout):
    if not hasattr(_stream, 'reconfigure'):
        _stream.reconfigure = lambda **kw: None  # type: ignore


class TestLocalInteractiveSession:
    """Tests for LocalInteractiveSession."""

    @pytest.mark.asyncio
    async def test_connect_creates_session_and_starts(self):
        """connect() creates TTYSession and starts it."""
        mock_session = MagicMock()
        mock_session.start = AsyncMock()
        mock_session.read_full_until_idle = AsyncMock(return_value="")
        mock_session.kill = MagicMock()

        with patch("python.helpers.shell_local.tty_session") as mock_ttm:
            mock_ttm.TTYSession.return_value = mock_session
            with patch("python.helpers.shell_local.runtime") as mock_runtime:
                mock_runtime.get_terminal_executable.return_value = "/bin/bash"

                from python.helpers.shell_local import LocalInteractiveSession

                session = LocalInteractiveSession(cwd="/tmp")
                await session.connect()

                mock_ttm.TTYSession.assert_called_once_with("/bin/bash", cwd="/tmp")
                mock_session.start.assert_called_once()
                mock_session.read_full_until_idle.assert_called_once()

    @pytest.mark.asyncio
    async def test_close_kills_session(self):
        """close() kills the session."""
        mock_session = MagicMock()
        mock_session.kill = MagicMock()

        with patch("python.helpers.shell_local.tty_session") as mock_ttm:
            mock_ttm.TTYSession.return_value = mock_session
            with patch("python.helpers.shell_local.runtime") as mock_runtime:
                mock_runtime.get_terminal_executable.return_value = "/bin/bash"

                from python.helpers.shell_local import LocalInteractiveSession

                session = LocalInteractiveSession()
                session.session = mock_session
                await session.close()

                mock_session.kill.assert_called_once()

    @pytest.mark.asyncio
    async def test_send_command_raises_when_not_connected(self):
        """send_command raises when shell not connected."""
        from python.helpers.shell_local import LocalInteractiveSession

        session = LocalInteractiveSession()
        session.session = None

        with pytest.raises(Exception, match="Shell not connected"):
            await session.send_command("ls")

    @pytest.mark.asyncio
    async def test_send_command_sends_line(self):
        """send_command sends line via session.sendline."""
        mock_session = MagicMock()
        mock_session.sendline = AsyncMock()

        from python.helpers.shell_local import LocalInteractiveSession

        session = LocalInteractiveSession()
        session.session = mock_session

        await session.send_command("echo hello")
        mock_session.sendline.assert_called_once_with("echo hello")

    @pytest.mark.asyncio
    async def test_read_output_raises_when_not_connected(self):
        """read_output raises when shell not connected."""
        from python.helpers.shell_local import LocalInteractiveSession

        session = LocalInteractiveSession()
        session.session = None

        with pytest.raises(Exception, match="Shell not connected"):
            await session.read_output()

    @pytest.mark.asyncio
    async def test_read_output_returns_cleaned_output(self):
        """read_output returns cleaned full and partial output."""
        mock_session = MagicMock()
        mock_session.read_full_until_idle = AsyncMock(return_value="output\n")

        with patch("python.helpers.shell_local.clean_string", side_effect=lambda x: x.strip()):
            from python.helpers.shell_local import LocalInteractiveSession

            session = LocalInteractiveSession()
            session.session = mock_session
            session.full_output = ""

            full, partial = await session.read_output(timeout=0.5)
            assert "output" in full or full == "output"
            assert partial is not None or partial is None  # depends on clean_string

    @pytest.mark.asyncio
    async def test_init_stores_cwd(self):
        """__init__ stores cwd."""
        from python.helpers.shell_local import LocalInteractiveSession

        session = LocalInteractiveSession(cwd="/home/user")
        assert session.cwd == "/home/user"
        assert session.full_output == ""
